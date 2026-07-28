from __future__ import annotations

from domain.output_scan import redact_outbound

# 以下はいずれも形状のみを模したダミー値（実在の資格情報ではない）。
DUMMY_BOT_TOKEN = "1234567890:AAdummyDUMMYdummyDUMMYdummyDUMMY123"
DUMMY_PAT = "ghp_dummyDUMMYdummyDUMMYdummy1234567890"
DUMMY_FINE_GRAINED_PAT = "github_pat_dummyDUMMYdummy_DUMMYdummy1234567890"


def test_clean_text_is_returned_unchanged_without_hits():
    text = "承知しました。明日の打ち合わせは 10 時からです。"
    redacted, hits = redact_outbound(text)
    assert redacted == text
    assert hits == []


def test_empty_text_is_noop():
    assert redact_outbound("") == ("", [])


def test_bot_token_shape_is_redacted():
    redacted, hits = redact_outbound(f"token is {DUMMY_BOT_TOKEN} ok")
    assert DUMMY_BOT_TOKEN not in redacted
    assert "[REDACTED:bot_token]" in redacted
    assert hits == ["bot_token"]


def test_classic_pat_shape_is_redacted():
    redacted, hits = redact_outbound(f"use {DUMMY_PAT} for push")
    assert DUMMY_PAT not in redacted
    assert hits == ["pat"]


def test_fine_grained_pat_shape_is_redacted():
    redacted, hits = redact_outbound(f"key={DUMMY_FINE_GRAINED_PAT}")
    assert DUMMY_FINE_GRAINED_PAT not in redacted
    assert hits == ["pat"]


def test_secret_env_var_names_are_redacted():
    redacted, hits = redact_outbound(
        "TELEGRAM_BOT_TOKEN と SHIORI_AUTHORIZED_CHATS を確認してください"
    )
    assert "TELEGRAM_BOT_TOKEN" not in redacted
    assert "SHIORI_AUTHORIZED_CHATS" not in redacted
    assert hits == ["env_var_name"]


def test_ordinary_uppercase_word_is_not_treated_as_env_var():
    # 秘匿を示す語尾（_TOKEN/_SECRET/_KEY/_PASSWORD/_PAT/_CHATS）を持たない大文字語は素通し
    redacted, hits = redact_outbound("README と CHANGELOG を更新しました")
    assert hits == []
    assert redacted == "README と CHANGELOG を更新しました"


def test_windows_absolute_path_is_redacted():
    redacted, hits = redact_outbound(
        r"ログは C:\Users\owner\state\wal.jsonl にあります"
    )
    assert "C:\\Users" not in redacted
    assert hits == ["local_path"]


def test_posix_home_path_is_redacted():
    redacted, hits = redact_outbound("output at /home/agent/state/registry.json")
    assert "/home/agent" not in redacted
    assert hits == ["local_path"]


def test_url_containing_home_segment_is_not_redacted():
    # 偽陽性ガード: URL のパス片は絶対パスとして扱わない
    text = "https://example.com/home/agent/index.html を参照"
    redacted, hits = redact_outbound(text)
    assert redacted == text
    assert hits == []


def test_multiple_categories_are_reported_once_each():
    redacted, hits = redact_outbound(
        f"{DUMMY_PAT} を TELEGRAM_BOT_TOKEN として /home/a/b に置いた（{DUMMY_PAT}）"
    )
    assert DUMMY_PAT not in redacted
    assert sorted(hits) == ["env_var_name", "local_path", "pat"]
