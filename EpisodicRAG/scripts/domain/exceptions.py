#!/usr/bin/env python3
"""
EpisodicRAG カスタム例外
========================

プロジェクト固有の例外クラス階層。
汎用Exceptionを具体的な例外に置き換え、デバッグを容易にする。

Usage:
    from domain.exceptions import ConfigError, DigestError, ValidationError, FileIOError
    from domain.exceptions import DiagnosticContext

    # 基本的な使用
    raise ConfigError("Invalid config.json format")
    raise ValidationError("source_files must be a list")

    # 診断コンテキスト付き
    ctx = DiagnosticContext(
        current_level="weekly",
        file_count=3,
        threshold=5
    )
    raise DigestError("Processing failed", context=ctx)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DiagnosticContext:
    """
    エラー診断用コンテキスト情報

    エラー発生時の状態を保持し、デバッグを支援する。

    Attributes:
        config_path: 設定ファイルのパス
        current_level: 処理中のダイジェストレベル
        file_count: 処理中のファイル数
        threshold: 適用されている閾値
        last_operation: 最後に実行した操作
        additional_info: その他の追加情報

    Example:
        >>> ctx = DiagnosticContext(
        ...     current_level="weekly",
        ...     file_count=3,
        ...     threshold=5,
        ...     last_operation="add_files_to_shadow"
        ... )
        >>> str(ctx)
        'current_level=weekly, file_count=3, threshold=5, last_operation=add_files_to_shadow'
    """

    config_path: Optional[Path] = None
    current_level: Optional[str] = None
    file_count: Optional[int] = None
    threshold: Optional[int] = None
    last_operation: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        非None値のみを含む辞書を返す

        Returns:
            キー=属性名、値=属性値の辞書（Noneは除外）
        """
        result: Dict[str, Any] = {}
        if self.config_path is not None:
            result["config_path"] = str(self.config_path)
        if self.current_level is not None:
            result["current_level"] = self.current_level
        if self.file_count is not None:
            result["file_count"] = self.file_count
        if self.threshold is not None:
            result["threshold"] = self.threshold
        if self.last_operation is not None:
            result["last_operation"] = self.last_operation
        if self.additional_info:
            result.update(self.additional_info)
        return result

    def __str__(self) -> str:
        """コンテキスト情報の文字列表現"""
        items = self.to_dict()
        if not items:
            return ""
        return ", ".join(f"{k}={v}" for k, v in items.items())


class EpisodicRAGError(Exception):
    """
    EpisodicRAG 基底例外クラス

    すべてのプロジェクト固有例外の親クラス。
    `except EpisodicRAGError` で全ての固有例外をキャッチ可能。

    Attributes:
        context: 診断コンテキスト（オプション）

    Example:
        >>> ctx = DiagnosticContext(current_level="weekly")
        >>> error = EpisodicRAGError("Something failed", context=ctx)
        >>> str(error)
        'Something failed [Context: current_level=weekly]'
    """

    def __init__(
        self, message: str, context: Optional[DiagnosticContext] = None
    ) -> None:
        """
        初期化

        Args:
            message: エラーメッセージ
            context: 診断コンテキスト（オプション）
        """
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        """エラーメッセージの文字列表現（コンテキスト付き）"""
        base = super().__str__()
        if self.context:
            ctx_str = str(self.context)
            if ctx_str:
                return f"{base} [Context: {ctx_str}]"
        return base


class ConfigError(EpisodicRAGError):
    """
    設定関連エラー

    Examples:
        - config.json が見つからない
        - config.json のフォーマットが不正
        - 必須の設定キーが存在しない
    """

    pass


class DigestError(EpisodicRAGError):
    """
    ダイジェスト処理エラー

    Examples:
        - Shadow/GrandDigest の読み込み失敗
        - ダイジェスト生成中のエラー
        - ダイジェストファイルの保存失敗
    """

    pass


class ValidationError(EpisodicRAGError):
    """
    バリデーションエラー

    Examples:
        - データ型が期待と異なる（dict が必要なのに list）
        - 必須フィールドが欠落
        - source_files が空
    """

    pass


class FileIOError(EpisodicRAGError):
    """
    ファイルI/Oエラー

    Examples:
        - ファイルの読み込み失敗
        - ファイルの書き込み失敗
        - ディレクトリの作成失敗

    Note:
        Python組み込みの IOError/OSError と区別するため、
        EpisodicRAGError を継承。
    """

    pass


class CorruptedDataError(EpisodicRAGError):
    """
    データ破損エラー

    Examples:
        - JSONファイルが壊れている
        - ダイジェストの整合性チェック失敗
        - 期待されるフィールドが不正な値を持つ

    Note:
        ValidationError（入力値エラー）とは異なり、
        保存済みデータの破損を示す。
    """

    pass
