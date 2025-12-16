#!/usr/bin/env python3
"""
Singleton Documentation Tests
=============================

シングルトンモジュールのドキュメントが適切に記載されているかを確認するテスト。

TDD Red Phase: このテストは最初は失敗する。
Green Phase: ドキュメントを追加してテストを通す。
"""

import pytest


@pytest.mark.unit
class TestSingletonDocumentation:
    """シングルトンモジュールのドキュメント品質テスト"""

    def test_level_registry_has_singleton_warning(self) -> None:
        """level_registryモジュールにシングルトン警告がある"""
        import domain.level_registry as module

        assert module.__doc__ is not None, "モジュールdocstringがない"
        doc_lower = module.__doc__.lower()

        assert "singleton" in doc_lower, "singletonパターンの説明がない"
        assert "reset_level_registry" in module.__doc__, "reset関数の説明がない"

    def test_error_formatter_has_singleton_warning(self) -> None:
        """error_formatterモジュールにシングルトン警告がある"""
        from domain import error_formatter

        assert error_formatter.__doc__ is not None, "モジュールdocstringがない"
        doc_lower = error_formatter.__doc__.lower()

        assert "singleton" in doc_lower, "singletonパターンの説明がない"
        assert "reset_error_formatter" in error_formatter.__doc__, "reset関数の説明がない"

    def test_file_naming_has_singleton_warning(self) -> None:
        """file_namingモジュールにシングルトン警告がある"""
        import domain.file_naming as module

        assert module.__doc__ is not None, "モジュールdocstringがない"
        doc_lower = module.__doc__.lower()

        assert "singleton" in doc_lower, "singletonパターンの説明がない"
        assert "reset_registry" in module.__doc__, "reset関数の説明がない"

    def test_logging_config_has_singleton_warning(self) -> None:
        """logging_configモジュールにシングルトン警告がある"""
        import infrastructure.logging_config as module

        assert module.__doc__ is not None, "モジュールdocstringがない"
        doc_lower = module.__doc__.lower()

        # logging_configはPython標準のloggingを使うため、
        # シングルトンリセットは logging.getLogger() 経由
        assert "singleton" in doc_lower or "global" in doc_lower, (
            "singletonまたはglobal stateの説明がない"
        )

    def test_all_singletons_have_test_instructions(self) -> None:
        """全シングルトンモジュールにテスト時の注意が記載されている"""
        modules_to_check = [
            ("domain.level_registry", "reset_level_registry"),
            ("domain.error_formatter", "reset_error_formatter"),
            ("domain.file_naming", "reset_registry"),
        ]

        for module_name, reset_func_name in modules_to_check:
            module = __import__(module_name, fromlist=[""])
            assert module.__doc__ is not None, f"{module_name}にdocstringがない"

            # テスト時の注意が含まれているか
            doc = module.__doc__
            has_test_mention = any(
                keyword in doc.lower() for keyword in ["test", "テスト", "conftest", "fixture"]
            )
            assert has_test_mention, f"{module_name}にテスト時の注意がない"
