#!/usr/bin/env python3
"""
interfaces/provisional/file_manager.py unit tests
==================================================

Tests for ProvisionalFileManager class.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from domain.exceptions import ConfigError
from interfaces.provisional.file_manager import ProvisionalFileManager


class TestProvisionalFileManagerInit(unittest.TestCase):
    """ProvisionalFileManager initialization tests"""

    def test_init_with_config(self) -> None:
        """Init with provided config uses that config"""
        mock_config = MagicMock()
        manager = ProvisionalFileManager(config=mock_config)
        self.assertEqual(manager.config, mock_config)

    def test_init_without_config_creates_default(self) -> None:
        """Init without config creates DigestConfig instance"""
        with patch("interfaces.provisional.file_manager.DigestConfig") as MockConfig:
            mock_instance = MagicMock()
            MockConfig.return_value = mock_instance
            manager = ProvisionalFileManager()
            MockConfig.assert_called_once()
            self.assertEqual(manager.config, mock_instance)


class TestGetCurrentDigestNumber(unittest.TestCase):
    """get_current_digest_number() tests"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        import shutil
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.provisional_dir = Path(self.temp_dir) / "provisional"
        self.provisional_dir.mkdir()

        self.mock_config = MagicMock()
        self.mock_config.get_provisional_dir.return_value = self.provisional_dir

        self.manager = ProvisionalFileManager(config=self.mock_config)

    def tearDown(self) -> None:
        """Clean up temp directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_directory_returns_none(self) -> None:
        """Empty directory returns None"""
        result = self.manager.get_current_digest_number("weekly")
        self.assertIsNone(result)

    def test_with_existing_files_returns_max_number(self) -> None:
        """Returns max number from existing files"""
        (self.provisional_dir / "W0001_Individual.txt").touch()
        (self.provisional_dir / "W0003_Individual.txt").touch()
        (self.provisional_dir / "W0002_Individual.txt").touch()

        result = self.manager.get_current_digest_number("weekly")
        self.assertEqual(result, 3)

    def test_with_single_file(self) -> None:
        """Single file returns that number"""
        (self.provisional_dir / "W0005_Individual.txt").touch()

        result = self.manager.get_current_digest_number("weekly")
        self.assertEqual(result, 5)

    def test_invalid_level_raises_config_error(self) -> None:
        """Invalid level raises ConfigError"""
        with self.assertRaises(ConfigError) as cm:
            self.manager.get_current_digest_number("invalid_level")
        self.assertIn("Invalid level", str(cm.exception))

    def test_monthly_level_prefix(self) -> None:
        """Monthly level uses M prefix"""
        (self.provisional_dir / "M0001_Individual.txt").touch()
        (self.provisional_dir / "M0002_Individual.txt").touch()

        result = self.manager.get_current_digest_number("monthly")
        self.assertEqual(result, 2)

    def test_ignores_non_matching_files(self) -> None:
        """Ignores files that don't match pattern"""
        (self.provisional_dir / "W0001_Individual.txt").touch()
        (self.provisional_dir / "W0002_Other.txt").touch()  # Different suffix
        (self.provisional_dir / "X0003_Individual.txt").touch()  # Different prefix

        result = self.manager.get_current_digest_number("weekly")
        self.assertEqual(result, 1)


class TestLoadExistingProvisional(unittest.TestCase):
    """load_existing_provisional() tests"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        import shutil
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.provisional_dir = Path(self.temp_dir) / "provisional"
        self.provisional_dir.mkdir()

        self.mock_config = MagicMock()
        self.mock_config.get_provisional_dir.return_value = self.provisional_dir

        self.manager = ProvisionalFileManager(config=self.mock_config)

    def tearDown(self) -> None:
        """Clean up temp directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_not_exists_returns_none(self) -> None:
        """Non-existent file returns None"""
        result = self.manager.load_existing_provisional("weekly", 1)
        self.assertIsNone(result)

    def test_loads_existing_file(self) -> None:
        """Loads and parses existing JSON file"""
        file_path = self.provisional_dir / "W0001_Individual.txt"
        data = {"individual_digests": [{"source_file": "a.txt"}]}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = self.manager.load_existing_provisional("weekly", 1)
        self.assertIsNotNone(result)
        self.assertIn("individual_digests", result)
        self.assertEqual(len(result["individual_digests"]), 1)

    def test_invalid_level_raises_config_error(self) -> None:
        """Invalid level raises ConfigError"""
        with self.assertRaises(ConfigError):
            self.manager.load_existing_provisional("invalid", 1)


class TestGetProvisionalPath(unittest.TestCase):
    """get_provisional_path() tests"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.provisional_dir = Path(self.temp_dir) / "provisional"

        self.mock_config = MagicMock()
        self.mock_config.get_provisional_dir.return_value = self.provisional_dir

        self.manager = ProvisionalFileManager(config=self.mock_config)

    def tearDown(self) -> None:
        """Clean up temp directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_returns_correct_path(self) -> None:
        """Returns correct file path"""
        result = self.manager.get_provisional_path("weekly", 1)
        self.assertEqual(result.name, "W0001_Individual.txt")
        self.assertEqual(result.parent, self.provisional_dir)

    def test_creates_directory_if_not_exists(self) -> None:
        """Creates provisional directory if it doesn't exist"""
        self.assertFalse(self.provisional_dir.exists())
        self.manager.get_provisional_path("weekly", 1)
        self.assertTrue(self.provisional_dir.exists())

    def test_monthly_format(self) -> None:
        """Monthly level uses correct format (4 digits)"""
        result = self.manager.get_provisional_path("monthly", 5)
        self.assertEqual(result.name, "M0005_Individual.txt")

    def test_large_number(self) -> None:
        """Handles larger digest numbers"""
        result = self.manager.get_provisional_path("weekly", 9999)
        self.assertEqual(result.name, "W9999_Individual.txt")


class TestGetDigitsForLevel(unittest.TestCase):
    """get_digits_for_level() tests"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        mock_config = MagicMock()
        self.manager = ProvisionalFileManager(config=mock_config)

    def test_weekly_has_4_digits(self) -> None:
        """Weekly level has 4 digits"""
        result = self.manager.get_digits_for_level("weekly")
        self.assertEqual(result, 4)

    def test_monthly_has_4_digits(self) -> None:
        """Monthly level has 4 digits"""
        result = self.manager.get_digits_for_level("monthly")
        self.assertEqual(result, 4)

    def test_quarterly_has_3_digits(self) -> None:
        """Quarterly level has 3 digits"""
        result = self.manager.get_digits_for_level("quarterly")
        self.assertEqual(result, 3)

    def test_annual_has_3_digits(self) -> None:
        """Annual level has 3 digits"""
        result = self.manager.get_digits_for_level("annual")
        self.assertEqual(result, 3)

    def test_invalid_level_raises_error(self) -> None:
        """Invalid level raises ConfigError"""
        with self.assertRaises(ConfigError):
            self.manager.get_digits_for_level("invalid")


class TestGetLevelConfig(unittest.TestCase):
    """_get_level_config() tests"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        mock_config = MagicMock()
        self.manager = ProvisionalFileManager(config=mock_config)

    def test_valid_level_returns_config(self) -> None:
        """Valid level returns config dict"""
        result = self.manager._get_level_config("weekly")
        self.assertIn("prefix", result)
        self.assertIn("digits", result)

    def test_all_valid_levels(self) -> None:
        """All valid levels return config"""
        valid_levels = [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]
        for level in valid_levels:
            with self.subTest(level=level):
                result = self.manager._get_level_config(level)
                self.assertIsNotNone(result)

    def test_invalid_level_raises_config_error(self) -> None:
        """Invalid level raises ConfigError"""
        with self.assertRaises(ConfigError) as cm:
            self.manager._get_level_config("not_a_level")
        self.assertIn("Invalid level", str(cm.exception))
        self.assertIn("not_a_level", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
