#!/usr/bin/env python3
"""
find_plugin_root テスト
=======================

EpisodicRAGプラグインルート検出のTDDテスト。
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# =============================================================================
# Stage 1: is_valid_plugin_root() 単体テスト
# =============================================================================


@pytest.mark.unit
def test_is_valid_plugin_root_with_marker_file(tmp_path):
    """GrandDigest.template.txtがあるディレクトリはvalid"""
    from interfaces.find_plugin_root import is_valid_plugin_root

    # EpisodicRAGを含むパスでテスト環境を構築
    episodic_dir = tmp_path / "EpisodicRAG"
    episodic_dir.mkdir()
    (episodic_dir / ".claude-plugin").mkdir()
    (episodic_dir / ".claude-plugin" / "GrandDigest.template.txt").touch()

    result = is_valid_plugin_root(episodic_dir)
    assert result is True


@pytest.mark.unit
def test_is_valid_plugin_root_without_marker_file(tmp_path):
    """マーカーファイルなしはinvalid"""
    from interfaces.find_plugin_root import is_valid_plugin_root

    episodic_dir = tmp_path / "EpisodicRAG"
    episodic_dir.mkdir()

    result = is_valid_plugin_root(episodic_dir)
    assert result is False


@pytest.mark.unit
def test_is_valid_plugin_root_nonexistent_directory():
    """存在しないディレクトリはinvalid"""
    from interfaces.find_plugin_root import is_valid_plugin_root

    result = is_valid_plugin_root(Path("/nonexistent/EpisodicRAG"))
    assert result is False


@pytest.mark.unit
def test_is_valid_plugin_root_requires_episodicrag_in_path(tmp_path):
    """パスに'EpisodicRAG'を含まないディレクトリはinvalid"""
    from interfaces.find_plugin_root import is_valid_plugin_root

    other_dir = tmp_path / "SomeOtherPlugin"
    other_dir.mkdir()
    (other_dir / ".claude-plugin").mkdir()
    (other_dir / ".claude-plugin" / "GrandDigest.template.txt").touch()

    result = is_valid_plugin_root(other_dir)
    assert result is False


# =============================================================================
# Stage 2: find_in_search_paths() 単体テスト
# =============================================================================


def _create_valid_plugin(path: Path) -> Path:
    """テスト用の有効なプラグインディレクトリを作成"""
    episodic_dir = path / "EpisodicRAG"
    episodic_dir.mkdir(parents=True, exist_ok=True)
    (episodic_dir / ".claude-plugin").mkdir(exist_ok=True)
    (episodic_dir / ".claude-plugin" / "GrandDigest.template.txt").touch()
    return episodic_dir


@pytest.mark.unit
def test_find_in_search_paths_found(tmp_path):
    """検索パス内でプラグインを発見"""
    from interfaces.find_plugin_root import find_in_search_paths

    install_dir = tmp_path / ".claude" / "plugins" / "marketplaces" / "plugins-weave"
    expected = _create_valid_plugin(install_dir)

    result = find_in_search_paths([install_dir])
    assert result == expected


@pytest.mark.unit
def test_find_in_search_paths_not_found(tmp_path):
    """見つからない場合はNone"""
    from interfaces.find_plugin_root import find_in_search_paths

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = find_in_search_paths([empty_dir])
    assert result is None


@pytest.mark.unit
def test_find_in_search_paths_priority_order(tmp_path):
    """最初の検索パスが優先される"""
    from interfaces.find_plugin_root import find_in_search_paths

    primary_dir = tmp_path / "primary"
    secondary_dir = tmp_path / "secondary"

    primary_plugin = _create_valid_plugin(primary_dir)
    _create_valid_plugin(secondary_dir)

    result = find_in_search_paths([primary_dir, secondary_dir])
    assert result == primary_plugin


@pytest.mark.unit
def test_find_in_search_paths_recursive(tmp_path):
    """ネストしたディレクトリを再帰検索"""
    from interfaces.find_plugin_root import find_in_search_paths

    nested = tmp_path / "deep" / "nested"
    expected = _create_valid_plugin(nested)

    result = find_in_search_paths([tmp_path], recursive=True)
    assert result == expected


# =============================================================================
# Stage 3: FindResult + find_plugin_root() 単体テスト
# =============================================================================


@pytest.mark.unit
def test_find_result_success_structure():
    """FindResult成功時の構造"""
    from interfaces.find_plugin_root import FindResult

    result = FindResult(status="ok", plugin_root="/path/to/EpisodicRAG")

    assert result.status == "ok"
    assert result.plugin_root == "/path/to/EpisodicRAG"
    assert result.error is None


@pytest.mark.unit
def test_find_result_error_structure():
    """FindResultエラー時の構造"""
    from interfaces.find_plugin_root import FindResult

    result = FindResult(status="error", error="EpisodicRAG plugin not found")

    assert result.status == "error"
    assert result.plugin_root is None
    assert result.error == "EpisodicRAG plugin not found"


@pytest.mark.unit
def test_find_plugin_root_custom_paths(tmp_path):
    """カスタム検索パスでプラグインを発見"""
    from interfaces.find_plugin_root import find_plugin_root

    custom_path = tmp_path / "custom"
    expected = _create_valid_plugin(custom_path)

    result = find_plugin_root(search_paths=[custom_path])

    assert result.status == "ok"
    assert result.plugin_root == str(expected)


@pytest.mark.unit
def test_find_plugin_root_not_found(tmp_path):
    """プラグインが見つからない場合はエラー"""
    from interfaces.find_plugin_root import find_plugin_root

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = find_plugin_root(search_paths=[empty_dir])

    assert result.status == "error"
    assert "not found" in result.error.lower()


# =============================================================================
# Stage 4: CLI統合テスト
# =============================================================================


@pytest.mark.integration
def test_cli_json_output(tmp_path):
    """CLI JSON出力形式"""
    plugin_path = _create_valid_plugin(tmp_path)

    with patch("sys.argv", ["find_plugin_root.py", "--search-paths", str(tmp_path)]):
        with patch("builtins.print") as mock_print:
            from interfaces.find_plugin_root import main

            main()

            output = mock_print.call_args[0][0]
            parsed = json.loads(output)

            assert parsed["status"] == "ok"
            assert "plugin_root" in parsed
            assert str(plugin_path) in parsed["plugin_root"]


@pytest.mark.integration
def test_cli_text_output(tmp_path):
    """CLI テキスト出力形式"""
    plugin_path = _create_valid_plugin(tmp_path)

    with patch(
        "sys.argv", ["find_plugin_root.py", "--output", "text", "--search-paths", str(tmp_path)]
    ):
        with patch("builtins.print") as mock_print:
            from interfaces.find_plugin_root import main

            main()

            output = mock_print.call_args[0][0]
            assert str(plugin_path) in output


@pytest.mark.integration
def test_cli_error_output_json(tmp_path):
    """CLI エラー時のJSON出力"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with patch("sys.argv", ["find_plugin_root.py", "--search-paths", str(empty_dir)]):
        with patch("builtins.print") as mock_print:
            from interfaces.find_plugin_root import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            output = mock_print.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["status"] == "error"


# =============================================================================
# Stage 5: Property-based テスト (Hypothesis)
# =============================================================================


@pytest.mark.property
@given(path_str=st.text(min_size=0, max_size=100))
@settings(max_examples=50)
def test_is_valid_plugin_root_never_crashes(path_str):
    """is_valid_plugin_root は任意の入力でクラッシュしない"""
    from interfaces.find_plugin_root import is_valid_plugin_root

    result = is_valid_plugin_root(Path(path_str))
    assert isinstance(result, bool)


@pytest.mark.property
@given(paths=st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=3))
@settings(max_examples=30, deadline=None)
def test_find_result_status_invariant(paths):
    """FindResult.status は常に 'ok' または 'error'"""
    from interfaces.find_plugin_root import find_plugin_root

    search_paths = [Path(p) for p in paths]
    result = find_plugin_root(search_paths=search_paths)

    assert result.status in ("ok", "error")
    if result.status == "ok":
        assert result.plugin_root is not None
    else:
        assert result.error is not None
