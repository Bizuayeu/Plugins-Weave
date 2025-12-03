#!/usr/bin/env python3
"""
domain/error_formatter FormatterRegistry テスト
================================================

FormatterRegistry パターン実装のテスト。
- 登録・取得機能
- 動的属性アクセス
- CompositeErrorFormatterとの統合
"""

import unittest
from pathlib import Path

from domain.error_formatter import (
    BaseErrorFormatter,
    CompositeErrorFormatter,
    ConfigErrorFormatter,
    DigestErrorFormatter,
    FileErrorFormatter,
    FormatterRegistry,
    ValidationErrorFormatter,
)

# =============================================================================
# FormatterRegistry Basic Tests
# =============================================================================


class TestFormatterRegistryInit(unittest.TestCase):
    """FormatterRegistry initialization tests"""

    def test_init_with_project_root(self) -> None:
        """Initializes with project root"""
        root = Path("/project")
        registry = FormatterRegistry(root)
        self.assertEqual(registry.project_root, root)

    def test_init_empty_registry(self) -> None:
        """Starts with no registered formatters"""
        registry = FormatterRegistry(Path("/project"))
        self.assertEqual(len(registry), 0)
        self.assertEqual(registry.categories(), [])


class TestFormatterRegistryRegister(unittest.TestCase):
    """FormatterRegistry.register() tests"""

    def setUp(self) -> None:
        """Set up test registry"""
        self.root = Path("/project")
        self.registry = FormatterRegistry(self.root)

    def test_register_formatter(self) -> None:
        """Registers a formatter with category name"""
        formatter = ConfigErrorFormatter(self.root)
        self.registry.register("config", formatter)
        self.assertTrue(self.registry.has("config"))
        self.assertEqual(len(self.registry), 1)

    def test_register_multiple_formatters(self) -> None:
        """Registers multiple formatters"""
        self.registry.register("config", ConfigErrorFormatter(self.root))
        self.registry.register("file", FileErrorFormatter(self.root))
        self.registry.register("validation", ValidationErrorFormatter(self.root))

        self.assertEqual(len(self.registry), 3)
        self.assertEqual(set(self.registry.categories()), {"config", "file", "validation"})

    def test_register_rejects_non_formatter(self) -> None:
        """Rejects non-BaseErrorFormatter objects"""
        with self.assertRaises(TypeError) as ctx:
            self.registry.register("invalid", "not a formatter")  # type: ignore
        self.assertIn("BaseErrorFormatter", str(ctx.exception))

    def test_register_overwrites_existing(self) -> None:
        """Overwrites existing formatter with same category"""
        formatter1 = ConfigErrorFormatter(self.root)
        formatter2 = ConfigErrorFormatter(Path("/other"))

        self.registry.register("config", formatter1)
        self.registry.register("config", formatter2)

        self.assertEqual(len(self.registry), 1)
        self.assertEqual(self.registry.get("config").project_root, Path("/other"))


class TestFormatterRegistryGet(unittest.TestCase):
    """FormatterRegistry.get() tests"""

    def setUp(self) -> None:
        """Set up test registry with formatters"""
        self.root = Path("/project")
        self.registry = FormatterRegistry(self.root)
        self.registry.register("config", ConfigErrorFormatter(self.root))
        self.registry.register("file", FileErrorFormatter(self.root))

    def test_get_registered_formatter(self) -> None:
        """Gets registered formatter by category"""
        formatter = self.registry.get("config")
        self.assertIsInstance(formatter, ConfigErrorFormatter)

    def test_get_raises_for_unknown_category(self) -> None:
        """Raises KeyError for unknown category"""
        with self.assertRaises(KeyError) as ctx:
            self.registry.get("unknown")
        self.assertIn("unknown", str(ctx.exception))
        self.assertIn("config", str(ctx.exception))  # Shows available

    def test_get_or_none_returns_formatter(self) -> None:
        """get_or_none returns formatter when exists"""
        formatter = self.registry.get_or_none("config")
        self.assertIsInstance(formatter, ConfigErrorFormatter)

    def test_get_or_none_returns_none(self) -> None:
        """get_or_none returns None when not exists"""
        result = self.registry.get_or_none("unknown")
        self.assertIsNone(result)


class TestFormatterRegistryDynamicAccess(unittest.TestCase):
    """FormatterRegistry dynamic attribute access tests"""

    def setUp(self) -> None:
        """Set up test registry with formatters"""
        self.root = Path("/project")
        self.registry = FormatterRegistry(self.root)
        self.registry.register("config", ConfigErrorFormatter(self.root))
        self.registry.register("file", FileErrorFormatter(self.root))

    def test_dynamic_attribute_access(self) -> None:
        """Access formatter via attribute: registry.config"""
        formatter = self.registry.config
        self.assertIsInstance(formatter, ConfigErrorFormatter)

    def test_dynamic_access_raises_attribute_error(self) -> None:
        """Raises AttributeError for unknown category"""
        with self.assertRaises(AttributeError) as ctx:
            _ = self.registry.unknown
        self.assertIn("unknown", str(ctx.exception))

    def test_in_operator(self) -> None:
        """'in' operator works for checking categories"""
        self.assertIn("config", self.registry)
        self.assertNotIn("unknown", self.registry)

    def test_private_attribute_access_fails(self) -> None:
        """Private attributes (_name) raise AttributeError normally"""
        with self.assertRaises(AttributeError):
            _ = self.registry._nonexistent


class TestFormatterRegistryUsability(unittest.TestCase):
    """FormatterRegistry practical usage tests"""

    def setUp(self) -> None:
        """Set up test registry with formatters"""
        self.root = Path("/project")
        self.registry = FormatterRegistry(self.root)
        self.registry.register("config", ConfigErrorFormatter(self.root))

    def test_formatter_methods_work(self) -> None:
        """Formatter methods work after retrieval"""
        formatter = self.registry.get("config")
        result = formatter.invalid_level("xyz", ["weekly", "monthly"])
        self.assertEqual(result, "Invalid level: 'xyz'. Valid levels: weekly, monthly")

    def test_dynamic_access_methods_work(self) -> None:
        """Formatter methods work via dynamic access"""
        result = self.registry.config.invalid_level("xyz")
        self.assertEqual(result, "Invalid level: 'xyz'")


# =============================================================================
# CompositeErrorFormatter Registry Integration Tests
# =============================================================================


class TestCompositeErrorFormatterRegistryIntegration(unittest.TestCase):
    """CompositeErrorFormatter registry integration tests"""

    def setUp(self) -> None:
        """Set up test formatter"""
        self.root = Path("/project")
        self.formatter = CompositeErrorFormatter(self.root)

    def test_has_internal_registry(self) -> None:
        """Has internal FormatterRegistry"""
        self.assertIsInstance(self.formatter.registry, FormatterRegistry)

    def test_registry_has_default_formatters(self) -> None:
        """Internal registry has all default formatters"""
        registry = self.formatter.registry
        self.assertEqual(len(registry), 4)
        self.assertTrue(registry.has("config"))
        self.assertTrue(registry.has("file"))
        self.assertTrue(registry.has("validation"))
        self.assertTrue(registry.has("digest"))

    def test_backward_compatible_property_access(self) -> None:
        """Backward compatible property access works"""
        # These are properties that delegate to registry
        self.assertIsInstance(self.formatter.config, ConfigErrorFormatter)
        self.assertIsInstance(self.formatter.file, FileErrorFormatter)
        self.assertIsInstance(self.formatter.validation, ValidationErrorFormatter)
        self.assertIsInstance(self.formatter.digest, DigestErrorFormatter)


class TestCompositeErrorFormatterExtension(unittest.TestCase):
    """CompositeErrorFormatter extension tests"""

    def setUp(self) -> None:
        """Set up test formatter"""
        self.root = Path("/project")
        self.formatter = CompositeErrorFormatter(self.root)

    def test_register_formatter_method(self) -> None:
        """register_formatter adds new category"""
        custom = ConfigErrorFormatter(self.root)  # Using existing class for simplicity
        self.formatter.register_formatter("custom", custom)

        self.assertTrue(self.formatter.has_formatter("custom"))
        self.assertEqual(len(self.formatter.registry), 5)

    def test_get_formatter_method(self) -> None:
        """get_formatter retrieves registered formatter"""
        formatter = self.formatter.get_formatter("config")
        self.assertIsInstance(formatter, ConfigErrorFormatter)

    def test_get_formatter_raises_for_unknown(self) -> None:
        """get_formatter raises KeyError for unknown category"""
        with self.assertRaises(KeyError):
            self.formatter.get_formatter("unknown")

    def test_has_formatter_method(self) -> None:
        """has_formatter checks if category exists"""
        self.assertTrue(self.formatter.has_formatter("config"))
        self.assertFalse(self.formatter.has_formatter("unknown"))


class TestCompositeErrorFormatterCustomFormatter(unittest.TestCase):
    """Tests for adding custom formatters"""

    def test_custom_formatter_accessible_via_registry(self) -> None:
        """Custom formatter accessible via registry"""
        root = Path("/project")
        formatter = CompositeErrorFormatter(root)

        # Create a custom formatter (using FileErrorFormatter as example)
        custom = FileErrorFormatter(root)
        formatter.register_formatter("custom_file", custom)

        # Access via get_formatter
        retrieved = formatter.get_formatter("custom_file")
        self.assertIsInstance(retrieved, FileErrorFormatter)

        # Access via registry
        retrieved2 = formatter.registry.get("custom_file")
        self.assertIs(retrieved, retrieved2)


# =============================================================================
# Import Path Tests
# =============================================================================


class TestFormatterRegistryImports(unittest.TestCase):
    """FormatterRegistry import path tests"""

    def test_import_from_package(self) -> None:
        """Import from domain.error_formatter package"""
        from domain.error_formatter import FormatterRegistry

        self.assertIsNotNone(FormatterRegistry)

    def test_import_from_module(self) -> None:
        """Import from domain.error_formatter.registry module"""
        from domain.error_formatter.registry import FormatterRegistry

        self.assertIsNotNone(FormatterRegistry)


if __name__ == "__main__":
    unittest.main()
