#!/usr/bin/env python3
"""
Digest Builder
==============

RegularDigest構造を構築するクラス
"""

from datetime import datetime
from typing import Dict, Any, List

from __version__ import DIGEST_FORMAT_VERSION


class RegularDigestBuilder:
    """RegularDigest構造の構築を担当"""

    @staticmethod
    def build(
        level: str,
        new_digest_name: str,
        digest_num: str,
        shadow_digest: Dict[str, Any],
        individual_digests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
        """
        source_files = shadow_digest.get("source_files", [])

        return {
            "metadata": {
                "digest_level": level,
                "digest_number": digest_num,
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION
            },
            "overall_digest": {
                "name": new_digest_name,
                "timestamp": datetime.now().isoformat(),
                "source_files": source_files,
                "digest_type": shadow_digest.get("digest_type", "統合"),
                "keywords": shadow_digest.get("keywords", []),
                "abstract": shadow_digest.get("abstract", ""),
                "impression": shadow_digest.get("impression", "")
            },
            "individual_digests": individual_digests
        }
