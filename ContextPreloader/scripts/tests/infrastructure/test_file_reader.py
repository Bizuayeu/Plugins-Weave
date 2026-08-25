"""T4: File reader tests."""
import tempfile
import unittest
from pathlib import Path

from scripts.domain.exceptions import SourceError
from scripts.infrastructure.file_reader import read_text_file


class TestReadTextFile(unittest.TestCase):
    def test_read_ascii_text(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Hello World")
            f.flush()
            path = f.name
        try:
            result = read_text_file(path, "utf-8", 0)
            self.assertEqual(result, "Hello World")
        finally:
            Path(path).unlink()

    def test_read_utf8_japanese(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("日本語テスト\n二行目")
            f.flush()
            path = f.name
        try:
            result = read_text_file(path, "utf-8", 0)
            self.assertIn("日本語テスト", result)
            self.assertIn("二行目", result)
        finally:
            Path(path).unlink()

    def test_read_with_max_lines(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for i in range(100):
                f.write(f"Line {i}\n")
            f.flush()
            path = f.name
        try:
            result = read_text_file(path, "utf-8", 10)
            lines = result.strip().split("\n")
            self.assertEqual(len(lines), 11)  # 10 lines + truncated notice
            self.assertIn("truncated", lines[-1].lower())
        finally:
            Path(path).unlink()

    def test_read_max_lines_zero(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for i in range(100):
                f.write(f"Line {i}\n")
            f.flush()
            path = f.name
        try:
            result = read_text_file(path, "utf-8", 0)
            lines = result.strip().split("\n")
            self.assertEqual(len(lines), 100)
        finally:
            Path(path).unlink()

    def test_read_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.flush()
            path = f.name
        try:
            result = read_text_file(path, "utf-8", 0)
            self.assertEqual(result, "")
        finally:
            Path(path).unlink()

    def test_read_missing_file(self) -> None:
        with self.assertRaises(SourceError):
            read_text_file("/nonexistent/path/file.txt", "utf-8", 0)


if __name__ == "__main__":
    unittest.main()
