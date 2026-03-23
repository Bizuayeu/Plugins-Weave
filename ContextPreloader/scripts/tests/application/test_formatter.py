"""T5: Output formatter tests."""
import unittest

from scripts.application.formatter import (
    format_binary_output,
    format_summary,
    format_text_output,
    format_url_ref_output,
    format_url_text_output,
)


class TestFormatter(unittest.TestCase):
    def test_format_text_output(self):
        result = format_text_output("Notes", "hello")
        self.assertTrue(result.startswith("=== Notes ==="))
        self.assertIn("hello", result)

    def test_format_binary_output(self):
        result = format_binary_output("Spec", "/path/to/spec.pdf", 2097152, ".pdf")
        self.assertIn("=== Spec [PDF document] ===", result)
        self.assertIn("Path:", result)
        self.assertIn("2.0 MB", result)
        self.assertIn("Read tool", result)

    def test_format_url_text_output(self):
        result = format_url_text_output("Docs", "https://example.com", "Hello World")
        self.assertIn("=== Docs [URL] ===", result)
        self.assertIn("Source: https://example.com", result)
        self.assertIn("Hello World", result)

    def test_format_url_ref_output(self):
        result = format_url_ref_output("File", "https://example.com/f.pdf", "application/pdf")
        self.assertIn("=== File [URL] ===", result)
        self.assertIn("Content-Type: application/pdf", result)
        self.assertIn("WebFetch", result)

    def test_format_summary(self):
        result = format_summary(3, 1, 2, 15.0)
        self.assertIn("3 text", result)
        self.assertIn("1 URL", result)
        self.assertIn("2 binary", result)


if __name__ == "__main__":
    unittest.main()
