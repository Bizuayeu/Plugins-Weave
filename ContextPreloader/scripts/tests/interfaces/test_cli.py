"""T11: CLI command tests."""

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.interfaces.cli import (
    cmd_add,
    cmd_list,
    cmd_profiles,
    cmd_remove,
    cmd_status,
    cmd_test,
)


class CLITestBase(unittest.TestCase):
    """Base class with temp config helpers."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = str(Path(self._tmpdir) / "sources.json")
        self._profiles_dir = str(Path(self._tmpdir) / "profiles")
        Path(self._profiles_dir).mkdir(parents=True, exist_ok=True)

        config = {
            "version": "1.0.0",
            "sources": [
                {"id": "a", "label": "A", "path": "/a.txt"},
                {"id": "b", "label": "B", "path": "/b.txt"},
                {"id": "c", "label": "C", "path": "/c.txt"},
            ],
        }
        with Path(self._config_path).open("w", encoding="utf-8") as f:
            json.dump(config, f)

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _reload_config(self) -> dict[str, Any]:
        with Path(self._config_path).open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data


class TestCmdList(CLITestBase):
    def test_cmd_list(self) -> None:
        result = cmd_list(self._config_path, None)
        self.assertEqual(len(result), 3)
        ids = {s["id"] for s in result}
        self.assertEqual(ids, {"a", "b", "c"})


class TestCmdAdd(CLITestBase):
    def test_cmd_add(self) -> None:
        cmd_add(self._config_path, "/d.txt", "D", "auto", None)
        data = self._reload_config()
        self.assertEqual(len(data["sources"]), 4)
        ids = {s["id"] for s in data["sources"]}
        self.assertIn("d", ids)

    def test_cmd_add_url(self) -> None:
        cmd_add(self._config_path, "https://example.com/api", "API Docs", "auto", None)
        data = self._reload_config()
        self.assertEqual(len(data["sources"]), 4)
        added = [s for s in data["sources"] if "example.com" in s["path"]][0]
        self.assertEqual(added["type"], "auto")

    def test_cmd_add_to_profile(self) -> None:
        profile_path = Path(self._profiles_dir) / "test.json"
        with Path(profile_path).open("w", encoding="utf-8") as f:
            json.dump({"sources": []}, f)

        cmd_add(self._config_path, "/e.txt", "E", "auto", str(profile_path))
        with Path(profile_path).open(encoding="utf-8") as f:
            profile_data = json.load(f)
        self.assertEqual(len(profile_data["sources"]), 1)


class TestCmdRemove(CLITestBase):
    def test_cmd_remove(self) -> None:
        cmd_remove(self._config_path, "b", None)
        data = self._reload_config()
        self.assertEqual(len(data["sources"]), 2)
        ids = {s["id"] for s in data["sources"]}
        self.assertNotIn("b", ids)

    def test_cmd_remove_nonexistent(self) -> None:
        with self.assertRaises(ValueError):
            cmd_remove(self._config_path, "nonexistent", None)


class TestCmdTest(CLITestBase):
    def test_cmd_test_all_ok(self) -> None:
        # Create actual files
        for name in ("a", "b", "c"):
            path = Path(self._tmpdir) / f"{name}.txt"
            with Path(path).open("w") as f:
                f.write(f"content {name}")

        config = {
            "version": "1.0.0",
            "sources": [
                {
                    "id": name,
                    "label": name.upper(),
                    "path": str(Path(self._tmpdir) / f"{name}.txt"),
                }
                for name in ("a", "b", "c")
            ],
        }
        with Path(self._config_path).open("w", encoding="utf-8") as f:
            json.dump(config, f)

        results = cmd_test(self._config_path, None)
        self.assertTrue(all(r["status"] == "ok" for r in results))

    def test_cmd_test_missing(self) -> None:
        results = cmd_test(self._config_path, None)
        failed = [r for r in results if r["status"] != "ok"]
        self.assertTrue(len(failed) >= 1)


class TestCmdProfiles(CLITestBase):
    def test_cmd_profiles(self) -> None:
        for name in ("alpha", "beta"):
            with (Path(self._profiles_dir) / f"{name}.json").open("w") as f:
                json.dump({"sources": []}, f)

        result = cmd_profiles(self._profiles_dir)
        self.assertEqual(set(result), {"alpha", "beta"})


class TestCmdStatus(unittest.TestCase):
    def test_cmd_status_returns_all_keys(self) -> None:
        result = cmd_status()
        self.assertIn("ready", result)
        self.assertIn("config", result)
        self.assertIn("hook", result)
        self.assertIn("settings", result)
        self.assertIn("profiles", result)
        self.assertIn("global_sources", result)

    def test_cmd_status_config_exists(self) -> None:
        """Config should exist (we created it during migration)."""
        result = cmd_status()
        self.assertIn("ok", result["config"])
        self.assertIn("path", result["config"])

    def test_cmd_status_hook_exists(self) -> None:
        """Hook should exist (we deployed it during migration)."""
        result = cmd_status()
        self.assertIn("ok", result["hook"])


if __name__ == "__main__":
    unittest.main()
