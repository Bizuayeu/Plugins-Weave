#!/usr/bin/env python3
"""
Digest Times Tracker
====================

last_digest_times.json の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import DigestConfig, LEVEL_CONFIG, LEVEL_NAMES, extract_file_number
from utils import log_info, load_json_with_template, save_json, log_warning


class DigestTimesTracker:
    """last_digest_times.json 管理クラス"""

    def __init__(self, config: DigestConfig):
        self.config = config
        self.last_digest_file = config.plugin_root / ".claude-plugin" / "last_digest_times.json"
        self.template_file = config.plugin_root / ".claude-plugin" / "last_digest_times.template.json"

    def _get_default_template(self) -> dict:
        """テンプレートがない場合のデフォルト構造を返す"""
        return {level: {"timestamp": "", "last_processed": None} for level in LEVEL_NAMES}

    def load_or_create(self) -> dict:
        """最終ダイジェスト生成時刻を読み込む（存在しなければテンプレートから初期化）"""
        return load_json_with_template(
            target_file=self.last_digest_file,
            template_file=self.template_file,
            default_factory=self._get_default_template,
            log_message="Initialized last_digest_times.json from template"
        )

    def extract_file_numbers(self, level: str, input_files: List[str]) -> List[str]:
        """ファイル名から連番を抽出（プレフィックス付き、ゼロ埋め維持）"""
        # None/空チェック
        if input_files is None:
            return []

        # 型チェック
        if not isinstance(input_files, list):
            log_warning(f"input_files is not a list: {type(input_files).__name__}")
            return []

        if not input_files:
            return []

        # プレフィックス→レベル の逆引きマップ
        prefix_to_level = {cfg["prefix"]: lvl for lvl, cfg in LEVEL_CONFIG.items()}

        numbers = []
        for file in input_files:
            # 各要素の型チェック
            if not isinstance(file, str):
                log_warning(f"Skipping non-string file: {file}")
                continue
            result = extract_file_number(file)
            if result:
                prefix, num = result
                # ゼロ埋めを維持した文字列を生成
                if prefix == "Loop":
                    numbers.append(f"Loop{num:04d}")
                else:
                    # プレフィックスからソースファイルのレベルを特定
                    source_level = prefix_to_level.get(prefix)
                    if source_level:
                        digits = LEVEL_CONFIG[source_level]["digits"]
                    else:
                        digits = 4  # fallback
                    numbers.append(f"{prefix}{num:0{digits}d}")

        return sorted(numbers)

    def save(self, level: str, input_files: List[str] = None):
        """最終ダイジェスト生成時刻と最新処理済みファイル番号を保存"""
        # 空リスト警告
        if input_files is not None and len(input_files) == 0:
            log_warning(f"Empty input_files list for level: {level}")

        times = self.load_or_create()

        # 連番を抽出
        file_numbers = self.extract_file_numbers(level, input_files)

        # 最後の要素のみを保存
        last_file = file_numbers[-1] if file_numbers else None

        # 保存
        times[level] = {
            "timestamp": datetime.now().isoformat(),
            "last_processed": last_file
        }

        save_json(self.last_digest_file, times)

        log_info(f"Updated last_digest_times.json for level: {level}")
        if last_file:
            log_info(f"Last processed: {last_file}")
