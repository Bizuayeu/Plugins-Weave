#!/usr/bin/env python3
"""
interfaces/provisional/merger.py unit tests
============================================

Tests for DigestMerger.merge() deduplication and merging logic.
"""

import unittest

from domain.exceptions import ValidationError
from interfaces.provisional.merger import DigestMerger


class TestDigestMergerMerge(unittest.TestCase):
    """DigestMerger.merge() tests"""

    def test_merge_empty_lists(self):
        """Merging two empty lists returns empty list"""
        result = DigestMerger.merge([], [])
        self.assertEqual(result, [])

    def test_merge_empty_existing_with_new(self):
        """Merging empty existing with new items returns new items"""
        new_digests = [
            {"source_file": "a.txt", "content": "a"},
            {"source_file": "b.txt", "content": "b"},
        ]
        result = DigestMerger.merge([], new_digests)
        self.assertEqual(len(result), 2)
        source_files = {d["source_file"] for d in result}
        self.assertEqual(source_files, {"a.txt", "b.txt"})

    def test_merge_existing_with_empty_new(self):
        """Merging existing with empty new returns existing items"""
        existing_digests = [
            {"source_file": "a.txt", "content": "a"},
            {"source_file": "b.txt", "content": "b"},
        ]
        result = DigestMerger.merge(existing_digests, [])
        self.assertEqual(len(result), 2)

    def test_merge_no_overlap(self):
        """Merging non-overlapping lists returns combined items"""
        existing = [{"source_file": "a.txt"}]
        new = [{"source_file": "b.txt"}]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 2)
        source_files = {d["source_file"] for d in result}
        self.assertEqual(source_files, {"a.txt", "b.txt"})

    def test_merge_with_overlap_new_overwrites(self):
        """When source_file overlaps, new digest overwrites existing"""
        existing = [{"source_file": "a.txt", "content": "old"}]
        new = [{"source_file": "a.txt", "content": "new"}]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["content"], "new")

    def test_merge_partial_overlap(self):
        """Partial overlap: some overwritten, some added"""
        existing = [
            {"source_file": "a.txt", "content": "old_a"},
            {"source_file": "b.txt", "content": "old_b"},
        ]
        new = [
            {"source_file": "b.txt", "content": "new_b"},
            {"source_file": "c.txt", "content": "new_c"},
        ]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 3)

        result_dict = {d["source_file"]: d for d in result}
        self.assertEqual(result_dict["a.txt"]["content"], "old_a")
        self.assertEqual(result_dict["b.txt"]["content"], "new_b")
        self.assertEqual(result_dict["c.txt"]["content"], "new_c")

    def test_merge_multiple_overlaps(self):
        """Multiple overlapping items all get overwritten"""
        existing = [
            {"source_file": "a.txt", "content": "old_a"},
            {"source_file": "b.txt", "content": "old_b"},
        ]
        new = [
            {"source_file": "a.txt", "content": "new_a"},
            {"source_file": "b.txt", "content": "new_b"},
        ]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 2)

        result_dict = {d["source_file"]: d for d in result}
        self.assertEqual(result_dict["a.txt"]["content"], "new_a")
        self.assertEqual(result_dict["b.txt"]["content"], "new_b")

    def test_missing_source_file_in_existing_raises_error(self):
        """Missing source_file in existing digests raises ValidationError"""
        existing = [{"missing_key": "value"}]
        new = [{"source_file": "a.txt"}]
        with self.assertRaises(ValidationError) as cm:
            DigestMerger.merge(existing, new)
        self.assertIn("existing", str(cm.exception))
        self.assertIn("missing 'source_file'", str(cm.exception))

    def test_missing_source_file_in_new_raises_error(self):
        """Missing source_file in new digests raises ValidationError"""
        existing = [{"source_file": "a.txt"}]
        new = [{"content": "no source file"}]
        with self.assertRaises(ValidationError) as cm:
            DigestMerger.merge(existing, new)
        self.assertIn("new", str(cm.exception))
        self.assertIn("missing 'source_file'", str(cm.exception))

    def test_non_dict_in_existing_raises_error(self):
        """Non-dict item in existing raises ValidationError"""
        existing = ["not a dict"]
        new = [{"source_file": "a.txt"}]
        with self.assertRaises(ValidationError) as cm:
            DigestMerger.merge(existing, new)
        self.assertIn("existing", str(cm.exception))
        self.assertIn("expected dict", str(cm.exception))

    def test_non_dict_in_new_raises_error(self):
        """Non-dict item in new raises ValidationError"""
        existing = [{"source_file": "a.txt"}]
        new = [123]
        with self.assertRaises(ValidationError) as cm:
            DigestMerger.merge(existing, new)
        self.assertIn("new", str(cm.exception))
        self.assertIn("expected dict", str(cm.exception))

    def test_preserves_additional_fields(self):
        """Merge preserves additional fields in digests"""
        existing = [
            {
                "source_file": "a.txt",
                "keywords": ["old"],
                "abstract": {"long": "old abstract long", "short": "old abstract short"},
            }
        ]
        new = [
            {
                "source_file": "a.txt",
                "keywords": ["new"],
                "impression": {"long": "new impression long", "short": "new impression short"},
            }
        ]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 1)
        # New digest completely replaces old
        self.assertEqual(result[0]["keywords"], ["new"])
        self.assertIn("impression", result[0])
        self.assertNotIn("abstract", result[0])

    def test_order_preserved_for_existing(self):
        """Existing items order is preserved, new items appended"""
        existing = [
            {"source_file": "a.txt"},
            {"source_file": "b.txt"},
            {"source_file": "c.txt"},
        ]
        new = [{"source_file": "d.txt"}]
        result = DigestMerger.merge(existing, new)
        # Dict preserves insertion order in Python 3.7+
        source_files = [d["source_file"] for d in result]
        self.assertEqual(source_files, ["a.txt", "b.txt", "c.txt", "d.txt"])


class TestDigestMergerEdgeCases(unittest.TestCase):
    """DigestMerger edge case tests"""

    def test_source_file_with_special_characters(self):
        """source_file with special characters handled correctly"""
        existing = [{"source_file": "path/to/file with spaces.txt"}]
        new = [{"source_file": "path/to/file with spaces.txt", "updated": True}]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["updated"])

    def test_source_file_unicode(self):
        """Unicode source_file handled correctly"""
        existing = [{"source_file": "日本語ファイル.txt"}]
        new = [{"source_file": "日本語ファイル.txt", "updated": True}]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["updated"])

    def test_empty_source_file_string(self):
        """Empty string source_file is valid but unusual"""
        existing = [{"source_file": ""}]
        new = [{"source_file": "", "updated": True}]
        result = DigestMerger.merge(existing, new)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["updated"])


if __name__ == "__main__":
    unittest.main()
