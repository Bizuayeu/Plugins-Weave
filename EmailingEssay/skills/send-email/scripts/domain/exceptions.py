# domain/exceptions.py
"""
例外階層

EmailingEssayプラグイン全体で使用される例外クラスを一元管理する。
Clean Architecture の原則に従い、domain層に配置。
"""

from __future__ import annotations


class EmailingEssayError(Exception):
    """
    EmailingEssayプラグインの基底例外クラス。

    全ての例外はこのクラスを継承し、main.pyで一括キャッチ可能。
    """

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


# =============================================================================
# ドメイン層例外
# =============================================================================


class DomainError(EmailingEssayError):
    """
    ドメイン層の基底例外。

    ビジネスルール違反やドメインモデルの不整合を表す。
    """

    pass


class ValidationError(DomainError):
    """
    バリデーションエラー。

    入力値の形式や範囲の検証失敗を表す。
    """

    pass


# =============================================================================
# アダプター層例外
# =============================================================================


class AdapterError(EmailingEssayError):
    """
    アダプター層の基底例外。

    外部システムとの連携における失敗を表す。
    """

    pass


class MailError(AdapterError):
    """
    メール操作エラー。

    SMTP接続失敗、認証エラー、送信失敗などを表す。
    """

    pass


class SchedulerError(AdapterError):
    """
    スケジューラ操作エラー。

    タスクスケジューラやcronの操作失敗を表す。
    """

    pass


class StorageError(AdapterError):
    """
    ストレージ操作エラー。

    ファイル読み書きやJSON操作の失敗を表す。
    """

    pass


class TemplateError(AdapterError):
    """
    テンプレート処理エラー。

    テンプレートファイルの読み込みやレンダリングの失敗を表す。
    """

    pass


# =============================================================================
# ユースケース層例外
# =============================================================================


class WaiterError(EmailingEssayError):
    """
    待機処理エラー。

    待機プロセスの起動や実行における失敗を表す。
    """

    pass
