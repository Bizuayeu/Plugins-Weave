#!/usr/bin/env python3
"""
Digest Auto CLI
===============

健全性診断CLI。Claudeから呼び出され、システム状態を分析し、
まだらボケを検出、生成可能なダイジェスト階層を推奨する。

Usage:
    python -m interfaces.digest_auto --output json
    python -m interfaces.digest_auto --output text
"""

import argparse
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from domain.constants import DIGEST_LEVEL_NAMES, LEVEL_CONFIG
from domain.exceptions import FileIOError
from domain.file_constants import (
    CONFIG_FILENAME,
    DIGEST_TIMES_FILENAME,
    GRAND_DIGEST_FILENAME,
    SHADOW_GRAND_DIGEST_FILENAME,
)
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json, try_load_json
from interfaces.cli_helpers import output_error, output_json

# 表示制限の定数
MAX_DISPLAY_FILES = 5  # テキストレポートに表示する最大ファイル数


@dataclass
class Issue:
    """検出された問題"""

    type: str  # "unprocessed_loops" | "placeholders" | "gaps"
    level: Optional[str] = None
    count: int = 0
    files: List[str] = field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


@dataclass
class LevelStatus:
    """階層の状態"""

    level: str
    current: int
    threshold: int
    ready: bool
    source_type: str  # "loops" | level name


@dataclass
class AnalysisResult:
    """分析結果"""

    status: str  # "ok" | "warning" | "error"
    issues: List[Issue] = field(default_factory=list)
    generatable_levels: List[LevelStatus] = field(default_factory=list)
    insufficient_levels: List[LevelStatus] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None


class DigestAutoAnalyzer:
    """健全性診断クラス"""

    # 階層の親子関係とレベル順序は domain.constants.LEVEL_CONFIG, DIGEST_LEVEL_NAMES を使用

    def __init__(self) -> None:
        """Initialize DigestAutoAnalyzer"""
        persistent_config_dir = get_persistent_config_dir()
        self.config_file = persistent_config_dir / CONFIG_FILENAME
        self.last_digest_file = persistent_config_dir / DIGEST_TIMES_FILENAME

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        return load_json(self.config_file)

    def _resolve_base_dir(self, config: Dict[str, Any]) -> Path:
        """base_dirを解決"""
        base_dir_str = config.get("base_dir", "")
        if not base_dir_str:
            raise ValueError("base_dir is required in config.json")
        base_path = Path(base_dir_str).expanduser()
        if not base_path.is_absolute():
            raise ValueError("base_dir must be an absolute path")
        return base_path.resolve()

    def _resolve_paths(self, config: Dict[str, Any]) -> Tuple[Path, Path, Path]:
        """設定から各種パスを解決

        Args:
            config: 設定データ

        Returns:
            (loops_path, essences_path, digests_path) のタプル
        """
        base_dir = self._resolve_base_dir(config)
        paths = config.get("paths", {})

        loops_path = base_dir / paths.get("loops_dir", "data/Loops")
        essences_path = base_dir / paths.get("essences_dir", "data/Essences")
        digests_path = base_dir / paths.get("digests_dir", "data/Digests")

        return loops_path, essences_path, digests_path

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """JSONファイルを読み込む（存在しない場合はNone）"""
        return try_load_json(file_path, log_on_error=False)

    def _extract_file_number(self, filename: str) -> Optional[int]:
        """ファイル名から番号を抽出"""
        # L00001, W0001, M001 などのパターンにマッチ
        match = re.search(r"[A-Z]+(\d+)", filename)
        if match:
            return int(match.group(1))
        return None

    def _find_gaps(self, numbers: List[int]) -> List[int]:
        """連番のギャップを検出"""
        if len(numbers) < 2:
            return []

        sorted_nums = sorted(numbers)
        gaps = []
        for i in range(len(sorted_nums) - 1):
            for n in range(sorted_nums[i] + 1, sorted_nums[i + 1]):
                gaps.append(n)
        return gaps

    def analyze(self) -> AnalysisResult:
        """分析実行"""
        issues: List[Issue] = []
        recommendations: List[str] = []

        try:
            # 1. 設定とパス解決
            config = self._load_config()
            loops_path, essences_path, digests_path = self._resolve_paths(config)

            # 2. 未処理Loop検出
            unprocessed_loops = self._check_unprocessed_loops(loops_path)
            if unprocessed_loops:
                issues.append(
                    Issue(
                        type="unprocessed_loops",
                        count=len(unprocessed_loops),
                        files=unprocessed_loops,
                    )
                )
                recommendations.append("Run /digest to process unprocessed loops first")

            # 3. ShadowGrandDigest確認
            shadow_file = essences_path / SHADOW_GRAND_DIGEST_FILENAME
            shadow_data = self._load_json_file(shadow_file)
            if shadow_data is None:
                return AnalysisResult(
                    status="error",
                    error="ShadowGrandDigest.txt not found or corrupted",
                    recommendations=["Run @digest-setup to initialize"],
                )

            # 4. プレースホルダー検出
            placeholders = self._check_placeholders(shadow_data)
            if placeholders:
                for level, files in placeholders:
                    issues.append(
                        Issue(
                            type="placeholders",
                            level=level,
                            count=len(files),
                            files=files,
                        )
                    )
                recommendations.append("Run /digest to complete pending analysis")

            # 5. 中間ファイルスキップ検出（警告のみ）
            gaps = self._check_gaps(shadow_data)
            if gaps:
                for level, gap_info in gaps.items():
                    issues.append(
                        Issue(
                            type="gaps",
                            level=level,
                            count=len(gap_info["missing"]),
                            details=gap_info,
                        )
                    )
                recommendations.append("Consider adding missing files to prevent memory gaps")

            # 6. GrandDigest確認と生成可能な階層判定
            grand_file = essences_path / GRAND_DIGEST_FILENAME
            grand_data = self._load_json_file(grand_file) or {}

            generatable, insufficient = self._determine_generatable_levels(
                config=config,
                loops_path=loops_path,
                digests_path=digests_path,
                grand_data=grand_data,
                unprocessed_count=len(unprocessed_loops),
            )

            # 推奨アクションの追加
            if generatable:
                for level_status in generatable:
                    recommendations.append(f"Run /digest {level_status.level} to generate digest")

            # 7. 結果構築
            return self._build_analysis_result(
                issues=issues,
                recommendations=recommendations,
                generatable=generatable,
                insufficient=insufficient,
                has_unprocessed=bool(unprocessed_loops),
                has_placeholders=bool(placeholders),
            )

        except FileIOError as e:
            return AnalysisResult(
                status="error",
                error=str(e),
                recommendations=["Run @digest-setup first"],
            )
        except Exception as e:
            return AnalysisResult(
                status="error",
                error=str(e),
            )

    def _check_unprocessed_loops(self, loops_path: Path) -> List[str]:
        """未処理Loop検出"""
        if not loops_path.exists():
            return []

        # Loopファイルを取得
        loop_files = list(loops_path.glob("L*.txt"))
        if not loop_files:
            return []

        # last_processed を取得
        # file_detector.py と同様に、loop.last_processed を参照
        # (weekly.last_processed は Weekly番号であり、Loop番号ではない)
        last_digest_data = self._load_json_file(self.last_digest_file)
        last_processed = None
        if last_digest_data:
            loop_data = last_digest_data.get("loop", {})
            last_processed = loop_data.get("last_processed")

        # last_processedより後のLoopを検出
        unprocessed = []
        for f in loop_files:
            file_num = self._extract_file_number(f.stem)
            if file_num is not None:
                if last_processed is None or file_num > last_processed:
                    unprocessed.append(f.stem)

        return sorted(unprocessed)

    def _check_placeholders(self, shadow_data: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """プレースホルダー検出"""
        placeholders = []
        latest_digests = shadow_data.get("latest_digests", {})

        for level in DIGEST_LEVEL_NAMES:
            level_data = latest_digests.get(level, {})
            overall_digest = level_data.get("overall_digest")

            if overall_digest is not None:
                source_files = overall_digest.get("source_files", [])
                # source_filesがあるのにabstractがプレースホルダーの場合
                abstract = overall_digest.get("abstract", "")
                if source_files and isinstance(abstract, str) and "<!-- PLACEHOLDER" in abstract:
                    placeholders.append((level, source_files))

        return placeholders

    def _check_gaps(self, shadow_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """中間ファイルスキップ検出"""
        gaps = {}
        latest_digests = shadow_data.get("latest_digests", {})

        for level in DIGEST_LEVEL_NAMES:
            level_data = latest_digests.get(level, {})
            overall_digest = level_data.get("overall_digest")

            if overall_digest is not None:
                source_files = overall_digest.get("source_files", [])
                if len(source_files) > 1:
                    numbers = []
                    for f in source_files:
                        num = self._extract_file_number(f)
                        if num is not None:
                            numbers.append(num)

                    if numbers:
                        missing = self._find_gaps(numbers)
                        if missing:
                            gaps[level] = {
                                "range": f"{source_files[0]}～{source_files[-1]}",
                                "missing": missing,
                            }

        return gaps

    def _determine_generatable_levels(
        self,
        config: Dict[str, Any],
        loops_path: Path,
        digests_path: Path,
        grand_data: Dict[str, Any],
        unprocessed_count: int,
    ) -> Tuple[List[LevelStatus], List[LevelStatus]]:
        """生成可能な階層判定"""
        levels_config = config.get("levels", {})
        major_digests = grand_data.get("major_digests", {})

        generatable = []
        insufficient = []

        # 各階層のファイル数をカウント
        level_counts: Dict[str, int] = {}

        for level in DIGEST_LEVEL_NAMES:
            level_cfg = LEVEL_CONFIG[level]
            source = level_cfg["source"]
            # 設定ファイルのthreshold_keyまたはLEVEL_CONFIGのデフォルト値を使用
            threshold_key = f"{level}_threshold"
            threshold = levels_config.get(threshold_key, level_cfg["threshold"])

            if source == "loops":
                # Loopファイル数（未処理含む）
                if loops_path.exists():
                    current = len(list(loops_path.glob("L*.txt")))
                else:
                    current = 0
            else:
                # 下位階層のRegular Digest数
                source_level_data = major_digests.get(source, {})
                overall = source_level_data.get("overall_digest")
                if overall:
                    # GrandDigestにある = 確定済み
                    # 実際のファイル数をカウント
                    source_dir = self._get_level_dir(digests_path, source)
                    if source_dir.exists():
                        # Provisional以外のファイルをカウント
                        current = len(
                            [
                                f
                                for f in source_dir.glob("*.txt")
                                if "Provisional" not in str(f.parent)
                            ]
                        )
                    else:
                        current = 0
                else:
                    current = 0

            level_counts[level] = current

            status = LevelStatus(
                level=level,
                current=current,
                threshold=threshold,
                ready=current >= threshold,
                source_type=source,
            )

            if status.ready:
                generatable.append(status)
            else:
                insufficient.append(status)

        return generatable, insufficient

    def _get_level_dir(self, digests_path: Path, level: str) -> Path:
        """階層のディレクトリパスを取得"""
        return digests_path / LEVEL_CONFIG[level]["dir"]

    def _build_analysis_result(
        self,
        issues: List[Issue],
        recommendations: List[str],
        generatable: List[LevelStatus],
        insufficient: List[LevelStatus],
        has_unprocessed: bool,
        has_placeholders: bool,
    ) -> AnalysisResult:
        """分析結果を構築

        Args:
            issues: 検出された問題リスト
            recommendations: 推奨アクションリスト
            generatable: 生成可能な階層リスト
            insufficient: 不足している階層リスト
            has_unprocessed: 未処理Loopがあるか
            has_placeholders: プレースホルダーがあるか

        Returns:
            構築された AnalysisResult
        """
        # ステータス判定
        if has_unprocessed or has_placeholders:
            status = "warning"
        else:
            status = "ok"

        return AnalysisResult(
            status=status,
            issues=issues,
            generatable_levels=generatable,
            insufficient_levels=insufficient,
            recommendations=recommendations,
        )


def format_text_report(result: AnalysisResult) -> str:
    """テキスト形式でレポートをフォーマット（テスト可能）

    Args:
        result: 分析結果

    Returns:
        フォーマットされたテキストレポート
    """
    output = []
    output.append("```text")
    output.append("━" * 40)
    output.append("📊 EpisodicRAG システム状態")
    output.append("━" * 40)
    output.append("")

    # エラーの場合
    if result.status == "error":
        output.append(f"❌ エラー: {result.error}")
        if result.recommendations:
            output.append("")
            for rec in result.recommendations:
                output.append(f"  → {rec}")
        output.append("")
        output.append("━" * 40)
        output.append("```")
        return "\n".join(output)

    # 問題の表示
    if result.issues:
        for issue in result.issues:
            if issue.type == "unprocessed_loops":
                output.append(f"⚠️ 未処理Loop検出: {issue.count}個")
                for f in issue.files[:MAX_DISPLAY_FILES]:
                    output.append(f"  - {f}")
                if len(issue.files) > MAX_DISPLAY_FILES:
                    output.append(f"  ... 他{len(issue.files) - MAX_DISPLAY_FILES}個")
                output.append("")

            elif issue.type == "placeholders":
                output.append(f"⚠️ プレースホルダー検出 ({issue.level}): {issue.count}個")
                output.append("")

            elif issue.type == "gaps":
                output.append(f"⚠️ 中間ファイルスキップ ({issue.level})")
                if issue.details:
                    output.append(f"  範囲: {issue.details.get('range', '')}")
                    missing = issue.details.get("missing", [])
                    output.append(f"  欠番: {len(missing)}個")
                output.append("")

    # 生成可能な階層
    if result.generatable_levels:
        output.append("✅ 生成可能なダイジェスト")
        for level in result.generatable_levels:
            output.append(f"  ✅ {level.level} ({level.current}/{level.threshold})")
        output.append("")

    # 不足している階層
    if result.insufficient_levels:
        output.append("⏳ 生成に必要なファイル数")
        for level in result.insufficient_levels:
            need = level.threshold - level.current
            output.append(
                f"  ❌ {level.level} ({level.current}/{level.threshold}) - あと{need}個必要"
            )
        output.append("")

    # 推奨アクション
    if result.recommendations:
        output.append("━" * 40)
        output.append("📈 推奨アクション")
        output.append("━" * 40)
        for i, rec in enumerate(result.recommendations, 1):
            output.append(f"  {i}. {rec}")
        output.append("")

    output.append("━" * 40)
    output.append("```")
    return "\n".join(output)


def print_text_report(result: AnalysisResult) -> None:
    """テキスト形式でレポートを出力（VSCode対応）"""
    print(format_text_report(result))


def main() -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="EpisodicRAG Health Diagnostic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    try:
        analyzer = DigestAutoAnalyzer()
        result = analyzer.analyze()

        if args.output == "json":
            output_json(asdict(result))
        else:
            print_text_report(result)

    except Exception as e:
        output_error(str(e))


if __name__ == "__main__":
    import io

    # Windows UTF-8入出力対応
    if sys.platform == "win32":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    main()
