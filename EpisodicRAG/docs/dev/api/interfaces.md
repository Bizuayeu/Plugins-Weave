[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Interfaces

# Interfaces層 API

外部からのエントリーポイント。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from interfaces import (
    # Main entry points
    DigestFinalizerFromShadow,
    ProvisionalDigestSaver,
    # CLI classes (v4.0.0)
    SetupManager,
    ConfigEditor,
    DigestAutoAnalyzer,
    # Helpers
    sanitize_filename,
    get_next_digest_number,
    # Provisional submodule
    InputLoader,
    ProvisionalFileManager,
    DigestMerger,
)
```

---

## 目次

1. [SetupManager（digest_setup.py）](#setupmanagerdigest_setuppy)
2. [ConfigEditor（digest_config.py）](#configeditordigest_configpy)
3. [DigestAutoAnalyzer（digest_auto.py）](#digestautoanalyzerdigest_autopy)
4. [DigestFinalizerFromShadow](#digestfinalizerfromshadow)
5. [ProvisionalDigestSaver](#provisionaldigestsaver)
6. [Provisionalサブパッケージ](#provisionalサブパッケージinterfacesprovisional)
7. [ヘルパー関数](#ヘルパー関数interfacesinterface_helperspy)
8. [ShadowStateChecker（内部CLI）](#shadowstatechecker内部cli)

---

## SetupManager（digest_setup.py）

初期セットアップCLI。設定ファイル・ディレクトリ・初期ファイルを作成。

```python
class SetupManager:
    def __init__(self, plugin_root: Optional[Path] = None): ...

    def check(self) -> Dict[str, Any]: ...
    def init(self, config_data: Dict[str, Any], force: bool = False) -> SetupResult: ...
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `check()` | セットアップ状態確認 | `{"status": "configured"\|"partial"\|"not_configured", ...}` |
| `init(config_data, force)` | 初期化実行（8階層ディレクトリ作成） | `SetupResult` |

**SetupResult構造**:
```python
@dataclass
class SetupResult:
    status: str  # "ok" | "error" | "already_configured"
    created: Optional[Dict[str, Any]] = None  # 作成されたファイル/ディレクトリ
    warnings: List[str] = field(default_factory=list)
    external_paths_detected: List[str] = field(default_factory=list)
    error: Optional[str] = None
```

**使用例（CLI）**:

```bash
cd scripts

# 状態確認
python -m interfaces.digest_setup check

# 初期化
python -m interfaces.digest_setup init --config '{"base_dir": ".", "paths": {...}, "levels": {...}}'

# 強制上書き
python -m interfaces.digest_setup init --config '...' --force
```

**スキル**: `@digest-setup`

---

## ConfigEditor（digest_config.py）

設定変更CLI。設定ファイルの読み取り・変更を行う。

```python
class ConfigEditor:
    def __init__(self, plugin_root: Optional[Path] = None): ...

    def show(self) -> Dict[str, Any]: ...
    def update(self, new_config: Dict[str, Any]) -> Dict[str, Any]: ...
    def set_value(self, key: str, value: Any) -> Dict[str, Any]: ...
    def add_trusted_path(self, path: str) -> Dict[str, Any]: ...
    def remove_trusted_path(self, path: str) -> Dict[str, Any]: ...
    def list_trusted_paths(self) -> Dict[str, Any]: ...
```

| メソッド | 説明 |
|---------|------|
| `show()` | 現在設定と解決後パスを表示 |
| `update(new_config)` | 設定を完全更新 |
| `set_value(key, value)` | 個別設定変更（ドット記法対応: `levels.weekly_threshold`） |
| `add_trusted_path(path)` | `trusted_external_paths`にパスを追加 |
| `remove_trusted_path(path)` | `trusted_external_paths`からパスを削除 |
| `list_trusted_paths()` | 許可済み外部パス一覧 |

**使用例（CLI）**:

```bash
cd scripts

# 現在設定を表示
python -m interfaces.digest_config show

# 個別設定を変更（ドット記法）
python -m interfaces.digest_config set --key "levels.weekly_threshold" --value 7

# 外部パス許可リスト管理
python -m interfaces.digest_config trusted-paths list
python -m interfaces.digest_config trusted-paths add "~/DEV/production"
python -m interfaces.digest_config trusted-paths remove "~/DEV/production"
```

**スキル**: `@digest-config`

---

## DigestAutoAnalyzer（digest_auto.py）

健全性診断CLI。システム状態を分析し、まだらボケを検出、生成可能なダイジェスト階層を推奨。

```python
class DigestAutoAnalyzer:
    def __init__(self, plugin_root: Optional[Path] = None): ...

    def analyze(self) -> AnalysisResult: ...
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `analyze()` | システム健全性診断を実行 | `AnalysisResult` |

**AnalysisResult構造**:
```python
@dataclass
class AnalysisResult:
    status: str  # "ok" | "warning" | "error"
    issues: List[Issue] = field(default_factory=list)
    generatable_levels: List[LevelStatus] = field(default_factory=list)
    insufficient_levels: List[LevelStatus] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None
```

**検出項目**:
- 未処理Loopファイル（`last_processed`より後）
- プレースホルダー（まだらボケ: `<!-- PLACEHOLDER -->`マーカー）
- 連番ギャップ（中間ファイルスキップ）
- 生成可能なダイジェスト階層

**使用例（CLI）**:

```bash
cd scripts

# JSON形式で出力
python -m interfaces.digest_auto --output json

# テキスト形式で出力（人間可読）
python -m interfaces.digest_auto --output text
```

**スキル**: `@digest-auto`

---

## DigestFinalizerFromShadow

メインエントリーポイント。Shadowから正式Digestを確定。

```python
class DigestFinalizerFromShadow:
    def __init__(
        self,
        config: Optional[DigestConfig] = None,
        grand_digest_manager: Optional[GrandDigestManager] = None,
        shadow_manager: Optional[ShadowGrandDigestManager] = None,
        times_tracker: Optional[DigestTimesTracker] = None,
    ): ...

    def validate_shadow_content(self, level: str, source_files: list) -> None: ...
    def finalize_from_shadow(self, level: str, weave_title: str) -> None: ...
```

| メソッド | 説明 | 例外 |
|---------|------|------|
| `validate_shadow_content(level, source_files)` | source_filesの形式・連番を検証 | `ValidationError` |
| `finalize_from_shadow(level, weave_title)` | Shadow→RegularDigest確定（処理1-5実行） | `ValidationError`, `DigestError`, `FileIOError` |

**処理フロー**:
1. RegularDigest作成
2. GrandDigest更新
3. ShadowGrandDigest更新（カスケード）
4. last_digest_times更新
5. ProvisionalDigest削除

**使用例（Python）**:

```python
from interfaces import DigestFinalizerFromShadow
from application.config import DigestConfig

config = DigestConfig()
finalizer = DigestFinalizerFromShadow(config)
finalizer.finalize_from_shadow("weekly", "認知アーキテクチャの深化")
```

**使用例（CLI）**:

```bash
cd scripts
python finalize_from_shadow.py weekly "認知アーキテクチャの深化"
```

**テスト時のモック注入**:

```python
# DI対応：テスト時にモックを注入可能
finalizer = DigestFinalizerFromShadow(
    config=mock_config,
    grand_digest_manager=mock_grand,
    shadow_manager=mock_shadow,
    times_tracker=mock_tracker
)
```

---

## ProvisionalDigestSaver

Provisional Digestを保存。

```python
class ProvisionalDigestSaver:
    def __init__(self, config: DigestConfig): ...
    def save(self, level: str, digest_data: Dict) -> Path: ...
    def run(self, level: str, input_data: Union[str, List], append: bool = False) -> None
```

| メソッド | 説明 |
|---------|------|
| `save(level, digest_data) -> Path` | Provisionalファイルを保存し、パスを返す |
| `run(level, input_data, append) -> None` | CLI/スクリプトからの実行エントリーポイント |

**使用例（Python）**:

```python
from interfaces import ProvisionalDigestSaver
from application.config import DigestConfig

config = DigestConfig()
saver = ProvisionalDigestSaver(config)

# 新規保存
saver.run("weekly", '[{"filename": "L00001.txt", "digest_type": "洞察", ...}]')

# 既存に追加（--append相当）
saver.run("weekly", '[{"filename": "L00002.txt", ...}]', append=True)

# ファイルパスから読み込んで保存
saver.run("weekly", "/path/to/input.json")
```

**使用例（CLI）**:

```bash
cd scripts

# JSON文字列を直接渡す
python save_provisional_digest.py weekly '[{"filename": "L00001.txt", ...}]'

# 既存に追加
python save_provisional_digest.py weekly '[{"filename": "L00002.txt", ...}]' --append
```

---

## Provisionalサブパッケージ（interfaces/provisional/）

Provisional Digest処理の詳細コンポーネント。

### InputLoader

入力データの読み込み。

```python
class InputLoader:
    def load_from_json_file(self, file_path: Path) -> List[IndividualDigestData]
    def parse_json_string(self, json_string: str) -> List[IndividualDigestData]
    def load_input(self, input_source: Union[str, Path]) -> List[IndividualDigestData]
```

| メソッド | 説明 |
|---------|------|
| `load_from_json_file(file_path)` | JSONファイルからダイジェストリストを読み込み |
| `parse_json_string(json_string)` | JSON文字列をパースしてダイジェストリストに変換 |
| `load_input(input_source)` | ファイルパスまたはJSON文字列から自動判定して読み込み |

### ProvisionalFileManager

Provisionalファイルの管理。

```python
class ProvisionalFileManager:
    def __init__(self, config: DigestConfig): ...

    def get_provisional_dir(self, level: str) -> Path
    def get_provisional_path(self, level: str, digest_number: str) -> Path
    def get_next_provisional_number(self, level: str) -> int
    def get_digits_for_level(self, level: str) -> int
    def list_provisional_files(self, level: str) -> List[Path]
```

| メソッド | 説明 |
|---------|------|
| `get_provisional_dir(level)` | Provisionalディレクトリのパスを取得 |
| `get_provisional_path(level, digest_number)` | Provisionalファイルのフルパスを取得 |
| `get_next_provisional_number(level)` | 次のProvisional番号を計算 |
| `list_provisional_files(level)` | 既存のProvisionalファイル一覧を取得 |

### DigestMerger

ダイジェストのマージ処理。

```python
class DigestMerger:
    def merge_digests(
        self,
        existing: List[IndividualDigestData],
        new: List[IndividualDigestData]
    ) -> List[IndividualDigestData]

    def remove_duplicates(
        self,
        digests: List[IndividualDigestData]
    ) -> List[IndividualDigestData]
```

| メソッド | 説明 |
|---------|------|
| `merge_digests(existing, new)` | 既存と新規のダイジェストをマージ |
| `remove_duplicates(digests)` | 重複を除去（source_fileベース） |

### バリデーション関数（interfaces/provisional/validator.py）

```python
def validate_individual_digest(data: Any) -> IndividualDigestData
def validate_individual_digests_list(data: Any) -> List[IndividualDigestData]
def validate_input_format(data: Any) -> List[IndividualDigestData]
def validate_provisional_structure(data: Any) -> Dict[str, Any]
```

| 関数 | 説明 | 例外 |
|------|------|------|
| `validate_individual_digest(data)` | 単一ダイジェストの形式を検証 | `ValidationError` |
| `validate_individual_digests_list(data)` | ダイジェストリストの形式を検証 | `ValidationError` |
| `validate_input_format(data)` | 入力データの形式を自動判定・検証 | `ValidationError` |
| `validate_provisional_structure(data)` | Provisionalファイル全体の構造を検証 | `ValidationError` |

---

## ヘルパー関数（interfaces/interface_helpers.py）

### sanitize_filename()

```python
def sanitize_filename(title: str, max_length: int = 50) -> str
```

ファイル名として安全な文字列に変換。

```python
sanitize_filename("技術探求/AI")        # "技術探求AI" (危険文字は削除)
sanitize_filename("技術 探求 AI")       # "技術_探求_AI" (空白は_に変換)
sanitize_filename("")                   # "untitled"
```

### get_next_digest_number()

```python
def get_next_digest_number(digests_path: Path, level: str) -> int
```

指定レベルの次のDigest番号を取得。

---

## ShadowStateChecker（内部CLI）

Shadow状態判定CLI。`__all__`にエクスポートされていない内部CLI。直接インポートせず、CLIとして使用。

> DigestAnalyzer起動が必要かを判定するためのユーティリティ。

```python
class ShadowStateChecker:
    def __init__(self, plugin_root: Optional[Path] = None): ...

    def check(self, level: str) -> ShadowStateResult: ...
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `check(level)` | 指定レベルのShadow状態確認 | `ShadowStateResult` |

**ShadowStateResult構造**:
```python
@dataclass
class ShadowStateResult:
    status: str  # "ok" | "error"
    level: str
    analyzed: bool  # True: 分析済み, False: プレースホルダーあり
    source_files: List[str] = field(default_factory=list)
    source_count: int = 0
    placeholder_fields: List[str] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None
```

**使用例（CLI）**:

```bash
cd scripts

# Weekly階層の状態確認
python -m interfaces.shadow_state_checker weekly

# Monthly階層の状態確認
python -m interfaces.shadow_state_checker monthly
```

**出力例**:
```json
{
  "status": "ok",
  "level": "weekly",
  "analyzed": false,
  "source_files": ["L00001_xxx.txt", "L00002_yyy.txt"],
  "source_count": 2,
  "placeholder_fields": ["abstract", "impression"],
  "message": "Placeholders detected in: abstract, impression - run DigestAnalyzer"
}
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
