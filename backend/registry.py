"""Central component registry. Versions come only from real inspection/release sources."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ComponentSpec:
    key: str
    name: str
    category: str
    required: bool
    source_repository: str
    licence: str
    minimum_version: str | None = None
    supported_major: int | None = None
    install_method: str | None = None
    package_id: str | None = None
    relationships: list[str] = field(default_factory=list)
    release_provider: str | None = None
    admin_reason: str | None = None


SPECS = [
    ComponentSpec("sentinel_core", "SENTINEL core", "application", True, "https://github.com/", "Project source", install_method="recovery"),
    ComponentSpec("database", "SQLite database", "service", True, "https://www.sqlite.org/", "Public Domain", install_method="builtin", relationships=["sentinel_core"]),
    ComponentSpec("docker_desktop", "Docker Desktop", "container", True, "https://docs.docker.com/desktop/", "Docker Subscription Service Agreement", install_method="winget", package_id="Docker.DockerDesktop", relationships=["wsl2"], release_provider="docker_desktop", admin_reason="Docker Desktop may need to install Windows services, WSL integration and networking components."),
    ComponentSpec("docker_engine", "Docker Engine", "service", True, "https://docs.docker.com/engine/", "Apache-2.0", relationships=["docker_desktop"]),
    ComponentSpec("docker_compose", "Docker Compose", "container", True, "https://github.com/docker/compose", "Apache-2.0", minimum_version="2.20.0", supported_major=2, relationships=["docker_engine"], release_provider="github:docker/compose"),
    ComponentSpec("wsl2", "Windows Subsystem for Linux 2", "windows", True, "https://learn.microsoft.com/windows/wsl/", "Microsoft Windows component", install_method="wsl", relationships=[], admin_reason="Enabling WSL uses Windows optional features and can require an administrator and a restart."),
    ComponentSpec("ollama", "Ollama", "ai", True, "https://github.com/ollama/ollama", "MIT", minimum_version="0.1.0", supported_major=0, install_method="winget", package_id="Ollama.Ollama", release_provider="github:ollama/ollama"),
    ComponentSpec("opencode", "OpenCode", "development", False, "https://github.com/anomalyco/opencode", "MIT", install_method="npm", package_id="@opencode/cli", relationships=["node"], release_provider="npm:@opencode/cli"),
    ComponentSpec("python", "Python runtime", "runtime", True, "https://www.python.org/", "PSF-2.0", minimum_version="3.12.0", supported_major=3, install_method="winget", package_id="Python.Python.3.12", release_provider="python", admin_reason="The selected Python installer can add a shared runtime for all users; a per-user install is preferred where possible."),
    ComponentSpec("node", "Node.js LTS", "runtime", True, "https://nodejs.org/", "MIT", minimum_version="20.0.0", supported_major=20, install_method="winget", package_id="OpenJS.NodeJS.LTS", release_provider="node"),
    ComponentSpec("npm", "npm", "runtime", True, "https://github.com/npm/cli", "Artistic-2.0", relationships=["node"], release_provider="npm:npm"),
    ComponentSpec("git", "Git for Windows", "runtime", True, "https://github.com/git-for-windows/git", "GPL-2.0", minimum_version="2.40.0", supported_major=2, install_method="winget", package_id="Git.Git", release_provider="github:git-for-windows/git"),
    ComponentSpec("security_tools", "Security research tools", "research", False, "https://github.com/vxcontrol/pentagi", "Mixed — review each tool", install_method="deferred", relationships=["docker_engine"]),
]
SPEC_MAP = {spec.key: spec for spec in SPECS}


def spec_dict(spec: ComponentSpec) -> dict[str, Any]:
    return asdict(spec)


def version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){0,3})(?!\d)", value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def compare_versions(left: str | None, right: str | None) -> int | None:
    a, b = version_tuple(left), version_tuple(right)
    if a is None or b is None:
        return None
    length = max(len(a), len(b))
    a += (0,) * (length - len(a))
    b += (0,) * (length - len(b))
    return (a > b) - (a < b)


def is_outdated(installed: str | None, minimum: str | None) -> bool | None:
    if installed is None or minimum is None:
        return None
    comparison = compare_versions(installed, minimum)
    return comparison is not None and comparison < 0


def same_supported_major(installed: str | None, candidate: str | None, supported_major: int | None) -> bool:
    if supported_major is None:
        return True
    current, proposed = version_tuple(installed), version_tuple(candidate)
    if proposed is None or proposed[0] != supported_major:
        return False
    # Missing installations may install the registry's supported generation.
    if current is None:
        return True
    return current[0] == proposed[0]
