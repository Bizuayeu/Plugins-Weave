"""T10: Profile merger tests."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.application.profile_merger import merge_sources
from scripts.domain.exceptions import ConfigError
from scripts.domain.models import Source
from scripts.infrastructure.config_repository import load_profile_sources


class TestMergeSources(unittest.TestCase):
    def test_no_profile_global_only(self) -> None:
        global_sources = [Source(id="a", label="A", path="/a.txt")]
        result = merge_sources(global_sources, None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "a")

    def test_profile_merges(self) -> None:
        global_sources = [Source(id="a", label="A", path="/a.txt")]
        profile_sources = [Source(id="b", label="B", path="/b.txt")]
        result = merge_sources(global_sources, profile_sources)
        self.assertEqual(len(result), 2)
        ids = {s.id for s in result}
        self.assertEqual(ids, {"a", "b"})

    def test_profile_override_by_id(self) -> None:
        global_sources = [Source(id="a", label="Global A", path="/a.txt")]
        profile_sources = [Source(id="a", label="Profile A", path="/a-override.txt")]
        result = merge_sources(global_sources, profile_sources)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, "Profile A")
        self.assertEqual(result[0].path, "/a-override.txt")

    def test_profile_disable_global(self) -> None:
        global_sources = [
            Source(id="a", label="A", path="/a.txt"),
            Source(id="b", label="B", path="/b.txt"),
        ]
        profile_sources = [Source(id="a", label="A", path="/a.txt", enabled=False)]
        result = merge_sources(global_sources, profile_sources)
        enabled = [s for s in result if s.enabled]
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0].id, "b")

    def test_profile_not_found(self) -> None:
        with self.assertRaises(ConfigError):
            load_profile_sources("/nonexistent/profile.json")

    def test_load_profile_sources(self) -> None:
        data = {
            "sources": [
                {"id": "x", "label": "X", "path": "/x.txt"},
                {"id": "y", "label": "Y", "path": "/y.txt"},
            ]
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
        try:
            sources = load_profile_sources(f.name)
            self.assertEqual(len(sources), 2)
            self.assertEqual(sources[0].id, "x")
        finally:
            Path(f.name).unlink()


if __name__ == "__main__":
    unittest.main()
