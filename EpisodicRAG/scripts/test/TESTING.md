# EpisodicRAG Testing Guide

テストスイートのガイドドキュメント。

## Table of Contents

**Overview**
- [Quick Start](#quick-start)
- [Test Organization](#test-organization)
- [Test Summary](#test-summary)

**Test Infrastructure**
- [Fixture Dependency Map](#fixture-dependency-map)

**Writing Tests**
- [Adding New Tests](#adding-new-tests)
- [Test Naming Convention](#test-naming-convention)
- [Property-Based Tests](#property-based-tests)
- [CLI Integration Tests](#cli-integration-tests-v400)
- [Tools Tests](#tools-tests-v410)
- [Encoding Tests](#encoding-tests-v420)
- [Bandit Security Scan Integration](#bandit-security-scan-integration-v500)
- [Persistent Configuration Directory](#persistent-configuration-directory-v520)

**Running Tests**
- [Debugging Tips](#debugging-tips)
- [Hypothesis Profiles](#hypothesis-profiles)
- [Performance Targets](#performance-targets)

**CI/CD**
- [Continuous Integration](#continuous-integration)
- [Known Gaps](#known-gaps)

---

## Quick Start

```bash
# 全テスト実行
pytest scripts/test/ -v

# 単体テストのみ
pytest scripts/test/ -m unit

# 統合テストのみ
pytest scripts/test/ -m integration

# slowマーカー以外（CI用：1秒超のテストを除外）
pytest scripts/test/ -m "not slow"

# fastマーカーのみ（純粋ロジック、I/Oなし）
pytest scripts/test/ -m fast

# Property-based tests のみ
pytest scripts/test/ -m property

# CLI統合テストのみ [v4.0.0+]
pytest scripts/test/cli_integration_tests/ -m cli
```

---

## Test Organization

### Architecture Layers

テストはアプリケーションのアーキテクチャ層に対応して構成されています：

```
test/
├── conftest.py              # 共通フィクスチャ
├── test_helpers.py          # テストヘルパー
├── test_constants.py        # テスト用定数
├── domain_tests/            # 純粋なビジネスロジック (33 files)
│   └── test_*_properties.py # Property-based (5 files)
├── config_tests/            # Config層3層化対応 (15 files) [v4.0.0+]
│   └── test_config_properties.py
├── application_tests/       # ユースケース (26 files)
│   ├── grand/               # GrandDigest関連
│   ├── shadow/              # Shadow関連（cascade_orchestrator含む）
│   │   ├── test_shadow_io_properties.py
│   │   ├── test_provisional_appender.py
│   │   └── test_shadow_components.py  # CascadeComponents [v5.2.0+]
│   ├── finalize/            # Finalize処理
│   │   └── validators/      # バリデータ
│   ├── test_cascade_properties.py
│   └── test_template_properties.py
├── infrastructure_tests/    # I/O操作 (12 files)
│   ├── config/              # PathValidatorChain [v4.1.0+]
│   ├── test_file_scanner_properties.py
│   └── test_json_repository_properties.py
├── interfaces_tests/        # エントリポイント (28 files)
│   ├── provisional/         # Provisional処理
│   └── digest_auto/         # digest_auto パッケージ [v5.3.0+]
│       └── (test_auto_*.py がパッケージ内モジュールをテスト)
├── integration_tests/       # E2Eシナリオ (14 files)
├── cli_integration_tests/   # CLI E2E (4 files) [v4.0.0+]
├── performance_tests/       # ベンチマーク (1 file)
└── tools_tests/             # 開発ツール (4 files) [v4.1.0+]
```

---

## Test Summary

### 層別テストファイル一覧

| 層 | 主なテストファイル | ファイル数 |
|----|-------------------|-----------|
| **Domain** | `test_validators.py`, `test_file_naming.py`, `test_level_registry.py`, `test_formatter_registry.py`, `test_types_imports.py`, `test_level_literals.py`, `test_constants.py` | 33 |
| **Config** | `test_config.py`, `test_path_resolver.py`, `test_threshold_provider.py`, `test_config_builder.py` | 15 |
| **Infrastructure** | `test_json_repository.py`, `test_file_scanner.py`, `test_logging_config.py`, `test_path_validators.py`, `test_persistent_path.py` | 13 |
| **Application** | `test_shadow_*.py`, `test_grand_digest.py`, `test_cascade_orchestrator.py`, `test_persistence.py` | 24 |
| **Interfaces** | `test_finalize_from_shadow.py`, `test_*_cli_*.py`, `test_setup_*.py`, `test_auto_*.py` (digest_autoパッケージ対応 v5.3.0+), `test_digest_auto_detection.py`, `test_cli_helpers.py`, `test_digest_readiness.py`, `test_digest_entry.py`, `test_encoding.py` | 27 |
| **Integration** | `test_e2e_workflow.py`, `test_full_cascade.py`, `test_config_integration.py` | 14 |
| **CLI Integration** | `test_digest_*_cli.py`, `test_workflow_cli.py` | 4 |
| **Performance** | `test_benchmarks.py` | 1 |
| **Tools** | `test_check_footer.py`, `test_link_checker.py`, `test_validate_json.py`, `test_bandit_integration.py` | 4 |
| **Property** | `test_*_properties.py` (全11ファイル、各層に分散) | 11 |

> 📊 最新のテスト数: `pytest --collect-only | tail -1`
> 📁 ファイル数確認: `find scripts/test -name "test_*.py" | wc -l`

### カバレッジ目標

| カテゴリ | 目標 | 現状 |
|---------|------|------|
| Domain層 | 90%+ | [Codecov参照](https://codecov.io/gh/Bizuayeu/Plugins-Weave) |
| Application層 | 80%+ | 同上 |
| 全体 | 80%+ | ~93% (2025-12 時点) |

### Test Markers

```python
@pytest.mark.unit          # 純粋ロジック、<100ms、I/Oなし
@pytest.mark.integration   # ファイルI/O、複数コンポーネント
@pytest.mark.slow          # 1秒超（-m "not slow" で除外）
@pytest.mark.fast          # 高速テスト（純粋ロジック、I/Oなし、明示的に指定）
@pytest.mark.property      # Hypothesis property-based tests
@pytest.mark.performance   # ベンチマーク（デフォルトでスキップ）
@pytest.mark.cli           # CLI統合テスト（subprocess経由）[v4.0.0+]
```

> **Note**: `slow` は除外用（`-m "not slow"`）、`fast` は選択用（`-m fast`）として使い分けます。

---

## Fixture Dependency Map

```mermaid
graph TD
    A["conftest.py<br/>(Shared Fixtures)"]
    R["reset_all_singletons<br/>(autouse=True)"]

    A --> B["temp_plugin_env<br/>(function scope)"]
    A --> C["shared_plugin_env<br/>(module scope)"]
    A --> L["level_hierarchy"]
    A --> P["placeholder_manager"]

    B --> D["digest_config"]
    B --> E["config (alias)"]
    B --> M["mock_digest_config"]

    D --> F["times_tracker"]
    D --> G["shadow_manager"]
    D --> H["grand_digest_manager"]
    D --> I["file_detector"]

    J["template"] --> K["shadow_io"]
    B --> K

    style A fill:#e1f5ff,color:#000000
    style B fill:#fff9c4,color:#000000
    style D fill:#f3e5f5,color:#000000
    style R fill:#ffcdd2,color:#000000
```

### Core Fixtures

#### `temp_plugin_env` (function scope)

隔離された一時ファイルシステムを提供。

```python
def test_something(temp_plugin_env):
    config = DigestConfig()  # 環境変数経由で自動設定
    # テスト後に自動クリーンアップ
```

> **v5.3.0変更**: `EPISODICRAG_CONFIG_DIR` 環境変数で永続化ディレクトリをテスト用にリダイレクトします。

**Properties:**
- `.plugin_root` - Pluginルートディレクトリ
- `.loops_path` - data/Loops ディレクトリ
- `.digests_path` - data/Digests ディレクトリ
- `.essences_path` - data/Essences ディレクトリ
- `.config_dir` - .claude-plugin ディレクトリ
- `.persistent_config_dir` - 永続化設定ディレクトリ（v5.2.0+）

#### `shared_plugin_env` (module scope)

モジュール内で共有される読み取り専用環境。

**注意:** このフィクスチャを使用するテストは環境を変更してはいけません。

#### `sample_loop_files`

5つのサンプルLoopファイルを含む環境を提供。

```python
def test_with_loops(sample_loop_files):
    env, loop_files = sample_loop_files
    assert len(loop_files) == 5
```

### Additional Fixtures [v4.0.0+]

#### `reset_all_singletons` (autouse=True)

テスト間の状態分離を保証する自動実行フィクスチャ。

**リセット対象 [v5.2.0+ 更新]:**

| モジュール | リセット関数 | 説明 |
|-----------|-------------|------|
| `level_registry` | `reset_level_registry()` | レベル設定のシングルトン |
| `file_naming` | `reset_registry()` | ファイル命名用レジストリ参照 |
| `error_formatter` | `reset_error_formatter()` | エラーフォーマッタのデフォルトインスタンス |

**手動リセット例:**
```python
from domain.level_registry import reset_level_registry
from domain.file_naming import reset_registry
from domain.error_formatter import reset_error_formatter

reset_level_registry()
reset_registry()
reset_error_formatter()
```

> **Note**: 各シングルトンモジュールのdocstringにリセット方法が記載されています（v5.2.0+）。

#### `mock_digest_config`

パス情報のみを持つ軽量モックDigestConfig。

```python
def test_with_mock(mock_digest_config):
    assert mock_digest_config.config_file.exists()
```

#### `level_hierarchy`

SSoT関数からレベル階層情報を取得。

#### `placeholder_manager`

PlaceholderManagerインスタンスを提供。

---

## Adding New Tests

### Unit Tests

```python
@pytest.mark.unit
class TestFileNaming:
    def test_extract_loop_number_valid_format(self):
        result = extract_file_number("L00123_test.txt")
        assert result == ("L", 123)

    @pytest.mark.parametrize("input,expected", [
        ("L00001_test.txt", 1),
        ("L99999_test.txt", 99999),
    ])
    def test_extract_with_various_formats(self, input, expected):
        _, number = extract_file_number(input)
        assert number == expected
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.slow
class TestShadowUpdate:
    def test_update_adds_files_to_shadow(self, temp_plugin_env):
        # Arrange
        config = DigestConfig()  # 環境変数で設定済み
        manager = ShadowGrandDigestManager(config)

        # Act
        manager.update_shadow_for_new_loops()

        # Assert
        shadow_data = manager.get_shadow_digest_for_level("weekly")
        assert shadow_data is not None
```

### Property-Based Tests

```python
@pytest.mark.property
class TestFileNamingInvariants:
    @given(st.integers(min_value=1, max_value=99999))
    @settings(max_examples=500)
    def test_format_extract_roundtrip(self, number):
        """フォーマット→抽出のラウンドトリップ不変条件"""
        formatted = format_digest_number("weekly", number)
        result = extract_file_number(formatted)
        assert result[1] == number
```

---

## Test Naming Convention

- `test_<module>.py` - 単体テスト
- `test_e2e_<scenario>.py` - E2Eワークフローテスト
- `test_<component>_properties.py` - Property-based tests
- `test_concurrent_<aspect>.py` - 並行処理テスト

---

## Property-Based Tests

Hypothesis を使用したプロパティベーステスト。
不変条件（invariants）と境界条件を網羅的にテスト。

### ファイル一覧 (11ファイル)

| 層 | ファイル | テスト数 | 対象 |
|----|---------|---------|-----|
| Domain | `test_constants_properties.py` | 14 | プレースホルダ生成 |
| Domain | `test_file_naming_properties.py` | 10 | ファイル命名規則 |
| Domain | `test_text_utils_properties.py` | 14 | テキスト抽出 |
| Domain | `test_validation_helpers_properties.py` | 14 | バリデーションヘルパー |
| Domain | `test_validators_properties.py` | 16 | 型バリデータ |
| Config | `test_config_properties.py` | 11 | 設定読込 |
| Application | `test_cascade_properties.py` | 12 | カスケード処理 |
| Application | `test_template_properties.py` | 13 | テンプレート生成 |
| Application | `test_shadow_io_properties.py` | 9 | Shadow I/O |
| Infrastructure | `test_file_scanner_properties.py` | 14 | ファイルスキャン |
| Infrastructure | `test_json_repository_properties.py` | 8 | JSON永続化 |

**合計**: 約125テストケース (Hypothesisにより各テストで100+の入力を生成)

### 実行方法

```bash
# Property-based tests のみ実行
pytest scripts/test/ -m property -v

# CI用プロファイル（500 examples）
HYPOTHESIS_PROFILE=ci pytest scripts/test/ -m property

# 高速チェック（20 examples）
HYPOTHESIS_PROFILE=quick pytest scripts/test/ -m property
```

---

## CLI Integration Tests [v4.0.0+]

v4.0.0で追加されたCLI E2Eテストフレームワーク。subprocess経由で実際のCLIコマンドを実行してテストします。

### ディレクトリ構成

```
cli_integration_tests/
├── __init__.py
├── conftest.py              # CLI専用フィクスチャ
├── cli_runner.py            # CLIRunner ヘルパークラス
├── test_digest_setup_cli.py
├── test_digest_config_cli.py
├── test_digest_auto_cli.py
└── test_workflow_cli.py     # ワークフロー統合テスト [v4.1.0+]
```

### CLIRunner

subprocess経由でCLIコマンドを実行するヘルパークラス:

```python
@pytest.mark.cli
def test_setup_check(cli_runner):
    result = cli_runner.run_digest_setup("check")
    result.assert_success()
    result.assert_json_status("not_configured")
```

### CLI専用フィクスチャ

| フィクスチャ | 説明 |
|-------------|------|
| `cli_temp_dir` | 一時ディレクトリ |
| `cli_plugin_root` | 最小構造のプラグインルート |
| `cli_runner` | CLIRunner インスタンス |
| `configured_cli_env` | 設定済み環境（config.json、テンプレート等） |
| `configured_cli_runner` | 設定済み環境のCLIRunner |

### 実行方法

```bash
# CLI統合テストのみ実行
pytest scripts/test/cli_integration_tests/ -m cli -v

# 特定のCLIテストのみ
pytest scripts/test/cli_integration_tests/test_digest_setup_cli.py -v
```

---

## Tools Tests [v4.1.0+]

開発支援ツールのテスト。

```
tools_tests/
├── test_check_footer.py       # Digestフッター検証
├── test_link_checker.py       # ドキュメントリンクチェック
├── test_validate_json.py      # JSON検証ツール
└── test_bandit_integration.py # セキュリティスキャン統合 (v5.0.0+)
```

---

## Encoding Tests [v4.2.0+]

Windows環境でのstdin UTF-8エンコーディングテスト。

```
interfaces_tests/
└── test_encoding.py          # stdin日本語入力の文字化け防止テスト
```

### テスト内容

| テスト名 | 検証内容 |
|---------|---------|
| `test_save_provisional_digest_japanese_input_no_garble` | 日本語JSONの文字化け防止 |
| `test_source_file_name_preserved` | source_fileフィールドの日本語保持 |

### 背景

Windows環境でsubprocess経由でstdinに日本語を渡す際、UTF-8エンコーディングが正しく設定されていないと文字化け（`???`パターン）が発生する。このテストは `io.TextIOWrapper` によるstdin UTF-8ラッパーの動作を検証する。

### 実行方法

```bash
# エンコーディングテストのみ
pytest scripts/test/interfaces_tests/test_encoding.py -v
```

---

## Bandit Security Scan Integration [v5.0.0+]

セキュリティスキャン統合テスト。

### テストファイル

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `tools_tests/test_bandit_integration.py` | 6 | Bandit統合 |

### テスト内容

| クラス | 検証内容 |
|-------|---------|
| `TestBanditExecution` | Banditのインストール・実行確認 |
| `TestBanditConfiguration` | `.bandit` 設定ファイル検証 |
| `TestSecurityQuality` | HIGH/MEDIUM severity 脆弱性がないことを確認 |

### 実行方法

```bash
# セキュリティテストのみ
pytest scripts/test/tools_tests/test_bandit_integration.py -v

# 手動セキュリティスキャン
make security
```

---

## Persistent Configuration Directory [v5.2.0+]

永続化設定ディレクトリ（`~/.claude/plugins/.episodicrag/`）のテスト。

### 背景

Claude Code のプラグイン自動更新により `.gitignore` 内の `config.json` が消失する問題を解決するため、
marketplaces/ 外の永続化ディレクトリを導入。

### テストファイル

| ファイル | 対象 | テスト数 |
|---------|------|--------|
| `infrastructure_tests/config/test_persistent_path.py` | `get_persistent_config_dir()` | 7 |
| `config_tests/test_config.py` | DigestConfig（永続化統合） | 30+ |
| `config_tests/test_config_builder.py` | DigestConfigBuilder | 15+ |

### 実行方法

```bash
# 永続化パステストのみ
pytest scripts/test/infrastructure_tests/config/test_persistent_path.py -v

# Config層全体（永続化統合テスト含む）
pytest scripts/test/config_tests/ -v
```

### テスト環境

- `TempPluginEnvironment` が自動的に `get_persistent_config_dir()` をモック
- 環境変数 `EPISODICRAG_CONFIG_DIR` でカスタムパス指定可能（テスト用）

---

## Debugging Tips

### Running Specific Tests

```bash
# 単一テストクラス
pytest scripts/test/integration_tests/test_e2e_workflow.py::TestE2ELoopDetectionToShadow -v

# 単一テストメソッド
pytest scripts/test/integration_tests/test_e2e_workflow.py::TestE2ELoopDetectionToShadow::test_new_loops_detected -v

# 出力付きで実行
pytest -s --tb=short
```

### Fixture Inspection

```bash
# 利用可能なフィクスチャを表示
pytest --fixtures

# カスタムフィクスチャのみ表示
pytest --fixtures scripts/test/conftest.py
```

---

## Hypothesis Profiles

```python
# デフォルト: 100 examples
settings.register_profile("default", max_examples=100)

# CI用: 500 examples
settings.register_profile("ci", max_examples=500, verbosity=Verbosity.verbose)

# 高速チェック: 20 examples
settings.register_profile("quick", max_examples=20)
```

使用方法:
```bash
HYPOTHESIS_PROFILE=ci pytest scripts/test/ -m property
```

---

## Performance Targets

- Unit test suite: <5秒
- Integration suite: <30秒
- Full test suite: <2分

---

## Continuous Integration

### GitHub Actions

[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Bizuayeu/Plugins-Weave/branch/main/graph/badge.svg)](https://codecov.io/gh/Bizuayeu/Plugins-Weave)

- **テスト実行**: PR作成時・mainマージ時に自動実行
- **カバレッジレポート**: [Codecov Dashboard](https://codecov.io/gh/Bizuayeu/Plugins-Weave)

### ローカル実行

```bash
# 最小テストセット（PR用）
pytest scripts/test/ -m "not performance" --tb=short

# フルテストセット（マージ後）
pytest scripts/test/ -v

# カバレッジ付き
pytest scripts/test/ --cov=. --cov-report=term-missing --cov-report=html

# HTMLレポート確認
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

---

## Known Gaps

### 将来の改善候補

1. **8レベル完全カスケードテスト** - 現在はWeekly→Monthlyの2レベルまで

> **Note**: 以下は実装済み
> - エラー回復テスト → `test_stateful_workflow.py::ErrorRecoveryStateMachine`
> - 境界条件テスト → `test_threshold_boundaries.py`
> - 並行アクセステスト → `test_concurrent_access.py`

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
