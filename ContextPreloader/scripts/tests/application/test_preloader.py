"""T9: Preloader integration tests."""
import os
import tempfile
import unittest
from unittest.mock import patch

from scripts.domain.models import Config, Settings, Source
from scripts.application.preloader import Preloader


class TestPreloader(unittest.TestCase):
    def _create_temp_file(self, content: str, suffix: str = ".txt") -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        return f.name

    def _make_config(self, sources: list[Source]) -> Config:
        return Config(
            version="1.0.0",
            settings=Settings(),
            text_extensions=[".txt", ".md"],
            sources=sources,
        )

    def test_preload_text_only(self):
        p1 = self._create_temp_file("Content A")
        p2 = self._create_temp_file("Content B")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path=p1),
                Source(id="b", label="B", path=p2),
            ])
            result = Preloader(cfg).run()
            self.assertIn("Content A", result)
            self.assertIn("Content B", result)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_preload_mixed(self):
        p1 = self._create_temp_file("Text content")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path=p1),
                Source(id="b", label="B", path="/fake/file.pdf"),
            ])
            result = Preloader(cfg).run()
            self.assertIn("Text content", result)
            self.assertIn("Path:", result)
        finally:
            os.unlink(p1)

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_preload_with_url(self, mock_urlopen):
        from scripts.tests.infrastructure.test_url_fetcher import _mock_response
        mock_urlopen.return_value = _mock_response(
            b"<p>URL content</p>", "text/html"
        )
        p1 = self._create_temp_file("File content")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path=p1),
                Source(id="b", label="B", path="https://example.com"),
            ])
            result = Preloader(cfg).run()
            self.assertIn("File content", result)
            self.assertIn("URL content", result)
        finally:
            os.unlink(p1)

    def test_preload_disabled_skipped(self):
        p1 = self._create_temp_file("Should appear")
        p2 = self._create_temp_file("Should NOT appear")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path=p1),
                Source(id="b", label="B", path=p2, enabled=False),
            ])
            result = Preloader(cfg).run()
            self.assertIn("Should appear", result)
            self.assertNotIn("Should NOT appear", result)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_preload_missing_continues(self):
        p1 = self._create_temp_file("Good content")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path="/nonexistent/file.txt"),
                Source(id="b", label="B", path=p1),
            ])
            result = Preloader(cfg).run()
            self.assertIn("Good content", result)
            self.assertIn("ERROR", result)
        finally:
            os.unlink(p1)

    def test_preload_empty_sources(self):
        cfg = self._make_config([])
        result = Preloader(cfg).run()
        self.assertIn("Summary", result)

    def test_preload_summary_counts(self):
        p1 = self._create_temp_file("A")
        p2 = self._create_temp_file("B")
        try:
            cfg = self._make_config([
                Source(id="a", label="A", path=p1),
                Source(id="b", label="B", path=p2),
                Source(id="c", label="C", path="/fake.pdf"),
            ])
            result = Preloader(cfg).run()
            self.assertIn("2 text", result)
            self.assertIn("1 binary", result)
        finally:
            os.unlink(p1)
            os.unlink(p2)


if __name__ == "__main__":
    unittest.main()
