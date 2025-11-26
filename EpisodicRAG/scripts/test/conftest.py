#!/usr/bin/env python3
"""
pytest 共通設定
===============

共通フィクスチャとマーカー定義を提供。
既存の test_helpers.py と連携し、テスト環境の一貫性を確保。
"""
import sys
from pathlib import Path

import pytest

# 親ディレクトリをパスに追加（scripts/をインポート可能に）
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_helpers import TempPluginEnvironment, create_test_loop_file


# =============================================================================
# pytestマーカー定義
# =============================================================================

def pytest_configure(config):
    """カスタムマーカーを登録"""
    config.addinivalue_line("markers", "unit: 単体テスト（高速、外部依存なし）")
    config.addinivalue_line("markers", "integration: 統合テスト（ファイルI/O）")
    config.addinivalue_line("markers", "slow: 時間のかかるテスト")


# =============================================================================
# 共通フィクスチャ
# =============================================================================

@pytest.fixture
def temp_plugin_env():
    """
    テスト用の一時プラグイン環境を提供（関数スコープ）

    Usage:
        def test_something(temp_plugin_env):
            config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
            # ... テスト実行 ...
    """
    with TempPluginEnvironment() as env:
        yield env


@pytest.fixture(scope="module")
def shared_plugin_env():
    """
    モジュール間で共有するプラグイン環境（読み取り専用テスト用）

    Note:
        この環境を変更するテストは避けること。
        変更が必要な場合は temp_plugin_env を使用。
    """
    with TempPluginEnvironment() as env:
        yield env


@pytest.fixture
def sample_loop_files(temp_plugin_env):
    """
    5つのサンプルLoopファイルを作成済みの環境を提供

    Returns:
        (env, loop_files): 環境とLoopファイルパスのリスト
    """
    loop_files = []
    for i in range(1, 6):
        loop_file = create_test_loop_file(
            temp_plugin_env.loops_path,
            i,
            f"test_loop_{i}"
        )
        loop_files.append(loop_file)
    return temp_plugin_env, loop_files


# =============================================================================
# DigestConfig関連フィクスチャ
# =============================================================================

@pytest.fixture
def digest_config(temp_plugin_env):
    """
    初期化済みのDigestConfigインスタンスを提供
    """
    from config import DigestConfig
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


# =============================================================================
# モックフィクスチャ
# =============================================================================

@pytest.fixture
def mock_digest_config(temp_plugin_env):
    """
    モック用のDigestConfig（パス情報のみ）

    Note:
        完全なモックが必要な場合はunittest.mockを使用。
        このフィクスチャは実際のファイルシステム上に環境を作成。
    """
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.plugin_root = temp_plugin_env.plugin_root
    mock.loops_path = temp_plugin_env.loops_path
    mock.digests_path = temp_plugin_env.digests_path
    mock.essences_path = temp_plugin_env.essences_path
    mock.config_dir = temp_plugin_env.config_dir
    return mock
