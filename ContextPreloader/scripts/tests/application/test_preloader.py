"""T9: Preloader integration tests."""

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from scripts.application.preloader import Preloader
from scripts.domain.models import Config, Settings, Source
from scripts.infrastructure.config_repository import load_config, load_profile_sources


class TestPreloader(unittest.TestCase):
    def _create_temp_file(self, content: str, suffix: str = ".txt") -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
        return f.name

    def _make_config(self, sources: list[Source]) -> Config:
        return Config(
            version="1.0.0",
            settings=Settings(),
            text_extensions=[".txt", ".md"],
            sources=sources,
        )

    def test_preload_text_only(self) -> None:
        p1 = self._create_temp_file("Content A")
        p2 = self._create_temp_file("Content B")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path=p1),
                    Source(id="b", label="B", path=p2),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("Content A", result)
            self.assertIn("Content B", result)
        finally:
            Path(p1).unlink()
            Path(p2).unlink()

    def test_preload_mixed(self) -> None:
        p1 = self._create_temp_file("Text content")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path=p1),
                    Source(id="b", label="B", path="/fake/file.pdf"),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("Text content", result)
            self.assertIn("Path:", result)
        finally:
            Path(p1).unlink()

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_preload_with_url(self, mock_urlopen: MagicMock) -> None:
        from scripts.tests.infrastructure.test_url_fetcher import _mock_response

        mock_urlopen.return_value = _mock_response(b"<p>URL content</p>", "text/html")
        p1 = self._create_temp_file("File content")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path=p1),
                    Source(id="b", label="B", path="https://example.com"),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("File content", result)
            self.assertIn("URL content", result)
        finally:
            Path(p1).unlink()

    def test_preload_disabled_skipped(self) -> None:
        p1 = self._create_temp_file("Should appear")
        p2 = self._create_temp_file("Should NOT appear")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path=p1),
                    Source(id="b", label="B", path=p2, enabled=False),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("Should appear", result)
            self.assertNotIn("Should NOT appear", result)
        finally:
            Path(p1).unlink()
            Path(p2).unlink()

    def test_preload_missing_continues(self) -> None:
        p1 = self._create_temp_file("Good content")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path="/nonexistent/file.txt"),
                    Source(id="b", label="B", path=p1),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("Good content", result)
            self.assertIn("ERROR", result)
        finally:
            Path(p1).unlink()

    def test_preload_empty_sources(self) -> None:
        cfg = self._make_config([])
        result = Preloader(cfg).run()
        self.assertIn("Summary", result)

    def test_preload_summary_counts(self) -> None:
        p1 = self._create_temp_file("A")
        p2 = self._create_temp_file("B")
        try:
            cfg = self._make_config(
                [
                    Source(id="a", label="A", path=p1),
                    Source(id="b", label="B", path=p2),
                    Source(id="c", label="C", path="/fake.pdf"),
                ]
            )
            result = Preloader(cfg).run()
            self.assertIn("2 text", result)
            self.assertIn("1 binary", result)
        finally:
            Path(p1).unlink()
            Path(p2).unlink()


class TestPreloaderReferenceMode(unittest.TestCase):
    def _make_config(self, sources: list[Source], mode: str = "reference") -> Config:
        return Config(
            version="1.0.0",
            settings=Settings(mode=mode),
            text_extensions=[".txt", ".md"],
            sources=sources,
        )

    def test_reference_mode_no_file_reading(self) -> None:
        """Reference mode succeeds even with nonexistent files (no I/O)."""
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/nonexistent/file.txt"),
                Source(id="b", label="B", path="/also/missing.md"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("/nonexistent/file.txt", result)
        self.assertIn("/also/missing.md", result)
        self.assertNotIn("ERROR", result)

    def test_reference_mode_contains_paths_and_labels(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="LabelA", path="C:/path/a.txt"),
                Source(id="b", label="LabelB", path="C:/path/b.md"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("LabelA", result)
        self.assertIn("LabelB", result)
        self.assertIn("Path: C:/path/a.txt", result)
        self.assertIn("Path: C:/path/b.md", result)

    def test_reference_mode_contains_header(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/a.txt"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("ContextPreloader: Session Context", result)

    def test_reference_mode_respects_enabled(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="Visible", path="/a.txt"),
                Source(id="b", label="Hidden", path="/b.txt", enabled=False),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("Visible", result)
        self.assertNotIn("Hidden", result)

    def test_reference_mode_includes_description(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/a.txt", description="memo text"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("memo text", result)

    def test_reference_mode_includes_priority(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/a.txt", priority="critical"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertIn("[CRITICAL]", result)

    def test_reference_mode_no_summary(self) -> None:
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/a.txt"),
            ]
        )
        result = Preloader(cfg).run()
        self.assertNotIn("Summary", result)

    @patch("sys.stderr")
    def test_reference_mode_warns_over_threshold(self, mock_stderr: MagicMock) -> None:
        """Output exceeding REFERENCE_OUTPUT_WARNING_BYTES triggers stderr warning."""
        long_desc = "A" * 500
        sources = [
            Source(
                id=f"s{i}",
                label=f"Source{i}",
                path=f"C:/path/file{i}.txt",
                description=long_desc,
                priority="normal",
            )
            for i in range(20)
        ]
        cfg = self._make_config(sources)
        Preloader(cfg).run()
        mock_stderr.write.assert_called()
        warning_text = "".join(
            str(call.args[0]) for call in mock_stderr.write.call_args_list if call.args
        )
        self.assertIn("warning", warning_text.lower())

    @patch("sys.stderr")
    def test_reference_mode_no_warning_under_threshold(
        self, mock_stderr: MagicMock
    ) -> None:
        """Output under threshold does not trigger warning."""
        cfg = self._make_config(
            [
                Source(id="a", label="A", path="/a.txt", description="short"),
            ]
        )
        Preloader(cfg).run()
        warning_text = "".join(
            str(call.args[0]) for call in mock_stderr.write.call_args_list if call.args
        )
        self.assertNotIn("warning", warning_text.lower())

    def test_inline_mode_unchanged(self) -> None:
        """Inline mode regression guard: file content appears in output."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("inline content here")
        try:
            cfg = self._make_config(
                [Source(id="a", label="A", path=f.name)],
                mode="inline",
            )
            result = Preloader(cfg).run()
            self.assertIn("inline content here", result)
        finally:
            Path(f.name).unlink()


class TestPreloaderReferenceIntegration(unittest.TestCase):
    """End-to-end: JSON config -> load_config -> Preloader -> reference output."""

    def _write_json(self, data: dict[str, Any]) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
        return f.name

    def test_reference_e2e_from_config(self) -> None:
        path = self._write_json(
            {
                "version": "1.0.0",
                "settings": {"mode": "reference"},
                "sources": [
                    {
                        "id": "gd",
                        "label": "GrandDigest",
                        "path": "C:/fake/GrandDigest.txt",
                        "description": "Long-term memory",
                        "priority": "critical",
                    },
                    {
                        "id": "ip",
                        "label": "IntentionPad",
                        "path": "C:/fake/IntentionPad.md",
                        "description": "Short-term notes",
                        "priority": "high",
                    },
                ],
            }
        )
        try:
            cfg = load_config(path)
            result = Preloader(cfg).run()
            self.assertIn("ContextPreloader: Session Context", result)
            self.assertIn("[CRITICAL]", result)
            self.assertIn("[HIGH]", result)
            self.assertIn("GrandDigest", result)
            self.assertIn("Path: C:/fake/GrandDigest.txt", result)
            self.assertIn("Long-term memory", result)
            self.assertLess(len(result.encode("utf-8")), 2048)
        finally:
            Path(path).unlink()

    def test_reference_e2e_with_profile(self) -> None:
        config_path = self._write_json(
            {
                "version": "1.0.0",
                "settings": {"mode": "reference"},
                "sources": [],
            }
        )
        profile_path = self._write_json(
            {
                "sources": [
                    {
                        "id": "x",
                        "label": "ProfileSource",
                        "path": "C:/fake/x.txt",
                        "description": "From profile",
                        "priority": "normal",
                    },
                ],
            }
        )
        try:
            cfg = load_config(config_path)
            profile_sources = load_profile_sources(profile_path)
            result = Preloader(cfg, profile_sources).run()
            self.assertIn("ProfileSource", result)
            self.assertIn("From profile", result)
        finally:
            Path(config_path).unlink()
            Path(profile_path).unlink()

    def test_inline_e2e_regression(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as content_file:
            content_file.write("actual file content")
        config_path = self._write_json(
            {
                "version": "1.0.0",
                "sources": [
                    {"id": "a", "label": "A", "path": content_file.name},
                ],
            }
        )
        try:
            cfg = load_config(config_path)
            result = Preloader(cfg).run()
            self.assertIn("actual file content", result)
        finally:
            Path(content_file.name).unlink()
            Path(config_path).unlink()


if __name__ == "__main__":
    unittest.main()
