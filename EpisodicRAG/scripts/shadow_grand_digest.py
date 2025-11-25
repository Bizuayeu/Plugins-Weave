#!/usr/bin/env python3
"""
ShadowGrandDigest Manager
=========================

GrandDigest更新後に作成された新しいコンテンツを保持し、
常に最新の知識にアクセス可能にするシステム

使用方法:
    from shadow_grand_digest import ShadowGrandDigestManager
    from config import DigestConfig

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    # 新しいLoopファイルを検出してShadowを更新
    manager.update_shadow_for_new_loops()

    # Weeklyダイジェスト確定時のカスケード処理
    manager.cascade_update_on_digest_finalize("weekly")
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Plugin版: config.pyをインポート
from config import DigestConfig, LEVEL_CONFIG, LEVEL_NAMES, PLACEHOLDER_LIMITS, extract_number_only
from utils import log_info, log_warning, load_json_with_template, save_json
from digest_times import DigestTimesTracker


class ShadowGrandDigestManager:
    """ShadowGrandDigest管理クラス（config.py統合版）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path
        self.loops_path = config.loops_path
        self.essences_path = config.essences_path

        # ファイルパスを設定
        self.grand_digest_file = self.essences_path / "GrandDigest.txt"
        self.shadow_digest_file = self.essences_path / "ShadowGrandDigest.txt"

        # DigestTimesTrackerを使用（重複コード排除）
        self.digest_times_tracker = DigestTimesTracker(config)

        # レベル設定（共通定数を参照）
        self.levels = LEVEL_NAMES
        self.level_hierarchy = {
            level: {"source": cfg["source"], "next": cfg["next"]}
            for level, cfg in LEVEL_CONFIG.items()
        }
        self.level_config = LEVEL_CONFIG

    def _create_empty_overall_digest(self) -> dict:
        """
        プレースホルダー付きoverall_digestを生成（Single Source of Truth）

        Returns:
            プレースホルダーを含むoverall_digest構造体
        """
        limits = PLACEHOLDER_LIMITS
        return {
            "timestamp": "<!-- PLACEHOLDER -->",
            "source_files": [],
            "digest_type": "<!-- PLACEHOLDER -->",
            "keywords": [f"<!-- PLACEHOLDER: keyword{i} -->" for i in range(1, limits["keyword_count"] + 1)],
            "abstract": f"<!-- PLACEHOLDER: 全体統合分析 ({limits['abstract_chars']}文字程度) -->",
            "impression": f"<!-- PLACEHOLDER: 所感・展望 ({limits['impression_chars']}文字程度) -->"
        }

    def get_template(self) -> dict:
        """ShadowGrandDigest.txtのテンプレートを返す"""
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト（下書き帳）"
            },
            "latest_digests": {
                level: {"overall_digest": self._create_empty_overall_digest()}
                for level in self.levels
            }
        }

    def load_or_create(self) -> dict:
        """ShadowGrandDigestを読み込む。存在しなければ作成"""
        return load_json_with_template(
            target_file=self.shadow_digest_file,
            default_factory=self.get_template,
            log_message="ShadowGrandDigest.txt not found. Creating new file."
        )

    def save(self, data: dict):
        """ShadowGrandDigestを保存"""
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        save_json(self.shadow_digest_file, data)

    def get_max_file_number(self, level: str) -> Optional[str]:
        """指定レベルの最大ファイル番号を取得"""
        times_data = self.digest_times_tracker.load_or_create()
        level_data = times_data.get(level, {})
        return level_data.get("last_processed")

    def extract_number_from_filename(self, filename: str) -> Optional[int]:
        """ファイル名から数値部分を抽出（共通関数を使用）"""
        return extract_number_only(filename)

    def find_new_files(self, level: str) -> List[Path]:
        """GrandDigest更新後に作成された新しいファイルを検出"""
        max_file_number = self.get_max_file_number(level)

        # ソースディレクトリとパターンを決定
        source_info = self.level_hierarchy[level]["source"]
        if source_info == "loops":
            source_dir = self.loops_path
            pattern = "Loop*.txt"
        else:
            config = self.level_config[source_info]
            source_dir = self.digests_path / config["dir"]
            pattern = f"{config['prefix']}*.txt"

        if not source_dir.exists():
            return []

        # ファイルを検出
        all_files = sorted(source_dir.glob(pattern))

        if max_file_number is None:
            # 初回は全ファイルを検出
            return all_files

        # 最大番号より大きいファイルを抽出
        max_num = self.extract_number_from_filename(max_file_number)

        # max_numがNoneの場合（max_file_numberが無効な場合）は全ファイルを返す
        if max_num is None:
            log_warning(f"Invalid max_file_number format: {max_file_number}, returning all files")
            return all_files

        new_files = []

        for file in all_files:
            file_num = self.extract_number_from_filename(file.name)
            if file_num is not None and file_num > max_num:
                new_files.append(file)

        return new_files

    def _get_source_path(self, level: str) -> Path:
        """
        指定レベルのソースファイルが格納されているディレクトリを返す

        Args:
            level: "weekly", "monthly", "quarterly"など

        Returns:
            Path: ソースファイルのディレクトリ
        """
        source_type = self.level_hierarchy[level]["source"]

        if source_type == "loops":
            # Weekly: Loopファイルを参照
            return self.loops_path
        else:
            # Monthly以上: 下位レベルのDigestファイルを参照
            source_config = self.level_config.get(source_type)
            if source_config:
                return self.digests_path / source_config["dir"]
            else:
                raise ValueError(f"Unknown source type: {source_type}")

    def add_files_to_shadow(self, level: str, new_files: List[Path]):
        """
        指定レベルのShadowに新しいファイルを追加（増分更新）

        Weekly: source_filesのみ追加（PLACEHOLDERのまま）→ Claude分析待ち
        Monthly以上: Digestファイル内容を読み込んでログ出力（まだらボケ回避）
        """
        shadow_data = self.load_or_create()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        # overall_digestがnullまたは非dict型の場合、初期化
        if overall_digest is None or not isinstance(overall_digest, dict):
            overall_digest = self._create_empty_overall_digest()
            shadow_data["latest_digests"][level]["overall_digest"] = overall_digest

        # source_filesがoverall_digest内に存在しない場合、初期化
        if "source_files" not in overall_digest:
            overall_digest["source_files"] = []

        # 既存のファイルリストを取得
        existing_files = set(overall_digest["source_files"])

        # レベルに応じたソースタイプを取得
        source_type = self.level_hierarchy[level]["source"]

        # 新しいファイルだけをsource_filesに追加
        added_count = 0
        for file_path in new_files:
            if file_path.name not in existing_files:
                overall_digest["source_files"].append(file_path.name)
                added_count += 1
                print(f"  + {file_path.name}")

                # Monthly以上: Digestファイルの内容を読み込んでログ出力（まだらボケ回避）
                if source_type != "loops":
                    source_dir = self._get_source_path(level)
                    full_path = source_dir / file_path.name

                    if full_path.exists() and full_path.suffix == '.txt':
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                digest_data = json.load(f)
                                # 型チェック
                                if not isinstance(digest_data, dict):
                                    log_warning(f"{file_path.name} is not a dict, skipping")
                                    continue
                                overall = digest_data.get("overall_digest")
                                if not isinstance(overall, dict):
                                    overall = {}

                                # ログ出力: Digestファイルから読み込んだ情報
                                log_info(f"Read digest content from {file_path.name}")
                                print(f"      - digest_type: {overall.get('digest_type', 'N/A')}")
                                print(f"      - keywords: {len(overall.get('keywords', []))} items")
                                print(f"      - abstract: {len(overall.get('abstract', ''))} chars")
                                print(f"      - impression: {len(overall.get('impression', ''))} chars")
                        except json.JSONDecodeError:
                            log_warning(f"Failed to parse {file_path.name} as JSON")
                        except Exception as e:
                            log_warning(f"Error reading {file_path.name}: {e}")

        # 既存分析がPLACEHOLDERかどうか確認
        total_files = len(overall_digest["source_files"])
        abstract = overall_digest.get("abstract", "")
        is_placeholder = (
            not abstract or  # 空文字列もプレースホルダー扱い
            (isinstance(abstract, str) and "<!-- PLACEHOLDER" in abstract)
        )

        if is_placeholder:
            # PLACEHOLDERの場合のみ更新（定数を使用）
            limits = PLACEHOLDER_LIMITS
            overall_digest["abstract"] = f"<!-- PLACEHOLDER: {total_files}ファイル分の全体統合分析 ({limits['abstract_chars']}文字程度) -->"
            overall_digest["impression"] = f"<!-- PLACEHOLDER: 所感・展望 ({limits['impression_chars']}文字程度) -->"
            overall_digest["keywords"] = [
                f"<!-- PLACEHOLDER: keyword{i} -->"
                for i in range(1, limits["keyword_count"] + 1)
            ]
            log_info(f"Initialized placeholder for {total_files} file(s)")
        else:
            # 既存の分析を保持
            log_info(f"Preserved existing analysis (now {total_files} file(s) total)")
            log_info(f"Claude should re-analyze all {total_files} files to integrate new content")

        self.save(shadow_data)
        log_info(f"Added {added_count} file(s) to ShadowGrandDigest.{level}")
        log_info(f"Total files in shadow: {total_files}")

    def clear_shadow_level(self, level: str):
        """指定レベルのShadowを初期化"""
        shadow_data = self.load_or_create()

        # overall_digestを空のプレースホルダーにリセット
        shadow_data["latest_digests"][level]["overall_digest"] = self._create_empty_overall_digest()

        self.save(shadow_data)
        log_info(f"Cleared ShadowGrandDigest for level: {level}")

    def get_shadow_digest_for_level(self, level: str) -> Optional[Dict[str, Any]]:
        """
        指定レベルのShadowダイジェストを取得

        finalize_from_shadow.pyで使用: これがRegularDigestの内容になります
        """
        shadow_data = self.load_or_create()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        if not overall_digest or not overall_digest.get("source_files"):
            log_info(f"No shadow digest for level: {level}")
            return None

        return overall_digest

    def promote_shadow_to_grand(self, level: str):
        """
        ShadowのレベルをGrandDigestに昇格

        注意: この機能は実際にはfinalize_from_shadow.pyの処理2で
        GrandDigestManagerが実行します。ここでは確認のみ。
        """
        digest = self.get_shadow_digest_for_level(level)

        if not digest:
            log_info(f"No shadow digest to promote for level: {level}")
            return

        file_count = len(digest.get("source_files", []))
        log_info(f"Shadow digest ready for promotion: {file_count} file(s)")
        # 実際の昇格処理はfinalize_from_shadow.pyで実行される

    def update_shadow_for_new_loops(self):
        """新しいLoopファイルを検出してShadowを増分更新"""
        # Shadowファイルを読み込み（存在しなければ作成）
        shadow_data = self.load_or_create()

        new_files = self.find_new_files("weekly")

        if not new_files:
            log_info("No new Loop files found")
            return

        log_info(f"Found {len(new_files)} new Loop file(s):")

        # Shadowに増分追加
        self.add_files_to_shadow("weekly", new_files)

    def cascade_update_on_digest_finalize(self, level: str):
        """
        ダイジェスト確定時のカスケード処理（処理3）

        処理内容:
        1. 現在のレベルのShadow → Grand に昇格（確認のみ、実際は処理2で完了）
        2. 次のレベルの新しいファイルを検出
        3. 次のレベルのShadowに増分追加
        4. 現在のレベルのShadowをクリア
        """
        print(f"\n[処理3] ShadowGrandDigest cascade for level: {level}")

        # 1. Shadow → Grand 昇格の確認
        self.promote_shadow_to_grand(level)

        # 2. 次のレベルの新しいファイルを検出
        next_level = self.level_hierarchy[level]["next"]
        if next_level:
            new_files = self.find_new_files(next_level)

            if new_files:
                log_info(f"Found {len(new_files)} new file(s) for {next_level}:")

                # 3. 次のレベルのShadowに増分追加
                self.add_files_to_shadow(next_level, new_files)
        else:
            log_info(f"No next level for {level} (top level)")

        # 4. 現在のレベルのShadowをクリア
        self.clear_shadow_level(level)

        print(f"[処理3] Cascade completed for level: {level}")


def main():
    """新しいLoopファイルを検出してShadowGrandDigest.weeklyに増分追加"""
    from pathlib import Path

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    print("="*60)
    print("ShadowGrandDigest Update - New Loop Detection")
    print("="*60)

    # 新しいLoopファイルの検出と追加
    manager.update_shadow_for_new_loops()

    print("\n" + "="*60)
    print("Placeholder added to ShadowGrandDigest.weekly")
    print("="*60)
    print("")
    print("[!] WARNING: Claude analysis required immediately!")
    print("Without analysis, memory fragmentation (madaraboke) occurs.")
    print("="*60)


if __name__ == "__main__":
    main()
