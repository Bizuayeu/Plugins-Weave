from __future__ import annotations

import math
import struct
import sys
import wave
from pathlib import Path

import numpy as np
import pytest
from adapters.audio.ffmpeg_preprocessor import FfmpegAudioPreprocessor
from domain.exceptions import AudioDecodeError


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


def test_raises_on_undecodable_file(tmp_path):
    """デコード不能なファイルは AudioDecodeError（空配列を返して無音に化けさせない）。

    「本当に無音だった」と「読めなかった」を呼び出し側が区別できないと、
    エージェントは失敗を無音として受け取ってしまう（うるさく失敗させる）。
    """
    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"not a real wav file at all")
    pre = FfmpegAudioPreprocessor()
    with pytest.raises(AudioDecodeError):
        pre.to_float_pcm(broken)


def test_returns_empty_for_valid_but_zero_length_audio(tmp_path):
    """デコードは成功したが中身が 0 サンプルなら空配列を返す（これは失敗ではない）。

    空判定は truthiness でなく len で行う契約（ndarray の bool は ambiguous）。
    """
    empty_wav = tmp_path / "empty.wav"
    _make_wav(empty_wav, dur=0.0)
    pre = FfmpegAudioPreprocessor()
    samples, rate = pre.to_float_pcm(empty_wav)
    assert isinstance(samples, np.ndarray)
    assert len(samples) == 0
    assert rate == 16000


# --- デコード途中で壊れるケース（コンテナは開けるが decode が例外を投げる） ---
#
# 壊れた bytes は `av.open` の段で落ちるため、ループ内での失敗は実ファイルでは作れない。
# 「一片も取れなければうるさく失敗、部分的に取れていれば取れた分を返す」という分岐は
# 本 Adapter の設計判断そのものなので、fake コンテナで両側を pin する。


class _FakeResampledFrame:
    def __init__(self, array):
        self._array = array

    def to_ndarray(self):
        return self._array


class _FakeResampler:
    def __init__(self, **_kwargs):
        pass

    def resample(self, frame):
        if frame is None:  # flush
            return []
        return [_FakeResampledFrame(np.full((1, 4), 0.25, dtype="float32"))]


class _FlushFailingResampler(_FakeResampler):
    def resample(self, frame):
        if frame is None:  # flush だけが失敗する
            raise RuntimeError("flush failed")
        return super().resample(frame)


class _FakeContainer:
    def __init__(self, frames: int, *, fails: bool = True):
        self._frames = frames
        self._fails = fails
        self.closed = False

    def decode(self, audio=0):
        for _ in range(self._frames):
            yield object()
        if self._fails:
            raise RuntimeError("stream broke mid-decode")

    def close(self):
        self.closed = True


def _install_fake_av(monkeypatch, container, resampler_cls=_FakeResampler):
    import types

    fake_av = types.ModuleType("av")
    fake_av.open = lambda _path: container
    fake_av.audio = types.SimpleNamespace(
        resampler=types.SimpleNamespace(AudioResampler=resampler_cls)
    )
    monkeypatch.setitem(sys.modules, "av", fake_av)


def test_raises_when_decode_fails_before_any_frame(tmp_path, monkeypatch):
    """一片もデコードできずに失敗したら AudioDecodeError（無音に化けさせない）。"""
    container = _FakeContainer(frames=0)
    _install_fake_av(monkeypatch, container)

    with pytest.raises(AudioDecodeError):
        FfmpegAudioPreprocessor().to_float_pcm(tmp_path / "broken-midway.ogg")
    assert container.closed, "例外経路でも container は閉じる（finally）"


def test_returns_partial_audio_when_decode_fails_midway(tmp_path, monkeypatch):
    """途中まで取れていれば部分音声を返す（無音化より情報が多い）。"""
    container = _FakeContainer(frames=3)
    _install_fake_av(monkeypatch, container)

    samples, rate = FfmpegAudioPreprocessor().to_float_pcm(tmp_path / "partial.ogg")
    assert rate == 16000
    assert len(samples) == 12  # 3 フレーム × 4 サンプル
    assert container.closed


def test_flush_failure_does_not_discard_already_decoded_audio(tmp_path, monkeypatch):
    """flush（最終フレーム回収）が失敗しても、取得済みの音声は失わない。"""
    container = _FakeContainer(frames=2, fails=False)
    _install_fake_av(monkeypatch, container, resampler_cls=_FlushFailingResampler)

    samples, rate = FfmpegAudioPreprocessor().to_float_pcm(tmp_path / "flush-fail.ogg")
    assert rate == 16000
    assert len(samples) == 8  # 2 フレーム × 4 サンプル（flush 分だけが落ちる）
