"""音声ファイルを 16kHz mono float PCM へデコードする Adapter。

PyAV（`av`）で ffmpeg を wheel 内包で呼ぶ（システム ffmpeg 不要）。
Telegram voice(OGG/OPUS) / audio(mp3/m4a) / video の音声トラックを、
Moonshine が食える 16kHz mono float（-1.0〜1.0）に正規化する。
デコード不能なファイルは AudioDecodeError を送出する（空配列で返して「無音」に化けさせない）。
デコードできて中身が 0 サンプルだった場合のみ空配列を返す。
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

from domain.exceptions import AudioDecodeError

TARGET_RATE = 16000


class FfmpegAudioPreprocessor:
    """任意音声 → 16kHz mono float PCM（PyAV、ffmpeg-free）。"""

    def to_float_pcm(self, path: Path) -> tuple[Sequence[float], int]:
        """path の音声を 16kHz mono float 配列へ。戻り値 (samples, sample_rate)。

        samples は numpy ndarray のまま返す（tolist() しない）——20MB OPUS ≒ 2 時間
        ≒ 1.15 億サンプルの Python float list 化は数 GB 級でコンテナ OOM を招く。
        Moonshine は ndarray を直接受理する。空判定は truthiness でなく
        `len(samples) == 0` で行う契約（ndarray の bool は ambiguous）。

        Raises:
            AudioDecodeError: コンテナが開けない/音声を一片もデコードできない場合。
                「本当に無音」と「読めなかった」を呼び出し側が区別できるようにする。
        """
        import av
        import numpy as np

        empty = np.empty(0, dtype=np.float32)
        try:
            container = av.open(str(path))
        except Exception as exc:
            raise AudioDecodeError(f"cannot open audio container: {path.name}") from exc

        chunks = []
        decode_error: Exception | None = None
        try:
            resampler = av.audio.resampler.AudioResampler(
                format="flt", layout="mono", rate=TARGET_RATE
            )
            for frame in container.decode(audio=0):
                for rframe in resampler.resample(frame):
                    chunks.append(rframe.to_ndarray().flatten())
            # flush（最終フレーム取りこぼし防止）。取得済み分は損なわないので握る。
            try:
                for rframe in resampler.resample(None):
                    chunks.append(rframe.to_ndarray().flatten())
            except Exception:
                pass
        except Exception as exc:
            decode_error = exc
        finally:
            container.close()

        # 一片も取れずに失敗した＝デコード不能。無音と区別してうるさく失敗する。
        # 途中まで取れていれば部分音声を返す（無音化より情報が多い）。
        if decode_error is not None and not chunks:
            raise AudioDecodeError(
                f"no audio stream decoded: {path.name}"
            ) from decode_error

        if not chunks:
            return cast("Sequence[float]", empty), TARGET_RATE
        samples = np.concatenate(chunks).astype("float32")
        # ndarray は実行時に Sequence 相当（len/添字/反復）だが typing 上は Sequence ではない。
        # 契約（to_float_pcm -> Sequence[float]）は変えず、意図を cast で書く。
        return cast("Sequence[float]", samples), TARGET_RATE
