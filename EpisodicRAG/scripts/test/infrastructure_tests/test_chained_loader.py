#!/usr/bin/env python3
"""
ChainedLoader ユニットテスト
============================

chained_loader.py のユニットテスト。
ChainedLoaderクラスの動作を検証:
- load: 戦略チェーンの実行と最初の成功結果の返却
- add_strategy: 戦略の追加
- insert_strategy: 指定位置への戦略挿入
- 空の戦略リスト、全戦略失敗などのエッジケース
"""

from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from unittest.mock import MagicMock

import pytest

from infrastructure.json_repository.chained_loader import ChainedLoader
from infrastructure.json_repository.load_strategy import LoadContext, LoadStrategy

# =============================================================================
# テスト用モック戦略クラス
# =============================================================================


class MockSuccessStrategy(LoadStrategy[Dict[str, Any]]):
    """常に成功を返す戦略"""

    def __init__(self, return_value: Dict[str, Any], description: str = "MockSuccess"):
        self.return_value = return_value
        self.description = description
        self.load_called = False

    def load(self, context: LoadContext) -> Optional[Dict[str, Any]]:
        self.load_called = True
        return self.return_value

    def get_description(self) -> str:
        return self.description


class MockFailureStrategy(LoadStrategy[Dict[str, Any]]):
    """常にNoneを返す戦略"""

    def __init__(self, description: str = "MockFailure"):
        self.description = description
        self.load_called = False

    def load(self, context: LoadContext) -> Optional[Dict[str, Any]]:
        self.load_called = True
        return None

    def get_description(self) -> str:
        return self.description


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def sample_context():
    """テスト用のLoadContext"""
    return LoadContext(
        target_file=Path("/tmp/test.json"),
        template_file=Path("/tmp/template.json"),
    )


@pytest.fixture
def success_data():
    """成功時に返すデータ"""
    return {"key": "value", "number": 42}


# =============================================================================
# TestChainedLoaderLoad - load メソッドテスト
# =============================================================================


class TestChainedLoaderLoad:
    """loadメソッドのテスト"""

    @pytest.mark.unit
    def test_returns_first_successful_result(self, sample_context, success_data):
        """最初に成功した戦略の結果を返す"""
        strategy1 = MockFailureStrategy("fail1")
        strategy2 = MockSuccessStrategy(success_data, "success")
        strategy3 = MockSuccessStrategy({"other": "data"}, "success2")

        loader = ChainedLoader([strategy1, strategy2, strategy3])
        result = loader.load(sample_context)

        assert result == success_data
        assert strategy1.load_called is True
        assert strategy2.load_called is True
        assert strategy3.load_called is False  # 短絡評価

    @pytest.mark.unit
    def test_first_strategy_succeeds(self, sample_context, success_data):
        """最初の戦略が成功した場合、それを返す"""
        strategy1 = MockSuccessStrategy(success_data, "success")
        strategy2 = MockFailureStrategy("fail")

        loader = ChainedLoader([strategy1, strategy2])
        result = loader.load(sample_context)

        assert result == success_data
        assert strategy1.load_called is True
        assert strategy2.load_called is False  # 呼ばれない

    @pytest.mark.unit
    def test_all_strategies_fail_returns_none(self, sample_context):
        """全戦略が失敗した場合Noneを返す"""
        strategy1 = MockFailureStrategy("fail1")
        strategy2 = MockFailureStrategy("fail2")
        strategy3 = MockFailureStrategy("fail3")

        loader = ChainedLoader([strategy1, strategy2, strategy3])
        result = loader.load(sample_context)

        assert result is None
        assert strategy1.load_called is True
        assert strategy2.load_called is True
        assert strategy3.load_called is True

    @pytest.mark.unit
    def test_empty_strategy_list_returns_none(self, sample_context):
        """空の戦略リストはNoneを返す"""
        loader: ChainedLoader[Dict[str, Any]] = ChainedLoader([])
        result = loader.load(sample_context)

        assert result is None

    @pytest.mark.unit
    def test_single_successful_strategy(self, sample_context, success_data):
        """単一の成功戦略"""
        strategy = MockSuccessStrategy(success_data, "only")

        loader = ChainedLoader([strategy])
        result = loader.load(sample_context)

        assert result == success_data

    @pytest.mark.unit
    def test_single_failing_strategy(self, sample_context):
        """単一の失敗戦略"""
        strategy = MockFailureStrategy("only")

        loader = ChainedLoader([strategy])
        result = loader.load(sample_context)

        assert result is None


# =============================================================================
# TestChainedLoaderStrategyOrder - 戦略実行順序テスト
# =============================================================================


class TestChainedLoaderStrategyOrder:
    """戦略の実行順序テスト"""

    @pytest.mark.unit
    def test_strategies_executed_in_order(self, sample_context):
        """戦略は追加順に実行される"""
        execution_order = []

        class OrderTrackingStrategy(LoadStrategy[Dict[str, Any]]):
            def __init__(self, name: str):
                self.name = name

            def load(self, context: LoadContext) -> Optional[Dict[str, Any]]:
                execution_order.append(self.name)
                return None

            def get_description(self) -> str:
                return self.name

        strategies = [
            OrderTrackingStrategy("first"),
            OrderTrackingStrategy("second"),
            OrderTrackingStrategy("third"),
        ]

        loader = ChainedLoader(strategies)
        loader.load(sample_context)

        assert execution_order == ["first", "second", "third"]


# =============================================================================
# TestChainedLoaderAddStrategy - add_strategy テスト
# =============================================================================


class TestChainedLoaderAddStrategy:
    """add_strategyメソッドのテスト"""

    @pytest.mark.unit
    def test_add_strategy_appends_to_end(self, sample_context, success_data):
        """add_strategyは最後に追加する"""
        strategy1 = MockFailureStrategy("fail")
        strategy2 = MockSuccessStrategy(success_data, "success")

        loader = ChainedLoader([strategy1])
        loader.add_strategy(strategy2)

        result = loader.load(sample_context)
        assert result == success_data

    @pytest.mark.unit
    def test_add_strategy_to_empty_list(self, sample_context, success_data):
        """空のリストに戦略を追加"""
        strategy = MockSuccessStrategy(success_data, "success")

        loader: ChainedLoader[Dict[str, Any]] = ChainedLoader([])
        loader.add_strategy(strategy)

        result = loader.load(sample_context)
        assert result == success_data


# =============================================================================
# TestChainedLoaderInsertStrategy - insert_strategy テスト
# =============================================================================


class TestChainedLoaderInsertStrategy:
    """insert_strategyメソッドのテスト"""

    @pytest.mark.unit
    def test_insert_at_beginning(self, sample_context, success_data):
        """先頭に挿入"""
        strategy1 = MockFailureStrategy("fail")
        strategy2 = MockSuccessStrategy(success_data, "success")

        loader = ChainedLoader([strategy1])
        loader.insert_strategy(0, strategy2)

        result = loader.load(sample_context)
        assert result == success_data
        assert strategy1.load_called is False  # 短絡で呼ばれない

    @pytest.mark.unit
    def test_insert_in_middle(self, sample_context, success_data):
        """中間に挿入"""
        strategy1 = MockFailureStrategy("fail1")
        strategy2 = MockFailureStrategy("fail2")
        success = MockSuccessStrategy(success_data, "success")

        loader = ChainedLoader([strategy1, strategy2])
        loader.insert_strategy(1, success)

        result = loader.load(sample_context)
        assert result == success_data
        assert strategy1.load_called is True
        assert strategy2.load_called is False

    @pytest.mark.unit
    def test_insert_at_end(self, sample_context, success_data):
        """最後に挿入（add_strategyと同等）"""
        strategy1 = MockFailureStrategy("fail")
        strategy2 = MockSuccessStrategy(success_data, "success")

        loader = ChainedLoader([strategy1])
        loader.insert_strategy(1, strategy2)

        result = loader.load(sample_context)
        assert result == success_data


# =============================================================================
# TestChainedLoaderContextPassing - コンテキスト伝達テスト
# =============================================================================


class TestChainedLoaderContextPassing:
    """コンテキストが正しく戦略に渡されるかテスト"""

    @pytest.mark.unit
    def test_context_passed_to_all_strategies(self, sample_context):
        """コンテキストが各戦略に渡される"""
        received_contexts = []

        class ContextCapturingStrategy(LoadStrategy[Dict[str, Any]]):
            def load(self, context: LoadContext) -> Optional[Dict[str, Any]]:
                received_contexts.append(context)
                return None

            def get_description(self) -> str:
                return "context_capture"

        strategies = [ContextCapturingStrategy(), ContextCapturingStrategy()]
        loader = ChainedLoader(strategies)
        loader.load(sample_context)

        assert len(received_contexts) == 2
        assert all(ctx is sample_context for ctx in received_contexts)


# =============================================================================
# TestLoadContext - LoadContext テスト
# =============================================================================


class TestLoadContext:
    """LoadContextのテスト"""

    @pytest.mark.unit
    def test_context_initialization(self):
        """コンテキストの初期化"""
        target = Path("/tmp/target.json")
        template = Path("/tmp/template.json")
        factory = lambda: {"default": True}

        context = LoadContext(
            target_file=target,
            template_file=template,
            default_factory=factory,
            save_on_create=False,
            log_message="test message",
        )

        assert context.target_file == target
        assert context.template_file == template
        assert context.default_factory == factory
        assert context.save_on_create is False
        assert context.log_message == "test message"

    @pytest.mark.unit
    def test_context_minimal_initialization(self):
        """最小限のコンテキスト初期化"""
        target = Path("/tmp/target.json")

        context = LoadContext(target_file=target)

        assert context.target_file == target
        assert context.template_file is None
        assert context.default_factory is None
        assert context.save_on_create is True  # default
        assert context.log_message is None
