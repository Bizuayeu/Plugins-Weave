"""T8: Config repository tests."""
import json
import os
import tempfile
import unittest

from scripts.domain.exceptions import ConfigError
from scripts.domain.models import Config
from scripts.infrastructure.config_repository import load_config


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


if __name__ == "__main__":
    unittest.main()
