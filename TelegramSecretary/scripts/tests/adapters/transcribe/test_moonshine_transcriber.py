from __future__ import annotations

import wave
from pathlib import Path

from domain.media import MediaAttachment
from adapters.transcribe.moonshine_transcriber import MoonshineTranscriber


class _FakePreprocessor:
    """to_float_pcm を固定値/例外で駆動する fake（Moonshine 本体を分離テスト）。"""

    def __init__(self, samples=None, raise_exc: bool = False) -> None:
        self._samples = list(samples or [])
        self._raise = raise_exc

    def to_float_pcm(self, path: Path):
        if self._raise:
            raise RuntimeError("decode boom")
        return self._samples, 16000


def _make_silence_wav(path: Path, dur: float = 1.0, rate: int = 16000) -> None:
    n = int(rate * dur)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)


def _voice(file_id: str = "v") -> MediaAttachment:
    return MediaAttachment(kind="voice", file_id=file_id, mime_type="audio/ogg", size=100)


def test_empty_samples_returns_ok_empty_without_model_load():
    """preprocessor が空（無音/デコード不可）なら ok + 空文字、Moonshine は呼ばない（lazy）。"""
    t = MoonshineTranscriber(preprocessor=_FakePreprocessor(samples=[]))
    result = t.render(_voice(), Path("x.ogg"))
    assert result.render_status == "ok"
    assert result.rendered_text == ""


def test_failed_on_preprocessor_exception():
    """前処理で例外 → failed（クラッシュさせず エージェントに正直に、markitdown 同型）。"""
    t = MoonshineTranscriber(preprocessor=_FakePreprocessor(raise_exc=True))
    result = t.render(_voice("abcdef1234"), Path("x.ogg"))
    assert result.render_status == "failed"
    assert result.rendered_text is None


def test_transcribes_real_silence_audio(tmp_path):
    """実 Moonshine + 実 preprocessor で無音 16kHz wav を処理 → ok（text は空 or 無音マーカー）。"""
    wav = tmp_path / "silence.wav"
    _make_silence_wav(wav, dur=1.0)
    t = MoonshineTranscriber(language="ja")
    result = t.render(_voice("silence"), wav)
    assert result.render_status == "ok"
    assert result.rendered_text is not None  # str（空 or "[No speech detected]" 等）
