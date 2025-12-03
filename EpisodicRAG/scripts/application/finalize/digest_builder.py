#!/usr/bin/env python3
"""
Digest Builder
==============

RegularDigest（確定済みダイジェスト）の構造を構築するアプリケーション層モジュール。

RegularDigestは、ShadowGrandDigestからfinalize（確定）されたダイジェストファイル。
各階層レベル（Weekly, Monthly等）のDigestsディレクトリに保存される永続的な記録。

Usage:
    from application.finalize import RegularDigestBuilder

    # RegularDigest構造を構築
    regular_digest = RegularDigestBuilder.build(
        level="weekly",
        new_digest_name="2025年11月第4週",
        digest_num="0042",
        shadow_digest=shadow_overall_digest,
        individual_digests=individual_list
    )

    # ファイルに保存
    save_json(digests_path / "1_Weekly" / "W0042_2025年11月第4週.txt", regular_digest)

Design Pattern:
    - Builder Pattern: 複雑なRegularDigest構造の組み立て
    - Static Factory: インスタンス不要の構築メソッド

Related Modules:
    - interfaces.finalize_from_shadow: このBuilderを使用
    - domain.types: RegularDigestData型定義
    - application.shadow: Shadow側のデータ提供

Note:
    RegularDigestは以下の構造を持つ：
    - metadata: level, number, timestamp, version
    - overall_digest: 統合要約（name, type, keywords, abstract, impression）
    - individual_digests: 個別要約のリスト
"""

from datetime import datetime
from typing import List

from domain.text_utils import extract_long_value
from domain.types import IndividualDigestData, OverallDigestData, RegularDigestData
from domain.version import DIGEST_FORMAT_VERSION


class RegularDigestBuilder:
    """
    RegularDigest（確定済みダイジェスト）構造を構築するBuilderクラス。

    このクラスはBuilder Patternを採用し、ShadowGrandDigestの
    overall_digestとindividual_digestsから、保存可能な
    RegularDigest構造を組み立てる。

    全メソッドがstaticmethodのため、インスタンス化不要。

    Example:
        >>> digest = RegularDigestBuilder.build(
        ...     level="weekly",
        ...     new_digest_name="2025年11月第4週",
        ...     digest_num="0042",
        ...     shadow_digest=shadow_data,
        ...     individual_digests=individuals
        ... )
        >>> digest["metadata"]["digest_level"]
        'weekly'

    Note:
        build()はmetadata.last_updatedを現在時刻で自動設定する。
        abstract/impressionはstring型とlong/shortオブジェクト型の両方に対応。
    """

    @staticmethod
    def _extract_long_value(value, default: str = "") -> str:
        """
        abstract/impression から long 版の値を抽出する。

        Args:
            value: LongShortText型 {"long": str, "short": str}
            default: 値が取得できない場合のデフォルト値

        Returns:
            long版の文字列

        Example:
            >>> RegularDigestBuilder._extract_long_value({"long": "2400字", "short": "1200字"})
            '2400字'

        Note:
            この実装はdomain.text_utils.extract_long_valueに委譲しています。
        """
        return extract_long_value(value, default)

    @staticmethod
    def build(
        level: str,
        new_digest_name: str,
        digest_num: str,
        shadow_digest: OverallDigestData,
        individual_digests: List[IndividualDigestData],
    ) -> RegularDigestData:
        """
        RegularDigest構造を作成

        Args:
            level: ダイジェストレベル
            new_digest_name: 新しいダイジェスト名
            digest_num: ダイジェスト番号
            shadow_digest: Shadowダイジェストデータ
            individual_digests: 個別ダイジェストのリスト

        Returns:
            RegularDigest構造体

        Example:
            >>> shadow = {"digest_type": "開発", "keywords": ["MCP"], "abstract": "...", "impression": "...", "source_files": ["W0001.txt"]}
            >>> individuals = [{"source_file": "W0001.txt", "digest_type": "開発", "keywords": ["API"], "abstract": "...", "impression": "..."}]
            >>> result = RegularDigestBuilder.build("monthly", "2025年11月", "0001", shadow, individuals)
            >>> result["metadata"]["digest_level"]
            'monthly'
            >>> result["overall_digest"]["name"]
            '2025年11月'
        """
        source_files = shadow_digest.get("source_files", [])

        # abstract/impression は string型 または {"long": str, "short": str} 型に対応
        # overall_digest には long 版を使用
        abstract = RegularDigestBuilder._extract_long_value(
            shadow_digest.get("abstract", "")
        )
        impression = RegularDigestBuilder._extract_long_value(
            shadow_digest.get("impression", "")
        )

        return {
            "metadata": {
                "digest_level": level,
                "digest_number": digest_num,
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION,
            },
            "overall_digest": {
                "name": new_digest_name,
                "timestamp": datetime.now().isoformat(),
                "source_files": source_files,
                "digest_type": shadow_digest.get("digest_type", "統合"),
                "keywords": shadow_digest.get("keywords", []),
                "abstract": abstract,
                "impression": impression,
            },
            "individual_digests": individual_digests,
        }
