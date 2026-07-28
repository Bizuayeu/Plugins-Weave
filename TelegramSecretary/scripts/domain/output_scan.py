"""送信本文の漏洩スキャン（post-generation、検出箇所を伏せて記録する）。

`normalize.py` が入力側の防御（NFKC 正規化＋injection フラグ）を担うのに対し、こちらは
出力側——エージェントが起草した外向きテキストに秘匿値が混入していないかを機械検査する。
`SECURITY.md` §4 が全面エージェント責務としていた確認のうち、**形状で決まる 4 種**
（bot token / PAT / 秘匿 env 変数名 / ローカル絶対パス）を機械化する。形状に現れない機密
（関係者の事情など）はここでは止まらないため、エージェント側の確認責務は残る。

injection フラグが「ブロックせずフラグのみ」なのに対し、こちらは **redact する**——
送ってしまえば取り消せない（不可逆）ため、偽陽性で伏せ字が増える方を安全側と見る。
"""

from __future__ import annotations

import re

# 検出パターン（順に適用し、マッチ全体を伏せ字へ置換する）。
_OUTBOUND_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Telegram bot token: <bot_id>:<35 文字前後の base64url 風文字列>
    ("bot_token", re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}")),
    # GitHub PAT: classic（ghp_/gho_/ghu_/ghs_/ghr_）と fine-grained（github_pat_）
    (
        "pat",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    # 秘匿を示す語尾を持つ env 変数名（TELEGRAM_BOT_TOKEN / SHIORI_AUTHORIZED_CHATS 等）。
    # 製品固有の接頭辞を列挙せず語尾で捕まえる（双子リポで同一実装を保つため）。
    (
        "env_var_name",
        re.compile(
            r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_(?:TOKEN|SECRET|KEY|PASSWORD|PAT|CHATS)\b"
        ),
    ),
    # ローカル絶対パス。Windows ドライブ形式と、実行環境で使う POSIX の起点のみ。
    # 直前が語/コロン/スラッシュ/ドットなら URL のパス片とみなして拾わない（偽陽性ガード）。
    (
        "local_path",
        re.compile(
            r"(?<![\w:/.])(?:[A-Za-z]:[\\/]|/(?:home|Users|root|mnt|tmp)/)[^\s\"'<>|]*"
        ),
    ),
]


def redact_outbound(text: str) -> tuple[str, list[str]]:
    """秘匿値の形状を伏せ字に置換したテキストと、検出したパターン名を返す。

    パターン名は重複を畳んで検出順に返す（呼び出し側はこれをログに残し、
    伏せた実値そのものは記録しない）。
    """
    if not text:
        return text, []
    redacted = text
    hits: list[str] = []
    for name, pattern in _OUTBOUND_PATTERNS:
        redacted, count = pattern.subn(f"[REDACTED:{name}]", redacted)
        if count:
            hits.append(name)
    return redacted, hits
