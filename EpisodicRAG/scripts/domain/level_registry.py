#!/usr/bin/env python3
"""
Level Registry - Strategy Pattern for Level-specific Behavior
==============================================================

レベル固有の振る舞いを拡張可能な方法で管理するRegistry。
Open/Closed Principle (OCP) を実現：コード修正なしで新レベルを追加可能。

Usage:
    from domain.level_registry import get_level_registry

    registry = get_level_registry()

    # レベル情報の取得
    metadata = registry.get_metadata("weekly")
    print(metadata.prefix)  # "W"

    # フォーマット（Strategy経由）
    behavior = registry.get_behavior("weekly")
    formatted = behavior.format_number(42)  # "W0042"

    # カスケード判定
    if registry.should_cascade("weekly"):
        # 次レベルへ伝播

Architecture:
    - LevelMetadata: 不変のレベルプロパティ（dataclass）
    - LevelBehavior: レベル固有の振る舞い（Strategy interface）
    - StandardLevelBehavior: 通常レベルの実装
    - LoopLevelBehavior: Loopファイル専用の実装
    - LevelRegistry: レベルとBehaviorのレジストリ（Singleton）
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from domain.constants import LEVEL_CONFIG
from domain.exceptions import ConfigError

# =============================================================================
# Metadata: 不変のレベルプロパティ
# =============================================================================


@dataclass(frozen=True)
class LevelMetadata:
    """
    レベルの不変プロパティ

    Attributes:
        name: レベル名（例: "weekly", "monthly"）
        prefix: ファイル名プレフィックス（例: "W", "M", "Loop"）
        digits: 番号の桁数（例: 4 -> W0001）
        dir: digests_path以下のサブディレクトリ名
        source: この階層を生成する際の入力元
        next_level: 確定時にカスケードする上位階層（None = 最上位）
    """

    name: str
    prefix: str
    digits: int
    dir: str
    source: str
    next_level: Optional[str]


# =============================================================================
# Strategy Interface: レベル固有の振る舞い
# =============================================================================


class LevelBehavior(ABC):
    """
    レベル固有の振る舞いを定義するStrategy interface

    新しい振る舞いが必要な場合、このクラスを継承して実装を追加。
    既存コードを修正せずに拡張可能（OCP準拠）。
    """

    @abstractmethod
    def format_number(self, number: int) -> str:
        """
        番号をレベル固有のフォーマットに変換

        Args:
            number: フォーマットする番号

        Returns:
            フォーマットされた文字列（例: "W0042", "L00186"）
        """
        pass

    @abstractmethod
    def should_cascade(self) -> bool:
        """
        このレベルが次レベルへカスケードするかどうか

        Returns:
            True: 次レベルへカスケードする
            False: カスケードしない（最上位、または特殊レベル）
        """
        pass


# =============================================================================
# Strategy Implementations
# =============================================================================


class StandardLevelBehavior(LevelBehavior):
    """
    通常ダイジェストレベルの振る舞い

    LEVEL_CONFIGで定義された標準的なダイジェストレベル用。
    """

    def __init__(self, metadata: LevelMetadata):
        """
        Args:
            metadata: このレベルのメタデータ
        """
        self.metadata = metadata

    def format_number(self, number: int) -> str:
        """プレフィックス + ゼロパディング番号"""
        return f"{self.metadata.prefix}{number:0{self.metadata.digits}d}"

    def should_cascade(self) -> bool:
        """次レベルが存在すればカスケードする"""
        return self.metadata.next_level is not None


class LoopLevelBehavior(LevelBehavior):
    """
    Loopファイル専用の振る舞い

    Loopファイルは特殊なフォーマット（L00001）を持ち、
    カスケードは行わない。
    """

    def format_number(self, number: int) -> str:
        """L + 5桁ゼロパディング"""
        return f"L{number:05d}"

    def should_cascade(self) -> bool:
        """Loopはカスケードしない"""
        return False


# =============================================================================
# Registry: レベルとBehaviorの管理
# =============================================================================


class LevelRegistry:
    """
    レベルとその振る舞いを管理するRegistry

    Open/Closed Principleを実現：
    - 新レベル追加: LEVEL_CONFIGに追加するだけ
    - 新しい振る舞い: LevelBehaviorを継承して登録

    Singleton: get_level_registry()でアクセス
    """

    def __init__(self) -> None:
        """Registryを初期化し、LEVEL_CONFIGからレベルを登録"""
        self._levels: Dict[str, tuple[LevelMetadata, LevelBehavior]] = {}
        self._prefix_to_level: Dict[str, str] = {}
        self._initialize_from_config()

    def _initialize_from_config(self) -> None:
        """LEVEL_CONFIGからレベルを登録"""
        for level_name, config in LEVEL_CONFIG.items():
            # Extract values with proper type casting
            next_val = config["next"]
            next_level: Optional[str] = str(next_val) if next_val else None
            metadata = LevelMetadata(
                name=level_name,
                prefix=str(config["prefix"]),
                digits=int(str(config["digits"])),
                dir=str(config["dir"]),
                source=str(config["source"]),
                next_level=next_level,
            )
            behavior = StandardLevelBehavior(metadata)
            self._register(level_name, metadata, behavior)

        # 特殊レベル: Loop
        loop_metadata = LevelMetadata(
            name="loop",
            prefix="L",
            digits=5,
            dir="",
            source="",
            next_level="weekly",
        )
        self._register("loop", loop_metadata, LoopLevelBehavior())

    def _register(
        self, name: str, metadata: LevelMetadata, behavior: LevelBehavior
    ) -> None:
        """
        レベルを登録（内部メソッド）

        Args:
            name: レベル名
            metadata: レベルメタデータ
            behavior: レベルの振る舞い
        """
        self._levels[name] = (metadata, behavior)
        self._prefix_to_level[metadata.prefix] = name

    def get_behavior(self, level: str) -> LevelBehavior:
        """
        レベルの振る舞いを取得

        Args:
            level: レベル名

        Returns:
            LevelBehavior実装

        Raises:
            ConfigError: 不明なレベル名の場合
        """
        if level not in self._levels:
            raise ConfigError(f"Unknown level: '{level}'")
        return self._levels[level][1]

    def get_metadata(self, level: str) -> LevelMetadata:
        """
        レベルのメタデータを取得

        Args:
            level: レベル名

        Returns:
            LevelMetadata

        Raises:
            ConfigError: 不明なレベル名の場合
        """
        if level not in self._levels:
            raise ConfigError(f"Unknown level: '{level}'")
        return self._levels[level][0]

    def get_level_names(self) -> List[str]:
        """
        登録されたレベル名一覧を取得（'loop'を除く）

        Returns:
            レベル名のリスト（LEVEL_CONFIGの順序を保持）
        """
        return [name for name in self._levels.keys() if name != "loop"]

    def get_all_level_names(self) -> List[str]:
        """
        全ての登録レベル名を取得（'loop'を含む）

        Returns:
            全レベル名のリスト
        """
        return list(self._levels.keys())

    def get_all_prefixes(self) -> List[str]:
        """
        全プレフィックスを長さ順（降順）で取得

        長いプレフィックスを先にすることで、正規表現マッチ時に
        "MD"が"M"より先にマッチする。

        Returns:
            プレフィックスのリスト（長さ降順）
        """
        return sorted(self._prefix_to_level.keys(), key=len, reverse=True)

    def get_level_by_prefix(self, prefix: str) -> Optional[str]:
        """
        プレフィックスからレベル名を逆引き

        Args:
            prefix: ファイル名プレフィックス

        Returns:
            レベル名、または見つからない場合None
        """
        return self._prefix_to_level.get(prefix)

    def should_cascade(self, level: str) -> bool:
        """
        レベルがカスケードするかどうかを判定

        Args:
            level: レベル名

        Returns:
            カスケードする場合True
        """
        return self.get_behavior(level).should_cascade()

    def build_prefix_pattern(self) -> str:
        """
        全プレフィックスの正規表現パターンを生成

        長いプレフィックスを先にして、"MD"が"M"より先にマッチするようにする。

        Returns:
            正規表現パターン文字列（例: "MD|W|M|Q|A|T|D|C|L"）
        """
        prefixes = self.get_all_prefixes()
        return "|".join(re.escape(p) for p in prefixes)


# =============================================================================
# Singleton アクセサ
# =============================================================================

_registry: Optional[LevelRegistry] = None


def get_level_registry() -> LevelRegistry:
    """
    LevelRegistryのSingletonインスタンスを取得

    Returns:
        LevelRegistryインスタンス

    Example:
        registry = get_level_registry()
        metadata = registry.get_metadata("weekly")
    """
    global _registry
    if _registry is None:
        _registry = LevelRegistry()
    return _registry


def reset_level_registry() -> None:
    """
    Registryをリセット（テスト用）

    テスト間でRegistryの状態をクリアするために使用。
    """
    global _registry
    _registry = None
