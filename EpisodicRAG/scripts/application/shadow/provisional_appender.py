#!/usr/bin/env python3
"""
Provisional Appender
====================

カスケード処理時、確定したダイジェストを次レベルのProvisionalに追加する。

ダイジェストがfinalize（確定）された際、次の階層レベルの
Provisionalファイルに、確定ダイジェストのoverall_digestを
individual_digestエントリとして追加する。

Usage:
    from application.shadow.provisional_appender import ProvisionalAppender

    appender = ProvisionalAppender(config, level_hierarchy)
    appender.append_to_next_provisional("weekly", finalized_digest)

Related Modules:
    - application.shadow.cascade_processor: カスケード処理本体
    - application.finalize.persistence: 永続化処理
    - interfaces.finalize_from_shadow: 確定処理の起点
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from application.config import DigestConfig
from domain.constants import LEVEL_CONFIG
from domain.types import LevelConfigData, LevelHierarchyEntry, RegularDigestData
from infrastructure import get_structured_logger, save_json, try_read_json_from_file

__all__ = ["ProvisionalAppender"]

_logger = get_structured_logger(__name__)


class ProvisionalAppender:
    """
    次レベルのProvisionalへのダイジェスト追加を担当するクラス。

    カスケード処理の一環として、確定したダイジェストを
    次レベルのProvisionalファイルに追加する。

    Attributes:
        config: DigestConfig インスタンス
        level_hierarchy: レベル階層情報
    """

    def __init__(
        self,
        config: DigestConfig,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
    ):
        """
        初期化

        Args:
            config: DigestConfig インスタンス
            level_hierarchy: レベル階層情報
        """
        self.config = config
        self.level_hierarchy = level_hierarchy
        self.level_config = LEVEL_CONFIG

    def _get_next_level(self, level: str) -> Optional[str]:
        """
        次のレベルを取得

        Args:
            level: 現在のレベル名

        Returns:
            次のレベル名、または最上位の場合はNone
        """
        return self.level_hierarchy[level]["next"]

    def _find_or_create_provisional_path(self, next_level: str) -> Path:
        """
        次レベルのProvisionalファイルパスを取得（存在しなければ作成準備）

        常にRegularDigestディレクトリから正しい次番号を取得し、
        その番号と一致するProvisionalファイルが存在すれば再利用する。
        番号が異なる古いProvisionalファイルがあれば警告ログを出力。

        Args:
            next_level: 次レベル名

        Returns:
            Provisionalファイルのパス
        """
        provisional_dir = self.config.get_provisional_dir(next_level)
        provisional_dir.mkdir(parents=True, exist_ok=True)

        level_cfg = self.level_config[next_level]
        prefix = level_cfg["prefix"]
        digits = level_cfg["digits"]

        # 常にRegularDigestから正しい次番号を取得
        # NOTE: 循環インポート回避のためローカルインポート
        from interfaces.interface_helpers import get_next_digest_number

        next_number = get_next_digest_number(self.config.digests_path, next_level)
        formatted_number = str(next_number).zfill(digits)
        expected_filename = f"{prefix}{formatted_number}_Individual.txt"
        expected_path = provisional_dir / expected_filename

        # 既存ファイルが正しい番号であれば再利用
        if expected_path.exists():
            return expected_path

        # 番号が異なる古いProvisionalファイルがあれば警告ログ
        pattern = f"{prefix}*_Individual.txt"
        existing_files = list(provisional_dir.glob(pattern))
        if existing_files:
            _logger.info(
                f"[WARN] 古いProvisionalファイルが存在: {[f.name for f in existing_files]}. "
                f"正しい番号は {expected_filename}"
            )

        return expected_path

    def _load_or_create_provisional(
        self, provisional_path: Path, next_level: str
    ) -> Dict[str, Any]:
        """
        Provisionalファイルを読み込み、存在しなければ新規作成

        Args:
            provisional_path: Provisionalファイルのパス
            next_level: 次レベル名

        Returns:
            Provisionalデータ辞書
        """
        if provisional_path.exists():
            data = try_read_json_from_file(provisional_path)
            if data is not None:
                return data

        # 新規作成
        level_cfg = self.level_config[next_level]
        prefix = level_cfg["prefix"]
        # パス名から番号を抽出
        filename = provisional_path.stem  # e.g., "M0011_Individual"
        digest_num = filename.replace(f"{prefix}", "").replace("_Individual", "")

        return {
            "metadata": {
                "digest_level": next_level,
                "digest_number": digest_num,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
            },
            "individual_digests": [],
        }

    def _build_individual_entry(self, finalized_digest: RegularDigestData) -> Dict[str, Any]:
        """
        確定ダイジェストから個別エントリを構築

        確定したダイジェストのoverall_digestを、
        次レベルのProvisionalのindividual_digest形式に変換。

        Args:
            finalized_digest: 確定したRegularDigest

        Returns:
            individual_digestエントリ辞書
        """
        metadata = finalized_digest.get("metadata", {})
        overall = finalized_digest.get("overall_digest", {})

        # ファイル名を構築: overall_digest.name にフル名が格納されている
        # (e.g., "W0053_タイトル" → "W0053_タイトル.txt")
        level = metadata.get("digest_level", "")
        level_cfg: Union[LevelConfigData, Dict[str, Any]] = self.level_config.get(level, {})
        prefix = level_cfg.get("prefix", "X")
        digest_num = metadata.get("digest_number", "0000")

        # overall_digest.name からフル名を取得（なければフォールバック）
        digest_name = overall.get("name", f"{prefix}{digest_num}")
        filename = f"{digest_name}.txt"

        return {
            "source_file": filename,  # digest_readiness.pyとの整合性のためsource_fileを使用
            "digest_type": overall.get("digest_type", ""),
            "keywords": overall.get("keywords", []),
            "abstract": overall.get("abstract", ""),
            "impression": overall.get("impression", ""),
        }

    def _is_duplicate(
        self, individual_digests: List[Dict[str, Any]], new_entry: Dict[str, Any]
    ) -> bool:
        """
        重複チェック

        Args:
            individual_digests: 既存のindividual_digestsリスト
            new_entry: 追加しようとする新エントリ

        Returns:
            重複していればTrue
        """
        new_source_file = new_entry.get("source_file", "")
        # プレフィックス+番号でマッチング (e.g., "W0053" の部分)
        new_base = new_source_file.split("_")[0].replace(".txt", "")

        for existing in individual_digests:
            # 既存データは filename または source_file のどちらかを持つ可能性がある
            existing_source_file = existing.get("source_file") or existing.get("filename", "")
            existing_base = existing_source_file.split("_")[0].replace(".txt", "")
            if new_base == existing_base:
                return True
        return False

    def append_to_next_provisional(self, level: str, finalized_digest: RegularDigestData) -> None:
        """
        次レベルのProvisionalに確定ダイジェストを追加

        Args:
            level: 確定したダイジェストのレベル
            finalized_digest: 確定したRegularDigest

        Example:
            >>> appender = ProvisionalAppender(config, level_hierarchy)
            >>> appender.append_to_next_provisional("weekly", finalized_digest)
            # M0011_Individual.txt に W0053 のエントリが追加される
        """
        # 次レベルを取得
        next_level = self._get_next_level(level)

        if next_level is None:
            _logger.info(f"{level}に上位レベルなし（最上位）、Provisional追加スキップ")
            return

        _logger.info(f"次レベルProvisionalへの追加開始: {level} → {next_level}")

        # Provisionalファイルのパスを取得
        provisional_path = self._find_or_create_provisional_path(next_level)
        _logger.info(f"Provisionalファイル: {provisional_path.name}")

        # Provisionalデータを読み込みまたは作成
        provisional_data = self._load_or_create_provisional(provisional_path, next_level)

        # 個別エントリを構築
        new_entry = self._build_individual_entry(finalized_digest)
        _logger.info(f"追加エントリ: {new_entry.get('filename', 'unknown')}")

        # 重複チェック
        individual_digests = provisional_data.get("individual_digests", [])
        if self._is_duplicate(individual_digests, new_entry):
            _logger.info(f"重複のためスキップ: {new_entry.get('filename', 'unknown')}")
            return

        # 追加
        individual_digests.append(new_entry)
        provisional_data["individual_digests"] = individual_digests

        # メタデータ更新
        provisional_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 保存
        save_json(provisional_path, provisional_data)
        _logger.info(f"Provisional追加完了: {provisional_path.name}")
