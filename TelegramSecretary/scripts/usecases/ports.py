"""UseCase 層が依存する Port（抽象インターフェース）群。

Port は Protocol で定義し、実装は adapters/ 配下に置く。テストは fake 実装で駆動する。
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Protocol

from domain.lease import SessionLease
from domain.media import MediaAttachment, RenderedMedia
from domain.models import OutboundMessage, TelegramUpdate
from domain.offset import UpdateOffset
from domain.wal import WalEntry


class UpdateSource(Protocol):
    """Telegram getUpdates を抽象化する Port。"""

    def fetch(self, offset: UpdateOffset, timeout_seconds: int = 30) -> List[TelegramUpdate]:
        ...


class MessageSink(Protocol):
    """sendMessage を抽象化する Port。"""

    def send(self, message: OutboundMessage) -> None:
        ...


class OffsetStore(Protocol):
    """update offset の永続化。in-memory + 定期 flush を許容。"""

    def load(self) -> UpdateOffset:
        ...

    def save(self, offset: UpdateOffset) -> None:
        ...


class LeaseStore(Protocol):
    """セッションリースの永続化。"""

    def load(self) -> Optional[SessionLease]:
        ...

    def save(self, lease: SessionLease) -> None:
        ...

    def clear(self) -> None:
        ...


class MediaDownloader(Protocol):
    """Telegram の file_id から実ファイルを download する Port（Stage 6.2）。

    実装は adapters/telegram/media_downloader.py（Stage 6.3）。
    target_dir は state_dir/media/ を想定（呼び出し側が用意）。
    戻り値は保存先の絶対 Path。
    """

    def download(self, file_id: str, target_dir: Path) -> Path:
        ...


class MediaRenderer(Protocol):
    """Download 済み media を エージェント が読める形式に変換する Port（Stage 7.2）。

    実装は adapters/render/markitdown_renderer.py（Stage 7.3）。
    mime-routing は呼び出し側（UseCase）が担い、ここに来た時点で render 対象は確定。
    Adapter は内部例外を catch して RenderedMedia(render_status="failed") を返す契約
    （Stage 6 の skip_reason 同型の「フラグ化、ブロックしない」スタンス）。
    """

    def render(self, media: MediaAttachment, local_path: Path) -> RenderedMedia:
        ...


class RegistryStore(Protocol):
    """管理表（INDIVIDUALS / TASKS / KNOWLEDGE）1 ファイルの永続化 Port。

    実装は adapters/registry/json_registry_store.py。records は dict のリスト
    （値オブジェクトへの変換は呼び出し側の責務）。
    """

    def load(self) -> List[dict]:
        ...

    def save(self, records: List[dict]) -> None:
        ...


class GitSyncPort(Protocol):
    """管理表ブランチの git 操作を抽象化する Port（R2）。

    実装は adapters/registry/git_cli.py（subprocess）。RegistrySyncService が
    commit/push 分離・non-ff rebase フォールバックのロジックをこの Port 越しに駆動する。
    """

    def commit(self, paths: List[Path], message: str) -> bool:
        """paths を stage して commit。変更が無ければ False（no-op）、commit したら True。"""
        ...

    def push(self) -> None:
        """現在ブランチを push。non-fast-forward は PushRejectedError、他失敗は GitSyncError。"""
        ...

    def pull_rebase(self) -> None:
        """リモートを pull --rebase（外部更新の取り込み）。"""
        ...

    def fetch_checkout(self, branch: str) -> None:
        """固定ブランチを fetch して checkout（起動時、最新管理表を引く）。"""
        ...


class WalLogStore(Protocol):
    """WAL ログ（JSONL）の永続化 Port（intent の追記・全読込・全書換）。

    実装は adapters/wal/jsonl_wal_log_store.py。append は O(1) 追記、
    rewrite は checkpoint 後の全書換（done 掃除の反映）。
    """

    def append(self, entry: WalEntry) -> None:
        ...

    def load(self) -> List[WalEntry]:
        ...

    def rewrite(self, entries: List[WalEntry]) -> None:
        ...
