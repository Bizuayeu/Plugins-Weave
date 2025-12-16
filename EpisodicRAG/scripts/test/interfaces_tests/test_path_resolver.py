#!/usr/bin/env python3
"""
Path Resolver テスト
====================

interfaces/digest_auto/path_resolver.py のユニットテスト。
v5.2.0 で digest_auto パッケージ分割により追加。

Functions tested:
    - resolve_base_dir: base_dirの解決
    - resolve_paths: loops, essences, digests パスの解決
"""

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interfaces.digest_auto.path_resolver import resolve_base_dir, resolve_paths


class TestResolveBaseDir(unittest.TestCase):
    """resolve_base_dir() のテスト"""

    def test_valid_absolute_path(self) -> None:
        """絶対パスを正常に解決"""
        with tempfile.TemporaryDirectory() as tmp:
            config = {"base_dir": tmp}
            result = resolve_base_dir(config)
            self.assertEqual(result, Path(tmp).resolve())

    def test_expanduser_tilde(self) -> None:
        """~（ホームディレクトリ）を展開"""
        config = {"base_dir": "~/test_dir"}
        result = resolve_base_dir(config)
        self.assertIn(str(Path.home()), str(result))
        self.assertTrue(result.is_absolute())

    def test_missing_base_dir_raises_value_error(self) -> None:
        """base_dir が未設定の場合 ValueError を発生"""
        config = {}
        with self.assertRaises(ValueError) as ctx:
            resolve_base_dir(config)
        self.assertIn("base_dir is required", str(ctx.exception))

    def test_empty_base_dir_raises_value_error(self) -> None:
        """base_dir が空文字列の場合 ValueError を発生"""
        config = {"base_dir": ""}
        with self.assertRaises(ValueError) as ctx:
            resolve_base_dir(config)
        self.assertIn("base_dir is required", str(ctx.exception))

    def test_relative_path_raises_value_error(self) -> None:
        """相対パスの場合 ValueError を発生"""
        config = {"base_dir": "relative/path"}
        with self.assertRaises(ValueError) as ctx:
            resolve_base_dir(config)
        self.assertIn("absolute path", str(ctx.exception))


class TestResolvePaths(unittest.TestCase):
    """resolve_paths() のテスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_paths(self) -> None:
        """デフォルトパス（data/Loops等）を使用"""
        config = {"base_dir": self.temp_dir}
        loops, essences, digests = resolve_paths(config)

        self.assertEqual(loops, Path(self.temp_dir) / "data" / "Loops")
        self.assertEqual(essences, Path(self.temp_dir) / "data" / "Essences")
        self.assertEqual(digests, Path(self.temp_dir) / "data" / "Digests")

    def test_custom_paths(self) -> None:
        """config.paths で指定されたカスタムパスを使用"""
        config = {
            "base_dir": self.temp_dir,
            "paths": {
                "loops_dir": "custom/loops",
                "essences_dir": "custom/essences",
                "digests_dir": "custom/digests",
            },
        }
        loops, essences, digests = resolve_paths(config)

        self.assertEqual(loops, Path(self.temp_dir) / "custom" / "loops")
        self.assertEqual(essences, Path(self.temp_dir) / "custom" / "essences")
        self.assertEqual(digests, Path(self.temp_dir) / "custom" / "digests")

    def test_empty_paths_uses_defaults(self) -> None:
        """paths が空辞書でもデフォルトを使用"""
        config = {"base_dir": self.temp_dir, "paths": {}}
        loops, essences, digests = resolve_paths(config)

        self.assertEqual(loops, Path(self.temp_dir) / "data" / "Loops")
        self.assertEqual(essences, Path(self.temp_dir) / "data" / "Essences")
        self.assertEqual(digests, Path(self.temp_dir) / "data" / "Digests")

    def test_partial_paths_uses_defaults_for_missing(self) -> None:
        """一部のパスのみ指定された場合、残りはデフォルト"""
        config = {
            "base_dir": self.temp_dir,
            "paths": {"loops_dir": "my_loops"},
        }
        loops, essences, digests = resolve_paths(config)

        self.assertEqual(loops, Path(self.temp_dir) / "my_loops")
        self.assertEqual(essences, Path(self.temp_dir) / "data" / "Essences")
        self.assertEqual(digests, Path(self.temp_dir) / "data" / "Digests")


if __name__ == "__main__":
    unittest.main()
