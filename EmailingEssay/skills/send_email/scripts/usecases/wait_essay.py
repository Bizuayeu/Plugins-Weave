# usecases/wait_essay.py
"""
エッセイ待機処理のユースケース

指定時刻まで待機してエッセイを実行する。
WaiterError は domain.exceptions に移動済み。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from domain.exceptions import WaiterError
from .command_builder import build_claude_args

if TYPE_CHECKING:
    from .ports import StoragePort, ProcessSpawnerPort

# 後方互換性のため再エクスポート
__all__ = [
    "WaitEssayUseCase",
    "WaiterError",
    "get_persistent_dir",
    "parse_target_time",
]


def get_persistent_dir() -> str:
    """
    永続ディレクトリを取得する。

    スクリプトやログファイルを保存するディレクトリ。
    Claude Code plugin convention: ~/.claude/plugins/.emailingessay

    Returns:
        永続ディレクトリのパス

    Note:
        この関数は後方互換性のために残されています。
        新しいコードでは StoragePort.get_persistent_dir() を使用してください。
    """
    path = Path.home() / ".claude" / "plugins" / ".emailingessay"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def parse_target_time(time_str: str) -> datetime:
    """
    時刻文字列をパースしてdatetimeを返す。

    後方互換性のためのラッパー関数。
    内部ではdomain.models.TargetTimeを使用する。

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
    from domain.models import TargetTime, ValidationError

    try:
        return TargetTime.parse(time_str).datetime
    except ValidationError as e:
        raise ValueError(str(e))


class WaitEssayUseCase:
    """エッセイ待機処理のユースケース"""

    def __init__(
        self,
        storage_port: "StoragePort",
        spawner_port: "ProcessSpawnerPort"
    ) -> None:
        """
        WaitEssayUseCaseを初期化する。

        Args:
            storage_port: ストレージポート（必須）
            spawner_port: プロセススポーナーポート（必須）
        """
        self._storage = storage_port
        self._spawner = spawner_port

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
        # Claudeコマンドの引数を構築（統一ユーティリティ使用）
        claude_args = build_claude_args(theme, context, file_list, lang)

        # 永続ディレクトリを取得（DIされたストレージを使用）
        persistent_dir = Path(self._storage.get_persistent_dir())
        log_file = str(persistent_dir / "essay_wait.log").replace("\\", "/")

        # 待機スクリプトを生成
        script = self._generate_waiter_script(target_time, claude_args, log_file)

        # スクリプトファイルに書き込み
        script_file = str(persistent_dir / "essay_waiter_temp.py")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)

        # デタッチドプロセスを起動（DIされたスポーナーを使用）
        pid = self._spawner.spawn_detached(script_file)

        # 待機プロセスを登録（PIDトラッキング）
        self._storage.register_waiter(pid, target_time, theme)

        # 情報を表示
        target = parse_target_time(target_time)
        print(f"Scheduled essay for {target.strftime('%Y-%m-%d %H:%M')}")
        print(f"Process ID: {pid}")
        print("You can close this terminal. Essay will execute at the scheduled time.")
        if theme:
            print(f"Theme: {theme}")
        if context:
            print(f"Context: {context}")
        if file_list:
            print(f"File list: {file_list}")
        if lang:
            print(f"Language: {lang}")

        return pid

    def _generate_waiter_script(
        self,
        target_time: str,
        claude_args_str: str,
        log_file: str
    ) -> str:
        """待機スクリプトを生成（テンプレートシステム使用）"""
        from frameworks.templates import load_template, render_template

        template = load_template("essay_waiter.py.template")
        return render_template(
            template,
            log_file=log_file,
            target_time=target_time,
            claude_args=claude_args_str
        )

    def list_waiters(self) -> list[dict]:
        """
        アクティブな待機プロセス一覧を取得する。

        Returns:
            待機プロセスのリスト
        """
        return self._storage.get_active_waiters()
