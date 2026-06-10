from __future__ import annotations

from pathlib import Path

import pytest

from domain.exceptions import AuthFailureError, TelegramSecretaryError
from domain.media import MediaAttachment
from domain.models import TelegramUpdate
from usecases.download_authorized_media import DownloadAuthorizedMedia
from usecases.fetch_authorized_updates import NormalizedUpdate

from tests.usecases.fakes import FakeMediaDownloader


def _nu(
    update_id: int,
    media: list[MediaAttachment],
    chat_id: int = 100,
    text: str = "",
) -> NormalizedUpdate:
    update = TelegramUpdate(
        update_id=update_id,
        chat_id=chat_id,
        user_id=1,
        username=None,
        text=text,
        media=media,
    )
    return NormalizedUpdate(update=update, normalized_text=text, injection_flags=[])


def test_downloads_media_within_size_limit():
    media = MediaAttachment(
        kind="photo", file_id="ok", mime_type="image/jpeg", size=1024
    )
    nu = _nu(update_id=1, media=[media])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20 * 1024 * 1024,
    )

    assert len(results) == 1
    assert results[0].update_id == 1
    assert results[0].media.file_id == "ok"
    assert results[0].local_path == Path("/tmp/media/ok.bin")
    assert results[0].skip_reason is None
    assert downloader.download_calls == [("ok", Path("/tmp/media"))]


def test_skips_media_exceeding_size_limit():
    big = MediaAttachment(
        kind="photo", file_id="big", mime_type="image/jpeg", size=30_000_000
    )
    nu = _nu(update_id=2, media=[big])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert len(results) == 1
    assert results[0].skip_reason == "media_size_exceeded"
    assert results[0].local_path is None
    # size 超過時は download を一切呼ばない
    assert downloader.download_calls == []


def test_continues_other_media_when_one_is_skipped():
    """単一 media の skip が他 media の download を妨げない。"""
    big = MediaAttachment(
        kind="photo", file_id="big", mime_type="image/jpeg", size=30_000_000
    )
    small = MediaAttachment(
        kind="document", file_id="small", mime_type="application/pdf", size=1024
    )
    nu = _nu(update_id=3, media=[big, small])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert len(results) == 2
    big_result = next(r for r in results if r.media.file_id == "big")
    small_result = next(r for r in results if r.media.file_id == "small")
    assert big_result.skip_reason == "media_size_exceeded"
    assert small_result.skip_reason is None
    assert small_result.local_path == Path("/tmp/media/small.bin")
    # skip された方は呼ばれず、成功した方だけ呼ばれる
    assert downloader.download_calls == [("small", Path("/tmp/media"))]


def test_empty_media_list_returns_empty_results():
    nu = _nu(update_id=4, media=[])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert results == []
    assert downloader.download_calls == []


def test_multiple_updates_each_with_media():
    media_a = MediaAttachment(
        kind="photo", file_id="a", mime_type="image/jpeg", size=1024
    )
    media_b = MediaAttachment(
        kind="photo", file_id="b", mime_type="image/jpeg", size=2048
    )
    nu_a = _nu(update_id=10, media=[media_a])
    nu_b = _nu(update_id=11, media=[media_b])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu_a, nu_b],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert len(results) == 2
    update_ids = {r.update_id for r in results}
    assert update_ids == {10, 11}
    assert len(downloader.download_calls) == 2


# === Stage 9.2: voice / audio / video が kind 非依存で download される ===

def test_downloads_voice_media_kind_agnostic():
    """voice も kind 非依存で download される（コード変更なしの実証）。"""
    voice = MediaAttachment(
        kind="voice", file_id="voice1", mime_type="audio/ogg", size=8192
    )
    nu = _nu(update_id=20, media=[voice])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20 * 1024 * 1024,
    )

    assert len(results) == 1
    assert results[0].media.kind == "voice"
    assert results[0].local_path == Path("/tmp/media/voice1.bin")
    assert results[0].skip_reason is None
    assert downloader.download_calls == [("voice1", Path("/tmp/media"))]


def test_downloads_audio_and_video_kinds():
    """audio / video も同様に download（file_id ベース、kind を見ない）。"""
    audio = MediaAttachment(kind="audio", file_id="aud", mime_type="audio/mpeg", size=3000)
    video = MediaAttachment(kind="video", file_id="vid", mime_type="video/mp4", size=1000000)
    nu = _nu(update_id=21, media=[audio, video])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20 * 1024 * 1024,
    )

    assert {r.media.kind for r in results} == {"audio", "video"}
    assert len(downloader.download_calls) == 2


def test_skips_oversized_voice():
    """大きすぎる voice/video も既存 size 上限ロジックで skip（kind 非依存）。"""
    big_video = MediaAttachment(
        kind="video", file_id="bigvid", mime_type="video/mp4", size=30_000_000
    )
    nu = _nu(update_id=22, media=[big_video])
    downloader = FakeMediaDownloader()
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert results[0].skip_reason == "media_size_exceeded"
    assert downloader.download_calls == []


# === 通信失敗のフラグ化（download_failed）と 401 の伝播 ===

def test_download_failure_is_flagged_not_raised():
    """通信失敗は skip_reason="download_failed" にフラグ化し、他 media を妨げない。

    fetch が download 前に offset を確定するため、ここで raise すると
    当該バッチの全メッセージが再取得不能になる（watch 即死＝メッセージ消失の根治）。
    """
    bad = MediaAttachment(kind="photo", file_id="bad", mime_type="image/jpeg", size=1024)
    good = MediaAttachment(
        kind="document", file_id="good", mime_type="application/pdf", size=1024
    )
    nu = _nu(update_id=30, media=[bad, good])
    downloader = FakeMediaDownloader(
        exc_by_file_id={"bad": TelegramSecretaryError("network error during media download")}
    )
    uc = DownloadAuthorizedMedia(downloader)

    results = uc.execute(
        normalized_updates=[nu],
        target_dir=Path("/tmp/media"),
        max_size_bytes=20_000_000,
    )

    assert len(results) == 2
    bad_result = next(r for r in results if r.media.file_id == "bad")
    good_result = next(r for r in results if r.media.file_id == "good")
    assert bad_result.skip_reason == "download_failed"
    assert bad_result.local_path is None
    assert good_result.skip_reason is None
    assert good_result.local_path == Path("/tmp/media/good.bin")


def test_auth_failure_propagates():
    """401（AuthFailureError）は exit 3 系の決定打なのでフラグ化せず伝播する。"""
    media = MediaAttachment(kind="photo", file_id="x", mime_type="image/jpeg", size=1024)
    nu = _nu(update_id=31, media=[media])
    downloader = FakeMediaDownloader(
        exc_by_file_id={"x": AuthFailureError("401 unauthorized")}
    )
    uc = DownloadAuthorizedMedia(downloader)

    with pytest.raises(AuthFailureError):
        uc.execute(
            normalized_updates=[nu],
            target_dir=Path("/tmp/media"),
            max_size_bytes=20_000_000,
        )
