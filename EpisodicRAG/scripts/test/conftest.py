#!/usr/bin/env python3
"""
pytest 共通設定
===============

共通フィクスチャとマーカー定義を提供。
既存の test_helpers.py と連携し、テスト環境の一貫性を確保。
"""

import os
import sys
from pathlib import Path

import pytest

# =============================================================================
# Hypothesis Configuration
# =============================================================================

try:
    from hypothesis import Verbosity, settings

    # Default profile for local development
    settings.register_profile("default", max_examples=100)

    # CI profile - more thorough but slower
    settings.register_profile("ci", max_examples=500, verbosity=Verbosity.verbose)

    # Quick profile for rapid iteration
    settings.register_profile("quick", max_examples=20)

    # Load profile from environment or use default
    settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))

except ImportError:
    # hypothesis is an optional dependency
    pass

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
    config.addinivalue_line("markers", "property: Property-based tests using hypothesis")


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
        loop_file = create_test_loop_file(temp_plugin_env.loops_path, i, f"test_loop_{i}")
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


@pytest.fixture
def config(temp_plugin_env):
    """
    digest_configのエイリアス（後方互換性のため）

    Note:
        新規テストではdigest_configを使用することを推奨。
    """
    from config import DigestConfig

    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


# =============================================================================
# Shadow関連共通フィクスチャ
# =============================================================================


@pytest.fixture
def times_tracker(config):
    """テスト用DigestTimesTracker"""
    from application.tracking import DigestTimesTracker

    return DigestTimesTracker(config)


@pytest.fixture
def template():
    """テスト用ShadowTemplate"""
    from application.shadow import ShadowTemplate
    from domain.constants import LEVEL_NAMES

    return ShadowTemplate(levels=LEVEL_NAMES)


@pytest.fixture
def shadow_io(temp_plugin_env, template):
    """テスト用ShadowIO"""
    from application.shadow import ShadowIO

    shadow_file = temp_plugin_env.plugin_root / ".claude-plugin" / "ShadowGrandDigest.txt"
    return ShadowIO(shadow_file, template.get_template)


@pytest.fixture
def file_detector(config, times_tracker):
    """テスト用FileDetector"""
    from application.shadow import FileDetector

    return FileDetector(config, times_tracker)


@pytest.fixture
def level_hierarchy():
    """レベル階層情報"""
    from domain.constants import LEVEL_CONFIG

    return {
        level: {"source": cfg["source"], "next": cfg["next"]} for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def placeholder_manager():
    """テスト用PlaceholderManager"""
    from application.shadow.placeholder_manager import PlaceholderManager

    return PlaceholderManager()


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
