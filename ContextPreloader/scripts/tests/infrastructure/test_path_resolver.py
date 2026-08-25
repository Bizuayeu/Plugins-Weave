"""T1.1-T1.2: Path resolver tests."""
import os
import unittest
from pathlib import Path

from scripts.infrastructure.path_resolver import expand_path


class TestExpandPath(unittest.TestCase):
    def test_expand_path_tilde(self) -> None:
        result = expand_path("~/docs/file.txt")
        expected = Path("~").expanduser() / "docs" / "file.txt"
        self.assertEqual(result, expected)

    def test_expand_path_absolute(self) -> None:
        if os.name == "nt":
            result = expand_path("C:/Users/test/file.txt")
            self.assertEqual(result, Path("C:/Users/test/file.txt"))
        else:
            result = expand_path("/home/test/file.txt")
            self.assertEqual(result, Path("/home/test/file.txt"))


if __name__ == "__main__":
    unittest.main()
