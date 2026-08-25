"""T1 (partial): Domain model tests for Source, Settings, Config."""

import unittest

from scripts.domain.models import Config, Settings, Source


class TestSource(unittest.TestCase):
    def test_source_defaults(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt")
        self.assertEqual(s.type, "auto")
        self.assertTrue(s.enabled)

    def test_source_frozen(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt")
        with self.assertRaises(AttributeError):
            s.id = "changed"  # type: ignore[misc]

    def test_source_description_default(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt")
        self.assertEqual(s.description, "")

    def test_source_priority_default(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt")
        self.assertEqual(s.priority, "normal")

    def test_source_description_custom(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt", description="memo")
        self.assertEqual(s.description, "memo")

    def test_source_priority_custom(self) -> None:
        s = Source(id="test", label="Test", path="/tmp/file.txt", priority="critical")
        self.assertEqual(s.priority, "critical")


class TestSettings(unittest.TestCase):
    def test_settings_defaults(self) -> None:
        s = Settings()
        self.assertEqual(s.encoding, "utf-8")
        self.assertEqual(s.max_lines_per_file, 0)
        self.assertTrue(s.show_summary)
        self.assertEqual(s.url_timeout, 10)

    def test_settings_mode_default(self) -> None:
        s = Settings()
        self.assertEqual(s.mode, "inline")

    def test_settings_mode_reference(self) -> None:
        s = Settings(mode="reference")
        self.assertEqual(s.mode, "reference")


class TestConfig(unittest.TestCase):
    def test_config_creation(self) -> None:
        cfg = Config(
            version="1.0.0",
            settings=Settings(),
            text_extensions=[".txt", ".md"],
            sources=[Source(id="a", label="A", path="/a.txt")],
        )
        self.assertEqual(cfg.version, "1.0.0")
        self.assertEqual(len(cfg.sources), 1)


if __name__ == "__main__":
    unittest.main()
