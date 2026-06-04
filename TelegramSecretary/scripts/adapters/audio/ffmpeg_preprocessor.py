"""音声ファイルを 16kHz mono float PCM へデコードする Adapter（Stage 9.5b）。

PyAV（`av`）で ffmpeg を wheel 内包で呼ぶ（システム ffmpeg 不要）。
Telegram voice(OGG/OPUS) / audio(mp3/m4a) / video の音声トラックを、
Moonshine が食える 16kHz mono float（-1.0〜1.0）に正規化する。
壊れた/音声なしファイルは空リストを返す（クラッシュしない、エージェントに「無音」を渡す）。
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

TARGET_RATE = 16000


class FfmpegAudioPreprocessor:
    """任意音声 → 16kHz mono float PCM（PyAV、ffmpeg-free）。"""

    def to_float_pcm(self, path: Path) -> Tuple[List[float], int]:
        """path の音声を 16kHz mono float list へ。戻り値 (samples, sample_rate)。

        音声ストリームなし/デコード失敗時は ([], TARGET_RATE) を返す（クラッシュしない）。
        """
        import av
        import numpy as np

        try:
            container = av.open(str(path))
        except Exception:
            return [], TARGET_RATE

        chunks = []
        try:
            resampler = av.audio.resampler.AudioResampler(
                format="flt", layout="mono", rate=TARGET_RATE
            )
            for frame in container.decode(audio=0):
                for rframe in resampler.resample(frame):
                    chunks.append(rframe.to_ndarray().flatten())
            # flush（最終フレーム取りこぼし防止）
            try:
                for rframe in resampler.resample(None):
                    chunks.append(rframe.to_ndarray().flatten())
            except Exception:
                pass
        except Exception:
            # 音声ストリームなし/デコード途中失敗: 取得済み分で続行（無ければ空）
            pass
        finally:
            container.close()

        if not chunks:
            return [], TARGET_RATE
        samples = np.concatenate(chunks).astype("float32")
        return samples.tolist(), TARGET_RATE
