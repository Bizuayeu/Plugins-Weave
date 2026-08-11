"""TelegramSecretary domain exceptions."""


class TelegramSecretaryError(Exception):
    """Base exception."""


class InvalidOffsetError(TelegramSecretaryError):
    """update offset が不正値（負数など）。"""


class LeaseConflictError(TelegramSecretaryError):
    """他セッションが lease を保持しており取得不可。"""


class AuthFailureError(TelegramSecretaryError):
    """Telegram bot token 認証失敗（401）。"""


class MediaSizeLimitExceededError(TelegramSecretaryError):
    """media のサイズが上限を超えた（download skip 対象、ブロックではなく flag）。

    DownloadAuthorizedMedia 内部で raise → 同 UseCase 内で catch して
    `MediaDownloadResult.skip_reason="media_size_exceeded"` に変換する。
    `flag_injection` と同型の「フラグ化して emit、判断は エージェントに委ねる」原則。
    """


class AudioDecodeError(TelegramSecretaryError):
    """音声のデコードに失敗した（コンテナが開けない/音声ストリームが取れない）。

    「本当に無音だった」と「読めなかった」を呼び出し側が区別できるようにするための例外。
    以前は前処理が両者とも空配列で返していたため、壊れた音声が transcribe 経路で
    `render_status="ok"` + 空 transcript となり、エージェントに「無音」として届いていた
    （静かな失敗）。デコード不能だけを本例外で表し、transcribe Adapter は `failed` に翻訳する。
    デコードは成功したが 0 サンプルだった場合は失敗ではないので raise しない。
    """


class AttachmentNotFoundError(TelegramSecretaryError):
    """outbound 添付ファイルのパスが存在しない（送信前検証で弾く）。"""


class AttachmentTooLargeError(TelegramSecretaryError):
    """outbound 添付ファイルのサイズが上限を超えた（送信前検証で弾く）。

    受信側の MediaSizeLimitExceededError（download skip = フラグ化）の送信側カウンターパート。
    こちらは送信を中止する（ブロック）: 誤送信・コスト事故防止のため明示的に弾く。
    """


class GitSyncError(TelegramSecretaryError):
    """管理表の git 同期失敗（push のネットワーク失敗等）。

    best-effort で握り、ローカル commit は残す（次回 sync でまとめて push）。
    """


class PushRejectedError(GitSyncError):
    """push が non-fast-forward で拒否された（外部更新あり）。

    pull --rebase で取り込んでから再 push する（独立ファイルは自動マージ）。
    GitSyncError のサブクラスゆえ、握り潰し catch でも拾われる（rebase を先に試す順序に注意）。
    """


class RegistryWorktreeError(GitSyncError):
    """registry_dir が独立した git 作業ツリーでない（親リポのサブディレクトリ等、層2）。

    checkout -B は cwd の作業ツリー全体をブランチへ切り替えるため、registry_dir が
    独立作業ツリーでないと親リポ（Private 等）を破壊する。fetch_checkout はこれを
    事前検証し、独立でなければ checkout を撃たず本例外で停止する。GitSyncError の
    サブクラスゆえ run_registry_fetch の except 経路に乗り、transient 扱い（空表継続）で
    後方互換を保つ（provisioning 完了までの過渡期も安全）。
    """
