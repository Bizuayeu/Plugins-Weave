#!/usr/bin/env python3
"""
domain/error_formatter 基本フォーマッタテスト
=============================================

BaseErrorFormatterとカテゴリ別フォーマッタのテスト。
test_error_formatter.py から分割。
"""

import unittest
from pathlib import Path

from domain.error_formatter import (
    BaseErrorFormatter,
    ConfigErrorFormatter,
    DigestErrorFormatter,
    FileErrorFormatter,
    ValidationErrorFormatter,
)

# =============================================================================
# BaseErrorFormatter Tests
# =============================================================================


class TestBaseErrorFormatterInit(unittest.TestCase):
    """BaseErrorFormatter initialization tests"""

    def test_init_with_path(self):
        """Initializes with provided project root"""
        root = Path("/test/project")
        formatter = BaseErrorFormatter(root)
        self.assertEqual(formatter.project_root, root)

    def test_init_with_relative_path(self):
        """Accepts relative path"""
        root = Path("relative/path")
        formatter = BaseErrorFormatter(root)
        self.assertEqual(formatter.project_root, root)


class TestFormatPath(unittest.TestCase):
    """format_path() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.root = Path("/project/root")
        self.formatter = BaseErrorFormatter(self.root)

    def test_relative_to_project_root(self):
        """Path within project root returns relative path"""
        path = Path("/project/root/data/file.txt")
        result = self.formatter.format_path(path)
        # Use os-independent comparison
        self.assertEqual(result, str(Path("data/file.txt")))

    def test_path_outside_project_root(self):
        """Path outside project root returns absolute path"""
        path = Path("/other/location/file.txt")
        result = self.formatter.format_path(path)
        self.assertEqual(result, str(path))

    def test_project_root_itself(self):
        """Project root itself returns empty or '.'"""
        result = self.formatter.format_path(self.root)
        self.assertEqual(result, ".")

    def test_nested_path(self):
        """Deeply nested path returns relative path"""
        path = Path("/project/root/a/b/c/d/file.txt")
        result = self.formatter.format_path(path)
        self.assertEqual(result, str(Path("a/b/c/d/file.txt")))


# =============================================================================
# ConfigErrorFormatter Tests
# =============================================================================


class TestConfigErrorFormatterInvalidLevel(unittest.TestCase):
    """ConfigErrorFormatter.invalid_level() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_without_valid_levels(self):
        """Message without valid levels list"""
        result = self.formatter.invalid_level("xyz")
        self.assertEqual(result, "Invalid level: 'xyz'")

    def test_with_valid_levels(self):
        """Message includes valid levels when provided"""
        result = self.formatter.invalid_level("xyz", ["weekly", "monthly"])
        self.assertIn("Invalid level: 'xyz'", result)
        self.assertIn("Valid levels: weekly, monthly", result)

    def test_with_single_valid_level(self):
        """Message with single valid level"""
        result = self.formatter.invalid_level("bad", ["good"])
        self.assertIn("Valid levels: good", result)

    def test_empty_valid_levels(self):
        """Empty valid levels list behaves like None"""
        result = self.formatter.invalid_level("xyz", [])
        self.assertEqual(result, "Invalid level: 'xyz'")


class TestConfigErrorFormatterUnknownLevel(unittest.TestCase):
    """ConfigErrorFormatter.unknown_level() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic unknown level message"""
        result = self.formatter.unknown_level("bad_level")
        self.assertEqual(result, "Unknown level: 'bad_level'")


class TestConfigErrorFormatterKeyMissing(unittest.TestCase):
    """ConfigErrorFormatter.config_key_missing() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic config key missing message"""
        result = self.formatter.config_key_missing("api_key")
        self.assertEqual(result, "Required configuration key missing: 'api_key'")


class TestConfigErrorFormatterInvalidValue(unittest.TestCase):
    """ConfigErrorFormatter.config_invalid_value() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_with_string_value(self):
        """Message for string actual value"""
        result = self.formatter.config_invalid_value("count", "int", "five")
        self.assertIn("Invalid configuration value for 'count'", result)
        self.assertIn("expected int", result)
        self.assertIn("got str", result)

    def test_with_int_value(self):
        """Message for int actual value"""
        result = self.formatter.config_invalid_value("name", "str", 123)
        self.assertIn("got int", result)

    def test_with_list_value(self):
        """Message for list actual value"""
        result = self.formatter.config_invalid_value("value", "dict", [1, 2])
        self.assertIn("got list", result)


class TestConfigErrorFormatterSectionMissing(unittest.TestCase):
    """ConfigErrorFormatter.config_section_missing() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_basic_section_missing(self):
        """Basic section missing message"""
        result = self.formatter.config_section_missing("paths")
        self.assertEqual(result, "'paths' section missing in config.json")

    def test_with_levels_section(self):
        """Message for levels section"""
        result = self.formatter.config_section_missing("levels")
        self.assertIn("'levels' section missing", result)


class TestConfigErrorFormatterInitializationFailed(unittest.TestCase):
    """ConfigErrorFormatter.initialization_failed() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ConfigErrorFormatter(Path("/root"))

    def test_basic_initialization_failed(self):
        """Basic initialization failure message"""
        error = Exception("Connection refused")
        result = self.formatter.initialization_failed("database", error)
        self.assertIn("Failed to initialize database", result)
        self.assertIn("Connection refused", result)


# =============================================================================
# FileErrorFormatter Tests
# =============================================================================


class TestFileErrorFormatterFileNotFound(unittest.TestCase):
    """FileErrorFormatter.file_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.root = Path("/project")
        self.formatter = FileErrorFormatter(self.root)

    def test_relative_path(self):
        """Message with relative path"""
        path = Path("/project/data/file.txt")
        result = self.formatter.file_not_found(path)
        expected = f"File not found: {Path('data/file.txt')}"
        self.assertEqual(result, expected)

    def test_absolute_path_outside_root(self):
        """Message with absolute path outside root"""
        path = Path("/other/file.txt")
        result = self.formatter.file_not_found(path)
        expected = f"File not found: {path}"
        self.assertEqual(result, expected)


class TestFileErrorFormatterFileAlreadyExists(unittest.TestCase):
    """FileErrorFormatter.file_already_exists() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = FileErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic file already exists message"""
        path = Path("/project/existing.txt")
        result = self.formatter.file_already_exists(path)
        self.assertEqual(result, "File already exists: existing.txt")


class TestFileErrorFormatterFileIOError(unittest.TestCase):
    """FileErrorFormatter.file_io_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = FileErrorFormatter(Path("/project"))

    def test_read_operation(self):
        """Message for read operation"""
        path = Path("/project/file.txt")
        error = IOError("Permission denied")
        result = self.formatter.file_io_error("read", path, error)
        self.assertIn("Failed to read file.txt", result)
        self.assertIn("Permission denied", result)

    def test_write_operation(self):
        """Message for write operation"""
        path = Path("/project/file.txt")
        error = IOError("Disk full")
        result = self.formatter.file_io_error("write", path, error)
        self.assertIn("Failed to write file.txt", result)


class TestFileErrorFormatterDirectoryNotFound(unittest.TestCase):
    """FileErrorFormatter.directory_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = FileErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic directory not found message"""
        path = Path("/project/data/subdir")
        result = self.formatter.directory_not_found(path)
        expected = f"Directory not found: {Path('data/subdir')}"
        self.assertEqual(result, expected)


class TestFileErrorFormatterInvalidJson(unittest.TestCase):
    """FileErrorFormatter.invalid_json() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = FileErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic invalid JSON message"""
        path = Path("/project/config.json")
        error = ValueError("Expecting value: line 1 column 1")
        result = self.formatter.invalid_json(path, error)
        self.assertIn("Invalid JSON in config.json", result)
        self.assertIn("Expecting value", result)


class TestFileErrorFormatterDirectoryCreationFailed(unittest.TestCase):
    """FileErrorFormatter.directory_creation_failed() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = FileErrorFormatter(Path("/project"))

    def test_basic_directory_creation_failed(self):
        """Basic directory creation failure message"""
        path = Path("/project/data/subdir")
        error = OSError("Permission denied")
        result = self.formatter.directory_creation_failed(path, error)
        self.assertIn("Failed to create directory", result)
        self.assertIn("Permission denied", result)


# =============================================================================
# ValidationErrorFormatter Tests
# =============================================================================


class TestValidationErrorFormatterInvalidType(unittest.TestCase):
    """ValidationErrorFormatter.invalid_type() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ValidationErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic invalid type message"""
        result = self.formatter.invalid_type("config.name", "str", 123)
        self.assertEqual(result, "config.name: expected str, got int")

    def test_with_dict(self):
        """Message for dict actual value"""
        result = self.formatter.invalid_type("field", "list", {"key": "value"})
        self.assertIn("got dict", result)

    def test_with_none(self):
        """Message for None actual value"""
        result = self.formatter.invalid_type("field", "str", None)
        self.assertIn("got NoneType", result)


class TestValidationErrorFormatterValidationError(unittest.TestCase):
    """ValidationErrorFormatter.validation_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ValidationErrorFormatter(Path("/root"))

    def test_without_value(self):
        """Message without actual value"""
        result = self.formatter.validation_error("email", "must be valid email")
        self.assertEqual(result, "Validation failed for 'email': must be valid email")

    def test_with_value(self):
        """Message with actual value"""
        result = self.formatter.validation_error("age", "must be positive", -5)
        self.assertIn("Validation failed for 'age'", result)
        self.assertIn("must be positive", result)
        self.assertIn("(got: -5)", result)


class TestValidationErrorFormatterEmptyCollection(unittest.TestCase):
    """ValidationErrorFormatter.empty_collection() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ValidationErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic empty collection message"""
        result = self.formatter.empty_collection("source_files")
        self.assertEqual(result, "source_files cannot be empty")


# =============================================================================
# DigestErrorFormatter Tests
# =============================================================================


class TestDigestErrorFormatterDigestNotFound(unittest.TestCase):
    """DigestErrorFormatter.digest_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = DigestErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic digest not found message"""
        result = self.formatter.digest_not_found("weekly", "W0001")
        self.assertEqual(result, "Digest not found: level='weekly', id='W0001'")


class TestDigestErrorFormatterShadowEmpty(unittest.TestCase):
    """DigestErrorFormatter.shadow_empty() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = DigestErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic shadow empty message"""
        result = self.formatter.shadow_empty("monthly")
        self.assertEqual(result, "Shadow digest for level 'monthly' has no source files")


class TestDigestErrorFormatterCascadeError(unittest.TestCase):
    """DigestErrorFormatter.cascade_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = DigestErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic cascade error message"""
        result = self.formatter.cascade_error("weekly", "monthly", "threshold not met")
        self.assertEqual(result, "Cascade failed from 'weekly' to 'monthly': threshold not met")


if __name__ == "__main__":
    unittest.main()
