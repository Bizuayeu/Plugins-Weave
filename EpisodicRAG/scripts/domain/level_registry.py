#!/usr/bin/env python3
"""
Level Registry - Registry for Levels and Behaviors
===================================================

レベルとその振る舞いを管理するRegistry。

## 使用デザインパターン

### Singleton Pattern
get_level_registry()でアクセスするSingletonインスタンス。
レベル設定はアプリケーション全体で不変かつ共有されるため、
複数インスタンスを作成する意味がない。

テスト時はreset_level_registry()でリセット可能。

## SOLID原則の実践

### OCP (Open/Closed Principle)
- 新レベル追加: LEVEL_CONFIGに設定を追加するだけ
- 新振る舞い: LevelBehaviorを継承してRegisterに登録
- 既存コードの修正は一切不要

### SRP (Single Responsibility Principle)
- LevelMetadata: レベルの静的プロパティのみ (level_metadata.py)
- LevelBehavior: レベル固有の動的振る舞いのみ (level_behaviors.py)
- LevelRegistry: レベルとBehaviorの登録・取得のみ (このファイル)

Usage:
    from domain.level_registry import get_level_registry

    registry = get_level_registry()

    # レベル情報の取得
    metadata = registry.get_metadata("weekly")
    metadata.prefix  # "W"

    # フォーマット（Strategy経由）
    behavior = registry.get_behavior("weekly")
    formatted = behavior.format_number(42)  # "W0042"

    # カスケード判定
    if registry.should_cascade("weekly"):
        # 次レベルへ伝播

Architecture:
    - LevelMetadata: 不変のレベルプロパティ（dataclass） → level_metadata.py
    - LevelBehavior: レベル固有の振る舞い（Strategy interface） → level_behaviors.py
    - LevelRegistry: レベルとBehaviorのレジストリ（Singleton） → このファイル
"""

import re
from typing import Dict, List, Optional

from domain.constants import LEVEL_CONFIG
from domain.error_formatter import get_error_formatter
from domain.exceptions import ConfigError
from domain.level_behaviors import (
    LevelBehavior,
    LoopLevelBehavior,
    StandardLevelBehavior,
)
from domain.level_metadata import LevelMetadata


class LevelRegistry:
    """
    レベルとその振る舞いを管理するRegistry

    Open/Closed Principleを実現：
    - 新レベル追加: LEVEL_CONFIGに追加するだけ
    - 新しい振る舞い: LevelBehaviorを継承して登録

    Singleton: get_level_registry()でアクセス

    Example:
        >>> registry = get_level_registry()
        >>> registry.get_metadata("weekly").prefix
        'W'
    """

    def __init__(self) -> None:
        """
        Registryを初期化し、LEVEL_CONFIGからレベルを登録

        Example:
            >>> registry = LevelRegistry()
            >>> "weekly" in registry.get_level_names()
            True
        """
        self._levels: Dict[str, tuple[LevelMetadata, LevelBehavior]] = {}
        self._prefix_to_level: Dict[str, str] = {}
        self._initialize_from_config()

    def _initialize_from_config(self) -> None:
        """
        LEVEL_CONFIGからレベルを登録

        Example:
            >>> registry = LevelRegistry()
            >>> # _initialize_from_config()は__init__で自動呼び出し
            >>> registry.get_all_level_names()
            ['weekly', 'monthly', 'quarterly', ..., 'loop']
        """
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

    def _register(self, name: str, metadata: LevelMetadata, behavior: LevelBehavior) -> None:
        """
        レベルを登録（内部メソッド）

        Args:
            name: レベル名
            metadata: レベルメタデータ
            behavior: レベルの振る舞い

        Example:
            >>> registry = LevelRegistry()
            >>> # 内部メソッドのため通常は直接呼び出さない
            >>> # _initialize_from_config()経由で自動的に呼び出される
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

        Example:
            >>> registry = get_level_registry()
            >>> behavior = registry.get_behavior("weekly")
            >>> behavior.format_number(1)
            'W0001'
        """
        if level not in self._levels:
            formatter = get_error_formatter()
            raise ConfigError(formatter.config.unknown_level(level))
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

        Example:
            >>> registry = get_level_registry()
            >>> metadata = registry.get_metadata("weekly")
            >>> metadata.prefix
            'W'
        """
        if level not in self._levels:
            formatter = get_error_formatter()
            raise ConfigError(formatter.config.unknown_level(level))
        return self._levels[level][0]

    def get_level_names(self) -> List[str]:
        """
        登録されたレベル名一覧を取得（'loop'を除く）

        Returns:
            レベル名のリスト（LEVEL_CONFIGの順序を保持）

        Example:
            >>> registry = get_level_registry()
            >>> registry.get_level_names()
            ['weekly', 'monthly', 'quarterly', ...]
        """
        return [name for name in self._levels.keys() if name != "loop"]

    def get_all_level_names(self) -> List[str]:
        """
        全ての登録レベル名を取得（'loop'を含む）

        Returns:
            全レベル名のリスト

        Example:
            >>> registry = get_level_registry()
            >>> 'loop' in registry.get_all_level_names()
            True
        """
        return list(self._levels.keys())

    def get_all_prefixes(self) -> List[str]:
        """
        全プレフィックスを長さ順（降順）で取得

        長いプレフィックスを先にすることで、正規表現マッチ時に
        "MD"が"M"より先にマッチする。

        Returns:
            プレフィックスのリスト（長さ降順）

        Example:
            >>> registry = get_level_registry()
            >>> prefixes = registry.get_all_prefixes()
            >>> prefixes[0]  # 最長プレフィックスが先頭
            'MD'
        """
        return sorted(self._prefix_to_level.keys(), key=len, reverse=True)

    def get_level_by_prefix(self, prefix: str) -> Optional[str]:
        """
        プレフィックスからレベル名を逆引き

        Args:
            prefix: ファイル名プレフィックス

        Returns:
            レベル名、または見つからない場合None

        Example:
            >>> registry = get_level_registry()
            >>> registry.get_level_by_prefix("W")
            'weekly'
            >>> registry.get_level_by_prefix("X")
            None
        """
        return self._prefix_to_level.get(prefix)

    def should_cascade(self, level: str) -> bool:
        """
        レベルがカスケードするかどうかを判定

        Args:
            level: レベル名

        Returns:
            カスケードする場合True

        Example:
            >>> registry = get_level_registry()
            >>> registry.should_cascade("weekly")
            True
            >>> registry.should_cascade("centennial")
            False
        """
        return self.get_behavior(level).should_cascade()

    def build_prefix_pattern(self) -> str:
        """
        全プレフィックスの正規表現パターンを生成

        長いプレフィックスを先にして、"MD"が"M"より先にマッチするようにする。

        Returns:
            正規表現パターン文字列（例: "MD|W|M|Q|A|T|D|C|L"）

        Example:
            >>> registry = get_level_registry()
            >>> pattern = registry.build_prefix_pattern()
            >>> 'MD|' in pattern  # MDが先頭付近
            True
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

    ## ARCHITECTURE: Singleton Pattern
    なぜSingletonか？
    - レベル設定はアプリケーション全体で不変
    - 複数インスタンスはメモリの無駄
    - DIコンテナを導入するほど複雑ではない

    なぜクラスベースSingletonではなく関数アクセサか？
    - Pythonらしいシンプルな実装
    - reset_level_registry()でテスト時にリセット可能
    - 遅延初期化が自然に実現

    Returns:
        LevelRegistryインスタンス

    Example:
        registry = get_level_registry()
        metadata = registry.get_metadata("weekly")
    """
    global _registry
    # ARCHITECTURE: 遅延初期化 - 最初のアクセス時にのみインスタンス化
    if _registry is None:
        _registry = LevelRegistry()
    return _registry


def reset_level_registry() -> None:
    """
    Registryをリセット（テスト用）

    テスト間でRegistryの状態をクリアするために使用。

    Example:
        >>> reset_level_registry()  # Singletonインスタンスをリセット
        >>> registry = get_level_registry()  # 新しいインスタンスが作成される
    """
    global _registry
    _registry = None
