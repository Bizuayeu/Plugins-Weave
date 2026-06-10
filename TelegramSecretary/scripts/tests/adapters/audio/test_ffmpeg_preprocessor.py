from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import numpy as np

from adapters.audio.ffmpeg_preprocessor import FfmpegAudioPreprocessor


def _make_wav(path: Path, freq: int = 440, dur: float = 0.5, rate: int = 16000) -> None:
    """16kHz mono の単純なサイン波 wav を生成（fixture）。"""
    n = int(rate * dur)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        for i in range(n):
            v = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / rate))
            w.writeframes(struct.pack("<h", v))


def _make_wav_stereo_44k(path: Path, dur: float = 0.5) -> None:
    """44.1kHz stereo wav（resample + downmix が要るケース）。"""
    rate = 44100
    n = int(rate * dur)
    with wave.open(str(path), "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        for i in range(n):
            v = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / rate))
            w.writeframes(struct.pack("<hh", v, v))


def test_decodes_16k_mono_wav_to_float(tmp_path):
    wav = tmp_path / "tone.wav"
    _make_wav(wav, dur=0.5)
    pre = FfmpegAudioPreprocessor()
    samples, rate = pre.to_float_pcm(wav)
    assert rate == 16000
    # ndarray のまま返す（Python float list 化は 2 時間級音声で数 GB → コンテナ OOM）
    assert isinstance(samples, np.ndarray)
    # 0.5s @16kHz ≒ 8000 サンプル（端数許容で範囲チェック）
    assert 7000 < len(samples) < 9000
    # float PCM は -1.0〜1.0
    assert all(-1.0 <= s <= 1.0 for s in samples[:200])


def test_resamples_and_downmixes_44k_stereo_to_16k_mono(tmp_path):
    """44.1kHz stereo → 16kHz mono へ resample + downmix されること。"""
    wav = tmp_path / "stereo.wav"
    _make_wav_stereo_44k(wav, dur=0.5)
    pre = FfmpegAudioPreprocessor()
    samples, rate = pre.to_float_pcm(wav)
    assert rate == 16000
    # 44.1k→16k で約 0.5s 分（8000 前後）に圧縮される
    assert 7000 < len(samples) < 9000


def test_returns_empty_for_no_audio_stream(tmp_path):
    """音声ストリームが無い/壊れたファイルは空配列を返す（クラッシュしない）。

    空判定は truthiness でなく len で行う契約（ndarray の bool は ambiguous）。
    """
    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"not a real wav file at all")
    pre = FfmpegAudioPreprocessor()
    samples, rate = pre.to_float_pcm(broken)
    assert isinstance(samples, np.ndarray)
    assert len(samples) == 0
    assert rate == 16000
