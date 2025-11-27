[Docs](../README.md) > API_REFERENCE

# API リファレンス

EpisodicRAGプラグインのPython API仕様書です。

> **対応バージョン**: EpisodicRAG Plugin v2.0.0+ / ファイルフォーマット 1.0

---

## 目次

1. [Domain層](#domain層)
2. [Infrastructure層](#infrastructure層)
3. [Application層](#application層)
4. [Interfaces層](#interfaces層)
5. [設定（config.py）](#設定configpy)
6. [CLI使用方法](#cli使用方法)

---

## Domain層

コアビジネスロジック。外部に依存しない純粋な定義。

```python
from domain import LEVEL_CONFIG, __version__, ValidationError
from domain.file_naming import extract_file_number, format_digest_number
```

### 定数

#### LEVEL_CONFIG

階層ごとの設定を定義する辞書。Single Source of Truth（唯一の真実の情報源）。

```python
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
```

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `prefix` | ファイル名プレフィックス | `W`, `M`, `MD` |
| `digits` | 番号の桁数 | `4` (W0001) |
| `dir` | digests_path以下のサブディレクトリ名 | `1_Weekly` |
| `source` | この階層を生成する際の入力元 | `loops`, `weekly` |
| `next` | 確定時にカスケードする上位階層 | `monthly`, `None` |

#### LEVEL_NAMES

```python
LEVEL_NAMES = ["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "multi_decadal", "centurial"]
```

#### PLACEHOLDER定数

プレースホルダー検出用のマーカー定数。

```python
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER"
PLACEHOLDER_END = " -->"
PLACEHOLDER_SIMPLE = "<!-- PLACEHOLDER -->"

PLACEHOLDER_LIMITS: Dict[str, int] = {
    "abstract_chars": 2400,
    "impression_chars": 800,
    "keyword_count": 5,
}
```

### 例外（domain/exceptions.py）

| 例外 | 説明 |
|------|------|
| `EpisodicRAGError` | 基底例外クラス |
| `ConfigError` | 設定関連エラー |
| `DigestError` | ダイジェスト処理エラー |
| `ValidationError` | バリデーションエラー |
| `FileIOError` | ファイルI/Oエラー |
| `CorruptedDataError` | データ破損エラー |

### 型定義（domain/types.py）

TypedDictを使用した型安全な定義。`Dict[str, Any]`の置き換え用。

```python
from domain.types import DigestMetadataComplete, ProvisionalDigestFile
```

#### DigestMetadataComplete

すべてのダイジェストファイルで使用される統一メタデータ型。

```python
class DigestMetadataComplete(TypedDict, total=False):
    version: str           # フォーマットバージョン（"1.0"）
    last_updated: str      # ISO 8601形式のタイムスタンプ
    digest_level: str      # "weekly", "monthly" など
    digest_number: str     # "W0001", "M001" など
    source_count: int      # ソースファイル数
    description: str       # 説明（オプション）
```

#### ProvisionalDigestFile

Provisional Digestファイル（`_Individual.txt`）の全体構造。

```python
class ProvisionalDigestFile(TypedDict):
    metadata: DigestMetadataComplete
    individual_digests: List[IndividualDigestData]
```

その他の型定義:
- `OverallDigestData` - overall_digestの構造
- `IndividualDigestData` - individual_digestsの各要素
- `ShadowDigestData` - ShadowGrandDigest.txtの全体構造
- `GrandDigestData` - GrandDigest.txtの全体構造
- `RegularDigestData` - Regular Digestファイルの構造

### 関数（domain/file_naming.py）

#### extract_file_number()

```python
def extract_file_number(filename: str) -> Optional[Tuple[str, int]]
```

ファイル名からプレフィックスと番号を抽出。

```python
extract_file_number("Loop0186_認知アーキテクチャ.txt")  # ("Loop", 186)
extract_file_number("W0001_Individual.txt")             # ("W", 1)
extract_file_number("MD01_xxx.txt")                     # ("MD", 1)
extract_file_number("invalid.txt")                      # None
```

#### format_digest_number()

```python
def format_digest_number(level: str, number: int) -> str
```

レベルと番号から統一されたフォーマットの文字列を生成。

```python
format_digest_number("loop", 186)         # "Loop0186"
format_digest_number("weekly", 1)         # "W0001"
format_digest_number("multi_decadal", 3)  # "MD03"
```

---

## Infrastructure層

外部関心事（ファイルI/O、ロギング）。

```python
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files, get_max_numbered_file
```

### JSON操作（infrastructure/json_repository.py）

#### load_json()

```python
def load_json(file_path: Path) -> Dict[str, Any]
```

JSONファイルを読み込む。

#### save_json()

```python
def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None
```

dictをJSONファイルに保存（親ディレクトリ自動作成）。

#### load_json_with_template()

```python
def load_json_with_template(
    target_file: Path,
    template_file: Optional[Path] = None,
    default_factory: Optional[Callable[[], Dict[str, Any]]] = None,
    save_on_create: bool = True,
    log_message: Optional[str] = None
) -> Dict[str, Any]
```

JSONファイルを読み込む。存在しない場合はテンプレートまたはデフォルトから作成。

### ファイルスキャン（infrastructure/file_scanner.py）

#### scan_files()

```python
def scan_files(directory: Path, pattern: str = "*") -> List[Path]
```

指定ディレクトリ内のファイルをスキャン。

#### get_max_numbered_file()

```python
def get_max_numbered_file(directory: Path, prefix: str) -> Optional[int]
```

指定プレフィックスの最大番号を取得。

### ロギング（infrastructure/logging_config.py）

```python
def log_info(message: str) -> None
def log_warning(message: str) -> None
def log_error(message: str, exit_code: Optional[int] = None) -> None
```

---

## Application層

ビジネスロジックの実装。

```python
from application.shadow import ShadowTemplate, ShadowUpdater
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from application.validators import validate_dict, is_valid_list
```

### バリデーション（application/validators.py）

```python
def validate_dict(data: Any) -> bool
def is_valid_dict(data: Any) -> bool
def is_valid_list(data: Any) -> bool
def is_valid_string(data: Any) -> bool
```

### Shadow管理（application/shadow/）

| クラス | 説明 |
|--------|------|
| `ShadowTemplate` | ShadowGrandDigestテンプレート生成 |
| `FileDetector` | 新規ファイル検出 |
| `ShadowIO` | Shadow読み書き |
| `ShadowUpdater` | Shadow更新処理 |

### GrandDigest管理（application/grand/）

| クラス | 説明 |
|--------|------|
| `GrandDigestManager` | GrandDigest.txt CRUD操作 |
| `ShadowGrandDigestManager` | ShadowGrandDigest.txt管理 |

### Finalize処理（application/finalize/）

| クラス | 説明 |
|--------|------|
| `ShadowValidator` | Shadow内容検証 |
| `ProvisionalLoader` | Provisionalファイル読込 |
| `RegularDigestBuilder` | RegularDigest構築 |
| `DigestPersistence` | 永続化処理 |

### 時間追跡（application/tracking/）

| クラス | 説明 |
|--------|------|
| `DigestTimesTracker` | last_digest_times.json管理 |

---

## Interfaces層

外部からのエントリーポイント。

```python
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number
```

### DigestFinalizerFromShadow

メインエントリーポイント。Shadowから正式Digestを確定。

```python
class DigestFinalizerFromShadow:
    def __init__(self, config: DigestConfig): ...
    def finalize(self, level: str, title: str) -> Path: ...
```

### ProvisionalDigestSaver

Provisional Digestを保存。

```python
class ProvisionalDigestSaver:
    def __init__(self, config: DigestConfig): ...
    def save(self, level: str, digest_data: Dict) -> Path: ...
```

### ヘルパー関数（interfaces/interface_helpers.py）

#### sanitize_filename()

```python
def sanitize_filename(title: str, max_length: int = 50) -> str
```

ファイル名として安全な文字列に変換。

```python
sanitize_filename("技術探求/AI")  # "技術探求_AI"
sanitize_filename("")             # "untitled"
```

#### get_next_digest_number()

```python
def get_next_digest_number(digests_path: Path, level: str) -> int
```

指定レベルの次のDigest番号を取得。

---

## 設定（config.py）

### DigestConfig クラス

```python
class DigestConfig:
    def __init__(self, plugin_root: Optional[Path] = None): ...
```

#### プロパティ（パス関連）

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `plugin_root` | `Path` | プラグインルートディレクトリ |
| `config_file` | `Path` | 設定ファイルのパス |
| `base_dir` | `Path` | 解決された基準ディレクトリ |
| `loops_path` | `Path` | Loopファイル配置先 |
| `digests_path` | `Path` | Digest出力先 |
| `essences_path` | `Path` | GrandDigest配置先 |

#### プロパティ（閾値関連）

| プロパティ | 型 | デフォルト |
|-----------|-----|----------|
| `weekly_threshold` | `int` | 5 |
| `monthly_threshold` | `int` | 5 |
| `quarterly_threshold` | `int` | 3 |
| `annual_threshold` | `int` | 4 |
| `triennial_threshold` | `int` | 3 |
| `decadal_threshold` | `int` | 3 |
| `multi_decadal_threshold` | `int` | 3 |
| `centurial_threshold` | `int` | 4 |

#### メソッド

```python
def resolve_path(self, key: str) -> Path
def get_level_dir(self, level: str) -> Path
def get_provisional_dir(self, level: str) -> Path
def get_threshold(self, level: str) -> int
def get_identity_file_path(self) -> Optional[Path]
def show_paths(self) -> None
def validate_directory_structure(self) -> list
```

---

## CLI使用方法

### config.py

```bash
# 設定をJSON形式で表示
python scripts/config.py

# パス設定を表示
python scripts/config.py --show-paths
```

### テスト実行

```bash
cd scripts

# 全テスト
python -m pytest test/ -v

# 層別インポート確認
python -c "from domain import LEVEL_CONFIG, __version__; print(__version__)"
python -c "from infrastructure import load_json; print('OK')"
python -c "from application import ShadowGrandDigestManager; print('OK')"
python -c "from interfaces import DigestFinalizerFromShadow; print('OK')"
```

---

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様・データフロー
- [GLOSSARY.md](../GLOSSARY.md) - 用語集
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発参加ガイド

---
