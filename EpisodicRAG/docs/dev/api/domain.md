[API Reference](../API_REFERENCE.md) > Domain層

# Domain層 API

コアビジネスロジック。外部に依存しない純粋な定義。

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

## 定数

### LEVEL_CONFIG

階層ごとの設定を定義する辞書。Single Source of Truth（唯一の真実の情報源）。

> 📖 8階層のプレフィックス・桁数・時間スケールは [用語集](../../../README.md#8階層構造) を参照

```python
LEVEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "weekly": {"prefix": "W", "digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly"},
    "monthly": {"prefix": "M", "digits": 4, "dir": "2_Monthly", "source": "weekly", "next": "quarterly"},
    "quarterly": {"prefix": "Q", "digits": 3, "dir": "3_Quarterly", "source": "monthly", "next": "annual"},
    "annual": {"prefix": "A", "digits": 3, "dir": "4_Annual", "source": "quarterly", "next": "triennial"},
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

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
