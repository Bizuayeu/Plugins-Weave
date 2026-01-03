"""GridConfig削除のTDDテスト (Task 1: GridConfig統合)"""

import pytest


class TestGridConfigRemoval:
    """GridConfigが削除されていることを確認するテスト"""

    def test_gridconfig_not_in_models(self):
        """GridConfigがmodels.pyから削除されている"""
        from domain import models

        assert not hasattr(models, "GridConfig")

    def test_gridconfig_not_exported(self):
        """GridConfigがdomain/__init__.pyからエクスポートされていない"""
        from domain import __all__

        assert "GridConfig" not in __all__

    def test_gridconfig_import_fails(self):
        """from domain import GridConfigが失敗する"""
        with pytest.raises(ImportError):
            from domain import GridConfig  # type: ignore[attr-defined]


class TestGridLayoutHasAllFunctionality:
    """GridLayoutがGridConfigの全機能を持っていることを確認"""

    def test_has_expected_width(self):
        """GridLayoutがexpected_widthプロパティを持つ"""
        from domain.grid_layout import GridLayout

        layout = GridLayout.default()
        assert layout.expected_width == 1400  # 5 * 280

    def test_has_expected_height(self):
        """GridLayoutがexpected_heightプロパティを持つ"""
        from domain.grid_layout import GridLayout

        layout = GridLayout.default()
        assert layout.expected_height == 1120  # 4 * 280

    def test_has_total_cells(self):
        """GridLayoutがtotal_cellsプロパティを持つ"""
        from domain.grid_layout import GridLayout

        layout = GridLayout.default()
        assert layout.total_cells == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
