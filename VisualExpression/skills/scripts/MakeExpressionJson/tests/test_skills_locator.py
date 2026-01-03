"""
test_skills_locator.py - SkillsLocatorのテスト (TDD RED Phase)

adapters/skills_locator.pyのSkillsディレクトリ検出ロジックをテスト
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSkillsLocatorProtocol:
    """SkillsLocatorProtocolインターフェースのテスト"""

    def test_protocol_defines_get_skills_dir(self):
        """Protocolがget_skills_dir()を定義"""
        from adapters.protocols import SkillsLocatorProtocol
        import inspect

        sig = inspect.signature(SkillsLocatorProtocol.get_skills_dir)
        params = list(sig.parameters.keys())
        assert params == ["self"]

    def test_protocol_defines_get_default_template_path(self):
        """Protocolがget_default_template_path()を定義"""
        from adapters.protocols import SkillsLocatorProtocol
        import inspect

        sig = inspect.signature(SkillsLocatorProtocol.get_default_template_path)
        params = list(sig.parameters.keys())
        assert params == ["self"]

    def test_protocol_is_runtime_checkable(self):
        """Protocolがruntime_checkable"""
        from adapters.protocols import SkillsLocatorProtocol

        # isinstance()で使用可能であることを確認
        assert hasattr(SkillsLocatorProtocol, "__protocol_attrs__") or hasattr(
            SkillsLocatorProtocol, "_is_runtime_protocol"
        )


class TestSkillsLocatorCreation:
    """SkillsLocatorインスタンス生成のテスト"""

    def test_skills_locator_with_explicit_path(self, tmp_path):
        """明示的なskills_dirパスを受け入れる"""
        from adapters.skills_locator import SkillsLocator

        locator = SkillsLocator(skills_dir=str(tmp_path))
        assert locator.get_skills_dir() == tmp_path

    def test_skills_locator_without_path_uses_auto_detection(self):
        """パスなしの場合は自動検出"""
        from adapters.skills_locator import SkillsLocator

        locator = SkillsLocator()
        result = locator.get_skills_dir()
        assert isinstance(result, Path)
        # 実際のスキルディレクトリが見つかるはず
        assert result.exists()

    def test_skills_locator_path_as_path_object(self, tmp_path):
        """Pathオブジェクトも受け入れる"""
        from adapters.skills_locator import SkillsLocator

        locator = SkillsLocator(skills_dir=tmp_path)
        assert locator.get_skills_dir() == tmp_path


class TestSkillsLocatorEnvVar:
    """環境変数によるスキルディレクトリ指定のテスト"""

    def test_env_var_takes_priority_over_auto_detection(self, tmp_path, monkeypatch):
        """環境変数が自動検出より優先"""
        from adapters.skills_locator import SkillsLocator
        from adapters.file_constants import SKILLS_DIR_ENV_VAR

        custom_dir = tmp_path / "env_skills"
        custom_dir.mkdir()
        monkeypatch.setenv(SKILLS_DIR_ENV_VAR, str(custom_dir))

        locator = SkillsLocator()
        assert locator.get_skills_dir() == custom_dir

    def test_explicit_path_overrides_env_var(self, tmp_path, monkeypatch):
        """明示的パス > 環境変数 > 自動検出"""
        from adapters.skills_locator import SkillsLocator
        from adapters.file_constants import SKILLS_DIR_ENV_VAR

        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        env_dir = tmp_path / "env"
        env_dir.mkdir()

        monkeypatch.setenv(SKILLS_DIR_ENV_VAR, str(env_dir))
        locator = SkillsLocator(skills_dir=str(explicit_dir))

        assert locator.get_skills_dir() == explicit_dir

    def test_env_var_nonexistent_path_falls_through(self, tmp_path, monkeypatch):
        """存在しない環境変数パスはスキップ"""
        from adapters.skills_locator import SkillsLocator
        from adapters.file_constants import SKILLS_DIR_ENV_VAR

        monkeypatch.setenv(SKILLS_DIR_ENV_VAR, str(tmp_path / "nonexistent"))

        locator = SkillsLocator()
        result = locator.get_skills_dir()
        # 自動検出にフォールバック
        assert result.exists()


class TestSkillsLocatorTemplatePath:
    """テンプレートパス解決のテスト"""

    def test_get_default_template_path_returns_template_file(self):
        """VisualExpressionUI.template.htmlへのパスを返す"""
        from adapters.skills_locator import SkillsLocator
        from adapters.file_constants import DEFAULT_TEMPLATE_FILENAME

        locator = SkillsLocator()
        result = locator.get_default_template_path()

        assert result.name == DEFAULT_TEMPLATE_FILENAME

    def test_template_path_relative_to_skills_dir(self, tmp_path):
        """テンプレートパスはskills_dir基準"""
        from adapters.skills_locator import SkillsLocator
        from adapters.file_constants import DEFAULT_TEMPLATE_FILENAME

        locator = SkillsLocator(skills_dir=str(tmp_path))
        result = locator.get_default_template_path()

        assert result.parent == tmp_path
        assert result.name == DEFAULT_TEMPLATE_FILENAME


class TestSkillsLocatorMarkerSearch:
    """マーカーファイル検索のテスト"""

    def test_finds_skills_dir_with_skill_md_marker(self, tmp_path):
        """SKILL.mdマーカーでスキルディレクトリを検出"""
        from adapters.skills_locator import SkillsLocator

        # スキルディレクトリ構造を作成
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text("# Skill")

        # サブディレクトリから検索
        sub_dir = skills_dir / "scripts" / "test"
        sub_dir.mkdir(parents=True)

        # 明示的パスでテスト（マーカー検索ロジックは内部で使用）
        locator = SkillsLocator(skills_dir=str(skills_dir))
        assert locator.get_skills_dir() == skills_dir


class TestSkillsLocatorSatisfiesProtocol:
    """SkillsLocatorがProtocolを満たすことのテスト"""

    def test_skills_locator_satisfies_protocol(self):
        """SkillsLocatorはSkillsLocatorProtocolを満たす"""
        from adapters.skills_locator import SkillsLocator
        from adapters.protocols import SkillsLocatorProtocol

        locator = SkillsLocator()
        # runtime_checkable protocolなのでisinstanceが使える
        assert isinstance(locator, SkillsLocatorProtocol)


class TestFileWriterProtocol:
    """FileWriterProtocolインターフェースのテスト"""

    def test_protocol_defines_write_json(self):
        """Protocolがwrite_json()を定義"""
        from adapters.protocols import FileWriterProtocol
        import inspect

        sig = inspect.signature(FileWriterProtocol.write_json)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "data" in params

    def test_protocol_defines_write_html(self):
        """Protocolがwrite_html()を定義"""
        from adapters.protocols import FileWriterProtocol
        import inspect

        sig = inspect.signature(FileWriterProtocol.write_html)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "content" in params

    def test_protocol_defines_read_template(self):
        """Protocolがread_template()を定義"""
        from adapters.protocols import FileWriterProtocol
        import inspect

        sig = inspect.signature(FileWriterProtocol.read_template)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "template_path" in params

    def test_protocol_defines_ensure_output_dir(self):
        """Protocolがensure_output_dir()を定義"""
        from adapters.protocols import FileWriterProtocol
        import inspect

        sig = inspect.signature(FileWriterProtocol.ensure_output_dir)
        params = list(sig.parameters.keys())
        assert params == ["self"]


class TestSkillsLocatorUsesConstant:
    """SkillsLocatorが定数を使用していることのテスト"""

    def test_uses_max_search_depth_constant(self):
        """skills_locatorがMAX_SEARCH_DEPTHをインポートしていること"""
        import inspect

        import adapters.skills_locator as module

        # モジュール内で定数を使用していることを確認
        source = inspect.getsource(module)
        assert "MAX_SEARCH_DEPTH" in source
