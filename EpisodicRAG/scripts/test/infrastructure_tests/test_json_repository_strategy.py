#!/usr/bin/env python3
"""
test_json_repository_strategy.py
================================

json_repository Strategy Pattern 実装のユニットテスト。

## テスト対象

- LoadStrategy（抽象基底クラス）
- FileLoadStrategy
- TemplateLoadStrategy
- FactoryLoadStrategy
- DefaultLoadStrategy
- ChainedLoader
- LoadContext
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from infrastructure.json_repository import (
    ChainedLoader,
    DefaultLoadStrategy,
    FactoryLoadStrategy,
    FileLoadStrategy,
    LoadContext,
    LoadStrategy,
    TemplateLoadStrategy,
)

# =============================================================================
# LoadContext Tests
# =============================================================================


class TestLoadContext:
    """LoadContext（コンテキストオブジェクト）のテスト"""

    def test_init_with_minimal_args(self, tmp_path: Path) -> None:
        """最小限の引数で初期化"""
        target = tmp_path / "target.json"
        context = LoadContext(target_file=target)

        assert context.target_file == target
        assert context.template_file is None
        assert context.default_factory is None
        assert context.save_on_create is True
        assert context.log_message is None

    def test_init_with_all_args(self, tmp_path: Path) -> None:
        """全ての引数で初期化"""
        target = tmp_path / "target.json"
        template = tmp_path / "template.json"
        def factory():
            return {"key": "value"}

        context = LoadContext(
            target_file=target,
            template_file=template,
            default_factory=factory,
            save_on_create=False,
            log_message="Custom message",
        )

        assert context.target_file == target
        assert context.template_file == template
        assert context.default_factory is factory
        assert context.save_on_create is False
        assert context.log_message == "Custom message"


# =============================================================================
# FileLoadStrategy Tests
# =============================================================================


class TestFileLoadStrategy:
    """FileLoadStrategy（既存ファイル読み込み戦略）のテスト"""

    def test_load_existing_file(self, tmp_path: Path) -> None:
        """既存ファイルがある場合は読み込む"""
        target = tmp_path / "target.json"
        target.write_text('{"key": "value"}')

        def mock_read(path: Path, raise_on_error: bool) -> Optional[Dict[str, Any]]:
            return json.loads(path.read_text())

        strategy = FileLoadStrategy(mock_read)
        context = LoadContext(target_file=target)
        result = strategy.load(context)

        assert result == {"key": "value"}

    def test_load_missing_file_returns_none(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合はNoneを返す"""
        target = tmp_path / "missing.json"

        mock_read = MagicMock()
        strategy = FileLoadStrategy(mock_read)
        context = LoadContext(target_file=target)
        result = strategy.load(context)

        assert result is None
        mock_read.assert_not_called()  # ファイルがないので読み込みは呼ばれない

    def test_get_description(self) -> None:
        """説明文を取得"""
        strategy = FileLoadStrategy(MagicMock())
        desc = strategy.get_description()
        assert "FileLoadStrategy" in desc
        assert "existing file" in desc


# =============================================================================
# TemplateLoadStrategy Tests
# =============================================================================


class TestTemplateLoadStrategy:
    """TemplateLoadStrategy（テンプレート読み込み戦略）のテスト"""

    def test_load_from_template(self, tmp_path: Path) -> None:
        """テンプレートファイルから読み込む"""
        target = tmp_path / "target.json"
        template = tmp_path / "template.json"
        template.write_text('{"source": "template"}')

        def mock_read(path: Path, raise_on_error: bool) -> Optional[Dict[str, Any]]:
            return json.loads(path.read_text())

        save_called = []

        def mock_save(path: Path, data: Dict[str, Any]) -> None:
            save_called.append((path, data))

        strategy = TemplateLoadStrategy(mock_read, mock_save)
        context = LoadContext(
            target_file=target, template_file=template, save_on_create=True
        )
        result = strategy.load(context)

        assert result == {"source": "template"}
        assert len(save_called) == 1
        assert save_called[0][0] == target

    def test_no_template_returns_none(self, tmp_path: Path) -> None:
        """テンプレートがない場合はNoneを返す"""
        target = tmp_path / "target.json"

        strategy = TemplateLoadStrategy(MagicMock(), MagicMock())
        context = LoadContext(target_file=target, template_file=None)
        result = strategy.load(context)

        assert result is None

    def test_missing_template_file_returns_none(self, tmp_path: Path) -> None:
        """テンプレートファイルが存在しない場合はNoneを返す"""
        target = tmp_path / "target.json"
        template = tmp_path / "missing_template.json"

        strategy = TemplateLoadStrategy(MagicMock(), MagicMock())
        context = LoadContext(target_file=target, template_file=template)
        result = strategy.load(context)

        assert result is None

    def test_save_on_create_false_does_not_save(self, tmp_path: Path) -> None:
        """save_on_create=Falseの場合は保存しない"""
        target = tmp_path / "target.json"
        template = tmp_path / "template.json"
        template.write_text('{"source": "template"}')

        def mock_read(path: Path, raise_on_error: bool) -> Optional[Dict[str, Any]]:
            return json.loads(path.read_text())

        mock_save = MagicMock()

        strategy = TemplateLoadStrategy(mock_read, mock_save)
        context = LoadContext(
            target_file=target, template_file=template, save_on_create=False
        )
        result = strategy.load(context)

        assert result == {"source": "template"}
        mock_save.assert_not_called()


# =============================================================================
# FactoryLoadStrategy Tests
# =============================================================================


class TestFactoryLoadStrategy:
    """FactoryLoadStrategy（ファクトリ生成戦略）のテスト"""

    def test_create_from_factory(self, tmp_path: Path) -> None:
        """ファクトリ関数から作成"""
        target = tmp_path / "target.json"

        def factory() -> Dict[str, Any]:
            return {"source": "factory", "created": True}

        save_called = []

        def mock_save(path: Path, data: Dict[str, Any]) -> None:
            save_called.append((path, data))

        strategy = FactoryLoadStrategy(mock_save)
        context = LoadContext(
            target_file=target, default_factory=factory, save_on_create=True
        )
        result = strategy.load(context)

        assert result == {"source": "factory", "created": True}
        assert len(save_called) == 1

    def test_no_factory_returns_none(self, tmp_path: Path) -> None:
        """ファクトリがない場合はNoneを返す"""
        target = tmp_path / "target.json"

        strategy = FactoryLoadStrategy(MagicMock())
        context = LoadContext(target_file=target, default_factory=None)
        result = strategy.load(context)

        assert result is None

    def test_save_on_create_false(self, tmp_path: Path) -> None:
        """save_on_create=Falseの場合は保存しない"""
        target = tmp_path / "target.json"

        def factory() -> Dict[str, Any]:
            return {"source": "factory"}

        mock_save = MagicMock()

        strategy = FactoryLoadStrategy(mock_save)
        context = LoadContext(
            target_file=target, default_factory=factory, save_on_create=False
        )
        result = strategy.load(context)

        assert result == {"source": "factory"}
        mock_save.assert_not_called()


# =============================================================================
# DefaultLoadStrategy Tests
# =============================================================================


class TestDefaultLoadStrategy:
    """DefaultLoadStrategy（デフォルト値戦略）のテスト"""

    def test_returns_empty_dict(self, tmp_path: Path) -> None:
        """常に空dictを返す"""
        strategy = DefaultLoadStrategy()
        context = LoadContext(target_file=tmp_path / "any.json")
        result = strategy.load(context)

        assert result == {}

    def test_get_description(self) -> None:
        """説明文を取得"""
        strategy = DefaultLoadStrategy()
        desc = strategy.get_description()
        assert "DefaultLoadStrategy" in desc
        assert "empty dict" in desc


# =============================================================================
# ChainedLoader Tests
# =============================================================================


class TestChainedLoader:
    """ChainedLoader（戦略チェーン）のテスト"""

    def test_first_strategy_succeeds(self, tmp_path: Path) -> None:
        """最初の戦略が成功した場合はその結果を返す"""
        strategy1 = MagicMock(spec=LoadStrategy)
        strategy1.load.return_value = {"from": "strategy1"}
        strategy1.get_description.return_value = "Strategy 1"

        strategy2 = MagicMock(spec=LoadStrategy)

        loader = ChainedLoader([strategy1, strategy2])
        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result == {"from": "strategy1"}
        strategy1.load.assert_called_once()
        strategy2.load.assert_not_called()  # 最初が成功したので呼ばれない

    def test_fallback_to_second_strategy(self, tmp_path: Path) -> None:
        """最初の戦略が失敗した場合は次の戦略を試行"""
        strategy1 = MagicMock(spec=LoadStrategy)
        strategy1.load.return_value = None
        strategy1.get_description.return_value = "Strategy 1"

        strategy2 = MagicMock(spec=LoadStrategy)
        strategy2.load.return_value = {"from": "strategy2"}
        strategy2.get_description.return_value = "Strategy 2"

        loader = ChainedLoader([strategy1, strategy2])
        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result == {"from": "strategy2"}
        strategy1.load.assert_called_once()
        strategy2.load.assert_called_once()

    def test_all_strategies_fail_returns_none(self, tmp_path: Path) -> None:
        """全ての戦略が失敗した場合はNoneを返す"""
        strategy1 = MagicMock(spec=LoadStrategy)
        strategy1.load.return_value = None
        strategy1.get_description.return_value = "Strategy 1"

        strategy2 = MagicMock(spec=LoadStrategy)
        strategy2.load.return_value = None
        strategy2.get_description.return_value = "Strategy 2"

        loader = ChainedLoader([strategy1, strategy2])
        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result is None

    def test_empty_chain_returns_none(self, tmp_path: Path) -> None:
        """空のチェーンはNoneを返す"""
        loader: ChainedLoader[Dict[str, Any]] = ChainedLoader([])
        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result is None

    def test_add_strategy(self, tmp_path: Path) -> None:
        """戦略を追加できる"""
        strategy1 = MagicMock(spec=LoadStrategy)
        strategy1.load.return_value = None
        strategy1.get_description.return_value = "Strategy 1"

        loader = ChainedLoader([strategy1])

        strategy2 = MagicMock(spec=LoadStrategy)
        strategy2.load.return_value = {"from": "added"}
        strategy2.get_description.return_value = "Strategy 2"

        loader.add_strategy(strategy2)

        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result == {"from": "added"}

    def test_insert_strategy(self, tmp_path: Path) -> None:
        """指定位置に戦略を挿入できる"""
        strategy1 = MagicMock(spec=LoadStrategy)
        strategy1.load.return_value = None
        strategy1.get_description.return_value = "Strategy 1"

        strategy2 = MagicMock(spec=LoadStrategy)
        strategy2.load.return_value = {"from": "strategy2"}
        strategy2.get_description.return_value = "Strategy 2"

        loader = ChainedLoader([strategy2])

        # 最初に挿入
        inserted = MagicMock(spec=LoadStrategy)
        inserted.load.return_value = {"from": "inserted"}
        inserted.get_description.return_value = "Inserted Strategy"

        loader.insert_strategy(0, inserted)

        context = LoadContext(target_file=tmp_path / "any.json")
        result = loader.load(context)

        assert result == {"from": "inserted"}


# =============================================================================
# Integration Tests
# =============================================================================


class TestStrategyIntegration:
    """Strategy Pattern統合テスト"""

    @pytest.mark.integration
    def test_full_chain_with_real_files(self, tmp_path: Path) -> None:
        """実際のファイルを使った完全なチェーンテスト"""
        from infrastructure.json_repository import (
            load_json_with_template,
            safe_read_json,
            save_json,
        )

        # ターゲットなし、テンプレートあり
        target = tmp_path / "target.json"
        template = tmp_path / "template.json"
        template.write_text('{"source": "template", "data": [1, 2, 3]}')

        result = load_json_with_template(target, template)

        assert result["source"] == "template"
        assert target.exists()  # save_on_create=True

    @pytest.mark.integration
    def test_custom_chain_order(self, tmp_path: Path) -> None:
        """カスタム戦略順序のテスト"""
        from infrastructure.json_repository import safe_read_json, save_json

        # DefaultLoadStrategyを最初に、FileLoadStrategyを2番目に
        # → 常に空dictが返る
        loader: ChainedLoader[Dict[str, Any]] = ChainedLoader([
            DefaultLoadStrategy(),
            FileLoadStrategy(safe_read_json),
        ])

        target = tmp_path / "target.json"
        target.write_text('{"key": "value"}')

        context = LoadContext(target_file=target)
        result = loader.load(context)

        # DefaultLoadStrategyが最初なので空dictが返る
        assert result == {}
