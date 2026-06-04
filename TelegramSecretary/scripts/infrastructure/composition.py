"""Composition Root: 依存組み立ての唯一点（Infrastructure 層）。

各 cmd_* ハンドラが個別に行っていた config ロードと media stack 構築をここに集約する。

- load_config(): `Config | int` union を廃止し fail-fast（EnvironmentError を伝播）。
  CLI 境界（main）が EnvironmentError を 1 度だけ捕捉して EXIT_CONFIG_INVALID へ変換する。
- build_media_stack(): poll の eager 構築と watch の lazy closure を 1 関数に統一。
  markitdown は必須、transcriber(moonshine)/pdf_renderer(pdfplumber) は optional
  （未導入なら None で構築し該当 media は skipped にフォールバック）。重い import は
  関数内 lazy に保ち、テストの monkeypatch（モジュールパス指定）と cloud routine 起動の
  軽量性を両立する（呼び出し＝実際に media を受けた時のみ重い import が走る）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrastructure.config import Config
from usecases.download_authorized_media import DownloadAuthorizedMedia
from usecases.render_authorized_media import RenderAuthorizedMedia

if TYPE_CHECKING:
    from adapters.telegram.media_downloader import TelegramMediaDownloader


def load_config() -> Config:
    """env から Config を構築。欠損・不正は EnvironmentError を伝播（fail-fast）。

    旧 `_load_config` の `Config | int` union を置き換える。union はハンドラ毎の
    `if isinstance(config, int): return config` ガード重複を生んでいた。例外伝播に統一し、
    CLI 境界で 1 度だけ exit code へ変換する。

    `from_sources` は秘匿（token/chats）を env、運用設定（session_duration_sec 等）を
    config.json（<INSTALL_DIR>/config.json 決め打ち）から読む（純2層）。
    """
    return Config.from_sources()


@dataclass
class MediaStack:
    """media download→render の組み立て済み一式。

    downloader は httpx.Client を保持するため、使用後に呼び出し側が close() する。
    """

    downloader: "TelegramMediaDownloader"
    download_uc: DownloadAuthorizedMedia
    render_uc: RenderAuthorizedMedia


def build_media_stack(config: Config, gateway) -> MediaStack:
    """media download + render の依存一式を組み立てる（poll/watch 共用）。

    markitdown は必須。transcriber(moonshine)/pdf_renderer(pdfplumber) は optional:
    未導入（bundle 除外）なら None で構築し、該当 media は render usecase 側で skipped に
    フォールバックする。重い import（markitdown/moonshine/pdfplumber）は関数内 lazy import。
    """
    from adapters.render.markitdown_renderer import MarkitdownRenderer
    from adapters.telegram.media_downloader import TelegramMediaDownloader

    downloader = TelegramMediaDownloader(bot_token=config.bot_token, gateway=gateway)
    download_uc = DownloadAuthorizedMedia(downloader)

    # 音声 transcriber(moonshine) は optional: 未導入（BUNDLE_VOICE=false 等）なら None。
    transcriber = None
    try:
        from adapters.transcribe.moonshine_transcriber import MoonshineTranscriber

        transcriber = MoonshineTranscriber()
    except ImportError:
        transcriber = None

    # PDF renderer(pdfplumber/pypdfium2) も optional: 未導入なら None で PDF は skipped。
    pdf_renderer = None
    try:
        from adapters.render.pdf_renderer import PdfRenderer

        pdf_renderer = PdfRenderer(image_max_pages=config.pdf_image_max_pages)
    except ImportError:
        pdf_renderer = None

    render_uc = RenderAuthorizedMedia(
        MarkitdownRenderer(),
        transcriber=transcriber,
        pdf_renderer=pdf_renderer,
    )
    return MediaStack(
        downloader=downloader, download_uc=download_uc, render_uc=render_uc
    )
