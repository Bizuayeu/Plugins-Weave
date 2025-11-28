#!/usr/bin/env python3
"""
interfaces/provisional/input_loader.py unit tests
==================================================

Tests for InputLoader.load() JSON parsing functionality.
"""

import json
import unittest
from pathlib import Path

from domain.exceptions import ValidationError
from interfaces.provisional.input_loader import InputLoader


class TestInputLoaderLoadFromString(unittest.TestCase):
    """InputLoader.load() with JSON string input tests"""

    def test_load_valid_list_string(self):
        """Loads valid JSON list string"""
        json_str = '[{"source_file": "a.txt"}, {"source_file": "b.txt"}]'
        result = InputLoader.load(json_str)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["source_file"], "a.txt")

    def test_load_valid_dict_string(self):
        """Loads valid JSON dict with individual_digests key"""
        json_str = '{"individual_digests": [{"source_file": "a.txt"}]}'
        result = InputLoader.load(json_str)
        self.assertEqual(len(result), 1)

    def test_load_empty_list_string(self):
        """Loads empty JSON list"""
        json_str = "[]"
        result = InputLoader.load(json_str)
        self.assertEqual(result, [])

    def test_load_empty_input_raises_error(self):
        """Empty string raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            InputLoader.load("")
        self.assertIn("cannot be empty", str(cm.exception))

    def test_load_whitespace_only_raises_error(self):
        """Whitespace-only string raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            InputLoader.load("   ")
        self.assertIn("cannot be empty", str(cm.exception))

    def test_load_invalid_json_raises_error(self):
        """Invalid JSON raises JSONDecodeError"""
        with self.assertRaises(json.JSONDecodeError):
            InputLoader.load("{not valid json}")

    def test_load_json_without_individual_digests_key(self):
        """JSON dict without individual_digests raises ValidationError"""
        json_str = '{"other_key": "value"}'
        with self.assertRaises(ValidationError) as cm:
            InputLoader.load(json_str)
        self.assertIn("Invalid input format", str(cm.exception))

    def test_load_json_string_not_object(self):
        """JSON primitive string raises ValidationError"""
        json_str = '"just a string"'
        with self.assertRaises(ValidationError):
            InputLoader.load(json_str)

    def test_load_json_number(self):
        """JSON number raises ValidationError"""
        json_str = "123"
        with self.assertRaises(ValidationError):
            InputLoader.load(json_str)


class TestInputLoaderLoadFromFile(unittest.TestCase):
    """InputLoader.load() with file path input tests"""

    def setUp(self):
        """Set up temp directory"""
        import shutil
        import tempfile

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_json_file(self, filename: str, data) -> Path:
        """Helper to create JSON file"""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return file_path

    def test_load_valid_list_file(self):
        """Loads valid JSON list from file"""
        data = [{"source_file": "a.txt"}, {"source_file": "b.txt"}]
        file_path = self._create_json_file("test.json", data)

        result = InputLoader.load(str(file_path))
        self.assertEqual(len(result), 2)

    def test_load_valid_dict_file(self):
        """Loads valid JSON dict from file"""
        data = {"individual_digests": [{"source_file": "a.txt"}]}
        file_path = self._create_json_file("test.json", data)

        result = InputLoader.load(str(file_path))
        self.assertEqual(len(result), 1)

    def test_load_nonexistent_file_parses_as_json(self):
        """Nonexistent file path is parsed as JSON string"""
        # This will fail as invalid JSON, not as file not found
        nonexistent = "/path/to/nonexistent/file.json"
        with self.assertRaises(json.JSONDecodeError):
            InputLoader.load(nonexistent)

    def test_load_empty_file(self):
        """Empty file raises JSONDecodeError"""
        file_path = Path(self.temp_dir) / "empty.json"
        file_path.touch()

        with self.assertRaises(json.JSONDecodeError):
            InputLoader.load(str(file_path))

    def test_load_file_with_invalid_json(self):
        """File with invalid JSON raises JSONDecodeError"""
        file_path = Path(self.temp_dir) / "invalid.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{not valid json}")

        with self.assertRaises(json.JSONDecodeError):
            InputLoader.load(str(file_path))

    def test_load_file_unicode_content(self):
        """Loads file with Unicode content"""
        data = [{"source_file": "日本語ファイル.txt", "content": "コンテンツ"}]
        file_path = self._create_json_file("unicode.json", data)

        result = InputLoader.load(str(file_path))
        self.assertEqual(result[0]["source_file"], "日本語ファイル.txt")


class TestInputLoaderLoadFromFilePath(unittest.TestCase):
    """InputLoader._load_from_file() tests"""

    def setUp(self):
        """Set up temp directory"""
        import tempfile

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_from_file_returns_list(self):
        """_load_from_file returns list when file contains list"""
        file_path = Path(self.temp_dir) / "list.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)

        result = InputLoader._load_from_file(file_path)
        self.assertEqual(result, [1, 2, 3])

    def test_load_from_file_returns_dict(self):
        """_load_from_file returns dict when file contains dict"""
        file_path = Path(self.temp_dir) / "dict.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"key": "value"}, f)

        result = InputLoader._load_from_file(file_path)
        self.assertEqual(result, {"key": "value"})


class TestInputLoaderParseJsonString(unittest.TestCase):
    """InputLoader._parse_json_string() tests"""

    def test_parse_list(self):
        """Parses JSON list string"""
        result = InputLoader._parse_json_string("[1, 2, 3]")
        self.assertEqual(result, [1, 2, 3])

    def test_parse_dict(self):
        """Parses JSON dict string"""
        result = InputLoader._parse_json_string('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_parse_nested_structure(self):
        """Parses nested JSON structure"""
        json_str = '{"list": [1, 2], "nested": {"a": "b"}}'
        result = InputLoader._parse_json_string(json_str)
        self.assertEqual(result["list"], [1, 2])
        self.assertEqual(result["nested"]["a"], "b")

    def test_parse_invalid_raises_error(self):
        """Invalid JSON raises JSONDecodeError"""
        with self.assertRaises(json.JSONDecodeError):
            InputLoader._parse_json_string("{invalid}")


class TestInputLoaderEdgeCases(unittest.TestCase):
    """InputLoader edge case tests"""

    def test_load_with_newlines_in_string(self):
        """Handles JSON string with embedded newlines"""
        json_str = '''[
            {"source_file": "a.txt"},
            {"source_file": "b.txt"}
        ]'''
        result = InputLoader.load(json_str)
        self.assertEqual(len(result), 2)

    def test_load_with_trailing_whitespace(self):
        """Handles JSON string with trailing whitespace"""
        json_str = '[{"source_file": "a.txt"}]   '
        result = InputLoader.load(json_str)
        self.assertEqual(len(result), 1)

    def test_load_with_leading_whitespace(self):
        """Handles JSON string with leading whitespace"""
        json_str = '   [{"source_file": "a.txt"}]'
        result = InputLoader.load(json_str)
        self.assertEqual(len(result), 1)

    def test_load_preserves_data_types(self):
        """Preserves various JSON data types"""
        json_str = '''[{
            "source_file": "a.txt",
            "count": 42,
            "enabled": true,
            "tags": ["a", "b"],
            "metadata": null
        }]'''
        result = InputLoader.load(json_str)
        self.assertEqual(result[0]["count"], 42)
        self.assertTrue(result[0]["enabled"])
        self.assertEqual(result[0]["tags"], ["a", "b"])
        self.assertIsNone(result[0]["metadata"])


if __name__ == "__main__":
    unittest.main()
