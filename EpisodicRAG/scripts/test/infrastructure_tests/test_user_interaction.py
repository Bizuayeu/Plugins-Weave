#!/usr/bin/env python3
"""
infrastructure/user_interaction.py のユニットテスト
=====================================================

ユーザー確認コールバック関数の動作を検証。
"""

import sys

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(__file__).rsplit("test", 1)[0])

from infrastructure.user_interaction import get_default_confirm_callback


# =============================================================================
# get_default_confirm_callback テスト
# =============================================================================


class TestGetDefaultConfirmCallback:
    """get_default_confirm_callback 関数のテスト"""

    @pytest.mark.unit
    def test_returns_callable(self):
        """callableを返す"""
        callback = get_default_confirm_callback()
        assert callable(callback)

    @pytest.mark.unit
    def test_accepts_y_response(self, monkeypatch):
        """'y'の回答でTrueを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "y")
        callback = get_default_confirm_callback()
        assert callback("Test?") is True

    @pytest.mark.unit
    def test_accepts_Y_response(self, monkeypatch):
        """'Y'（大文字）の回答でもTrueを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "Y")
        callback = get_default_confirm_callback()
        assert callback("Test?") is True

    @pytest.mark.unit
    def test_rejects_n_response(self, monkeypatch):
        """'n'の回答でFalseを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        callback = get_default_confirm_callback()
        assert callback("Test?") is False

    @pytest.mark.unit
    def test_rejects_N_response(self, monkeypatch):
        """'N'（大文字）の回答でもFalseを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "N")
        callback = get_default_confirm_callback()
        assert callback("Test?") is False

    @pytest.mark.unit
    def test_rejects_yes_response(self, monkeypatch):
        """'yes'（yではない）の回答でFalseを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        callback = get_default_confirm_callback()
        assert callback("Test?") is False

    @pytest.mark.unit
    def test_rejects_empty_response(self, monkeypatch):
        """空の回答でFalseを返す"""
        monkeypatch.setattr("builtins.input", lambda _: "")
        callback = get_default_confirm_callback()
        assert callback("Test?") is False

    @pytest.mark.unit
    def test_handles_eof_error(self, monkeypatch):
        """EOFError発生時はTrueを返す（非対話環境での自動承認）"""

        def raise_eof(_):
            raise EOFError()

        monkeypatch.setattr("builtins.input", raise_eof)
        callback = get_default_confirm_callback()
        assert callback("Test?") is True

    @pytest.mark.unit
    def test_prompt_format(self, monkeypatch):
        """プロンプト形式が正しい"""
        captured_prompt = []

        def capture_input(prompt):
            captured_prompt.append(prompt)
            return "y"

        monkeypatch.setattr("builtins.input", capture_input)
        callback = get_default_confirm_callback()
        callback("Continue?")

        assert len(captured_prompt) == 1
        assert captured_prompt[0] == "Continue? (y/n): "

    @pytest.mark.unit
    def test_unicode_message(self, monkeypatch):
        """Unicode文字を含むメッセージを受け付ける"""
        captured_prompt = []

        def capture_input(prompt):
            captured_prompt.append(prompt)
            return "y"

        monkeypatch.setattr("builtins.input", capture_input)
        callback = get_default_confirm_callback()
        result = callback("ファイルを上書きしますか？")

        assert result is True
        assert "ファイルを上書きしますか？" in captured_prompt[0]

    @pytest.mark.unit
    def test_each_call_returns_new_function(self):
        """毎回新しい関数を返す"""
        callback1 = get_default_confirm_callback()
        callback2 = get_default_confirm_callback()
        # 同じ振る舞いだが異なるインスタンス
        assert callback1 is not callback2
