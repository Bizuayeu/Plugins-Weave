#!/usr/bin/env python3
"""
CLI Runner Module
=================

Subprocess-based CLI execution helper for E2E testing.
Provides utilities for running CLI commands and validating their output.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class CLIResult:
    """
    CLI実行結果を格納するデータクラス

    Attributes:
        exit_code: プロセスの終了コード
        stdout: 標準出力
        stderr: 標準エラー出力
        json_output: JSON出力（パース可能な場合）
        command: 実行されたコマンド
    """

    exit_code: int
    stdout: str
    stderr: str
    json_output: Optional[Dict[str, Any]] = None
    command: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """終了コードが0かどうか"""
        return self.exit_code == 0

    @property
    def status(self) -> Optional[str]:
        """JSON出力のstatusフィールド（存在する場合）"""
        if self.json_output and isinstance(self.json_output, dict):
            return self.json_output.get("status")
        return None

    def assert_success(self) -> None:
        """
        コマンドが成功したことをアサート

        Raises:
            AssertionError: 終了コードが0でない場合
        """
        assert self.exit_code == 0, (
            f"Command failed with exit code {self.exit_code}\n"
            f"stdout: {self.stdout}\n"
            f"stderr: {self.stderr}"
        )

    def assert_failure(self, expected_code: Optional[int] = None) -> None:
        """
        コマンドが失敗したことをアサート

        Args:
            expected_code: 期待する終了コード（省略時は0以外）

        Raises:
            AssertionError: 終了コードが期待と異なる場合
        """
        if expected_code is not None:
            assert self.exit_code == expected_code, (
                f"Expected exit code {expected_code}, got {self.exit_code}\n"
                f"stdout: {self.stdout}\n"
                f"stderr: {self.stderr}"
            )
        else:
            assert self.exit_code != 0, (
                f"Expected non-zero exit code, got {self.exit_code}\nstdout: {self.stdout}"
            )

    def assert_json_status(self, expected_status: str) -> None:
        """
        JSON出力のstatusが期待値と一致することをアサート

        Args:
            expected_status: 期待するステータス（"ok", "error", etc.）

        Raises:
            AssertionError: ステータスが期待と異なる場合
        """
        assert self.json_output is not None, f"Output is not JSON: {self.stdout}"
        actual = self.json_output.get("status")
        assert actual == expected_status, (
            f"Expected status '{expected_status}', got '{actual}'\nFull output: {self.json_output}"
        )

    def assert_json_contains(self, key: str, value: Any = None) -> None:
        """
        JSON出力が指定キーを含むことをアサート

        Args:
            key: 存在すべきキー
            value: 期待する値（省略時はキーの存在のみチェック）

        Raises:
            AssertionError: キーが存在しない、または値が異なる場合
        """
        assert self.json_output is not None, f"Output is not JSON: {self.stdout}"
        assert key in self.json_output, f"Key '{key}' not found in output: {self.json_output}"
        if value is not None:
            actual = self.json_output[key]
            assert actual == value, f"Expected {key}='{value}', got '{actual}'"


class CLIRunner:
    """
    CLI実行ヘルパークラス

    subprocess経由でCLIコマンドを実行し、結果をCLIResultとして返す。

    Usage:
        runner = CLIRunner(plugin_root)
        result = runner.run_digest_setup("check")
        result.assert_success()
        assert result.json_output["status"] == "not_configured"
    """

    def __init__(
        self,
        plugin_root: Path,
        scripts_dir: Optional[Path] = None,
        python_executable: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """
        CLIRunnerを初期化

        Args:
            plugin_root: テスト用プラグインルート
            scripts_dir: scriptsディレクトリ（省略時は自動検出）
            python_executable: Pythonインタプリタパス（省略時はsys.executable）
            timeout: コマンドタイムアウト（秒）
        """
        self.plugin_root = Path(plugin_root)
        self.scripts_dir = scripts_dir or self._find_scripts_dir()
        self.python = python_executable or sys.executable
        self.timeout = timeout

    def _find_scripts_dir(self) -> Path:
        """scriptsディレクトリを検出"""
        # 現在のファイルから相対的に scripts を見つける
        current_file = Path(__file__)
        # cli_integration_tests -> test -> scripts
        scripts_dir = current_file.parent.parent.parent
        if (scripts_dir / "interfaces").exists():
            return scripts_dir
        raise RuntimeError(f"Could not find scripts directory from {current_file}")

    def _run_command(
        self,
        args: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CLIResult:
        """
        サブプロセスでコマンドを実行

        Args:
            args: コマンド引数リスト
            cwd: 作業ディレクトリ
            env: 環境変数

        Returns:
            CLIResult: 実行結果
        """
        # 環境変数を設定
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        # PYTHONPATHにscriptsを追加
        python_path = str(self.scripts_dir)
        if "PYTHONPATH" in run_env:
            run_env["PYTHONPATH"] = f"{python_path}{os.pathsep}{run_env['PYTHONPATH']}"
        else:
            run_env["PYTHONPATH"] = python_path

        # Windows環境でのエンコーディング問題を回避
        run_env["PYTHONIOENCODING"] = "utf-8"

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                cwd=cwd or self.scripts_dir,
                env=run_env,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            exit_code = result.returncode
        except subprocess.TimeoutExpired as e:
            stdout = (
                (e.stdout or b"").decode("utf-8", errors="replace")
                if isinstance(e.stdout, bytes)
                else (e.stdout or "")
            )
            stderr = (
                (e.stderr or b"").decode("utf-8", errors="replace")
                if isinstance(e.stderr, bytes)
                else (e.stderr or "")
            )
            exit_code = -1

        # JSON出力のパースを試行
        json_output = None
        if stdout and stdout.strip():
            try:
                json_output = json.loads(stdout.strip())
            except json.JSONDecodeError:
                # 複数行の場合、最後の行を試行
                lines = stdout.strip().split("\n")
                for line in reversed(lines):
                    try:
                        json_output = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

        return CLIResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            json_output=json_output,
            command=args,
        )

    def _build_module_args(
        self, module_name: str, *args: str, **kwargs: Union[str, bool]
    ) -> List[str]:
        """
        モジュール実行用の引数リストを構築

        Args:
            module_name: モジュール名（interfaces.digest_setup など）
            *args: 位置引数
            **kwargs: オプション引数（--key=value形式に変換）

        Returns:
            引数リスト
        """
        cmd = [self.python, "-m", module_name, "--plugin-root", str(self.plugin_root)]
        cmd.extend(args)

        for key, value in kwargs.items():
            key_name = key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key_name}")
            else:
                cmd.extend([f"--{key_name}", str(value)])

        return cmd

    # =========================================================================
    # digest_setup CLI
    # =========================================================================

    def run_digest_setup(self, *args: str, **kwargs) -> CLIResult:
        """
        digest_setup.py を実行

        Args:
            *args: サブコマンドと引数（"check", "init"など）
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果

        Examples:
            result = runner.run_digest_setup("check")
            result = runner.run_digest_setup("init", config=json_config)
            result = runner.run_digest_setup("init", config=json_config, force=True)
        """
        cmd = self._build_module_args("interfaces.digest_setup", *args, **kwargs)
        return self._run_command(cmd)

    # =========================================================================
    # digest_config CLI
    # =========================================================================

    def run_digest_config(self, *args: str, **kwargs) -> CLIResult:
        """
        digest_config.py を実行

        Args:
            *args: サブコマンドと引数（"show", "set", "update"など）
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果

        Examples:
            result = runner.run_digest_config("show")
            result = runner.run_digest_config("set", key="levels.weekly_threshold", value="10")
            result = runner.run_digest_config("update", config=json_config)
        """
        cmd = self._build_module_args("interfaces.digest_config", *args, **kwargs)
        return self._run_command(cmd)

    # =========================================================================
    # digest_auto CLI
    # =========================================================================

    def run_digest_auto(self, *args: str, **kwargs) -> CLIResult:
        """
        digest_auto.py を実行

        Args:
            *args: 引数
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果

        Examples:
            result = runner.run_digest_auto(output="json")
            result = runner.run_digest_auto(output="text")
        """
        cmd = self._build_module_args("interfaces.digest_auto", *args, **kwargs)
        return self._run_command(cmd)

    # =========================================================================
    # shadow_state_checker CLI
    # =========================================================================

    def run_shadow_state_checker(self, level: str, *args: str, **kwargs) -> CLIResult:
        """
        shadow_state_checker.py を実行

        Args:
            level: チェックするレベル（"weekly", "monthly"など）
            *args: 追加引数
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果
        """
        cmd = self._build_module_args("interfaces.shadow_state_checker", level, *args, **kwargs)
        return self._run_command(cmd)

    # =========================================================================
    # save_provisional_digest CLI
    # =========================================================================

    def run_save_provisional_digest(
        self,
        level: str,
        digest_json: str,
        *args: str,
        append: bool = False,
        **kwargs,
    ) -> CLIResult:
        """
        save_provisional_digest.py を実行

        Args:
            level: 保存先レベル（"weekly", "monthly"など）
            digest_json: 保存するダイジェストJSON
            append: 追記モード
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果
        """
        if append:
            kwargs["append"] = True
        cmd = self._build_module_args(
            "interfaces.save_provisional_digest", level, digest_json, *args, **kwargs
        )
        return self._run_command(cmd)

    # =========================================================================
    # finalize_from_shadow CLI
    # =========================================================================

    def run_finalize_from_shadow(self, level: str, title: str, *args: str, **kwargs) -> CLIResult:
        """
        finalize_from_shadow.py を実行

        Args:
            level: 確定するレベル（"weekly", "monthly"など）
            title: ダイジェストタイトル
            **kwargs: オプション引数

        Returns:
            CLIResult: 実行結果
        """
        cmd = self._build_module_args(
            "interfaces.finalize_from_shadow", level, title, *args, **kwargs
        )
        return self._run_command(cmd)

    # =========================================================================
    # generate_digest_auto.sh（Bashスクリプト）
    # =========================================================================

    def run_generate_digest_auto_sh(self, level: Optional[str] = None, **kwargs) -> CLIResult:
        """
        generate_digest_auto.sh を実行

        Args:
            level: ダイジェストレベル（省略時は新Loop検出モード）
            **kwargs: 環境変数として渡す追加設定

        Returns:
            CLIResult: 実行結果

        Note:
            Windows環境ではGit Bashを使用して実行
        """
        script_path = self.scripts_dir / "generate_digest_auto.sh"

        # シェルを選択（Windows: Git Bash, その他: sh）
        if sys.platform == "win32":
            # Git Bash経由で実行
            bash_path = self._find_git_bash()
            if bash_path:
                args = [bash_path, str(script_path)]
            else:
                # Git Bashが見つからない場合はスキップ
                return CLIResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Git Bash not found on Windows",
                    json_output=None,
                    command=["bash", str(script_path)],
                )
        else:
            args = ["bash", str(script_path)]

        if level:
            args.append(level)

        # 環境変数にPLUGIN_ROOTを設定
        env = {"PLUGIN_ROOT": str(self.plugin_root)}
        env.update(kwargs)

        return self._run_command(args, env=env)

    def _find_git_bash(self) -> Optional[str]:
        """Git Bashのパスを検出（Windows用）"""
        possible_paths = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ]
        for path in possible_paths:
            if Path(path).exists():
                return path

        # PATHから検索
        try:
            result = subprocess.run(["where", "bash"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None
