"""JSON store 共有の atomic 書込＋破損フォールバック load ヘルパ。

write_text（truncate→write）は書込中クラッシュでファイル全損する——WAL（must-succeed
装置）の自己矛盾であり、registry では破損→load() が []→次の add で 1 件だけの表が
push されリモートへ伝播する silent wipe 経路になる。本モジュールは
「同一ディレクトリの tmp へ書く → os.replace() で publish」（Win/POSIX とも atomic）で
publish 前にクラッシュしても旧内容が無傷であることを保証する。

破損フォールバック付き load（offset/lease/registry の「missing/破損 → 初期値」、
WAL JSONL の「破損行スキップ」）も 4 store で同型だったため本モジュールへ集約する。
state/registry/wal の兄弟パッケージどこからも引けるよう、media_failure.py と同じく
adapters 直下に中立配置。
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable, List, TypeVar

T = TypeVar("T")


def write_text_atomic(path: Path, text: str) -> None:
    """text を path へ atomic に書く（同一ディレクトリ tmp 書込 → os.replace で publish）。

    - 親ディレクトリは自動作成（既存 store の save 契約を踏襲）
    - publish 前に失敗しても旧ファイルは無傷、tmp 残骸も残さない（best-effort 掃除）
    - tmp は target と同一ディレクトリに作る（別 filesystem 跨ぎだと replace が atomic でない）
    - encoding は UTF-8 固定（ensure_ascii=False の日本語をそのまま保存）
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=target.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_name, str(target))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def load_json_or_default(
    path: Path, parse: Callable[[object], T], default: Callable[[], T]
) -> T:
    """JSON ファイルを読み parse(decoded) を返す。missing/破損/parse 失敗は default() に倒す。

    catch 集合は既存 store（offset/lease/registry）の和集合
    （OSError / ValueError / KeyError、json.JSONDecodeError は ValueError の子）。
    「読めない永続 state は安全側の初期値で続行する」既存方針の共通化であり、
    握り潰し範囲の拡大ではない。
    """
    target = Path(path)
    if not target.exists():
        return default()
    try:
        return parse(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError):
        return default()


def load_jsonl(path: Path, parse_line: Callable[[dict], T]) -> List[T]:
    """JSONL を 1 行ずつ parse_line(decoded) する。破損行・空行はスキップして読める行だけ返す。

    一部の行が壊れていても全損させない（WAL の破損行スキップと同型の安全側）。
    parse_line 内の KeyError/ValueError（from_dict の欠損キー等）も行スキップに含める。
    """
    target = Path(path)
    if not target.exists():
        return []
    items: List[T] = []
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            items.append(parse_line(json.loads(line)))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return items
