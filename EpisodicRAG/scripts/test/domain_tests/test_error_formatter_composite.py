#!/usr/bin/env python3
"""
domain/error_formatter CompositeErrorFormatter テスト
=====================================================

CompositeErrorFormatterとモジュールレベル関数のテスト。
test_error_formatter.py から分割。
"""

import unittest
from pathlib import Path

from domain.error_formatter import (
    CompositeErrorFormatter,
    ConfigErrorFormatter,
    DigestErrorFormatter,
    FileErrorFormatter,
    ValidationErrorFormatter,
    get_error_formatter,
    reset_error_formatter,
)

# =============================================================================
# CompositeErrorFormatter Tests
# =============================================================================


class TestCompositeErrorFormatterInit(unittest.TestCase):
    """CompositeErrorFormatter initialization tests"""

    def test_init_creates_category_formatters(self):
        """Initializes with all category formatters"""
        formatter = CompositeErrorFormatter(Path("/root"))
        self.assertIsInstance(formatter.config, ConfigErrorFormatter)
        self.assertIsInstance(formatter.file, FileErrorFormatter)
        self.assertIsInstance(formatter.validation, ValidationErrorFormatter)
        self.assertIsInstance(formatter.digest, DigestErrorFormatter)

    def test_category_formatters_share_project_root(self):
        """All category formatters have same project root"""
        root = Path("/test/project")
        formatter = CompositeErrorFormatter(root)
        self.assertEqual(formatter.config.project_root, root)
        self.assertEqual(formatter.file.project_root, root)
        self.assertEqual(formatter.validation.project_root, root)
        self.assertEqual(formatter.digest.project_root, root)


class TestCompositeErrorFormatterFormatPath(unittest.TestCase):
    """CompositeErrorFormatter.format_path() tests"""

    def test_convenience_method(self):
        """format_path convenience method works"""
        root = Path("/project")
        formatter = CompositeErrorFormatter(root)
        path = Path("/project/data/file.txt")
        result = formatter.format_path(path)
        self.assertEqual(result, str(Path("data/file.txt")))


class TestCompositeErrorFormatterCategoryAccess(unittest.TestCase):
    """CompositeErrorFormatter category access tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = CompositeErrorFormatter(Path("/root"))

    def test_config_category_access(self):
        """Access config methods via category"""
        result = self.formatter.config.invalid_level("xyz")
        self.assertEqual(result, "Invalid level: 'xyz'")

    def test_file_category_access(self):
        """Access file methods via category"""
        path = Path("/root/file.txt")
        result = self.formatter.file.file_not_found(path)
        self.assertEqual(result, "File not found: file.txt")

    def test_validation_category_access(self):
        """Access validation methods via category"""
        result = self.formatter.validation.empty_collection("items")
        self.assertEqual(result, "items cannot be empty")

    def test_digest_category_access(self):
        """Access digest methods via category"""
        result = self.formatter.digest.shadow_empty("weekly")
        self.assertEqual(result, "Shadow digest for level 'weekly' has no source files")


# =============================================================================
# Module-level Function Tests
# =============================================================================


class TestGetErrorFormatter(unittest.TestCase):
    """get_error_formatter() tests"""

    def setUp(self):
        """Reset formatter before each test"""
        reset_error_formatter()

    def tearDown(self):
        """Reset formatter after each test"""
        reset_error_formatter()

    def test_returns_composite_formatter(self):
        """Returns CompositeErrorFormatter instance"""
        formatter = get_error_formatter()
        self.assertIsInstance(formatter, CompositeErrorFormatter)

    def test_with_explicit_root(self):
        """Creates formatter with provided root"""
        root = Path("/explicit/root")
        formatter = get_error_formatter(root)
        self.assertEqual(formatter.project_root, root)

    def test_caches_default_formatter(self):
        """Caches and returns same formatter instance"""
        formatter1 = get_error_formatter()
        formatter2 = get_error_formatter()
        self.assertIs(formatter1, formatter2)

    def test_explicit_root_overrides_cache(self):
        """Explicit root creates new formatter"""
        _ = get_error_formatter()
        root = Path("/new/root")
        formatter2 = get_error_formatter(root)
        self.assertEqual(formatter2.project_root, root)


class TestResetErrorFormatter(unittest.TestCase):
    """reset_error_formatter() tests"""

    def test_resets_cached_formatter(self):
        """Resets the cached formatter"""
        formatter1 = get_error_formatter(Path("/first"))
        reset_error_formatter()
        formatter2 = get_error_formatter(Path("/second"))

        self.assertIsNot(formatter1, formatter2)
        self.assertEqual(formatter2.project_root, Path("/second"))


if __name__ == "__main__":
    unittest.main()
