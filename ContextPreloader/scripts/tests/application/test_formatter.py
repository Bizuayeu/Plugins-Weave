"""T5: Output formatter tests."""
import unittest

from scripts.application.formatter import (
    format_binary_output,
    format_reference_output,
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


class TestFormatReferenceOutput(unittest.TestCase):
    def test_reference_output_header(self):
        sources = [("C:/path/file.txt", "MyLabel", "A description", "critical")]
        result = format_reference_output(sources)
        self.assertIn("=== ContextPreloader: Session Context ===", result)
        self.assertIn("Read the following files using the Read tool", result)

    def test_reference_output_single_source(self):
        sources = [("C:/path/file.txt", "MyLabel", "A description", "critical")]
        result = format_reference_output(sources)
        self.assertIn("1.", result)
        self.assertIn("[CRITICAL]", result)
        self.assertIn("MyLabel", result)
        self.assertIn("Path: C:/path/file.txt", result)
        self.assertIn("A description", result)

    def test_reference_output_multiple_sources(self):
        sources = [
            ("C:/a.txt", "FileA", "Desc A", "critical"),
            ("C:/b.txt", "FileB", "Desc B", "high"),
            ("C:/c.txt", "FileC", "Desc C", "normal"),
        ]
        result = format_reference_output(sources)
        self.assertIn("1.", result)
        self.assertIn("2.", result)
        self.assertIn("3.", result)
        # Order preserved
        a_pos = result.index("FileA")
        b_pos = result.index("FileB")
        c_pos = result.index("FileC")
        self.assertLess(a_pos, b_pos)
        self.assertLess(b_pos, c_pos)

    def test_reference_output_empty_description(self):
        sources = [("C:/a.txt", "FileA", "", "normal")]
        result = format_reference_output(sources)
        self.assertIn("Path: C:/a.txt", result)
        # With description: label, path, description, separator = 4 lines per entry
        # Without description: label, path, separator = 3 lines per entry
        with_desc = format_reference_output([("C:/a.txt", "FileA", "Has desc", "normal")])
        lines_without = [l for l in result.split("\n") if l.startswith("   ")]
        lines_with = [l for l in with_desc.split("\n") if l.startswith("   ")]
        self.assertEqual(len(lines_without), 1)  # only Path line
        self.assertEqual(len(lines_with), 2)     # Path + description

    def test_reference_output_priority_mapping(self):
        for priority, expected in [
            ("critical", "[CRITICAL]"),
            ("high", "[HIGH]"),
            ("normal", "[NORMAL]"),
            ("low", "[LOW]"),
        ]:
            sources = [("C:/a.txt", "File", "Desc", priority)]
            result = format_reference_output(sources)
            self.assertIn(expected, result, f"Priority '{priority}' should map to '{expected}'")

    def test_reference_output_size_under_2kb(self):
        sources = [
            ("C:/Users/anyth/DEV/homunculus/Weave/Identities/GrandDigest.txt",
             "GrandDigest (Long-term Memory Summary)",
             "8層階層的長期記憶ダイジェスト（週次〜世紀）", "critical"),
            ("C:/Users/anyth/DEV/homunculus/Weave/Identities/ShadowGrandDigest.txt",
             "ShadowGrandDigest (Latest Context)",
             "直近の文脈層、GrandDigestの影", "critical"),
            ("C:/Users/anyth/DEV/homunculus/Weave/Identities/IntentionPad.md",
             "IntentionPad (Session-crossing Short-term Memory)",
             "セッション横断の短期記憶・意図メモ", "high"),
        ]
        result = format_reference_output(sources)
        self.assertLess(len(result.encode("utf-8")), 2048)


if __name__ == "__main__":
    unittest.main()
