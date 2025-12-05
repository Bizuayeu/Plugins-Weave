#!/usr/bin/env python3
"""
test_validate_json.py
=====================

tools/validate_json.py の単体テスト。
JSON検証機能をTDDで開発。
"""

from pathlib import Path

import pytest

from tools.validate_json import JSONStatus, JSONValidator, ValidationResult

# =============================================================================
# Cycle 1: 基本構造テスト
# =============================================================================


class TestJSONValidator:
    """JSONValidator 基本テスト"""

    def test_valid_json_file_returns_valid_status(self, tmp_path: Path) -> None:
        """有効なJSONファイルはVALIDステータスを返す"""
        json_file = tmp_path / "valid.json"
        json_file.write_text('{"key": "value"}', encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.status == JSONStatus.VALID

    def test_invalid_json_syntax_returns_invalid_status(self, tmp_path: Path) -> None:
        """不正なJSON構文はINVALIDステータスを返す"""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"key": }', encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.status == JSONStatus.INVALID
        assert "syntax" in result.message.lower()

    def test_file_not_found_returns_not_found_status(self, tmp_path: Path) -> None:
        """存在しないファイルはNOT_FOUNDステータスを返す"""
        validator = JSONValidator()
        result = validator.validate_file(tmp_path / "nonexistent.json")

        assert result.status == JSONStatus.NOT_FOUND

    def test_empty_json_object_is_valid(self, tmp_path: Path) -> None:
        """空のJSONオブジェクトは有効"""
        json_file = tmp_path / "empty.json"
        json_file.write_text("{}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.status == JSONStatus.VALID

    def test_json_array_is_valid(self, tmp_path: Path) -> None:
        """JSON配列も有効"""
        json_file = tmp_path / "array.json"
        json_file.write_text("[1, 2, 3]", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.status == JSONStatus.VALID


class TestValidationResult:
    """ValidationResult データクラスのテスト"""

    def test_result_contains_file_path(self, tmp_path: Path) -> None:
        """結果にファイルパスが含まれる"""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.file_path == json_file

    def test_result_message_empty_on_success(self, tmp_path: Path) -> None:
        """成功時はメッセージが空"""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.message == ""

    def test_result_message_not_empty_on_error(self, tmp_path: Path) -> None:
        """エラー時はメッセージが設定される"""
        json_file = tmp_path / "test.json"
        json_file.write_text("{invalid}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_file(json_file)

        assert result.message != ""


# =============================================================================
# Cycle 2: config.template.json 整合性テスト
# =============================================================================


class TestConfigTemplateValidation:
    """config.template.json との整合性テスト"""

    @pytest.fixture
    def template_json(self, tmp_path: Path) -> Path:
        """テスト用テンプレートJSONを作成"""
        import json

        template = tmp_path / "config.template.json"
        template.write_text(
            json.dumps(
                {
                    "base_dir": ".",
                    "paths": {"loops_dir": "data/Loops", "digests_dir": "data/Digests"},
                    "levels": {"weekly_threshold": 5, "monthly_threshold": 5},
                }
            ),
            encoding="utf-8",
        )
        return template

    def test_config_matches_template_structure(self, tmp_path: Path, template_json: Path) -> None:
        """configがtemplateと同じ構造を持つ場合はVALID"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": "./custom",
                    "paths": {"loops_dir": "Loops", "digests_dir": "Digests"},
                    "levels": {"weekly_threshold": 7, "monthly_threshold": 4},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_against_template(config, template_json)

        assert result.status == JSONStatus.VALID

    def test_config_missing_required_key_returns_invalid(
        self, tmp_path: Path, template_json: Path
    ) -> None:
        """必須キーが欠けているとINVALID"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    # base_dir が欠けている
                    "paths": {"loops_dir": "Loops"},
                    "levels": {"weekly_threshold": 5},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_against_template(config, template_json)

        assert result.status == JSONStatus.INVALID
        assert "base_dir" in result.message

    def test_config_with_extra_keys_is_valid(self, tmp_path: Path, template_json: Path) -> None:
        """templateにないキーがあってもVALID（拡張可能）"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": ".",
                    "paths": {"loops_dir": "Loops", "digests_dir": "Digests"},
                    "levels": {"weekly_threshold": 5, "monthly_threshold": 5},
                    "extra_key": "extra_value",  # 追加キー
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_against_template(config, template_json)

        assert result.status == JSONStatus.VALID

    def test_template_not_found_returns_not_found(self, tmp_path: Path) -> None:
        """テンプレートが見つからない場合はNOT_FOUND"""
        import json

        config = tmp_path / "config.json"
        config.write_text(json.dumps({"base_dir": "."}), encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_against_template(config, tmp_path / "nonexistent.json")

        assert result.status == JSONStatus.NOT_FOUND

    def test_config_not_found_returns_not_found(self, tmp_path: Path, template_json: Path) -> None:
        """configが見つからない場合はNOT_FOUND"""
        validator = JSONValidator()
        result = validator.validate_against_template(tmp_path / "nonexistent.json", template_json)

        assert result.status == JSONStatus.NOT_FOUND

    def test_invalid_config_json_syntax_in_template_check(
        self, tmp_path: Path, template_json: Path
    ) -> None:
        """configが不正なJSON構文の場合はINVALID（L118-119カバー）"""
        config = tmp_path / "config.json"
        config.write_text("{invalid json}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_against_template(config, template_json)

        assert result.status == JSONStatus.INVALID
        assert "syntax" in result.message.lower()

    def test_config_missing_nested_key_returns_invalid(
        self, tmp_path: Path, template_json: Path
    ) -> None:
        """ネストされたキーが欠けている場合はINVALID（L149カバー：paths.loops_dir形式）"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": ".",
                    "paths": {},  # loops_dir, digests_dir が欠けている
                    "levels": {"weekly_threshold": 5, "monthly_threshold": 5},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_against_template(config, template_json)

        assert result.status == JSONStatus.INVALID
        assert "paths.loops_dir" in result.message


# =============================================================================
# Cycle 3: パス形式検証テスト
# =============================================================================


class TestPathValidation:
    """パス形式の検証テスト"""

    def test_valid_relative_path(self, tmp_path: Path) -> None:
        """相対パスは有効"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": ".",
                    "paths": {"loops_dir": "./data/Loops"},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.VALID

    def test_absolute_path_without_trusted_returns_warning(self, tmp_path: Path) -> None:
        """trusted_external_pathsなしの絶対パスは警告"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": "C:/Users/test/data",
                    "paths": {},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.WARNING
        assert "absolute" in result.message.lower() or "trusted" in result.message.lower()

    def test_absolute_path_with_trusted_is_valid(self, tmp_path: Path) -> None:
        """trusted_external_pathsがあれば絶対パスも有効"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": "C:/Users/test/data",
                    "trusted_external_paths": ["C:/Users/test"],
                    "paths": {},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.VALID

    def test_unix_absolute_path_without_trusted_returns_warning(self, tmp_path: Path) -> None:
        """Unix形式の絶対パスも警告対象"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": "/home/user/data",
                    "paths": {},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.WARNING

    def test_tilde_path_without_trusted_returns_warning(self, tmp_path: Path) -> None:
        """チルダ展開パスも警告対象"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": "~/Documents/data",
                    "paths": {},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.WARNING

    def test_file_not_found_returns_not_found(self, tmp_path: Path) -> None:
        """ファイルが見つからない場合はNOT_FOUND"""
        validator = JSONValidator()
        result = validator.validate_paths(tmp_path / "nonexistent.json")

        assert result.status == JSONStatus.NOT_FOUND

    def test_invalid_json_syntax_returns_invalid(self, tmp_path: Path) -> None:
        """不正なJSON構文の場合はINVALID（L185-186カバー）"""
        config = tmp_path / "config.json"
        config.write_text("{invalid}", encoding="utf-8")

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.INVALID
        assert "syntax" in result.message.lower()

    def test_absolute_path_in_paths_returns_warning(self, tmp_path: Path) -> None:
        """paths内の絶対パスは警告（L208-212カバー）"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps(
                {
                    "base_dir": ".",
                    "paths": {"loops_dir": "C:/absolute/path"},
                }
            ),
            encoding="utf-8",
        )

        validator = JSONValidator()
        result = validator.validate_paths(config)

        assert result.status == JSONStatus.WARNING
        assert "paths.loops_dir" in result.message


# =============================================================================
# Cycle 4: CLI統合テスト
# =============================================================================


class TestCLIIntegration:
    """CLI実行テスト"""

    def test_main_returns_zero_on_valid_json(self, tmp_path: Path) -> None:
        """有効なJSONで終了コード0"""
        import json

        config = tmp_path / "config.json"
        config.write_text(json.dumps({"base_dir": "."}), encoding="utf-8")

        from tools.validate_json import main

        exit_code = main([str(config)])

        assert exit_code == 0

    def test_main_returns_nonzero_on_invalid_json(self, tmp_path: Path) -> None:
        """無効なJSONで終了コード非0"""
        config = tmp_path / "config.json"
        config.write_text("{invalid}", encoding="utf-8")

        from tools.validate_json import main

        exit_code = main([str(config)])

        assert exit_code != 0

    def test_main_returns_nonzero_on_file_not_found(self, tmp_path: Path) -> None:
        """ファイルが見つからない場合は終了コード非0"""
        from tools.validate_json import main

        exit_code = main([str(tmp_path / "nonexistent.json")])

        assert exit_code != 0

    def test_main_with_template_check(self, tmp_path: Path) -> None:
        """--templateオプションでテンプレートとの整合性チェック"""
        import json

        template = tmp_path / "template.json"
        template.write_text(json.dumps({"base_dir": ".", "paths": {}}), encoding="utf-8")

        config = tmp_path / "config.json"
        config.write_text(json.dumps({"base_dir": "./custom", "paths": {}}), encoding="utf-8")

        from tools.validate_json import main

        exit_code = main([str(config), "--template", str(template)])

        assert exit_code == 0

    def test_main_with_check_paths(self, tmp_path: Path) -> None:
        """--check-pathsオプションでパス検証"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps({"base_dir": ".", "paths": {"loops_dir": "./Loops"}}),
            encoding="utf-8",
        )

        from tools.validate_json import main

        exit_code = main([str(config), "--check-paths"])

        assert exit_code == 0

    def test_main_with_check_paths_warning(self, tmp_path: Path) -> None:
        """--check-pathsで警告がある場合は終了コード非0"""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps({"base_dir": "C:/absolute/path", "paths": {}}),
            encoding="utf-8",
        )

        from tools.validate_json import main

        exit_code = main([str(config), "--check-paths"])

        assert exit_code != 0

    def test_main_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """引数なしでヘルプ表示"""
        from tools.validate_json import main

        exit_code = main([])

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "usage" in captured.err.lower()

    def test_main_template_mismatch_returns_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--templateで構造不一致の場合は終了コード非0（L303-305カバー）"""
        import json

        from tools.validate_json import main

        template = tmp_path / "template.json"
        template.write_text(
            json.dumps({"base_dir": ".", "required_key": "value"}), encoding="utf-8"
        )

        config = tmp_path / "config.json"
        config.write_text(json.dumps({"base_dir": "."}), encoding="utf-8")

        exit_code = main([str(config), "--template", str(template)])

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "ERROR" in captured.err

    def test_main_verbose_output_on_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """quietなしで成功時にOKメッセージを出力（L306-307, L318-319カバー）"""
        import json

        from tools.validate_json import main

        template = tmp_path / "template.json"
        template.write_text(json.dumps({"base_dir": "."}), encoding="utf-8")

        config = tmp_path / "config.json"
        config.write_text(json.dumps({"base_dir": "."}), encoding="utf-8")

        exit_code = main([str(config), "--template", str(template), "--check-paths"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "OK" in captured.out
        assert "Template structure valid" in captured.out
        assert "Path validation passed" in captured.out
