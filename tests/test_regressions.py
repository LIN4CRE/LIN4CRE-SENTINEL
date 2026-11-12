"""Regression tests for the 2026-11-12 forensic audit fixes.

Each test reproduces the original defect and pins the corrected behaviour, so a
future change cannot silently reintroduce it.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

TEMP = tempfile.TemporaryDirectory()
if "backend.db" in sys.modules:
    # Discovery shares one imported application; keep fixtures on the same
    # isolated database instead of redirecting only the environment.
    from backend.db import BACKUP_DIR, DATA_DIR, DB_PATH

    os.environ["SENTINEL_DATA_DIR"] = str(DATA_DIR)
    os.environ["SENTINEL_DB_PATH"] = str(DB_PATH)
    os.environ["SENTINEL_BACKUP_DIR"] = str(BACKUP_DIR)
else:
    os.environ["SENTINEL_DATA_DIR"] = TEMP.name
    os.environ["SENTINEL_DB_PATH"] = str(Path(TEMP.name) / "test.db")
    os.environ["SENTINEL_BACKUP_DIR"] = str(Path(TEMP.name) / "backups")
os.environ["SENTINEL_DISABLE_MONITOR"] = "1"


def _backend():
    """Import the backend lazily.

    ``test_upgrade`` expects to be the first module to import ``backend.db`` so
    that the isolated database path it configures is the one bound. Importing at
    module scope here would bind it to this module's temp directory during test
    discovery and break that assumption, so the import is deferred.
    """
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient, app


def load_runtime():
    """Import windows/sentinel_runtime.py without adding it to the package path."""
    spec = importlib.util.spec_from_file_location(
        "sentinel_runtime", REPO / "windows" / "sentinel_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApiNotFoundHandlingTests(unittest.TestCase):
    """The core app must answer unknown API paths with JSON, not the SPA shell.

    Regression for: a catch-all route returned the SPA index.html (HTTP 200, HTML)
    for every unknown /api/* path, which masked real API failures — including the
    mobile companion routes, which are served by a separate ASGI application.
    """

    @classmethod
    def setUpClass(cls):
        TestClient, app = _backend()
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_unknown_api_path_returns_json_404(self):
        response = self.client.get("/api/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"].split(";")[0], "application/json")
        payload = response.json()
        self.assertIn("detail", payload)

    def test_unknown_api_subpath_returns_json_404(self):
        response = self.client.get("/api/no/such/subpath")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"].split(";")[0], "application/json")

    def test_mobile_companion_routes_are_not_served_by_the_core_app(self):
        """The mobile app is a separate ASGI app; the core must not return HTML 200."""
        response = self.client.get("/api/mobile/v1/overview")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"].split(";")[0], "application/json")
        self.assertNotIn("<!doctype html", response.text.lower())

    def test_known_api_paths_are_unaffected(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"].split(";")[0], "application/json")

    def test_frontend_routes_still_serve_the_spa(self):
        response = self.client.get("/some/deep/route")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("<!doctype html", response.text.lower())


class ReleaseExtractionSafetyTests(unittest.TestCase):
    """The Windows release installer must not extract outside its destination.

    Regression for: containment used a string ``startswith`` check, so an archive
    entry such as ``LIN4CRE-SENTINEL/../app-evil/escape.txt`` wrote a file to a
    sibling directory.
    """

    def setUp(self):
        self.runtime = load_runtime()
        self._tmp = tempfile.TemporaryDirectory(prefix="sentinel-extract-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.destination = self.root / "app"
        self.destination.mkdir()
        self.sibling = self.root / "app-evil"

    def _extract(self, entries):
        archive = self.root / "release.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            for name, content in entries:
                bundle.writestr(name, content)
        self.runtime.extract_release(archive, self.destination)
        return archive

    def test_sibling_escape_is_refused(self):
        with self.assertRaises(RuntimeError) as caught:
            self._extract([
                ("LIN4CRE-SENTINEL/legit.txt", "ok"),
                ("../app-evil/escape.txt", "PWNED"),
            ])
        self.assertIn("unsafe path", str(caught.exception))
        self.assertFalse((self.sibling / "escape.txt").exists())

    def test_deep_traversal_is_refused(self):
        with self.assertRaises(RuntimeError):
            self._extract([("../..", "x")])
        self.assertFalse(self.root.parent.parent.joinpath("x").exists())

    def test_legit_single_prefix_archive_is_extracted(self):
        # A single common top-level folder is stripped, so its contents land
        # at the destination root.
        self._extract([
            ("LIN4CRE-SENTINEL/legit.txt", "ok"),
            ("LIN4CRE-SENTINEL/windows/SentinelSetup.pyw", "ok"),
        ])
        self.assertTrue((self.destination / "legit.txt").is_file())
        self.assertTrue((self.destination / "windows" / "SentinelSetup.pyw").is_file())

    def test_multi_top_archive_is_extracted(self):
        self._extract([("backend/main.py", "ok"), ("tests/test_regressions.py", "ok")])
        self.assertTrue((self.destination / "backend" / "main.py").is_file())
        self.assertTrue((self.destination / "tests" / "test_regressions.py").is_file())


class CompanionUrlOverrideTests(unittest.TestCase):
    """The SENTINEL_HOST_COMPANION_URL override must be honoured but stay loopback-only.

    Regression for: the Windows setup manager exported the override, but the backend
    ignored it and dialed host.docker.internal:8765, which does not resolve on Windows.
    """

    def setUp(self):
        from backend.host_client import COMPANION_DEFAULT, companion_base

        self.COMPANION_DEFAULT = COMPANION_DEFAULT
        self.companion_base = companion_base
        self._saved = os.environ.pop("SENTINEL_HOST_COMPANION_URL", None)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("SENTINEL_HOST_COMPANION_URL", None)
        else:
            os.environ["SENTINEL_HOST_COMPANION_URL"] = self._saved

    def _override(self, value):
        if value is None:
            os.environ.pop("SENTINEL_HOST_COMPANION_URL", None)
        else:
            os.environ["SENTINEL_HOST_COMPANION_URL"] = value

    def test_loopback_override_is_honoured(self):
        self._override("http://127.0.0.1:8765")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            "http://127.0.0.1:8765",
        )

    def test_localhost_override_is_honoured(self):
        self._override("http://localhost:8765")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            "http://localhost:8765",
        )

    def test_host_docker_internal_override_is_honoured(self):
        self._override("http://host.docker.internal:8765")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            "http://host.docker.internal:8765",
        )

    def test_non_loopback_override_is_rejected(self):
        self._override("http://192.168.1.50:8765")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            self.COMPANION_DEFAULT,
        )

    def test_non_default_port_is_rejected(self):
        self._override("http://127.0.0.1:9000")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            self.COMPANION_DEFAULT,
        )

    def test_https_override_is_rejected(self):
        self._override("https://127.0.0.1:8765")
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            self.COMPANION_DEFAULT,
        )

    def test_operator_setting_beats_environment_override(self):
        self._override("http://127.0.0.1:8765")
        stored = {"host_companion_url": "http://192.168.1.50:8765"}
        self.assertEqual(self.companion_base(stored), "http://192.168.1.50:8765")

    def test_no_override_uses_stored_value(self):
        self._override(None)
        self.assertEqual(
            self.companion_base({"host_companion_url": self.COMPANION_DEFAULT}),
            self.COMPANION_DEFAULT,
        )


if __name__ == "__main__":
    unittest.main()
