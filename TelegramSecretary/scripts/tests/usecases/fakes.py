"""UseCase テスト用の fake adapter 群。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from domain.lease import SessionLease
from domain.media import MediaAttachment, RenderedMedia
from domain.models import OutboundMessage, TelegramUpdate
from domain.offset import UpdateOffset
from domain.wal import WalEntry


class FakeUpdateSource:
    """fetch をスクリプト化された応答列で駆動する fake。"""

    def __init__(self, batches: Optional[List[List[TelegramUpdate]]] = None) -> None:
        self.batches = list(batches or [])
        self.fetch_calls: List[tuple[UpdateOffset, int]] = []

    def fetch(self, offset: UpdateOffset, timeout_seconds: int = 30) -> List[TelegramUpdate]:
        self.fetch_calls.append((offset, timeout_seconds))
        if not self.batches:
            return []
        return self.batches.pop(0)


class FakeMessageSink:
    """send を記録、`fail` フラグで例外を投げる fake。"""

    def __init__(self, fail: bool = False) -> None:
        self.sent: List[OutboundMessage] = []
        self.fail = fail

    def send(self, message: OutboundMessage) -> None:
        if self.fail:
            raise RuntimeError("simulated send failure")
        self.sent.append(message)


class FakeOffsetStore:
    """in-memory な offset store。"""

    def __init__(self, initial: Optional[UpdateOffset] = None) -> None:
        self.offset = initial or UpdateOffset.initial()
        self.save_calls: List[UpdateOffset] = []

    def load(self) -> UpdateOffset:
        return self.offset

    def save(self, offset: UpdateOffset) -> None:
        self.offset = offset
        self.save_calls.append(offset)


class FakeLeaseStore:
    """in-memory な lease store。"""

    def __init__(self, initial: Optional[SessionLease] = None) -> None:
        self.lease: Optional[SessionLease] = initial
        self.save_calls: List[SessionLease] = []
        self.clear_calls: int = 0

    def load(self) -> Optional[SessionLease]:
        return self.lease

    def save(self, lease: SessionLease) -> None:
        self.lease = lease
        self.save_calls.append(lease)

    def clear(self) -> None:
        self.lease = None
        self.clear_calls += 1


class FakeMediaDownloader:
    """Stage 6.2: download 呼び出しを記録、`fail` フラグで例外を投げる fake。

    成功時は target_dir / f"{file_id}.bin" を返す（実 I/O はなし）。
    """

    def __init__(self, fail: bool = False) -> None:
        self.download_calls: List[Tuple[str, Path]] = []
        self.fail = fail

    def download(self, file_id: str, target_dir: Path) -> Path:
        self.download_calls.append((file_id, target_dir))
        if self.fail:
            raise RuntimeError("simulated download failure")
        return target_dir / f"{file_id}.bin"


class FakeMediaRenderer:
    """Stage 7.2: render 呼び出しを記録、固定値を返す fake。

    Adapter 側で内部 catch + flag 化のため、UseCase は raise を期待しない契約。
    fail フラグで raise すれば契約違反を観察できる（テスト用、通常未使用）。
    """

    def __init__(
        self,
        rendered_text: str = "# rendered\n",
        render_status: str = "ok",
        fail: bool = False,
    ) -> None:
        self.render_calls: List[Tuple[MediaAttachment, Path]] = []
        self._rendered_text = rendered_text
        self._render_status = render_status
        self._fail = fail

    def render(self, media: MediaAttachment, local_path: Path) -> RenderedMedia:
        self.render_calls.append((media, local_path))
        if self._fail:
            raise RuntimeError("simulated renderer failure")
        return RenderedMedia(
            rendered_text=self._rendered_text,
            render_status=self._render_status,
        )


class FakeGitSync:
    """git 同期操作を記録する fake（R2）。

    - commit: `committed` 値を返す（変更有無の擬似）
    - push: `push_outcomes` の先頭を順に消費。None=成功、例外インスタンス=raise
    - pull_rebase / fetch_checkout: 呼び出し回数・引数を記録
    """

    def __init__(self, committed: bool = True, push_outcomes=None) -> None:
        self.committed = committed
        self.commit_calls: List[Tuple[List[Path], str]] = []
        self.push_calls = 0
        self.pull_rebase_calls = 0
        self.fetch_calls: List[str] = []
        self._push_outcomes = list(push_outcomes) if push_outcomes is not None else [None]

    def commit(self, paths, message: str) -> bool:
        self.commit_calls.append((list(paths), message))
        return self.committed

    def push(self) -> None:
        self.push_calls += 1
        outcome = self._push_outcomes.pop(0) if self._push_outcomes else None
        if outcome is not None:
            raise outcome

    def pull_rebase(self) -> None:
        self.pull_rebase_calls += 1

    def fetch_checkout(self, branch: str) -> None:
        self.fetch_calls.append(branch)


class FakeWalLogStore:
    """in-memory な WAL ログ store（append/load/rewrite）。"""

    def __init__(self, entries=None) -> None:
        self.entries: List[WalEntry] = list(entries or [])
        self.append_calls: List[WalEntry] = []
        self.rewrite_calls: List[List[WalEntry]] = []

    def append(self, entry: WalEntry) -> None:
        self.entries.append(entry)
        self.append_calls.append(entry)

    def load(self) -> List[WalEntry]:
        return list(self.entries)

    def rewrite(self, entries: List[WalEntry]) -> None:
        self.entries = list(entries)
        self.rewrite_calls.append(list(entries))


class FakeRegistryStore:
    """in-memory な RegistryStore（RegistryService に渡して redo の upsert 先にする）。"""

    def __init__(self, records=None) -> None:
        self.records: List[dict] = list(records or [])

    def load(self) -> List[dict]:
        return list(self.records)

    def save(self, records: List[dict]) -> None:
        self.records = list(records)
