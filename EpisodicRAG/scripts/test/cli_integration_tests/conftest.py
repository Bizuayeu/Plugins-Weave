#!/usr/bin/env python3
"""
CLI Integration Tests Conftest
==============================

CLI E2Eテスト専用フィクスチャとマーカー定義。
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator

import pytest

from .cli_runner import CLIRunner

# =============================================================================
# pytest マーカー登録
# =============================================================================


def pytest_configure(config) -> None:
    """カスタムマーカーを登録"""
    config.addinivalue_line("markers", "cli: CLI統合テスト（subprocess経由）")


# =============================================================================
# 基本フィクスチャ
# =============================================================================


@pytest.fixture
def cli_temp_dir() -> Generator[Path, None, None]:
    """
    CLI E2Eテスト用の一時ディレクトリを提供

    各テスト終了後に自動的にクリーンアップされる。
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="episodicrag_cli_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def cli_plugin_root(cli_temp_dir: Path) -> Path:
    """
    CLI E2Eテスト用のプラグインルートを提供

    基本的なディレクトリ構造のみ作成（設定ファイルなし）。
    """
    plugin_root = cli_temp_dir
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    return plugin_root


@pytest.fixture
def cli_runner(cli_plugin_root: Path) -> CLIRunner:
    """
    CLIRunner インスタンスを提供

    Usage:
        def test_something(cli_runner):

            result = cli_runner.run_digest_setup("check")
            result.assert_success()
    """
    return CLIRunner(plugin_root=cli_plugin_root)


# =============================================================================
# 設定済み環境フィクスチャ
# =============================================================================

LEVEL_DIRS = [
    "1_Weekly",
    "2_Monthly",
    "3_Quarterly",
    "4_Annual",
    "5_Triennial",
    "6_Decadal",
    "7_Multi-decadal",
    "8_Centurial",
]


def _create_full_plugin_structure(plugin_root: Path) -> Dict[str, Path]:
    """
    本番同等の完全なプラグイン構造を作成

    Returns:
        作成されたパスの辞書
    """
    config_dir = plugin_root / ".claude-plugin"
    data_dir = plugin_root / "data"
    loops_path = data_dir / "Loops"
    digests_path = data_dir / "Digests"
    essences_path = data_dir / "Essences"

    # ディレクトリ作成
    config_dir.mkdir(parents=True, exist_ok=True)
    loops_path.mkdir(parents=True, exist_ok=True)
    digests_path.mkdir(parents=True, exist_ok=True)
    essences_path.mkdir(parents=True, exist_ok=True)

    # レベルディレクトリとProvisional
    for level_dir in LEVEL_DIRS:
        level_path = digests_path / level_dir
        level_path.mkdir(exist_ok=True)
        (level_path / "Provisional").mkdir(exist_ok=True)

    return {
        "plugin_root": plugin_root,
        "config_dir": config_dir,
        "loops": loops_path,
        "digests": digests_path,
        "essences": essences_path,
    }


def _create_config_file(config_dir: Path) -> Path:
    """設定ファイルを作成"""
    config_data = {
        "base_dir": ".",
        "trusted_external_paths": [],
        "paths": {
            "loops_dir": "data/Loops",
            "digests_dir": "data/Digests",
            "essences_dir": "data/Essences",
            "identity_file_path": None,
        },
        "levels": {
            "weekly_threshold": 5,
            "monthly_threshold": 5,
            "quarterly_threshold": 3,
            "annual_threshold": 4,
            "triennial_threshold": 3,
            "decadal_threshold": 3,
            "multi_decadal_threshold": 3,
            "centurial_threshold": 4,
        },
    }
    config_file = config_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    return config_file


def _create_template_files(config_dir: Path) -> None:
    """テンプレートファイルを作成"""
    levels = [
        "weekly",
        "monthly",
        "quarterly",
        "annual",
        "triennial",
        "decadal",
        "multi_decadal",
        "centurial",
    ]

    # last_digest_times.template.json
    times_template = {level: {"timestamp": "", "last_processed": None} for level in levels}
    with open(config_dir / "last_digest_times.template.json", "w", encoding="utf-8") as f:
        json.dump(times_template, f, indent=2, ensure_ascii=False)

    # GrandDigest.template.txt
    grand_template = {
        "metadata": {"last_updated": None, "version": "1.0"},
        "major_digests": {level: {"overall_digest": None} for level in levels},
    }
    with open(config_dir / "GrandDigest.template.txt", "w", encoding="utf-8") as f:
        json.dump(grand_template, f, indent=2, ensure_ascii=False)

    # ShadowGrandDigest.template.txt
    shadow_template = {
        "metadata": {"last_updated": None, "version": "1.0"},
        "latest_digests": {level: {"overall_digest": None} for level in levels},
    }
    with open(config_dir / "ShadowGrandDigest.template.txt", "w", encoding="utf-8") as f:
        json.dump(shadow_template, f, indent=2, ensure_ascii=False)


def _create_essence_files(essences_path: Path) -> None:
    """Essenceファイルを作成"""
    levels = [
        "weekly",
        "monthly",
        "quarterly",
        "annual",
        "triennial",
        "decadal",
        "multi_decadal",
        "centurial",
    ]

    # GrandDigest.txt
    grand_data = {
        "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
        "major_digests": {level: {"overall_digest": None} for level in levels},
    }
    with open(essences_path / "GrandDigest.txt", "w", encoding="utf-8") as f:
        json.dump(grand_data, f, indent=2, ensure_ascii=False)

    # ShadowGrandDigest.txt
    shadow_data = {
        "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
        "latest_digests": {level: {"overall_digest": None} for level in levels},
    }
    with open(essences_path / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
        json.dump(shadow_data, f, indent=2, ensure_ascii=False)


def _create_times_file(config_dir: Path) -> Path:
    """last_digest_times.json を作成"""
    levels = [
        "weekly",
        "monthly",
        "quarterly",
        "annual",
        "triennial",
        "decadal",
        "multi_decadal",
        "centurial",
    ]
    times_data = {level: {"timestamp": "", "last_processed": None} for level in levels}
    times_file = config_dir / "last_digest_times.json"
    with open(times_file, "w", encoding="utf-8") as f:
        json.dump(times_data, f, indent=2, ensure_ascii=False)
    return times_file


@pytest.fixture
def configured_cli_env(cli_temp_dir: Path) -> Dict[str, Path]:
    """
    設定済みのCLI環境を提供

    - 完全なディレクトリ構造
    - 設定ファイル
    - テンプレートファイル
    - Essenceファイル
    - last_digest_times.json

    Returns:
        パスの辞書
    """
    paths = _create_full_plugin_structure(cli_temp_dir)
    _create_config_file(paths["config_dir"])
    _create_template_files(paths["config_dir"])
    _create_essence_files(paths["essences"])
    _create_times_file(paths["config_dir"])
    return paths


@pytest.fixture
def configured_cli_runner(configured_cli_env: Dict[str, Path]) -> CLIRunner:
    """
    設定済み環境のCLIRunnerを提供

    Usage:
        def test_something(configured_cli_runner):

            result = configured_cli_runner.run_digest_auto(output="json")
            result.assert_success()
    """
    return CLIRunner(plugin_root=configured_cli_env["plugin_root"])


# =============================================================================
# ヘルパーフィクスチャ
# =============================================================================


@pytest.fixture
def valid_config_json() -> str:
    """有効な設定JSON文字列を提供"""
    return json.dumps(
        {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
    )


@pytest.fixture
def sample_loop_json() -> str:
    """サンプルLoopファイルJSON"""
    return json.dumps(
        {
            "overall_digest": {
                "timestamp": "2025-01-01T00:00:00",
                "digest_type": "テスト",
                "keywords": ["test", "sample"],
                "abstract": "テスト用のループ内容です。",
                "impression": "テスト用の所感です。",
            }
        }
    )


@pytest.fixture
def sample_digest_json() -> str:
    """サンプルDigestファイルJSON"""
    return json.dumps(
        {
            "individual_digests": [
                {
                    "source_file": "L00001_test.txt",
                    "digest_type": "テスト",
                    "keywords": ["keyword1", "keyword2"],
                    "abstract": "テスト要約",
                    "impression": "テスト所感",
                }
            ]
        }
    )


def create_loop_file(loops_path: Path, loop_num: int, title: str = "test") -> Path:
    """
    Loopファイルを作成するヘルパー関数

    Args:
        loops_path: Loopsディレクトリ
        loop_num: Loop番号
        title: ファイルタイトル

    Returns:
        作成されたファイルのPath
    """
    filename = f"L{loop_num:05d}_{title}.txt"
    file_path = loops_path / filename

    loop_data = {
        "overall_digest": {
            "timestamp": "2025-01-01T00:00:00",
            "digest_type": "テスト",
            "keywords": ["test", "sample"],
            "abstract": f"L{loop_num:05d}のテスト内容です。",
            "impression": "テスト用の所感です。",
        }
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(loop_data, f, indent=2, ensure_ascii=False)

    return file_path
