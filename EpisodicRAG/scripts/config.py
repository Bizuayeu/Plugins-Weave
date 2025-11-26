#!/usr/bin/env python3
"""
Digest Plugin Configuration Manager
====================================

Plugin自己完結版：Plugin内の.claude-plugin/config.jsonから設定を読み込む
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


# =============================================================================
# 共通定数: レベル設定（Single Source of Truth）
# =============================================================================
#
# LEVEL_CONFIG フィールド説明:
#   prefix  - ファイル名プレフィックス（例: W0001, M001, MD01）
#   digits  - 番号の桁数（例: W0001は4桁）
#   dir     - digests_path 以下のサブディレクトリ名
#   source  - この階層を生成する際の入力元（"loops" または下位階層名）
#   next    - 確定時にカスケードする上位階層（None = 最上位）
#
LEVEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "weekly": {"prefix": "W", "digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly"},
    "monthly": {"prefix": "M", "digits": 3, "dir": "2_Monthly", "source": "weekly", "next": "quarterly"},
    "quarterly": {"prefix": "Q", "digits": 3, "dir": "3_Quarterly", "source": "monthly", "next": "annual"},
    "annual": {"prefix": "A", "digits": 2, "dir": "4_Annual", "source": "quarterly", "next": "triennial"},
    "triennial": {"prefix": "T", "digits": 2, "dir": "5_Triennial", "source": "annual", "next": "decadal"},
    "decadal": {"prefix": "D", "digits": 2, "dir": "6_Decadal", "source": "triennial", "next": "multi_decadal"},
    "multi_decadal": {"prefix": "MD", "digits": 2, "dir": "7_Multi-decadal", "source": "decadal", "next": "centurial"},
    "centurial": {"prefix": "C", "digits": 2, "dir": "8_Centurial", "source": "multi_decadal", "next": None}
}

LEVEL_NAMES = list(LEVEL_CONFIG.keys())

# プレースホルダー文字数制限（Claudeへのガイドライン）
PLACEHOLDER_LIMITS: Dict[str, int] = {
    "abstract_chars": 2400,      # abstract（全体統合分析）の文字数
    "impression_chars": 800,     # impression（所感・展望）の文字数
    "keyword_count": 5,          # キーワードの個数
}

# プレースホルダーマーカー（Single Source of Truth）
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER"
PLACEHOLDER_END = " -->"
PLACEHOLDER_SIMPLE = f"{PLACEHOLDER_MARKER}{PLACEHOLDER_END}"  # "<!-- PLACEHOLDER -->"


# =============================================================================
# 共通関数: ファイル番号抽出
# =============================================================================

def extract_file_number(filename: str) -> Optional[Tuple[str, int]]:
    """
    ファイル名からプレフィックスと番号を抽出

    Args:
        filename: ファイル名（例: "Loop0186_xxx.txt", "MD01_xxx.txt"）

    Returns:
        (prefix, number) のタプル、またはNone
    """
    # 型チェック
    if not isinstance(filename, str):
        return None

    # MDプレフィックス（2文字）を先にチェック（M単独より優先）
    match = re.search(r'(Loop|MD)(\d+)', filename)
    if match:
        return (match.group(1), int(match.group(2)))

    # 1文字プレフィックス
    match = re.search(r'([WMQATDC])(\d+)', filename)
    if match:
        return (match.group(1), int(match.group(2)))

    return None


def extract_number_only(filename: str) -> Optional[int]:
    """番号のみを抽出（後方互換性用）"""
    result = extract_file_number(filename)
    return result[1] if result else None


def format_digest_number(level: str, number: int) -> str:
    """
    レベルと番号から統一されたフォーマットの文字列を生成

    Args:
        level: 階層名（"loop", "weekly", "monthly", ...）
        number: 番号

    Returns:
        ゼロ埋めされた文字列（例: "Loop0186", "W0001", "MD01"）

    Raises:
        ValueError: 不正なレベル名の場合

    Examples:
        >>> format_digest_number("loop", 186)
        'Loop0186'
        >>> format_digest_number("weekly", 1)
        'W0001'
        >>> format_digest_number("multi_decadal", 3)
        'MD03'
    """
    if level == "loop":
        return f"Loop{number:04d}"

    if level not in LEVEL_CONFIG:
        raise ValueError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES + ['loop']}")

    config = LEVEL_CONFIG[level]
    return f"{config['prefix']}{number:0{config['digits']}d}"


# =============================================================================
# DigestConfig クラス
# =============================================================================


class DigestConfig:
    """設定管理クラス（Plugin自己完結版）"""

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        初期化

        Args:
            plugin_root: Pluginルート（省略時は自動検出）
        """
        # Pluginルート検出
        if plugin_root is None:
            plugin_root = self._find_plugin_root()

        self.plugin_root = plugin_root
        self.config_file = self.plugin_root / ".claude-plugin" / "config.json"
        self.config = self.load_config()
        self.base_dir = self._resolve_base_dir()

    def _find_plugin_root(self) -> Path:
        """
        Plugin自身のルートディレクトリを検出

        scripts/config.py から実行された場合:
          scripts/config.py の親（scripts/）の親（EpisodicRAG/）がPluginルート

        Returns:
            PluginルートのPath

        Raises:
            FileNotFoundError: __file__が定義されていない場合、またはPluginルートが見つからない場合
        """
        # このファイル（config.py）の場所から相対的にPluginルートを検出
        try:
            current_file = Path(__file__).resolve()
        except NameError:
            raise FileNotFoundError("Cannot determine script location (__file__ not defined)")

        # scripts/config.py なので、2階層上がPluginルート
        plugin_root = current_file.parent.parent

        # .claude-plugin/config.json が存在するか確認
        if (plugin_root / ".claude-plugin" / "config.json").exists():
            return plugin_root

        # 見つからない場合はエラー
        raise FileNotFoundError(
            f"Plugin root not found. Expected .claude-plugin/config.json at: {plugin_root}"
        )

    def _resolve_base_dir(self) -> Path:
        """
        base_dir設定を解釈して基準ディレクトリを返す

        base_dir設定値（相対パスのみ）:
          - ".": プラグインルート自身（デフォルト）
          - "../../..": プラグインルートから3階層上
          - 任意の相対パス: プラグインルートからの相対パス

        Returns:
            解決された基準ディレクトリのPath

        Note:
            絶対パスは使用しない（Git公開時の可搬性のため）
        """
        base_dir_setting = self.config.get("base_dir", ".")
        return (self.plugin_root / base_dir_setting).resolve()

    def load_config(self) -> Dict[str, Any]:
        """
        設定読み込み

        Returns:
            設定辞書

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            json.JSONDecodeError: JSONのパースに失敗した場合
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in config file {self.config_file}: {e.msg}",
                    e.doc, e.pos
                )

        raise FileNotFoundError(
            f"Config file not found: {self.config_file}\n"
            f"Run setup first: bash {self.plugin_root}/scripts/setup.sh"
        )

    def resolve_path(self, key: str) -> Path:
        """
        相対パスを絶対パスに解決（base_dir基準）

        Args:
            key: paths以下のキー（loops_dir, digests_dir, essences_dir）

        Returns:
            解決された絶対Path

        Raises:
            KeyError: pathsセクションまたはキーが存在しない場合
        """
        if "paths" not in self.config:
            raise KeyError("'paths' section missing in config.json")
        if key not in self.config["paths"]:
            raise KeyError(f"Path key '{key}' not found in config.json")
        rel_path = self.config["paths"][key]
        return (self.base_dir / rel_path).resolve()

    @property
    def loops_path(self) -> Path:
        """Loopファイル配置先"""
        return self.resolve_path("loops_dir")

    @property
    def digests_path(self) -> Path:
        """Digest出力先"""
        return self.resolve_path("digests_dir")

    @property
    def essences_path(self) -> Path:
        """GrandDigest配置先"""
        return self.resolve_path("essences_dir")

    def get_level_dir(self, level: str) -> Path:
        """
        指定レベルのRegularDigest格納ディレクトリを取得

        Args:
            level: 階層名（weekly, monthly, ...）

        Returns:
            RegularDigest格納ディレクトリの絶対Path

        Raises:
            ValueError: 不正なレベル名の場合
        """
        if level not in LEVEL_CONFIG:
            raise ValueError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES}")
        return self.digests_path / LEVEL_CONFIG[level]["dir"]

    def get_provisional_dir(self, level: str) -> Path:
        """
        指定レベルのProvisionalDigest格納ディレクトリを取得

        Args:
            level: 階層名（weekly, monthly, ...）

        Returns:
            ProvisionalDigest格納ディレクトリの絶対Path
            例: digests_path/1_Weekly/Provisional

        Raises:
            ValueError: 不正なレベル名の場合
        """
        return self.get_level_dir(level) / "Provisional"

    def validate_directory_structure(self) -> list:
        """
        ディレクトリ構造の検証

        期待される構造:
          - loops_path が存在
          - digests_path が存在
          - essences_path が存在
          - 各レベルディレクトリ (1_Weekly, 2_Monthly, ...) が存在
          - 各レベルディレクトリ内にProvisionalが存在

        Returns:
            エラーメッセージのリスト（問題がなければ空リスト）
        """
        errors = []

        # 基本ディレクトリのチェック
        for path, name in [
            (self.loops_path, "Loops"),
            (self.digests_path, "Digests"),
            (self.essences_path, "Essences"),
        ]:
            if not path.exists():
                errors.append(f"{name} directory missing: {path}")

        # 各レベルディレクトリとProvisionalのチェック
        for level in LEVEL_NAMES:
            level_dir = self.get_level_dir(level)
            prov_dir = self.get_provisional_dir(level)

            if not level_dir.exists():
                errors.append(f"{level} directory missing: {level_dir}")
            elif not prov_dir.exists():
                # レベルディレクトリがある場合のみProvisionalをチェック
                errors.append(f"{level} Provisional missing: {prov_dir}")

        return errors

    @property
    def weekly_threshold(self) -> int:
        """Weekly生成に必要なLoop数"""
        return self.get_threshold("weekly")

    @property
    def monthly_threshold(self) -> int:
        """Monthly生成に必要なWeekly数"""
        return self.get_threshold("monthly")

    @property
    def quarterly_threshold(self) -> int:
        """Quarterly生成に必要なMonthly数"""
        return self.get_threshold("quarterly")

    @property
    def annual_threshold(self) -> int:
        """Annual生成に必要なQuarterly数"""
        return self.get_threshold("annual")

    @property
    def triennial_threshold(self) -> int:
        """Triennial生成に必要なAnnual数"""
        return self.get_threshold("triennial")

    @property
    def decadal_threshold(self) -> int:
        """Decadal生成に必要なTriennial数"""
        return self.get_threshold("decadal")

    @property
    def multi_decadal_threshold(self) -> int:
        """Multi-decadal生成に必要なDecadal数"""
        return self.get_threshold("multi_decadal")

    @property
    def centurial_threshold(self) -> int:
        """Centurial生成に必要なMulti-decadal数"""
        return self.get_threshold("centurial")

    def get_threshold(self, level: str) -> int:
        """
        指定レベルのthresholdを動的に取得（8つのプロパティを統合）

        Args:
            level: 階層名（weekly, monthly, quarterly, annual, triennial, decadal, multi_decadal, centurial）

        Returns:
            そのレベルのthreshold値

        Raises:
            ValueError: 不正なレベル名の場合
        """
        if level not in LEVEL_CONFIG:
            raise ValueError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES}")

        # デフォルト値
        defaults = {
            "weekly": 5,
            "monthly": 5,
            "quarterly": 3,
            "annual": 4,
            "triennial": 3,
            "decadal": 3,
            "multi_decadal": 3,
            "centurial": 4
        }

        key = f"{level}_threshold"
        return self.config.get("levels", {}).get(key, defaults.get(level, 5))

    def get_identity_file_path(self) -> Optional[Path]:
        """
        外部identityファイルのパス（設定されている場合のみ）

        Returns:
            identityファイルの絶対Path（設定されていない場合はNone）
        """
        identity_file = self.config.get("paths", {}).get("identity_file_path")

        if identity_file is None:
            return None

        return (self.base_dir / identity_file).resolve()

    def show_paths(self):
        """パス設定を表示（デバッグ用）"""
        print(f"Plugin Root: {self.plugin_root}")
        print(f"Config File: {self.config_file}")
        print(f"Base Dir (setting): {self.config.get('base_dir', '.')}")
        print(f"Base Dir (resolved): {self.base_dir}")
        print(f"Loops Path: {self.loops_path}")
        print(f"Digests Path: {self.digests_path}")
        print(f"Essences Path: {self.essences_path}")

        identity_file = self.get_identity_file_path()
        if identity_file:
            print(f"Identity File: {identity_file}")


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Digest Plugin Configuration Manager")
    parser.add_argument("--show-paths", action="store_true", help="Show all configured paths")
    parser.add_argument("--plugin-root", type=Path, help="Override plugin root")

    args = parser.parse_args()

    try:
        config = DigestConfig(plugin_root=args.plugin_root)

        if args.show_paths:
            config.show_paths()
        else:
            # デフォルト: JSON出力
            print(json.dumps(config.config, indent=2, ensure_ascii=False))

    except FileNotFoundError as e:
        # 循環インポートを避けるため直接出力
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
