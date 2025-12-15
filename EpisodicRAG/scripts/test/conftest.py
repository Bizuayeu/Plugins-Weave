#!/usr/bin/env python3
"""
pytest 共通設定
===============

共通フィクスチャとマーカー定義を提供。
既存の test_helpers.py と連携し、テスト環境の一貫性を確保。
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Tuple
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from application.config import DigestConfig
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types import LevelHierarchy

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

# pythonpath設定により scripts/ は自動的にパスに追加される（pyproject.toml参照）

from test_helpers import TempPluginEnvironment, create_test_loop_file

# =============================================================================
# シングルトンリセット（テスト分離保証）
# =============================================================================


@pytest.fixture(autouse=True)
def reset_all_singletons() -> Generator[None, None, None]:
    """
    全テスト前後でシングルトンをリセット

    テスト間の状態分離を保証し、テスト順序依存やグローバル状態による
    予期しない干渉を防ぐ。

    Note:
        - level_registry: レベル設定のシングルトン
        - file_naming: ファイル命名用レジストリ参照
        - error_formatter: エラーフォーマッタのデフォルトインスタンス
    """
    # テスト実行前：クリーンな状態で開始
    from domain.error_formatter import reset_error_formatter
    from domain.file_naming import reset_registry
    from domain.level_registry import reset_level_registry

    reset_level_registry()
    reset_registry()
    reset_error_formatter()

    yield  # テスト実行

    # テスト実行後：次のテストのためにクリーンアップ
    reset_level_registry()
    reset_registry()
    reset_error_formatter()


# =============================================================================
# pytestマーカー定義
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """カスタムマーカーを登録"""
    config.addinivalue_line("markers", "unit: 単体テスト（高速、外部依存なし）")
    config.addinivalue_line("markers", "integration: 統合テスト（ファイルI/O）")
    config.addinivalue_line(
        "markers", "slow: 時間のかかるテスト（ファイルI/O、複数コンポーネント連携）"
    )
    config.addinivalue_line("markers", "fast: 高速テスト（純粋ロジック、I/Oなし）")
    config.addinivalue_line("markers", "property: Property-based tests using hypothesis")
    config.addinivalue_line("markers", "performance: パフォーマンス・ベンチマークテスト")
    config.addinivalue_line("markers", "cli: CLI統合テスト（subprocess経由）")


# =============================================================================
# 共通フィクスチャ
# =============================================================================


@pytest.fixture
def temp_plugin_env() -> Generator[TempPluginEnvironment, None, None]:
    """
    テスト用の一時プラグイン環境を提供（関数スコープ）

    Usage:
        def test_something(temp_plugin_env) -> None:

            config = DigestConfig()  # get_config_path() は自動モック済み
            # ... テスト実行 ...
    """
    with TempPluginEnvironment() as env:
        yield env


@pytest.fixture(scope="module")
def shared_plugin_env() -> Generator[TempPluginEnvironment, None, None]:
    """
    モジュール間で共有するプラグイン環境（読み取り専用テスト用）

    Note:
        この環境を変更するテストは避けること。
        変更が必要な場合は temp_plugin_env を使用。
    """
    with TempPluginEnvironment() as env:
        yield env


@pytest.fixture
def sample_loop_files(
    temp_plugin_env: TempPluginEnvironment,
) -> Tuple[TempPluginEnvironment, List[Path]]:
    """
    5つのサンプルLoopファイルを作成済みの環境を提供

    Returns:
        (env, loop_files): 環境とLoopファイルパスのリスト
    """
    loop_files: List[Path] = []
    for i in range(1, 6):
        loop_file = create_test_loop_file(temp_plugin_env.loops_path, i, f"test_loop_{i}")
        loop_files.append(loop_file)
    return temp_plugin_env, loop_files


# =============================================================================
# DigestConfig関連フィクスチャ
# =============================================================================


@pytest.fixture(autouse=True)
def mock_persistent_config_dir(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """
    get_persistent_config_dir()とget_config_path()をモックして一時ディレクトリを返す

    テスト時に本番の~/.claude/plugins/.episodicrag/を使用しないようにする。

    Note:
        autouse=Trueで全テストに自動適用。
        temp_plugin_envフィクスチャを使用するテストでのみモックが有効。

        Pythonのインポートシステムでは、関数がインポートされると
        インポート先のモジュールに新しい参照が作成される。
        そのため、定義元ではなく使用箇所でパッチする必要がある。
    """
    from contextlib import ExitStack

    # temp_plugin_envを使用しているかチェック
    if "temp_plugin_env" in request.fixturenames:
        env = request.getfixturevalue("temp_plugin_env")

        # get_persistent_config_dir() のパッチ対象
        persistent_dir_targets = [
            "infrastructure.config.persistent_path.get_persistent_config_dir",
            "infrastructure.config.get_persistent_config_dir",
            "application.tracking.digest_times.get_persistent_config_dir",
        ]

        # get_config_path() のパッチ対象
        config_path_targets = [
            "infrastructure.config.persistent_path.get_config_path",
            "application.config.get_config_path",
            "application.config.config_builder.get_config_path",
        ]

        config_path = env.persistent_config_dir / "config.json"

        with ExitStack() as stack:
            for target in persistent_dir_targets:
                stack.enter_context(patch(target, return_value=env.persistent_config_dir))
            for target in config_path_targets:
                stack.enter_context(patch(target, return_value=config_path))
            yield
    else:
        # temp_plugin_envを使用しないテストはモックなしで実行
        yield


@pytest.fixture
def digest_config(
    temp_plugin_env: TempPluginEnvironment,
) -> "DigestConfig":
    """
    初期化済みのDigestConfigインスタンスを提供

    Note:
        mock_persistent_config_dirがautouse=Trueで自動適用されるため、
        永続化パスは自動的にテスト用ディレクトリにモックされる。
    """
    from application.config import DigestConfig

    return DigestConfig()


@pytest.fixture
def config(digest_config: "DigestConfig") -> "DigestConfig":
    """
    digest_configのエイリアス（後方互換性のため）

    Note:
        新規テストではdigest_configを使用することを推奨。
        このフィクスチャは同一インスタンスを返すため、
        digest_configとconfigは相互に置き換え可能。
    """
    return digest_config


# =============================================================================
# Shadow関連共通フィクスチャ
# =============================================================================


@pytest.fixture
def times_tracker(config: "DigestConfig") -> "DigestTimesTracker":
    """テスト用DigestTimesTracker"""
    from application.tracking import DigestTimesTracker

    return DigestTimesTracker(config)


@pytest.fixture
def template() -> "ShadowTemplate":
    """テスト用ShadowTemplate"""
    from application.shadow import ShadowTemplate
    from domain.constants import LEVEL_NAMES

    return ShadowTemplate(levels=LEVEL_NAMES)


@pytest.fixture
def shadow_io(temp_plugin_env: TempPluginEnvironment, template: "ShadowTemplate") -> "ShadowIO":
    """テスト用ShadowIO"""
    from application.shadow import ShadowIO

    shadow_file = temp_plugin_env.config_dir / "ShadowGrandDigest.txt"
    return ShadowIO(shadow_file, template.get_template)


@pytest.fixture
def file_detector(config: "DigestConfig", times_tracker: "DigestTimesTracker") -> "FileDetector":
    """テスト用FileDetector"""
    from application.shadow import FileDetector

    return FileDetector(config, times_tracker)


@pytest.fixture
def level_hierarchy() -> "LevelHierarchy":
    """レベル階層情報（SSoT関数を使用）"""
    from domain.constants import build_level_hierarchy

    return build_level_hierarchy()


@pytest.fixture
def placeholder_manager() -> "PlaceholderManager":
    """テスト用PlaceholderManager"""
    from application.shadow.placeholder_manager import PlaceholderManager

    return PlaceholderManager()


# =============================================================================
# モックフィクスチャ
# =============================================================================


@pytest.fixture
def mock_digest_config(temp_plugin_env: TempPluginEnvironment) -> MagicMock:
    """
    モック用のDigestConfig（パス情報のみ）

    Note:
        完全なモックが必要な場合はunittest.mockを使用。
        このフィクスチャは実際のファイルシステム上に環境を作成。
    """
    from application.config import DigestConfig

    mock = MagicMock(spec=DigestConfig)
    mock.base_dir = temp_plugin_env.plugin_root
    mock.loops_path = temp_plugin_env.loops_path
    mock.digests_path = temp_plugin_env.digests_path
    mock.essences_path = temp_plugin_env.essences_path
    mock.config_dir = temp_plugin_env.config_dir
    return mock


# =============================================================================
# Application層フィクスチャ
# =============================================================================


@pytest.fixture
def shadow_manager(config: "DigestConfig") -> "ShadowGrandDigestManager":
    """
    テスト用ShadowGrandDigestManager

    Note:
        実際のDigestConfigを使用する標準版。
        カスタムモックが必要な場合は各テストで独自定義。
    """
    from application.grand import ShadowGrandDigestManager

    return ShadowGrandDigestManager(config)


@pytest.fixture
def grand_digest_manager(config: "DigestConfig") -> "GrandDigestManager":
    """テスト用GrandDigestManager"""
    from application.grand import GrandDigestManager

    return GrandDigestManager(config)


# =============================================================================
# LongShortText関連フィクスチャ
# =============================================================================


@pytest.fixture
def valid_digest_long_short() -> Dict[str, Any]:
    """有効な{long, short}形式のdigestデータ"""
    return {
        "source_file": "L00001_test.txt",
        "digest_type": "テスト",
        "keywords": ["test", "sample"],
        "abstract": {"long": "詳細な要約（2400字程度）...", "short": "簡潔な要約（1200字程度）"},
        "impression": {"long": "詳細な所感（800字程度）...", "short": "簡潔な所感（400字程度）"},
    }


@pytest.fixture
def valid_individual_digests_list() -> List[Dict[str, Any]]:
    """有効なindividual_digestsリスト"""
    return [
        {
            "source_file": "L00001_test.txt",
            "digest_type": "開発",
            "keywords": ["MCP", "Python"],
            "abstract": {"long": "詳細1...", "short": "簡潔1"},
            "impression": {"long": "所感1...", "short": "短い所感1"},
        },
        {
            "source_file": "L00002_test.txt",
            "digest_type": "学習",
            "keywords": ["API", "認証"],
            "abstract": {"long": "詳細2...", "short": "簡潔2"},
            "impression": {"long": "所感2...", "short": "短い所感2"},
        },
    ]
