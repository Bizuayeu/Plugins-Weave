[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Domain

# Domain層 API

コアビジネスロジック。外部に依存しない純粋な定義。

> **v4.0.0**: エラーフォーマッタがCompositeパターンに再編成されました。詳細は [DESIGN_DECISIONS.md](../DESIGN_DECISIONS.md) を参照。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from domain import (
    # 定数
    LEVEL_CONFIG, LEVEL_NAMES, PLACEHOLDER_LIMITS, DEFAULT_THRESHOLDS,
    # 例外
    EpisodicRAGError, ValidationError, ConfigError, DigestError, FileIOError,
    # 型
    OverallDigestData, ShadowDigestData, GrandDigestData,
    # ファイル命名
    extract_file_number, extract_number_only, format_digest_number,
    # バージョン
    __version__, DIGEST_FORMAT_VERSION,
)
```

---

## 目次

**定数・設定**
- [定数](#定数) - バージョン、LEVEL_CONFIG、PLACEHOLDER
- [例外](#例外domainexceptionspy) - EpisodicRAGError階層
- [型定義](#型定義domaintypespy) - TypedDict、スキーマ

**ファイル・階層操作**
- [関数](#関数domainfile_namingpy) - ファイル命名、番号抽出
- [レベルレジストリ](#レベルレジストリdomainlevel_registrypy) - 階層設定の一元管理
- [定数ユーティリティ](#定数ユーティリティ関数domainconstantspy) - プレースホルダー生成

**エラー処理**
- [エラーフォーマット](#エラーフォーマットdomainerror_formatter) - CompositeErrorFormatter *(v4.0.0+)*

---

## 定数

### バージョン定数

| 定数 | 値 | 説明 |
|------|-----|------|
| `__version__` | (動的) | plugin.jsonから読み込み（SSoT） |
| `DIGEST_FORMAT_VERSION` | `"1.0"` | データフォーマットバージョン |

```python
from domain import __version__, DIGEST_FORMAT_VERSION

print(__version__)           # "4.0.0" (plugin.jsonから)
print(DIGEST_FORMAT_VERSION) # "1.0"
```

### LEVEL_CONFIG

階層ごとの設定を定義する辞書。Single Source of Truth（唯一の真実の情報源）。

> 📖 8階層のプレフィックス・桁数・時間スケールは [用語集](../../../README.md#8階層構造) を参照

```python
LEVEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "weekly": {"prefix": "W", "digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly", "threshold": 5},
    "monthly": {"prefix": "M", "digits": 4, "dir": "2_Monthly", "source": "weekly", "next": "quarterly", "threshold": 5},
    "quarterly": {"prefix": "Q", "digits": 3, "dir": "3_Quarterly", "source": "monthly", "next": "annual", "threshold": 3},
    "annual": {"prefix": "A", "digits": 3, "dir": "4_Annual", "source": "quarterly", "next": "triennial", "threshold": 4},
    "triennial": {"prefix": "T", "digits": 2, "dir": "5_Triennial", "source": "annual", "next": "decadal", "threshold": 3},
    "decadal": {"prefix": "D", "digits": 2, "dir": "6_Decadal", "source": "triennial", "next": "multi_decadal", "threshold": 3},
    "multi_decadal": {"prefix": "MD", "digits": 2, "dir": "7_Multi-decadal", "source": "decadal", "next": "centurial", "threshold": 3},
    "centurial": {"prefix": "C", "digits": 2, "dir": "8_Centurial", "source": "multi_decadal", "next": None, "threshold": 4}
}
```

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `prefix` | ファイル名プレフィックス | `W`, `M`, `MD` |
| `digits` | 番号の桁数 | `4` (W0001) |
| `dir` | digests_path以下のサブディレクトリ名 | `1_Weekly` |
| `source` | この階層を生成する際の入力元 | `loops`, `weekly` |
| `next` | 確定時にカスケードする上位階層 | `monthly`, `None` |
| `threshold` | ダイジェスト生成に必要なソースファイル数 | `5`, `3`, `4` |

### LEVEL_NAMES

```python
LEVEL_NAMES = ["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "multi_decadal", "centurial"]
```

### PLACEHOLDER定数

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

---

## 例外（domain/exceptions.py）

| 例外 | 説明 |
|------|------|
| `EpisodicRAGError` | 基底例外クラス |
| `ConfigError` | 設定関連エラー |
| `DigestError` | ダイジェスト処理エラー |
| `ValidationError` | バリデーションエラー |
| `FileIOError` | ファイルI/Oエラー |
| `CorruptedDataError` | データ破損エラー |

---

## 型定義（domain/types.py）

TypedDictを使用した型安全な定義。`Dict[str, Any]`の置き換え用。

```python
from domain.types import DigestMetadataComplete, ProvisionalDigestFile
```

### DigestMetadataComplete

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

### ProvisionalDigestFile

Provisional Digestファイル（`_Individual.txt`）の全体構造。

```python
class ProvisionalDigestFile(TypedDict):
    metadata: DigestMetadataComplete
    individual_digests: List[IndividualDigestData]
```

### その他の型定義

| 型名 | 説明 |
|------|------|
| `BaseMetadata` | 共通メタデータ（version, last_updated） |
| `DigestMetadata` | ダイジェスト固有メタデータ（digest_level, digest_number, source_count） |
| `LevelConfigData` | LEVEL_CONFIGの各レベル設定 |
| `OverallDigestData` | overall_digestの構造 |
| `IndividualDigestData` | individual_digestsの各要素 |
| `ShadowLevelData` | ShadowGrandDigestの各レベルデータ |
| `ShadowDigestData` | ShadowGrandDigest.txtの全体構造 |
| `GrandDigestLevelData` | GrandDigestの各レベルデータ |
| `GrandDigestData` | GrandDigest.txtの全体構造 |
| `RegularDigestData` | Regular Digestファイルの構造 |
| `PathsConfigData` | config.jsonのpathsセクション |
| `LevelsConfigData` | config.jsonのlevelsセクション（threshold設定） |
| `ConfigData` | config.jsonの全体構造 |
| `DigestTimeData` | last_digest_times.jsonの各レベルデータ |
| `DigestTimesData` | `Dict[str, DigestTimeData]`のエイリアス |
| `ProvisionalDigestEntry` | Provisional Digestの各エントリ |

### 主要TypedDictスキーマ

JSONファイル構造を理解するためのスキーマ定義です（TypeScript形式で表現、`?`はオプショナル）。

#### ConfigData

config.json全体構造の型定義。

```python
from domain.types import ConfigData
```

> 📖 詳細スキーマは [config.md](config.md#configdata型定義) を参照

#### ShadowDigestData（ShadowGrandDigest.txt全体構造）

```typescript
interface ShadowDigestData {
  metadata: {
    version: string;           // "1.0"
    last_updated: string;      // ISO 8601形式
    digest_level?: string;
    digest_number?: string;
  };
  latest_digests: {
    [level: string]: {         // "weekly", "monthly" など
      overall_digest?: {
        timestamp?: string;
        source_files?: string[];
        digest_type?: string;
        keywords?: string[];
        abstract?: string;
        impression?: string;
      } | null;
      individual_digests?: IndividualDigestData[];
      source_files?: string[];
    };
  };
}
```

#### GrandDigestData（GrandDigest.txt全体構造）

```typescript
interface GrandDigestData {
  metadata: {
    version: string;           // "1.0"
    last_updated: string;      // ISO 8601形式
  };
  major_digests: {
    [level: string]: {         // "weekly", "monthly" など
      overall_digest?: OverallDigestData | null;
    };
  };
}
```

#### RegularDigestData（確定済みDigestファイル）

```typescript
interface RegularDigestData {
  metadata: {
    version: string;
    last_updated: string;
    digest_level: string;      // "weekly", "monthly" など
    digest_number: string;     // "W0001", "M001" など
    source_count?: number;
  };
  overall_digest: {
    name?: string;             // タイトル
    timestamp: string;
    source_files: string[];
    digest_type: string;
    keywords: string[];
    abstract: string;          // 最大2400文字
    impression: string;        // 最大800文字
  };
  individual_digests: IndividualDigestData[];
}
```

#### IndividualDigestData（個別ダイジェスト要素）

```typescript
interface IndividualDigestData {
  source_file: string;         // "L00001_タイトル.txt"
  digest_type: string;         // "洞察", "問題解決" など
  keywords: string[];          // 最大5個
  abstract: string;            // 最大1200文字
  impression: string;          // 最大400文字
}
```

> 📖 完全な型定義は [scripts/domain/types.py](../../../scripts/domain/types.py) を参照

---

## 関数（domain/file_naming.py）

### extract_file_number()

```python
def extract_file_number(filename: str) -> Optional[Tuple[str, int]]
```

ファイル名からプレフィックスと番号を抽出。

```python
extract_file_number("L00186_認知アーキテクチャ.txt")  # ("L", 186)
extract_file_number("W0001_Individual.txt")           # ("W", 1)
extract_file_number("MD01_xxx.txt")                   # ("MD", 1)
extract_file_number("invalid.txt")                    # None
```

### extract_number_only()

```python
def extract_number_only(filename: str) -> Optional[int]
```

ファイル名から番号のみを抽出（後方互換性用）。

```python
extract_number_only("L00186_test.txt")  # 186
extract_number_only("W0001_weekly.txt")   # 1
extract_number_only("invalid.txt")        # None
```

### format_digest_number()

```python
def format_digest_number(level: str, number: int) -> str
```

レベルと番号から統一されたフォーマットの文字列を生成。

```python
format_digest_number("loop", 186)         # "L00186"
format_digest_number("weekly", 1)         # "W0001"
format_digest_number("multi_decadal", 3)  # "MD03"
```

### find_max_number()

```python
def find_max_number(files: List[Union[Path, str]], prefix: str) -> Optional[int]
```

指定プレフィックスを持つファイル群から最大番号を取得。

```python
find_max_number(["W0001.txt", "W0005.txt", "W0003.txt"], "W")  # 5
find_max_number([], "W")  # None
```

### filter_files_after()

```python
def filter_files_after(files: List[Path], threshold: int) -> List[Path]
```

指定番号より大きいファイルのみをフィルタ。

### extract_numbers_formatted()

```python
def extract_numbers_formatted(files: List[Union[str, None]]) -> List[str]
```

ファイル名リストからプレフィックス付き番号を抽出（ゼロ埋め維持）。

```python
extract_numbers_formatted(["L00001.txt", "L00005.txt"])  # ["L00001", "L00005"]
```

---

## レベルレジストリ（domain/level_registry.py）

階層設定の一元管理（Singletonパターン）。

### LevelMetadata

```python
@dataclass(frozen=True)
class LevelMetadata:
    name: str           # レベル名（"weekly", "monthly"等）
    prefix: str         # プレフィックス（"W", "M"等）
    digits: int         # 番号の桁数
    dir: str            # ディレクトリ名（"1_Weekly"等）
    source: str         # 入力元レベル
    next_level: Optional[str]  # カスケード先（None=最上位）
```

### LevelBehavior（抽象基底クラス）

```python
class LevelBehavior(ABC):
    @abstractmethod
    def format_number(self, number: int) -> str: ...

    @abstractmethod
    def should_cascade(self) -> bool: ...
```

| 実装クラス | 説明 |
|-----------|------|
| `StandardLevelBehavior` | 通常階層（weekly〜centurial） |
| `LoopLevelBehavior` | Loopファイル用（5桁、カスケードなし） |

#### 実装例

```python
from domain.level_behaviors import StandardLevelBehavior, LoopLevelBehavior
from domain.level_metadata import LevelMetadata

# StandardLevelBehavior使用例
metadata = LevelMetadata(
    name="weekly", prefix="W", digits=4,
    dir="1_Weekly", source="loops", next_level="monthly"
)
behavior = StandardLevelBehavior(metadata)
print(behavior.format_number(42))      # "W0042"
print(behavior.should_cascade())       # True

# LoopLevelBehavior使用例
loop_behavior = LoopLevelBehavior()
print(loop_behavior.format_number(186))  # "L00186"
print(loop_behavior.should_cascade())    # False
```

### LevelRegistry

```python
class LevelRegistry:
    """階層設定の一元管理（Singleton）"""

    def get_behavior(self, level: str) -> LevelBehavior
    def get_metadata(self, level: str) -> LevelMetadata

    @staticmethod
    def get_level_names() -> List[str]      # ["weekly", "monthly", ...]
    @staticmethod
    def get_all_prefixes() -> List[str]     # ["W", "M", "Q", ...]
    @staticmethod
    def get_level_by_prefix(prefix: str) -> Optional[str]
    @staticmethod
    def should_cascade(level: str) -> bool
    @staticmethod
    def build_prefix_pattern() -> str       # 正規表現パターン生成
```

### ファクトリ関数

```python
def get_level_registry() -> LevelRegistry   # Singletonインスタンス取得
def reset_level_registry() -> None          # テスト用リセット
```

---

## 定数ユーティリティ関数（domain/constants.py）

### create_placeholder_text()

```python
def create_placeholder_text(content_type: str, char_limit: int) -> str
```

プレースホルダーテキストを生成。

```python
create_placeholder_text("abstract", 2400)
# "<!-- PLACEHOLDER: abstract (max 2400 chars) -->"
```

### create_placeholder_keywords()

```python
def create_placeholder_keywords(count: int) -> List[str]
```

プレースホルダーキーワードリストを生成。

```python
create_placeholder_keywords(5)
# ["<!-- PLACEHOLDER -->", "<!-- PLACEHOLDER -->", ...]
```

### build_level_hierarchy()

```python
def build_level_hierarchy() -> Dict[str, Dict[str, object]]
```

LEVEL_CONFIGから階層関係（source/next）を抽出した辞書を構築。

---

## エラーフォーマット（domain/error_formatter/）

エラーメッセージの標準化を担当。Compositeパターンによりカテゴリ別フォーマッタを統合。

> 📖 デザインパターン詳細は [DESIGN_DECISIONS.md](../DESIGN_DECISIONS.md) を参照

### CompositeErrorFormatter

全エラーフォーマッタを統合するComposite。カテゴリを明示的に指定してメソッドを呼び出す。

```python
class CompositeErrorFormatter:
    """全エラーフォーマッタを統合するComposite"""

    config: ConfigErrorFormatter      # 設定関連エラー
    file: FileErrorFormatter          # ファイルI/Oエラー
    validation: ValidationErrorFormatter  # バリデーションエラー
    digest: DigestErrorFormatter      # ダイジェスト処理エラー

    def format_path(self, path: Path) -> str: ...
```

### カテゴリ別メソッド一覧

#### config（設定関連）

| メソッド | 説明 |
|---------|------|
| `invalid_level(level, valid_levels)` | 無効レベルエラー |
| `config_key_missing(key)` | 設定キー欠落エラー |
| `config_invalid_value(key, expected, actual)` | 設定値不正エラー |
| `config_section_missing(section)` | 設定セクション欠落エラー |

#### file（ファイルI/O）

| メソッド | 説明 |
|---------|------|
| `file_not_found(path)` | ファイル未検出エラー |
| `file_already_exists(path)` | ファイル既存エラー |
| `file_io_error(operation, path, error)` | ファイルI/Oエラー |
| `directory_not_found(path)` | ディレクトリ未検出エラー |
| `directory_creation_failed(path, error)` | ディレクトリ作成失敗エラー |
| `invalid_json(path, error)` | JSON不正エラー |

#### validation（バリデーション）

| メソッド | 説明 |
|---------|------|
| `invalid_type(context, expected, actual)` | 型不正エラー |
| `validation_error(field, reason, value)` | バリデーションエラー |
| `empty_collection(context)` | 空コレクションエラー |

#### digest（ダイジェスト処理）

| メソッド | 説明 |
|---------|------|
| `digest_not_found(level, identifier)` | ダイジェスト未検出エラー |
| `shadow_empty(level)` | Shadow空エラー |
| `cascade_error(from_level, to_level, reason)` | カスケードエラー |
| `initialization_failed(component, error)` | 初期化失敗エラー |

### ファクトリ関数

```python
def get_error_formatter(project_root: Optional[Path] = None) -> CompositeErrorFormatter
def reset_error_formatter() -> None  # テスト用リセット
```

### 使用例

```python
from domain.error_formatter import get_error_formatter

formatter = get_error_formatter()

# 設定関連エラー
msg = formatter.config.invalid_level("xyz", ["weekly", "monthly"])
# -> "Invalid level: 'xyz'. Valid levels: weekly, monthly"

# ファイルI/Oエラー
msg = formatter.file.file_not_found(Path("/path/to/file.txt"))
# -> "File not found: path/to/file.txt"

# バリデーションエラー
msg = formatter.validation.invalid_type("config", "dict", "list")
# -> "Invalid type for config: expected dict, got list"

# ダイジェスト処理エラー
msg = formatter.digest.shadow_empty("weekly")
# -> "Shadow is empty for level: weekly"
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
