"""T8: Config repository tests."""
import json
import os
import tempfile
import unittest

from scripts.domain.exceptions import ConfigError
from scripts.domain.models import Config, Settings, Source
from scripts.infrastructure.config_repository import (
    load_config,
    load_profile_sources,
    save_config,
)


class TestLoadConfig(unittest.TestCase):
    def _write_config(self, data: dict) -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(data, f)
        f.close()
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
            os.unlink(path)

    def test_load_missing_config(self):
        with self.assertRaises(ConfigError):
            load_config("/nonexistent/config.json")

    def test_load_invalid_json(self):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        f.write("{broken json")
        f.close()
        try:
            with self.assertRaises(ConfigError):
                load_config(f.name)
        finally:
            os.unlink(f.name)

    def test_load_missing_sources(self):
        path = self._write_config({"version": "1.0.0"})
        try:
            with self.assertRaises(ConfigError):
                load_config(path)
        finally:
            os.unlink(path)

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
            os.unlink(path)

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
            os.unlink(path)


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
            os.unlink(path)

    def test_load_config_mode_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.settings.mode, "inline")
        finally:
            os.unlink(path)

    def test_load_config_with_source_description(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt", "description": "memo"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].description, "memo")
        finally:
            os.unlink(path)

    def test_load_config_source_description_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].description, "")
        finally:
            os.unlink(path)

    def test_load_config_with_source_priority(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt", "priority": "critical"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].priority, "critical")
        finally:
            os.unlink(path)

    def test_load_config_source_priority_default(self):
        path = self._write_config({
            "version": "1.0.0",
            "sources": [{"id": "a", "label": "A", "path": "/a.txt"}],
        })
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.sources[0].priority, "normal")
        finally:
            os.unlink(path)


class TestSaveConfig(unittest.TestCase):
    def test_save_config_includes_mode(self):
        cfg = Config(
            version="1.0.0",
            settings=Settings(mode="reference"),
            text_extensions=[".txt"],
            sources=[],
        )
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        f.close()
        try:
            save_config(f.name, cfg)
            with open(f.name, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["settings"]["mode"], "reference")
        finally:
            os.unlink(f.name)

    def test_save_config_includes_description_priority(self):
        cfg = Config(
            version="1.0.0",
            settings=Settings(),
            text_extensions=[".txt"],
            sources=[Source(id="a", label="A", path="/a.txt", description="memo", priority="high")],
        )
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        f.close()
        try:
            save_config(f.name, cfg)
            with open(f.name, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["sources"][0]["description"], "memo")
            self.assertEqual(data["sources"][0]["priority"], "high")
        finally:
            os.unlink(f.name)

    def test_save_load_roundtrip(self):
        original = Config(
            version="1.0.0",
            settings=Settings(mode="reference"),
            text_extensions=[".txt", ".md"],
            sources=[
                Source(id="a", label="A", path="/a.txt", description="desc", priority="critical"),
            ],
        )
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        f.close()
        try:
            save_config(f.name, original)
            loaded = load_config(f.name)
            self.assertEqual(loaded.version, original.version)
            self.assertEqual(loaded.settings.mode, original.settings.mode)
            self.assertEqual(loaded.sources[0].description, original.sources[0].description)
            self.assertEqual(loaded.sources[0].priority, original.sources[0].priority)
        finally:
            os.unlink(f.name)


class TestLoadProfileSources(unittest.TestCase):
    def _write_profile(self, data: dict) -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(data, f)
        f.close()
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
            os.unlink(path)

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
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
