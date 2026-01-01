# usecases/wait_essay.py
"""
エッセイ待機処理のユースケース

指定時刻まで待機してエッセイを実行する。
"""
from __future__ import annotations

import os
import sys
import subprocess
from datetime import datetime, timedelta
from typing import Optional


class WaiterError(Exception):
    """待機処理エラー"""
    pass


def get_persistent_dir() -> str:
    """
    永続ディレクトリを取得する。

    スクリプトやログファイルを保存するディレクトリ。

    Returns:
        永続ディレクトリのパス
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        path = os.path.join(base, "EmailingEssay")
    else:
        path = os.path.expanduser("~/.emailingessay")

    os.makedirs(path, exist_ok=True)
    return path


def parse_target_time(time_str: str) -> datetime:
    """
    時刻文字列をパースしてdatetimeを返す。

    サポートする形式:
        HH:MM           - 今日（過ぎていれば明日）
        YYYY-MM-DD HH:MM - 特定の日時

    Args:
        time_str: 時刻文字列

    Returns:
        ターゲットのdatetime

    Raises:
        ValueError: 無効な形式または過去の日時
    """
    # YYYY-MM-DD HH:MM 形式を試行
    if " " in time_str and len(time_str) > 10:
        try:
            target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            if target < datetime.now():
                raise ValueError(f"Target time {time_str} is in the past")
            return target
        except ValueError as e:
            if "is in the past" in str(e):
                raise
            pass  # HH:MM形式を試行

    # HH:MM 形式（今日または明日）
    try:
        target = datetime.strptime(time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        # 今日の指定時刻が過ぎていれば明日にスケジュール
        if target < datetime.now():
            target += timedelta(days=1)
        return target
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}")


class WaitEssayUseCase:
    """エッセイ待機処理のユースケース"""

    def spawn(
        self,
        target_time: str,
        theme: str = "",
        context: str = "",
        file_list: str = "",
        lang: str = ""
    ) -> int:
        """
        デタッチドプロセスを起動して待機・実行する。

        Args:
            target_time: HH:MM または YYYY-MM-DD HH:MM
            theme: エッセイのテーマ
            context: コンテキストファイルパス
            file_list: ファイルリストパス
            lang: 言語（ja, en, auto）

        Returns:
            プロセスID

        Raises:
            WaiterError: 起動に失敗した場合
        """
        # Claudeコマンドの引数を構築
        claude_args = []
        if theme:
            theme_escaped = theme.replace("'", "\\'")
            claude_args.append(f"'{theme_escaped}'")
        if context:
            context_safe = context.replace("\\", "/")
            claude_args.append(f"-c '{context_safe}'")
        if file_list:
            file_list_safe = file_list.replace("\\", "/")
            claude_args.append(f"-f '{file_list_safe}'")
        if lang:
            claude_args.append(f"-l {lang}")
        claude_args_str = " ".join(claude_args) if claude_args else ""

        # ログファイル
        persistent_dir = get_persistent_dir()
        log_file = os.path.join(persistent_dir, "essay_wait.log").replace("\\", "/")

        # 待機スクリプトを生成
        script = self._generate_waiter_script(target_time, claude_args_str, log_file)

        # スクリプトファイルに書き込み
        script_file = os.path.join(persistent_dir, "essay_waiter_temp.py")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)

        # デタッチドプロセスを起動
        proc = self._spawn_detached(script_file)

        # 情報を表示
        target = parse_target_time(target_time)
        print(f"Scheduled essay for {target.strftime('%Y-%m-%d %H:%M')}")
        print(f"Process ID: {proc.pid}")
        print("You can close this terminal. Essay will execute at the scheduled time.")
        if theme:
            print(f"Theme: {theme}")
        if context:
            print(f"Context: {context}")
        if file_list:
            print(f"File list: {file_list}")
        if lang:
            print(f"Language: {lang}")

        return proc.pid

    def _generate_waiter_script(
        self,
        target_time: str,
        claude_args_str: str,
        log_file: str
    ) -> str:
        """待機スクリプトを生成"""
        return f'''# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import subprocess
import sys
import os

LOG_FILE = r"{log_file}"
TARGET_TIME = "{target_time}"
CLAUDE_ARGS = """{claude_args_str}"""

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write("[" + timestamp + "] " + str(msg) + "\\n")

try:
    log("Started. Target: " + TARGET_TIME)

    # Parse time - support both HH:MM and YYYY-MM-DD HH:MM
    time_str = TARGET_TIME
    if " " in time_str and len(time_str) > 10:
        target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    else:
        target = datetime.strptime(time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        if target < datetime.now():
            target += timedelta(days=1)

    log("Waiting until " + target.strftime("%Y-%m-%d %H:%M") + "...")

    # Poll every minute (sleep-resilient)
    while datetime.now() < target:
        time.sleep(60)

    log("Target time reached: " + datetime.now().strftime("%H:%M"))
    log("Launching Claude Code for essay...")

    # Execute Claude Code (--dangerously-skip-permissions for non-interactive)
    cmd = 'claude --dangerously-skip-permissions -p "/essay ' + CLAUDE_ARGS + '"'
    log("Command: " + cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    log("Return code: " + str(result.returncode))
    if result.stdout:
        log("Stdout: " + result.stdout[:500])
    if result.stderr:
        log("Stderr: " + result.stderr[:500])
    log("Done.")

except Exception as e:
    log("ERROR: " + str(e))
'''

    def _spawn_detached(self, script_file: str) -> subprocess.Popen:
        """デタッチドプロセスを起動"""
        if sys.platform == "win32":
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            proc = subprocess.Popen(
                [sys.executable, script_file],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, script_file],
                start_new_session=True,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return proc
