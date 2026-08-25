"""T8: Config repository tests."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.domain.exceptions import ConfigError
from scripts.domain.models import Config, Settings, Source
from scripts.infrastructure.config_repository import (
    load_config,
    load_profile_sources,
    save_config,
)


class TestLoadConfig(unittest.TestCase):
    def _write_config(self, data: dict) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
        return f.name

    def test_load_valid_config(self):
        path = self._write_config({
            "version": "1.0.0",
            "settings": {"encoding": "utf-8"},
            "text_extensions": [".txt"],
            "sources": [
                {"id": "a", "label": "A", "path": "/a.txt"}
            ],
        })
        try:
            cfg = load_config(path)
            self.assertIsInstance(cfg, Config)
            self.assertEqual(cfg.version, "1.0.0")
            self.assertEqual(len(cfg.sources), 1)
        finally:
            Path(path).unlink()

    def test_load_missing_config(self):
        with self.assertRaises(ConfigError):
            load_config("/nonexistent/config.json")

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{broken json")
        try:
            with self.assertRaises(ConfigError):
                load_config(f.name)
        finally:
            Path(f.name).unlink()

    def test_load_missing_sources(self):
        path = self._write_config({"version": "1.0.0"})
        try:
            with self.assertRaises(ConfigError):
                load_config(path)
        finally:
            Path(path).unlink()

    def test_default_settings(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.settings.encoding, "utf-8")
            self.assertEqual(cfg.settings.max_lines_per_file, 0)
        finally:
            Path(path).unlink()

    def test_default_text_extensions(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [],
        })
        try:
            cfg = load_config(path)
            self.assertIn(".txt", cfg.text_extensions)
            self.assertIn(".md", cfg.text_extensions)
        finally:
            Path(path).unlink()


    def test_load_config_with_mode(self):
        path = self._write_config({
            "version": "1.0.0",
            "settings": {"mode": "reference"},
            "sources": [],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.settings.mode, "reference")
        finally:
            Path(path).unlink()

    def test_load_config_mode_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.settings.mode, "inline")
        finally:
            Path(path).unlink()

    def test_load_config_with_source_description(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt", "description": "memo"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].description, "memo")
        finally:
            Path(path).unlink()

    def test_load_config_source_description_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].description, "")
        finally:
            Path(path).unlink()

    def test_load_config_with_source_priority(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt", "priority": "critical"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].priority, "critical")
        finally:
            Path(path).unlink()

    def test_load_config_source_priority_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].priority, "normal")
        finally:
            Path(path).unlink()


class TestSaveConfig(unittest.TestCase):
    def test_save_config_includes_mode(self):
        cfg = Config(
            version="1.0.0",
            settings=Settings(mode="reference"),
            text_extensions=[".txt"],
            sources=[],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            pass
        try:
            save_config(f.name, cfg)
            with Path(f.name).open(encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["settings"]["mode"], "reference")
        finally:
            Path(f.name).unlink()

    def test_save_config_includes_description_priority(self):
        cfg = Config(
            version="1.0.0",
            settings=Settings(),
            text_extensions=[".txt"],
            sources=[Source(id="a", label="A", path="/a.txt", description="memo", priority="high")],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            pass
        try:
            save_config(f.name, cfg)
            with Path(f.name).open(encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["sources"][0]["description"], "memo")
            self.assertEqual(data["sources"][0]["priority"], "high")
        finally:
            Path(f.name).unlink()

    def test_save_load_roundtrip(self):
        original = Config(
            version="1.0.0",
            settings=Settings(mode="reference"),
            text_extensions=[".txt", ".md"],
            sources=[
                Source(id="a", label="A", path="/a.txt", description="desc", priority="critical"),
            ],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            pass
        try:
            save_config(f.name, original)
            loaded = load_config(f.name)
            self.assertEqual(loaded.version, original.version)
            self.assertEqual(loaded.settings.mode, original.settings.mode)
            self.assertEqual(loaded.sources[0].description, original.sources[0].description)
            self.assertEqual(loaded.sources[0].priority, original.sources[0].priority)
        finally:
            Path(f.name).unlink()


class TestLoadProfileSources(unittest.TestCase):
    def _write_profile(self, data: dict) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
        return f.name

    def test_load_profile_with_description_priority(self):
        path = self._write_profile({
            "sources": [
                {"id": "a", "label": "A", "path": "/a.txt",
                 "description": "profile desc", "priority": "high"},
            ],
        })
        try:
            sources = load_profile_sources(path)
            self.assertEqual(sources[0].description, "profile desc")
            self.assertEqual(sources[0].priority, "high")
        finally:
            Path(path).unlink()

    def test_load_profile_defaults_description_priority(self):
        path = self._write_profile({
            "sources": [
                {"id": "a", "label": "A", "path": "/a.txt"},
            ],
        })
        try:
            sources = load_profile_sources(path)
            self.assertEqual(sources[0].description, "")
            self.assertEqual(sources[0].priority, "normal")
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
