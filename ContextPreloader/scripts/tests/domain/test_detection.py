"""T2: Source Kind Detection tests for domain/detection.py"""
import unittest

from scripts.domain.constants import DEFAULT_TEXT_EXTENSIONS
from scripts.domain.detection import (
    detect_source_kind,
    format_file_size,
    get_file_type_label,
    is_url,
)


class TestIsUrl(unittest.TestCase):
    """T1.3-T1.6: URL detection (pure domain logic)."""

    def test_is_url_http(self):
        self.assertTrue(is_url("http://example.com"))

    def test_is_url_https(self):
        self.assertTrue(is_url("https://example.com/path?q=1"))

    def test_is_url_file_path(self):
        self.assertFalse(is_url("C:/Users/test/file.txt"))

    def test_is_url_relative(self):
        self.assertFalse(is_url("./file.txt"))


class TestDetectSourceKind(unittest.TestCase):
    """T2: detect_source_kind() tests."""

    def test_detect_text_by_ext(self):
        result = detect_source_kind("notes.md", DEFAULT_TEXT_EXTENSIONS, "auto")
        self.assertEqual(result, "text")

    def test_detect_binary_by_ext(self):
        result = detect_source_kind("spec.pdf", DEFAULT_TEXT_EXTENSIONS, "auto")
        self.assertEqual(result, "binary")

    def test_detect_unknown_ext(self):
        result = detect_source_kind("data.xyz", DEFAULT_TEXT_EXTENSIONS, "auto")
        self.assertEqual(result, "binary")

    def test_force_text(self):
        result = detect_source_kind("spec.pdf", DEFAULT_TEXT_EXTENSIONS, "text")
        self.assertEqual(result, "text")

    def test_force_binary(self):
        result = detect_source_kind("notes.md", DEFAULT_TEXT_EXTENSIONS, "binary")
        self.assertEqual(result, "binary")

    def test_url_detected(self):
        result = detect_source_kind(
            "https://example.com/api", DEFAULT_TEXT_EXTENSIONS, "auto"
        )
        self.assertEqual(result, "url")


class TestFormatFileSize(unittest.TestCase):
    """T3.1-T3.3: format_file_size() tests."""

    def test_format_size_bytes(self):
        self.assertEqual(format_file_size(500), "500 B")

    def test_format_size_kb(self):
        self.assertEqual(format_file_size(2048), "2.0 KB")

    def test_format_size_mb(self):
        self.assertEqual(format_file_size(5242880), "5.0 MB")


class TestGetFileTypeLabel(unittest.TestCase):
    """T3.4-T3.6: get_file_type_label() tests."""

    def test_file_type_label_pdf(self):
        self.assertEqual(get_file_type_label(".pdf"), "PDF document")

    def test_file_type_label_png(self):
        self.assertEqual(get_file_type_label(".png"), "PNG image")

    def test_file_type_label_unknown(self):
        self.assertEqual(get_file_type_label(".xyz"), "XYZ file")


if __name__ == "__main__":
    unittest.main()
