"""TelegramSecretary domain exceptions."""


class TelegramSecretaryError(Exception):
    """Base exception."""


class InvalidOffsetError(TelegramSecretaryError):
    """update offset が不正値（負数など）。"""


class LeaseConflictError(TelegramSecretaryError):
    """他セッションが lease を保持しており取得不可。"""


class AuthFailureError(TelegramSecretaryError):
    """Telegram bot token 認証失敗（401）。"""


class MediaSizeLimitExceeded(TelegramSecretaryError):
    """media のサイズが上限を超えた（download skip 対象、ブロックではなく flag）。

    DownloadAuthorizedMedia 内部で raise → 同 UseCase 内で catch して
    `MediaDownloadResult.skip_reason="media_size_exceeded"` に変換する。
    Stage 1 の `flag_injection` と同型の「フラグ化して emit、判断は エージェント に委ねる」原則。
    """


class AttachmentNotFound(TelegramSecretaryError):
    """outbound 添付ファイルのパスが存在しない（送信前検証で弾く、Stage 8.1）。"""


class AttachmentTooLarge(TelegramSecretaryError):
    """outbound 添付ファイルのサイズが上限を超えた（送信前検証で弾く、Stage 8.1）。

    受信側の MediaSizeLimitExceeded（download skip = フラグ化）の送信側カウンターパート。
    こちらは送信を中止する（ブロック）: 誤送信・コスト事故防止のため明示的に弾く。
    """
