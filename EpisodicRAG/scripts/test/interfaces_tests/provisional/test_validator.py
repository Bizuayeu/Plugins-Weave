#!/usr/bin/env python3
"""
interfaces/provisional/validator.py unit tests
===============================================

Tests for validate_individual_digest, validate_individual_digests_list,
validate_provisional_structure, and validate_input_format.
"""

import unittest
from unittest.mock import patch

from domain.exceptions import ValidationError
from interfaces.provisional.validator import (
    validate_individual_digest,
    validate_individual_digests_list,
    validate_input_format,
    validate_provisional_structure,
)


class TestValidateIndividualDigest(unittest.TestCase):
    """validate_individual_digest() tests"""

    def test_valid_digest(self):
        """Valid digest with source_file key passes"""
        digest = {"source_file": "test.txt", "content": "test content"}
        # Should not raise
        validate_individual_digest(digest, 0)

    def test_valid_digest_minimal(self):
        """Minimal valid digest with only source_file"""
        digest = {"source_file": "test.txt"}
        validate_individual_digest(digest, 0)

    def test_non_dict_raises_validation_error(self):
        """Non-dict input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest("not a dict", 0)
        self.assertIn("expected dict", str(cm.exception))
        self.assertIn("str", str(cm.exception))

    def test_none_raises_validation_error(self):
        """None input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest(None, 0)
        self.assertIn("expected dict", str(cm.exception))

    def test_list_raises_validation_error(self):
        """List input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest(["item"], 1)
        self.assertIn("expected dict", str(cm.exception))
        self.assertIn("index 1", str(cm.exception))

    def test_missing_source_file_raises_validation_error(self):
        """Dict without source_file raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest({"content": "test"}, 2)
        self.assertIn("missing 'source_file'", str(cm.exception))
        self.assertIn("index 2", str(cm.exception))

    def test_empty_dict_raises_validation_error(self):
        """Empty dict raises ValidationError (missing source_file)"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest({}, 0)
        self.assertIn("missing 'source_file'", str(cm.exception))

    def test_context_included_in_error_message(self):
        """Context string is included in error message"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest("invalid", 0, context="existing")
        self.assertIn("existing", str(cm.exception))

    def test_context_with_missing_key(self):
        """Context included when source_file missing"""
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digest({"other": "value"}, 3, context="new")
        self.assertIn("new", str(cm.exception))
        self.assertIn("index 3", str(cm.exception))


class TestValidateIndividualDigestsList(unittest.TestCase):
    """validate_individual_digests_list() tests"""

    def test_valid_list(self):
        """Valid list of digests passes"""
        digests = [
            {"source_file": "a.txt"},
            {"source_file": "b.txt", "keywords": ["test"]},
        ]
        # Should not raise
        validate_individual_digests_list(digests)

    def test_empty_list_passes(self):
        """Empty list is valid"""
        validate_individual_digests_list([])

    def test_invalid_item_raises_error(self):
        """Invalid item in list raises ValidationError"""
        digests = [
            {"source_file": "a.txt"},
            {"missing_key": "value"},  # Invalid
        ]
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digests_list(digests)
        self.assertIn("index 1", str(cm.exception))

    def test_context_passed_to_validation(self):
        """Context is passed through to individual validation"""
        digests = [{"no_source": "value"}]
        with self.assertRaises(ValidationError) as cm:
            validate_individual_digests_list(digests, context="merged")
        self.assertIn("merged", str(cm.exception))


class TestValidateProvisionalStructure(unittest.TestCase):
    """validate_provisional_structure() tests"""

    def test_valid_structure(self):
        """Valid dict with individual_digests returns list"""
        with patch("infrastructure.log_warning") as mock_log:
            data = {
                "individual_digests": [
                    {"source_file": "a.txt"},
                    {"source_file": "b.txt"},
                ]
            }
            result = validate_provisional_structure(data)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["source_file"], "a.txt")
            mock_log.assert_not_called()

    def test_empty_individual_digests(self):
        """Empty individual_digests returns empty list"""
        with patch("infrastructure.log_warning") as mock_log:
            data = {"individual_digests": []}
            result = validate_provisional_structure(data)
            self.assertEqual(result, [])
            mock_log.assert_not_called()

    def test_non_dict_returns_empty_list(self):
        """Non-dict input returns empty list with warning"""
        with patch("infrastructure.log_warning") as mock_log:
            result = validate_provisional_structure("not a dict")
            self.assertEqual(result, [])
            mock_log.assert_called_once()
            self.assertIn("Invalid existing data format", mock_log.call_args[0][0])

    def test_none_returns_empty_list(self):
        """None input returns empty list with warning"""
        with patch("infrastructure.log_warning") as mock_log:
            result = validate_provisional_structure(None)
            self.assertEqual(result, [])
            mock_log.assert_called_once()

    def test_list_input_returns_empty_list(self):
        """List input (not dict) returns empty list"""
        with patch("infrastructure.log_warning") as mock_log:
            result = validate_provisional_structure([{"source_file": "a.txt"}])
            self.assertEqual(result, [])
            mock_log.assert_called_once()

    def test_missing_individual_digests_key(self):
        """Dict without individual_digests key returns empty list"""
        with patch("infrastructure.log_warning") as mock_log:
            data = {"other_key": "value"}
            result = validate_provisional_structure(data)
            self.assertEqual(result, [])
            # No warning because empty list is returned from .get()
            mock_log.assert_not_called()

    def test_invalid_individual_digests_type(self):
        """Non-list individual_digests returns empty list"""
        with patch("infrastructure.log_warning") as mock_log:
            data = {"individual_digests": "not a list"}
            result = validate_provisional_structure(data)
            self.assertEqual(result, [])
            mock_log.assert_called_once()
            self.assertIn("Invalid individual_digests format", mock_log.call_args[0][0])

    def test_individual_digests_is_none(self):
        """individual_digests=None returns empty list"""
        with patch("infrastructure.log_warning") as mock_log:
            data = {"individual_digests": None}
            result = validate_provisional_structure(data)
            self.assertEqual(result, [])
            mock_log.assert_called_once()


class TestValidateInputFormat(unittest.TestCase):
    """validate_input_format() tests"""

    def test_list_input_returned_directly(self):
        """List input is returned as-is"""
        data = [{"source_file": "a.txt"}, {"source_file": "b.txt"}]
        result = validate_input_format(data)
        self.assertEqual(result, data)

    def test_empty_list_returned(self):
        """Empty list is valid and returned"""
        result = validate_input_format([])
        self.assertEqual(result, [])

    def test_dict_with_individual_digests_key(self):
        """Dict with individual_digests key extracts the list"""
        data = {
            "individual_digests": [{"source_file": "a.txt"}],
            "metadata": "ignored",
        }
        result = validate_input_format(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_file"], "a.txt")

    def test_dict_without_key_raises_error(self):
        """Dict without individual_digests raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_input_format({"other_key": "value"})
        self.assertIn("Invalid input format", str(cm.exception))
        self.assertIn("dict with 'individual_digests' key", str(cm.exception))

    def test_none_raises_error(self):
        """None input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_input_format(None)
        self.assertIn("Invalid input format", str(cm.exception))

    def test_string_raises_error(self):
        """String input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_input_format("invalid")
        self.assertIn("Invalid input format", str(cm.exception))
        self.assertIn("str", str(cm.exception))

    def test_int_raises_error(self):
        """Integer input raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_input_format(123)
        self.assertIn("Invalid input format", str(cm.exception))

    def test_empty_dict_raises_error(self):
        """Empty dict raises ValidationError"""
        with self.assertRaises(ValidationError) as cm:
            validate_input_format({})
        self.assertIn("Invalid input format", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
