"""Moonshine で音声を transcript 化する MediaRenderer Port 実装（Stage 9.5b）。

FfmpegAudioPreprocessor で 16kHz mono float にした音声を Moonshine 日本語モデルで
transcribe し、transcript を RenderedMedia.rendered_text に乗せ render_status="ok"。
例外は内部 catch → render_status="failed"（markitdown_renderer 同型、クラッシュしない）。

model load は lazy（初回の実音声 render 時）。Cloud Routine 起動を速くし、
空音声/前処理失敗では load しない。

ライセンス: Moonshine Community License（年商 $1M 未満は商用も無料）。年商 $1M 以上の組織本番は
Enterprise License or kotoba-whisper(Apache-2.0) へ Port 差し替え。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from adapters.audio.ffmpeg_preprocessor import FfmpegAudioPreprocessor
from adapters.media_failure import failed_render
from domain.media import MediaAttachment, RenderedMedia


class MoonshineTranscriber:
    """音声 → transcript（Moonshine、MediaRenderer Port 実装）。

    `RenderAuthorizedMedia` の transcriber として注入。watch ループでは loop 外で
    1 インスタンス作り使い回す。model load は lazy（初回の実音声 render 時）。
    """

    def __init__(
        self,
        language: str = "ja",
        preprocessor: Optional[FfmpegAudioPreprocessor] = None,
    ) -> None:
        self._language = language
        self._preprocessor = preprocessor or FfmpegAudioPreprocessor()
        self._model = None  # (Transcriber, model_path, model_arch) を lazy load

    def _ensure_model(self):
        if self._model is None:
            import moonshine_voice
            from moonshine_voice.transcriber import Transcriber

            model_path, model_arch = moonshine_voice.get_model_for_language(self._language)
            self._model = (Transcriber, model_path, model_arch)
        return self._model

    def render(self, media: MediaAttachment, local_path: Path) -> RenderedMedia:
        """音声を transcript 化。失敗は flag 化、エージェント に正直に伝える。"""
        try:
            samples, rate = self._preprocessor.to_float_pcm(local_path)
            if not samples:
                # 無音/デコード不可: 失敗ではなく「音声なし」として空 transcript
                return RenderedMedia(rendered_text="", render_status="ok")
            transcriber_cls, model_path, model_arch = self._ensure_model()
            with transcriber_cls(model_path, model_arch) as tr:
                transcript = tr.transcribe_without_streaming(samples, rate)
            text = "".join(line.text for line in transcript.lines)
            return RenderedMedia(rendered_text=text, render_status="ok")
        except Exception:
            return failed_render(
                "moonshine-transcriber", "transcribe", "file_id", media.file_id[:8]
            )
