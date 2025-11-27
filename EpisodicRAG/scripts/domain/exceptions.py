#!/usr/bin/env python3
"""
EpisodicRAG カスタム例外
========================

プロジェクト固有の例外クラス階層。
汎用Exceptionを具体的な例外に置き換え、デバッグを容易にする。

Usage:
    from domain.exceptions import ConfigError, DigestError, ValidationError, FileIOError

    raise ConfigError("Invalid config.json format")
    raise ValidationError("source_files must be a list")
"""


class EpisodicRAGError(Exception):
    """
    EpisodicRAG 基底例外クラス

    すべてのプロジェクト固有例外の親クラス。
    `except EpisodicRAGError` で全ての固有例外をキャッチ可能。
    """

    pass


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
