[Docs](../README.md) > API_REFERENCE

# API リファレンス

EpisodicRAGプラグインのPython API仕様書です。

> **対応バージョン**: EpisodicRAG Plugin（[version.py](../../scripts/domain/version.py) 参照）/ ファイルフォーマット 1.0

---

## 目次

1. [Domain層](#domain層)
2. [Infrastructure層](#infrastructure層)
3. [Application層](#application層)
4. [Interfaces層](#interfaces層)
5. [設定（config）](#設定configinitpy)
6. [CLI使用方法](#cli使用方法)

---

## Domain層

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

#### その他の型定義

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

#### extract_number_only()

```python
def extract_number_only(filename: str) -> Optional[int]
```

ファイル名から番号のみを抽出（後方互換性用）。

```python
extract_number_only("Loop0186_test.txt")  # 186
extract_number_only("W0001_weekly.txt")   # 1
extract_number_only("invalid.txt")        # None
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

#### file_exists()

```python
def file_exists(file_path: Path) -> bool
```

ファイルが存在するかチェック。

#### ensure_directory()

```python
def ensure_directory(dir_path: Path) -> None
```

ディレクトリが存在することを保証する（なければ作成）。

### ファイルスキャン（infrastructure/file_scanner.py）

#### scan_files()

```python
def scan_files(
    directory: Path,
    pattern: str = "*.txt",
    sort: bool = True
) -> List[Path]
```

指定ディレクトリ内のファイルをスキャン。

#### get_files_by_pattern()

```python
def get_files_by_pattern(
    directory: Path,
    pattern: str,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> List[Path]
```

パターンとフィルタ関数でファイルを取得。

#### filter_files_after_number()

```python
def filter_files_after_number(
    files: List[Path],
    threshold: int,
    number_extractor: Callable[[str], Optional[int]]
) -> List[Path]
```

指定番号より大きいファイルのみをフィルタ。

#### count_files()

```python
def count_files(directory: Path, pattern: str = "*.txt") -> int
```

パターンにマッチするファイル数をカウント。

#### get_max_numbered_file()

```python
def get_max_numbered_file(
    directory: Path,
    pattern: str,
    number_extractor: Callable[[str], Optional[int]]
) -> Optional[int]
```

ディレクトリ内の最大番号を取得。

```python
from domain.file_naming import extract_number_only

# Loopファイルの最大番号を取得
max_loop = get_max_numbered_file(
    loops_path,
    "Loop*.txt",
    extract_number_only
)  # 186
```

### ロギング（infrastructure/logging_config.py）

#### get_logger()

```python
def get_logger(name: str = "episodic_rag") -> logging.Logger
```

モジュールロガーを取得。

#### setup_logging()

```python
def setup_logging(level: Optional[int] = None) -> logging.Logger
```

デフォルトのロギング設定をセットアップ。

#### ユーティリティ関数

```python
def log_info(message: str) -> None
def log_warning(message: str) -> None
def log_error(message: str, exit_code: Optional[int] = None) -> None
```

環境変数でログ設定をカスタマイズ可能:
- `EPISODIC_RAG_LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR)
- `EPISODIC_RAG_LOG_FORMAT`: ログフォーマット (simple, detailed)

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

#### validate_dict()

```python
def validate_dict(data: Any, context: str) -> Dict[str, Any]
```

データがdictであることを検証。違反時は`ValidationError`を送出。

#### validate_list()

```python
def validate_list(data: Any, context: str) -> List[Any]
```

データがlistであることを検証。違反時は`ValidationError`を送出。

#### validate_source_files()

```python
def validate_source_files(files: Any, context: str = "source_files") -> List[str]
```

source_filesの形式を検証（listでNone/空でないこと）。

#### is_valid_dict() / is_valid_list()

```python
def is_valid_dict(data: Any) -> bool
def is_valid_list(data: Any) -> bool
```

例外を投げずにboolで型チェック。

#### get_dict_or_default() / get_list_or_default()

```python
def get_dict_or_default(data: Any, default: Optional[Dict] = None) -> Dict[str, Any]
def get_list_or_default(data: Any, default: Optional[List] = None) -> List[Any]
```

型が一致すればそのまま返し、不一致ならデフォルト値を返す。

### Shadow管理（application/shadow/）

#### CascadeProcessor

ダイジェスト確定時のカスケード処理を担当。

```python
class CascadeProcessor:
    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
        file_appender: FileAppender
    ): ...
```

| メソッド | 説明 |
|---------|------|
| `get_shadow_digest_for_level(level: str) -> Optional[OverallDigestData]` | 指定レベルのShadowダイジェストを取得 |
| `promote_shadow_to_grand(level: str) -> None` | ShadowをGrandDigestに昇格（確認のみ） |
| `clear_shadow_level(level: str) -> None` | 指定レベルのShadowを初期化 |
| `cascade_update_on_digest_finalize(level: str) -> None` | ダイジェスト確定時のカスケード処理（処理3） |

**cascade_update_on_digest_finalize処理フロー**:
1. Shadow → Grand 昇格の確認
2. 次のレベルの新しいファイルを検出
3. 次のレベルのShadowに増分追加
4. 現在のレベルのShadowをクリア

#### PlaceholderManager

PLACEHOLDER管理（更新・保持判定）を担当。

```python
class PlaceholderManager:
    def update_or_preserve(
        self,
        overall_digest: OverallDigestData,
        total_files: int
    ) -> None
```

| メソッド | 説明 |
|---------|------|
| `update_or_preserve(overall_digest, total_files) -> None` | PLACEHOLDERの更新または既存分析の保持 |

**動作**:
- `abstract`がPLACEHOLDER（空または`<!-- PLACEHOLDER`を含む）の場合: 新規PLACEHOLDER生成
- それ以外: 既存分析を保持し、再分析を促すログ出力

#### その他のShadowクラス

| クラス | 説明 |
|--------|------|
| `ShadowTemplate` | ShadowGrandDigestテンプレート生成 |
| `FileDetector` | 新規ファイル検出 |
| `ShadowIO` | Shadow読み書き |
| `ShadowUpdater` | Shadow更新処理 |
| `FileAppender` | Shadowへのファイル追加 |

### GrandDigest管理（application/grand/）

| クラス | 説明 |
|--------|------|
| `GrandDigestManager` | GrandDigest.txt CRUD操作 |
| `ShadowGrandDigestManager` | ShadowGrandDigest.txt管理 |

### Finalize処理（application/finalize/）

#### ShadowValidator

ShadowGrandDigestの内容を検証。

```python
class ShadowValidator:
    def __init__(self, shadow_manager: ShadowGrandDigestManager): ...
```

| メソッド | 説明 | 例外 |
|---------|------|------|
| `validate_shadow_content(level: str, source_files: list) -> None` | source_filesの形式・連番を検証 | `ValidationError` |
| `validate_and_get_shadow(level: str, weave_title: str) -> OverallDigestData` | Shadowの検証と取得（メイン） | `ValidationError`, `DigestError` |

**validate_shadow_content検証項目**:
- source_filesがlist型であること
- source_filesが空でないこと
- ファイル名がすべて文字列であること
- ファイル名から番号が抽出できること
- 連番チェック（警告のみ、ユーザー確認で継続可能）

#### ProvisionalLoader

ProvisionalDigestの読み込みまたはソースファイルからの自動生成。

```python
class ProvisionalLoader:
    def __init__(self, config: DigestConfig, shadow_manager: ShadowGrandDigestManager): ...
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `load_or_generate(level, shadow_digest, digest_num) -> Tuple[List[IndividualDigestData], Optional[Path]]` | Provisionalの読み込みまたは自動生成 | (individual_digests, provisional_file_to_delete) |
| `generate_from_source(level, shadow_digest) -> List[IndividualDigestData]` | ソースファイルから自動生成（まだらボケ回避） | individual_digestsのリスト |

**load_or_generate動作**:
1. `{prefix}{digest_num}_Individual.txt`が存在すれば読み込み
2. 存在しなければ`generate_from_source`で自動生成

#### RegularDigestBuilder

RegularDigest構造を構築。

```python
class RegularDigestBuilder:
    @staticmethod
    def build(
        level: str,
        new_digest_name: str,
        digest_num: str,
        shadow_digest: OverallDigestData,
        individual_digests: List[IndividualDigestData]
    ) -> RegularDigestData
```

**出力構造**:
```python
{
    "metadata": {
        "digest_level": level,
        "digest_number": digest_num,
        "last_updated": datetime.now().isoformat(),
        "version": DIGEST_FORMAT_VERSION
    },
    "overall_digest": {
        "name": new_digest_name,
        "timestamp": datetime.now().isoformat(),
        "source_files": source_files,
        "digest_type": shadow_digest.get("digest_type", "統合"),
        "keywords": shadow_digest.get("keywords", []),
        "abstract": shadow_digest.get("abstract", ""),
        "impression": shadow_digest.get("impression", "")
    },
    "individual_digests": individual_digests
}
```

#### DigestPersistence

RegularDigestの保存、GrandDigest更新、カスケード処理を担当。

```python
class DigestPersistence:
    def __init__(
        self,
        config: DigestConfig,
        grand_digest_manager: GrandDigestManager,
        shadow_manager: ShadowGrandDigestManager,
        times_tracker: DigestTimesTracker
    ): ...
```

| メソッド | 説明 | 例外 |
|---------|------|------|
| `save_regular_digest(level, regular_digest, new_digest_name) -> Path` | RegularDigestをファイルに保存 | `FileIOError`, `ValidationError`（上書きキャンセル時） |
| `update_grand_digest(level, regular_digest, new_digest_name) -> None` | GrandDigestを更新 | `DigestError` |
| `process_cascade_and_cleanup(level, source_files, provisional_file_to_delete) -> None` | カスケード処理とProvisional削除 | - |

**save_regular_digest動作**:
1. 既存ファイルがあれば上書き確認（対話/非対話モード対応）
2. `{digests_path}/{level_dir}/{new_digest_name}.txt`に保存

### 時間追跡（application/tracking/）

#### DigestTimesTracker

last_digest_times.json管理クラス。

```python
class DigestTimesTracker:
    def __init__(self, config: DigestConfig): ...
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `load_or_create() -> DigestTimesData` | 最終ダイジェスト生成時刻を読み込み | DigestTimesData |
| `extract_file_numbers(level, input_files) -> List[str]` | ファイル名から連番を抽出（ゼロ埋め維持） | プレフィックス付き連番リスト |
| `save(level, input_files=None) -> None` | 最終生成時刻と処理済みファイル番号を保存 | - |

**save動作**:
1. 既存データを読み込み
2. `input_files`から最後のファイル番号を抽出
3. `{level: {timestamp: ISO8601, last_processed: "W0005"}}`形式で保存

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
sanitize_filename("技術探求/AI")        # "技術探求AI" (危険文字は削除)
sanitize_filename("技術 探求 AI")       # "技術_探求_AI" (空白は_に変換)
sanitize_filename("")                   # "untitled"
```

#### get_next_digest_number()

```python
def get_next_digest_number(digests_path: Path, level: str) -> int
```

指定レベルの次のDigest番号を取得。

---

## config.json 詳細仕様

> 📖 クイックリファレンスは [GUIDE.md](../user/GUIDE.md#設定ファイル仕様クイックリファレンス) を参照

### 設定ファイルの場所

`~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/.claude-plugin/config.json`

### 設定項目詳細

#### base_dir

パス解決の基準ディレクトリ（プラグインルートからの相対パス）

**デフォルト**: `.` (プラグインルート自身)

**設定例：**
- `"."` (デフォルト): プラグインルート自身を基準とする（完全自己完結型）
- `"../../.."`: 3階層上を基準とする（例: DEVルート基準でデータを共有）
- `"../.."`: 2階層上

**パス解決の仕組み:**
```
最終的なパス = {plugin_root} / {base_dir} / {paths.*_dir}

例:
plugin_root = ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
base_dir = "../../.."
loops_dir = "homunculus/Weave/EpisodicRAG/Loops"

最終パス = {plugin_root}/../../.. / homunculus/Weave/EpisodicRAG/Loops
         = {DEV}/homunculus/Weave/EpisodicRAG/Loops
```

**注意:**
- 絶対パスは使用しないでください（Git公開時の可搬性のため）
- 相対パスはプラグインルート基準で解釈されます

---

#### paths設定

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| `loops_dir` | Loopファイル配置先 | `data/Loops` |
| `digests_dir` | Digest出力先 | `data/Digests` |
| `essences_dir` | GrandDigest配置先 | `data/Essences` |
| `identity_file_path` | 外部identityファイルのパス（オプション） | `null` |

**digests_dir サブディレクトリ構造:**
自動的に8階層のサブディレクトリが作成されます：
- `1_Weekly`, `2_Monthly`, `3_Quarterly`, `4_Annual`, `5_Triennial`, `6_Decadal`, `7_Multi-decadal`, `8_Centurial`
- 各階層に `Provisional/` サブディレクトリ（一時作業用）

**Provisionalファイル命名規則:**

| 階層 | プレフィックス | 桁数 | ファイル名例 |
|------|---------------|------|-------------|
| Weekly | W | 4 | `W0001_Individual.txt` |
| Monthly | M | 3 | `M001_Individual.txt` |
| Quarterly | Q | 3 | `Q001_Individual.txt` |
| Annual | A | 2 | `A01_Individual.txt` |
| Triennial | T | 2 | `T01_Individual.txt` |
| Decadal | D | 2 | `D01_Individual.txt` |
| Multi-decadal | MD | 2 | `MD01_Individual.txt` |
| Centurial | C | 2 | `C01_Individual.txt` |

---

#### levels設定（Threshold）

各階層のDigestを生成するために必要な最小ファイル数を設定します。

| 階層 | 設定項目 | デフォルト | 説明 |
|------|----------|-----------|------|
| Weekly | `weekly_threshold` | 5 | 5つのLoopファイルでWeekly Digest生成 |
| Monthly | `monthly_threshold` | 5 | 5つのWeekly DigestでMonthly Digest生成 |
| Quarterly | `quarterly_threshold` | 3 | 3つのMonthly DigestでQuarterly Digest生成 |
| Annual | `annual_threshold` | 4 | 4つのQuarterly DigestでAnnual Digest生成 |
| Triennial | `triennial_threshold` | 3 | 3つのAnnual DigestでTriennial Digest生成 |
| Decadal | `decadal_threshold` | 3 | 3つのTriennial DigestでDecadal Digest生成 |
| Multi-decadal | `multi_decadal_threshold` | 3 | 3つのDecadal DigestでMulti-decadal Digest生成 |
| Centurial | `centurial_threshold` | 4 | 4つのMulti-decadal DigestでCenturial Digest生成 |

---

### よくある設定パターン

#### パターン1: 完全自己完結（推奨）

プラグインをクリーンに管理したい場合：

```json
{
  "base_dir": ".",
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": {
    "weekly_threshold": 5,
    "monthly_threshold": 5,
    "quarterly_threshold": 3,
    "annual_threshold": 4,
    "triennial_threshold": 3,
    "decadal_threshold": 3,
    "multi_decadal_threshold": 3,
    "centurial_threshold": 4
  }
}
```

#### パターン2: 外部ディレクトリ統合型

既存プロジェクトのデータを共有する場合：

```json
{
  "base_dir": "../../..",
  "paths": {
    "loops_dir": "homunculus/Weave/EpisodicRAG/Loops",
    "digests_dir": "homunculus/Weave/EpisodicRAG/Digests",
    "essences_dir": "homunculus/Weave/EpisodicRAG/Essences",
    "identity_file_path": "homunculus/Weave/Identities/UserIdentity.md"
  },
  "levels": { ... }
}
```

---

## 設定（config/__init__.py）

### DigestConfig クラス

```python
class DigestConfig:
    def __init__(self, plugin_root: Optional[Path] = None): ...
```

#### プロパティ（パス関連）

> 📖 パス用語の定義は [GLOSSARY.md](../GLOSSARY.md#基本概念) を参照

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

### config モジュール

```bash
cd scripts

# 設定をJSON形式で表示
python -m config

# パス設定を表示
python -m config --show-paths

# プラグインルートを指定
python -m config --plugin-root /path/to/plugin
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
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
