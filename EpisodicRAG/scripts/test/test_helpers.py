#!/usr/bin/env python3
"""
Test Helpers Module
===================

共通テストヘルパー関数とフィクスチャを提供。
本番環境と同一のディレクトリ構造を作成し、テスト間で一貫性を確保。
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# 本番環境と同じディレクトリ構造定義
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


def create_standard_test_structure(base_path: Path) -> Dict[str, Path]:
    """
    本番環境と同一のディレクトリ構造を作成

    Args:
        base_path: テスト用の一時ディレクトリ

    Returns:
        作成されたパスの辞書:
        {
            "plugin_root": Path,
            "loops": Path,
            "digests": Path,
            "essences": Path,
            "config_dir": Path,
        }

    Note:
        正しい構造は各レベルディレクトリ内にProvisionalを配置:
        Digests/1_Weekly/Provisional/ (正しい)
        Digests/Provisional/1_Weekly/ (間違い)
    """
    plugin_root = base_path
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

    # 各レベルディレクトリとProvisional（レベル内に配置）
    for level_dir in LEVEL_DIRS:
        level_path = digests_path / level_dir
        level_path.mkdir(exist_ok=True)
        # 正しい構造: Provisional は各レベルディレクトリの中
        (level_path / "Provisional").mkdir(exist_ok=True)

    return {
        "plugin_root": plugin_root,
        "loops": loops_path,
        "digests": digests_path,
        "essences": essences_path,
        "config_dir": config_dir,
    }


def create_default_config(config_dir: Path, base_dir: str = ".") -> Path:
    """
    テスト用のconfig.jsonを作成

    Args:
        config_dir: .claude-pluginディレクトリ
        base_dir: 基準ディレクトリ設定

    Returns:
        作成されたconfig.jsonのPath
    """
    config_data = {
        "base_dir": base_dir,
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
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    return config_file


def create_default_templates(config_dir: Path) -> None:
    """
    テスト用のテンプレートファイルを作成

    Args:
        config_dir: .claude-pluginディレクトリ
    """
    # last_digest_times.template.json
    times_template = {
        level: {"timestamp": "", "last_processed": None}
        for level in [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]
    }
    with open(config_dir / "last_digest_times.template.json", 'w', encoding='utf-8') as f:
        json.dump(times_template, f, indent=2, ensure_ascii=False)

    # GrandDigest.template.txt
    grand_template = {
        "metadata": {"last_updated": None, "version": "1.0"},
        "major_digests": {
            level: {"overall_digest": None}
            for level in [
                "weekly",
                "monthly",
                "quarterly",
                "annual",
                "triennial",
                "decadal",
                "multi_decadal",
                "centurial",
            ]
        },
    }
    with open(config_dir / "GrandDigest.template.txt", 'w', encoding='utf-8') as f:
        json.dump(grand_template, f, indent=2, ensure_ascii=False)

    # ShadowGrandDigest.template.txt
    shadow_template = {
        "metadata": {"last_updated": None, "version": "1.0"},
        "latest_digests": {
            level: {"overall_digest": None}
            for level in [
                "weekly",
                "monthly",
                "quarterly",
                "annual",
                "triennial",
                "decadal",
                "multi_decadal",
                "centurial",
            ]
        },
    }
    with open(config_dir / "ShadowGrandDigest.template.txt", 'w', encoding='utf-8') as f:
        json.dump(shadow_template, f, indent=2, ensure_ascii=False)


def create_test_loop_file(loops_path: Path, loop_num: int, title: str = "test") -> Path:
    """
    テスト用のLoopファイルを作成

    Args:
        loops_path: Loopsディレクトリ
        loop_num: Loop番号
        title: ファイルタイトル

    Returns:
        作成されたLoopファイルのPath
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

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(loop_data, f, indent=2, ensure_ascii=False)

    return file_path


class TempPluginEnvironment:
    """
    テスト用の一時プラグイン環境を管理するコンテキストマネージャー

    Usage:
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)
            # ... テスト実行 ...
    """

    def __init__(self):
        self.temp_dir: Optional[Path] = None
        self.paths: Optional[Dict[str, Path]] = None

    def __enter__(self) -> "TempPluginEnvironment":
        self.temp_dir = Path(tempfile.mkdtemp())
        self.paths = create_standard_test_structure(self.temp_dir)
        create_default_config(self.paths["config_dir"])
        create_default_templates(self.paths["config_dir"])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @property
    def plugin_root(self) -> Path:
        return self.paths["plugin_root"]

    @property
    def loops_path(self) -> Path:
        return self.paths["loops"]

    @property
    def digests_path(self) -> Path:
        return self.paths["digests"]

    @property
    def essences_path(self) -> Path:
        return self.paths["essences"]

    @property
    def config_dir(self) -> Path:
        return self.paths["config_dir"]

    def create_grand_digest(self, initial_data: Optional[Dict[str, Any]] = None) -> Path:
        """
        GrandDigest.txt を作成

        Args:
            initial_data: 初期データ（省略時はデフォルトテンプレート）

        Returns:
            作成されたファイルのPath
        """
        data = initial_data or {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {
                level: {"overall_digest": None}
                for level in [
                    "weekly",
                    "monthly",
                    "quarterly",
                    "annual",
                    "triennial",
                    "decadal",
                    "multi_decadal",
                    "centurial",
                ]
            },
        }
        file_path = self.essences_path / "GrandDigest.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def create_shadow_digest(
        self,
        level: str = "weekly",
        source_files: Optional[list] = None,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        ShadowGrandDigest.txt を作成

        Args:
            level: 設定するレベル
            source_files: source_filesリスト
            initial_data: 初期データ全体（省略時は自動生成）

        Returns:
            作成されたファイルのPath
        """
        if initial_data is None:
            data = {
                "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
                "latest_digests": {
                    lv: {"overall_digest": None}
                    for lv in [
                        "weekly",
                        "monthly",
                        "quarterly",
                        "annual",
                        "triennial",
                        "decadal",
                        "multi_decadal",
                        "centurial",
                    ]
                },
            }
            if source_files:
                data["latest_digests"][level] = {
                    "overall_digest": {
                        "source_files": source_files,
                        "digest_type": "テスト",
                        "keywords": ["keyword1", "keyword2"],
                        "abstract": "テスト用の要約です。",
                        "impression": "テスト用の所感です。",
                    }
                }
        else:
            data = initial_data

        file_path = self.essences_path / "ShadowGrandDigest.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def create_last_digest_times(self) -> Path:
        """
        last_digest_times.json を作成

        Returns:
            作成されたファイルのPath
        """
        data = {
            level: {"timestamp": "", "last_processed": None}
            for level in [
                "weekly",
                "monthly",
                "quarterly",
                "annual",
                "triennial",
                "decadal",
                "multi_decadal",
                "centurial",
            ]
        }
        file_path = self.config_dir / "last_digest_times.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path
