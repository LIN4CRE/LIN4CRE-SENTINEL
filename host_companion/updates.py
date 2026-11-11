from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.registry import SPEC_MAP, compare_versions, same_supported_major, version_tuple

USER_AGENT = "LIN4CRE-SENTINEL-Update-Check/0.2"
TIMEOUT = httpx.Timeout(12.0, connect=5.0)


def checked_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_release(text: str) -> tuple[str, list[str]]:
    lower = text.lower()
    reasons = []
    if re.search(r"\b(security|cve-|vulnerabilit|security fix)\b", lower):
        category = "security"
        reasons.append("The official release notes contain security-related fixes; review the exact CVEs before installing.")
    elif re.search(r"\b(critical|data loss|crash|corruption)\b", lower):
        category = "critical"
        reasons.append("The official release notes mention critical reliability or data-integrity fixes.")
    elif re.search(r"\b(breaking|removed|deprecat|no longer|end of support)\b", lower):
        category = "application"
        reasons.append("The release notes contain possible compatibility or deprecation changes.")
    else:
        category = "application"
        reasons.append("A newer official release is available; review the complete release notes before approval.")
    if re.search(r"\b(breaking change|incompatible)\b", lower):
        reasons.append("Potential breaking changes were detected in the official notes.")
    return category, reasons


def base_update(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "component": component["component"],
        "installed_version": component.get("installed_version"),
        "latest_compatible_version": None,
        "latest_upstream_version": None,
        "update_available": None,
        "category": "application",
        "status": "not_checked",
        "last_checked": checked_at(),
        "release_url": SPEC_MAP[component["component"]].source_repository,
        "release_notes": None,
        "download_size_bytes": None,
        "published_at": None,
        "new_cost_detected": None,
        "cost_note": "SENTINEL adds no charge. Upstream licence, subscription and usage terms must be reviewed before installation.",
        "reasons": [],
        "error": None,
    }


def finalise(component: dict[str, Any], update: dict[str, Any], candidate: str | None, notes: str, url: str, published: str | None = None, size: int | None = None) -> dict[str, Any]:
    update.update({"status": "checked", "latest_upstream_version": candidate, "release_url": url, "release_notes": notes[-16000:] if notes else None, "published_at": published, "download_size_bytes": size})
    if not candidate:
        update["status"] = "no_data"
        update["error"] = "The official source did not provide a usable version"
        return update
    category, reasons = classify_release(notes or "")
    update["category"] = category
    update["reasons"] = reasons
    spec = SPEC_MAP[component["component"]]
    installed = component.get("installed_version")
    if same_supported_major(installed, candidate, spec.supported_major):
        update["latest_compatible_version"] = candidate
    else:
        update["latest_compatible_version"] = None
        update["reasons"].append("This release is outside the currently supported major-version policy and requires a separate compatibility review.")
    comparison = compare_versions(installed, candidate)
    update["update_available"] = comparison is not None and comparison < 0 if installed else None
    if installed and comparison is not None and comparison >= 0:
        update["reasons"] = ["No newer version was detected at the official source at this check time."]
    if re.search(r"\b(subscription|paid plan|pricing|license required|licence required)\b", (notes or "").lower()):
        update["new_cost_detected"] = True
        update["cost_note"] = "The release notes mention pricing or licensing. Manual cost review is required before approval."
    return update


async def github_release(client: httpx.AsyncClient, component: dict[str, Any], provider: str) -> dict[str, Any]:
    update = base_update(component)
    repository = provider.split(":", 1)[1]
    url = f"https://api.github.com/repos/{repository}/releases/latest"
    try:
        response = await client.get(url)
        response.raise_for_status()
        release = response.json()
        candidate = str(release.get("tag_name") or release.get("name") or "").lstrip("v")
        if component["component"] == "git":
            match = re.search(r"v?(\d+\.\d+\.\d+)", str(release.get("tag_name", "")))
            candidate = match.group(1) if match else candidate
        size = None
        assets = release.get("assets") or []
        if assets:
            matching = [asset for asset in assets if os_match(asset.get("name", ""))]
            if matching:
                size = sum(int(asset.get("size") or 0) for asset in matching)
        return finalise(component, update, candidate, release.get("body") or "", release.get("html_url") or url, release.get("published_at"), size)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        update.update({"status": "verification_failed", "error": f"Official release check failed: {type(exc).__name__}"})
        return update


def os_match(filename: str) -> bool:
    lower = filename.lower()
    return any(token in lower for token in ("windows", "win32", "win64", ".exe", ".msi"))


async def npm_release(client: httpx.AsyncClient, component: dict[str, Any], provider: str) -> dict[str, Any]:
    update = base_update(component)
    package = provider.split(":", 1)[1]
    url = f"https://registry.npmjs.org/{package.replace('/', '%2f')}/latest"
    try:
        response = await client.get(url)
        response.raise_for_status()
        release = response.json()
        notes = release.get("description") or "The npm registry provides package metadata but not complete release notes. Follow the source repository link before installation."
        return finalise(component, update, release.get("version"), notes, f"https://www.npmjs.com/package/{package}", None, release.get("dist", {}).get("unpackedSize"))
    except (httpx.HTTPError, ValueError) as exc:
        update.update({"status": "verification_failed", "error": f"npm release check failed: {type(exc).__name__}"})
        return update


async def docker_release(client: httpx.AsyncClient, component: dict[str, Any]) -> dict[str, Any]:
    update = base_update(component)
    url = "https://docs.docker.com/desktop/release-notes.md"
    try:
        response = await client.get(url)
        response.raise_for_status()
        text = response.text
        match = re.search(r"^##\s+(?:Docker Desktop\s+)?v?(\d+\.\d+\.\d+)", text, re.MULTILINE)
        if not match:
            raise ValueError("No release heading found")
        candidate = match.group(1)
        section = text[match.start():]
        next_heading = re.search(r"^##\s+", section[3:], re.MULTILINE)
        notes = section[: next_heading.start() + 3] if next_heading else section[:16000]
        return finalise(component, update, candidate, notes, "https://docs.docker.com/desktop/release-notes/")
    except (httpx.HTTPError, ValueError) as exc:
        update.update({"status": "verification_failed", "error": f"Docker Desktop release check failed: {type(exc).__name__}"})
        return update


async def node_release(client: httpx.AsyncClient, component: dict[str, Any]) -> dict[str, Any]:
    update = base_update(component)
    url = "https://nodejs.org/dist/index.json"
    try:
        response = await client.get(url)
        response.raise_for_status()
        releases = response.json()
        installed_major = (version_tuple(component.get("installed_version")) or (20,))[0]
        compatible = [release for release in releases if release.get("lts") and (version_tuple(release.get("version")) or (0,))[0] == installed_major]
        release = compatible[0] if compatible else None
        if not release:
            raise ValueError("No compatible LTS release found")
        version = str(release["version"]).lstrip("v")
        notes = f"Official Node.js distribution index reports this LTS release. npm: {release.get('npm') or 'not specified'}. Review the linked Node.js release notes before installation."
        return finalise(component, update, version, notes, f"https://nodejs.org/en/blog/release/v{version}", release.get("date"))
    except (httpx.HTTPError, ValueError, IndexError) as exc:
        update.update({"status": "verification_failed", "error": f"Node.js release check failed: {type(exc).__name__}"})
        return update


async def python_release(client: httpx.AsyncClient, component: dict[str, Any]) -> dict[str, Any]:
    update = base_update(component)
    url = "https://www.python.org/ftp/python/"
    try:
        response = await client.get(url)
        response.raise_for_status()
        current = version_tuple(component.get("installed_version")) or (3, 12, 0)
        versions = set(re.findall(r'href="(3\.\d+\.\d+)/"', response.text))
        compatible = [version for version in versions if version_tuple(version)[:2] == current[:2]]
        if not compatible:
            raise ValueError("No compatible Python bugfix release found")
        candidate = sorted(compatible, key=lambda value: version_tuple(value) or (0,))[-1]
        notes = "Official Python FTP index lists this bugfix release in the currently installed feature series. Review the official release page and installer hashes before installation."
        return finalise(component, update, candidate, notes, f"https://www.python.org/downloads/release/python-{candidate.replace('.', '')}/")
    except (httpx.HTTPError, ValueError) as exc:
        update.update({"status": "verification_failed", "error": f"Python release check failed: {type(exc).__name__}"})
        return update


async def check_updates(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}, timeout=TIMEOUT, follow_redirects=True) as client:
        for component in components:
            spec = SPEC_MAP.get(component.get("component"))
            if not spec or not spec.release_provider:
                continue
            provider = spec.release_provider
            if provider.startswith("github:"):
                result = await github_release(client, component, provider)
            elif provider.startswith("npm:"):
                result = await npm_release(client, component, provider)
            elif provider == "docker_desktop":
                result = await docker_release(client, component)
            elif provider == "node":
                result = await node_release(client, component)
            elif provider == "python":
                result = await python_release(client, component)
            else:
                continue
            results.append(result)
    return results


async def check_model_updates(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, follow_redirects=True) as client:
        for model in models:
            name = model.get("name") or ""
            repository, _, tag = name.partition(":")
            tag = tag or "latest"
            if "/" not in repository:
                repository = f"library/{repository}"
            url = f"https://registry.ollama.ai/v2/{repository}/manifests/{tag}"
            result = {"name": name, "installed_digest": model.get("digest"), "remote_digest": None, "update_available": None, "download_size_bytes": None, "status": "not_checked", "last_checked": checked_at(), "error": None}
            try:
                response = await client.get(url, headers={"Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json"})
                response.raise_for_status()
                result["remote_digest"] = response.headers.get("Docker-Content-Digest")
                payload = response.json()
                layers = payload.get("layers") or []
                result["download_size_bytes"] = sum(int(layer.get("size") or 0) for layer in layers) or None
                if result["remote_digest"] and result["installed_digest"]:
                    result["update_available"] = result["remote_digest"] != result["installed_digest"]
                    result["status"] = "checked"
                else:
                    result["status"] = "no_data"
                    result["error"] = "A local or remote digest was unavailable, so an update cannot be asserted"
            except (httpx.HTTPError, ValueError) as exc:
                result["status"] = "verification_failed"
                result["error"] = f"Official Ollama registry check failed: {type(exc).__name__}"
            results.append(result)
    return results
