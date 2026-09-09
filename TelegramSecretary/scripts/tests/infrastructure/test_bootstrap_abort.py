"""bootstrap.sh の中断が source 形態でも本体まで届くことを張る。

`_ts_die` は exec 形態では `exit 1` でシェルごと止まるが、source 形態では `return 1` が
関数から抜けるだけで、`cmd || _ts_die "..."` の次の行がそのまま走る——2026-09-10 04:0x JST 枠で
pip の read timeout により `FAIL:` 3 行が出た後、同じ stdout の最終行に `ready` が出た
（K-20260910-a-dual-mode-abort-aborts-only-where-it-can-exit）。ROUTINE_PROMPT が推奨する経路は
source 側なので、効かないのは推奨側だった。

処方は呼び出し側で `|| { _ts_die "..."; return 1; }` と書くこと（トップレベルの `return` は
sourced ファイルから抜ける。exec 形態では `_ts_die` が先に exit するので `return` は不達）。
書式は静的に、挙動は fake python で実際に source して張る。
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

BOOTSTRAP = Path(__file__).parents[3] / "bootstrap.sh"

# `_ts_die` の呼び出し規約: 中断の射程を本体へ伸ばす `return 1` を同じ群に同梱する。
_DIE_CALL_SHAPE = re.compile(r'\|\| \{ _ts_die "[^"]*"; return 1; \}')


def test_every_die_call_site_returns_from_sourced_file():
    """`_ts_die` の全呼び出しが `|| { _ts_die "..."; return 1; }` の形。

    8 箇所目の呼び出しが素の `|| _ts_die "..."` で追加されると、そこだけ source 形態で
    素通りする（2026-09-10 の再発）。コメント行は対象外。
    """
    lines = BOOTSTRAP.read_text(encoding="utf-8").splitlines()
    call_sites = [
        ln for ln in lines if '_ts_die "' in ln and not ln.lstrip().startswith("#")
    ]
    assert call_sites, "_ts_die の呼び出しが 1 つも無い（関数名が変わった？）"
    bad = [ln for ln in call_sites if not _DIE_CALL_SHAPE.search(ln)]
    assert not bad, (
        "source 形態で中断が届かない呼び出し（`return 1` 同梱漏れ）:\n" + "\n".join(bad)
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が無い環境")
def test_sourced_bootstrap_stops_at_first_fail_and_never_prints_ready(tmp_path: Path):
    """pip が落ちたら source でも非 0 で抜け、`ready` は出ない。

    fake python: `-m pip` だけ失敗させ、それ以外は本物へ委譲する。bootstrap は依存導入の
    前に python を呼ばないので、最初の `FAIL:` で止まれば後続の `ready` は出ないはず。
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_python = bin_dir / "python"
    real_python = Path(sys.executable).as_posix()
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "${1:-}" = "-m" ] && [ "${2:-}" = "pip" ]; then\n'
        '  echo "fake pip: read timeout" >&2; exit 1\n'
        "fi\n"
        f'exec "{real_python}" "$@"\n',
        encoding="utf-8",
        newline="\n",
    )
    fake_python.chmod(fake_python.stat().st_mode | stat.S_IEXEC)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir.as_posix()}{os.pathsep}{env.get('PATH', '')}"
    env["TELEGRAM_SECRETARY_ENV_FILE"] = (tmp_path / "env.sh").as_posix()
    env["TELEGRAM_SECRETARY_STATE_DIR"] = (tmp_path / "state").as_posix()

    proc = subprocess.run(
        ["bash", "-c", f'source "{BOOTSTRAP.as_posix()}"'],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode != 0, f"source が exit 0 で抜けた\nstdout:\n{proc.stdout}"
    assert "FAIL:" in proc.stderr, f"FAIL 行が stderr に無い\nstderr:\n{proc.stderr}"
    assert "ready" not in proc.stdout, f"失敗後に ready が出た\nstdout:\n{proc.stdout}"
    assert not (tmp_path / "env.sh").exists(), (
        "失敗後に env snapshot が書かれた（後続が走った）"
    )
