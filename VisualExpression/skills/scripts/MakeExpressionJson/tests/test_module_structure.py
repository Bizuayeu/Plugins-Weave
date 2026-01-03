"""Tests for module structure after constants.py refactoring."""

import importlib.util


class TestModuleStructure:
    """Test that the new module structure is correctly organized."""

    def test_definitions_module_exists(self):
        """definitions.py モジュールが存在し、データ定義を含むことを確認"""
        from domain import definitions

        # Enum
        assert hasattr(definitions, "ExpressionCategory")
        # Constants
        assert hasattr(definitions, "EXPRESSION_CODES")
        assert hasattr(definitions, "GRID_ROWS")
        assert hasattr(definitions, "GRID_COLS")
        assert hasattr(definitions, "CELL_SIZE")
        # Dicts
        assert hasattr(definitions, "EXPRESSION_LABELS")
        assert hasattr(definitions, "CATEGORY_CODES")
        assert hasattr(definitions, "GRID_CONFIG")

    def test_builders_module_exists(self):
        """builders.py モジュールが存在し、ビルダー関数を含むことを確認"""
        from domain import builders

        assert hasattr(builders, "build_expression_codes")
        assert hasattr(builders, "build_expression_labels")
        assert hasattr(builders, "get_cell_position")
        assert hasattr(builders, "get_cell_position_dynamic")

    def test_constants_removed(self):
        """constants.py が削除されていることを確認"""
        spec = importlib.util.find_spec("domain.constants")
        assert spec is None, "domain.constants should be removed"

    def test_domain_reexports_all(self):
        """domain/__init__.py が全てを再エクスポートすることを確認"""
        from domain import (
            CATEGORY_CODES,
            # From definitions
            CELL_SIZE,
            EXPRESSION_CODES,
            EXPRESSION_LABELS,
            GRID_COLS,
            GRID_CONFIG,
            GRID_ROWS,
            ExpressionCategory,
            # From builders
            build_expression_codes,
            build_expression_labels,
            get_cell_position,
            get_cell_position_dynamic,
        )

        # Just check they're callable/accessible
        assert GRID_ROWS == 4
        assert GRID_COLS == 5
        assert callable(build_expression_codes)
        assert callable(get_cell_position)


class TestDefinitionsContent:
    """Test the content of definitions module."""

    def test_expression_codes_is_list(self):
        """EXPRESSION_CODES が20要素のリストであることを確認"""
        from domain.definitions import EXPRESSION_CODES

        assert isinstance(EXPRESSION_CODES, list)
        assert len(EXPRESSION_CODES) == 20

    def test_grid_constants(self):
        """グリッド定数が正しい値であることを確認"""
        from domain.definitions import CELL_SIZE, GRID_COLS, GRID_ROWS

        assert GRID_ROWS == 4
        assert GRID_COLS == 5
        assert CELL_SIZE == 280

    def test_expression_category_enum(self):
        """ExpressionCategory Enum が正しいカテゴリを持つことを確認"""
        from domain.definitions import ExpressionCategory

        assert hasattr(ExpressionCategory, "BASIC")
        assert hasattr(ExpressionCategory, "EMOTION")
        assert hasattr(ExpressionCategory, "NEGATIVE")
        assert hasattr(ExpressionCategory, "ANXIETY")
        assert hasattr(ExpressionCategory, "SPECIAL")


class TestBuildersContent:
    """Test the content of builders module."""

    def test_build_expression_codes_default(self):
        """build_expression_codes がデフォルトで20コードを返すことを確認"""
        from domain.builders import build_expression_codes

        codes = build_expression_codes()
        assert len(codes) == 20

    def test_build_expression_codes_custom(self):
        """build_expression_codes がカスタムSpecialコードを受け入れることを確認"""
        from domain.builders import build_expression_codes

        custom = ["a", "b", "c", "d"]
        codes = build_expression_codes(special_codes=custom)
        assert len(codes) == 20
        assert "a" in codes
        assert "d" in codes

    def test_get_cell_position(self):
        """get_cell_position が正しい座標を返すことを確認"""
        from domain.builders import get_cell_position

        # First cell (0, 0, 280, 280)
        pos = get_cell_position(0)
        assert pos == (0, 0, 280, 280)

    def test_get_cell_position_dynamic(self):
        """get_cell_position_dynamic がカスタムパラメータを受け入れることを確認"""
        from domain.builders import get_cell_position_dynamic

        pos = get_cell_position_dynamic(0, cols=5, cell_width=100, cell_height=100)
        assert pos == (0, 0, 100, 100)
