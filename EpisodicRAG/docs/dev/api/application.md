[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Application

# Application層 API

ビジネスロジックの実装。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from application.shadow import ShadowTemplate, ShadowUpdater
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from application.validators import validate_dict, is_valid_list
```

---

## 目次

1. [バリデーション（validators.py）](#バリデーションapplicationvalidatorspy)
2. [Shadow管理（shadow/）](#shadow管理applicationshadow)
3. [GrandDigest管理（grand/）](#granddigest管理applicationgrand)
4. [Finalize処理（finalize/）](#finalize処理applicationfinalize)
5. [時間追跡（tracking/）](#時間追跡applicationtracking)

---

## バリデーション（application/validators.py）

データ型検証の共通関数群。重複する`isinstance`チェックを統一し、一貫したエラーメッセージを提供。

### validate_dict()

```python
def validate_dict(data: Any, context: str) -> Dict[str, Any]
```

データがdictであることを検証。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `data` | `Any` | 検証対象のデータ |
| `context` | `str` | エラーメッセージに含める文脈情報（例: `"config.json"`） |

| 戻り値 | 説明 |
|--------|------|
| `Dict[str, Any]` | 検証済みのdict |

| 例外 | 発生条件 |
|------|----------|
| `ValidationError` | `data`がdictでない場合 |

**使用例**:
```python
from application.validators import validate_dict

raw_data = load_some_json()
config = validate_dict(raw_data, "config.json")  # 失敗時はValidationError
```

### validate_list()

```python
def validate_list(data: Any, context: str) -> List[Any]
```

データがlistであることを検証。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `data` | `Any` | 検証対象のデータ |
| `context` | `str` | エラーメッセージに含める文脈情報 |

| 戻り値 | 説明 |
|--------|------|
| `List[Any]` | 検証済みのlist |

| 例外 | 発生条件 |
|------|----------|
| `ValidationError` | `data`がlistでない場合 |

### validate_source_files()

```python
def validate_source_files(files: Any, context: str = "source_files") -> List[str]
```

source_filesの形式を検証。

| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `files` | `Any` | - | 検証対象のデータ |
| `context` | `str` | `"source_files"` | エラーメッセージに含める文脈情報 |

| 戻り値 | 説明 |
|--------|------|
| `List[str]` | 検証済みのファイルリスト |

| 例外 | 発生条件 |
|------|----------|
| `ValidationError` | `files`がNone、listでない、または空の場合 |

**使用例**:
```python
from application.validators import validate_source_files

files = validate_source_files(shadow_digest.get("source_files"))
# files: ["L00001_xxx.txt", "L00002_yyy.txt"]
```

### is_valid_dict() / is_valid_list()

```python
def is_valid_dict(data: Any) -> bool
def is_valid_list(data: Any) -> bool
```

例外を投げずにboolで型チェック。条件分岐での使用に適している。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `data` | `Any` | 検証対象のデータ |

| 戻り値 | 説明 |
|--------|------|
| `bool` | `data`が期待する型なら`True` |

**使用例**:
```python
from application.validators import is_valid_dict, is_valid_list

if is_valid_dict(data):
    process_dict(data)
elif is_valid_list(data):
    process_list(data)
```

### get_dict_or_default() / get_list_or_default()

```python
def get_dict_or_default(data: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
def get_list_or_default(data: Any, default: Optional[List[Any]] = None) -> List[Any]
```

型が一致すればそのまま返し、不一致ならデフォルト値を返す。

| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `data` | `Any` | - | 検証対象のデータ |
| `default` | `Optional[Dict]` / `Optional[List]` | `None`（空のdict/list） | 型不一致時の戻り値 |

| 戻り値 | 説明 |
|--------|------|
| `Dict[str, Any]` / `List[Any]` | `data`が期待する型なら`data`、そうでなければ`default` |

**使用例**:
```python
from application.validators import get_dict_or_default

# Noneや不正な型でも安全に空dictを取得
keywords = get_dict_or_default(raw_data.get("keywords"), {})
```

---

## Shadow管理（application/shadow/）

### CascadeProcessor

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

### PlaceholderManager

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

### FileAppender

Shadowへのファイル追加を担当。

```python
class FileAppender:
    def __init__(
        self,
        shadow_io: ShadowIO,
        placeholder_manager: PlaceholderManager,
        level_hierarchy: Dict[str, LevelHierarchyEntry]
    ): ...

    def append_files_to_level(self, level: str, files: List[Path]) -> None
```

| メソッド | 説明 |
|---------|------|
| `append_files_to_level(level, files) -> None` | 指定レベルのShadowに新規ファイルを追加 |

**動作**:
1. 現在のShadowデータを読み込み
2. 既存の`source_files`に新規ファイルを追加
3. PlaceholderManagerで`overall_digest`を更新
4. Shadowファイルに保存

### ShadowTemplate

ShadowGrandDigestのテンプレート生成。

```python
class ShadowTemplate:
    def __init__(self, levels: List[str]): ...

    def create_empty_overall_digest(self) -> OverallDigestData
    def get_template(self) -> ShadowDigestData
```

### FileDetector

新規ファイルの検出。

```python
class FileDetector:
    def __init__(self, config: DigestConfig, times_tracker: DigestTimesTracker): ...

    def get_max_file_number(self, level: str) -> Optional[int]
    def get_source_path(self, level: str) -> Path
    def find_new_files(self, level: str) -> List[Path]
```

| メソッド | 説明 |
|---------|------|
| `find_new_files(level) -> List[Path]` | 最後の処理以降に追加されたファイルを検出 |
| `get_source_path(level) -> Path` | レベルの入力元ディレクトリを取得 |

### ShadowIO

Shadow読み書き操作。

```python
class ShadowIO:
    def __init__(
        self,
        shadow_digest_file: Path,
        template_factory: Callable[[], ShadowDigestData]
    ): ...

    def load_or_create(self) -> ShadowDigestData
    def save(self, data: ShadowDigestData) -> None
```

### ShadowUpdater

Shadow更新処理のFacade。

```python
class ShadowUpdater:
    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry]
    ): ...

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None
    def clear_shadow_level(self, level: str) -> None
    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]
    def promote_shadow_to_grand(self, level: str) -> None
    def update_shadow_for_new_loops(self) -> None
```

---

## GrandDigest管理（application/grand/）

### GrandDigestManager

GrandDigest.txt の CRUD操作を担当。

```python
class GrandDigestManager:
    def __init__(self, config: DigestConfig): ...
```

| メソッド | 説明 | 例外 |
|---------|------|------|
| `get_template() -> GrandDigestData` | テンプレート生成（全8レベル対応） | - |
| `load_or_create() -> GrandDigestData` | 読み込みまたは新規作成 | `FileIOError` |
| `save(data: GrandDigestData) -> None` | GrandDigest.txtを保存 | `FileIOError` |
| `update_digest(level, digest_name, overall_digest) -> None` | 指定レベルのダイジェスト更新 | `DigestError` |

**使用例**:

```python
from application.grand import GrandDigestManager
from config import DigestConfig

config = DigestConfig()
manager = GrandDigestManager(config)

# テンプレート取得
template = manager.get_template()

# 読み込みまたは作成
data = manager.load_or_create()

# ダイジェスト更新
manager.update_digest("weekly", "W0001_タイトル", overall_digest_data)
```

### ShadowGrandDigestManager

ShadowGrandDigest.txt 管理のFacade。Shadow更新・カスケード処理を統括。

```python
class ShadowGrandDigestManager:
    def __init__(self, config: Optional[DigestConfig] = None): ...
```

| メソッド | 説明 |
|---------|------|
| `add_files_to_shadow(level, new_files) -> None` | Shadowに新規ファイル追加（増分更新） |
| `clear_shadow_level(level) -> None` | 指定レベルのShadow初期化 |
| `get_shadow_digest_for_level(level) -> Optional[OverallDigestData]` | Shadowダイジェスト取得 |
| `promote_shadow_to_grand(level) -> None` | Shadow→Grand昇格 |
| `update_shadow_for_new_loops() -> None` | 新規Loop検出→weekly Shadow更新 |
| `cascade_update_on_digest_finalize(level) -> None` | 確定時カスケード処理 |

**使用例**:

```python
from application.grand import ShadowGrandDigestManager
from config import DigestConfig

config = DigestConfig()
manager = ShadowGrandDigestManager(config)

# 新しいLoopファイルを検出してShadowを更新
manager.update_shadow_for_new_loops()

# Weeklyダイジェスト確定時のカスケード処理
manager.cascade_update_on_digest_finalize("weekly")

# 指定レベルのShadowダイジェストを取得
shadow = manager.get_shadow_digest_for_level("weekly")
```

---

## Finalize処理（application/finalize/）

### ShadowValidator

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

### ProvisionalLoader

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

### RegularDigestBuilder

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

### DigestPersistence

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

---

## 時間追跡（application/tracking/）

### DigestTimesTracker

`last_digest_times.json` 管理クラス。各レベルの最終処理ファイル番号を追跡。

```python
class DigestTimesTracker:
    def __init__(self, config: DigestConfig): ...
```

**コンストラクタ引数**:

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `config` | `DigestConfig` | 設定オブジェクト |

**インスタンス属性**:

| 属性 | 型 | 説明 |
|------|------|------|
| `last_digest_file` | `Path` | `{plugin_root}/.claude-plugin/last_digest_times.json` |
| `template_file` | `Path` | `{plugin_root}/.claude-plugin/last_digest_times.template.json` |

---

#### load_or_create()

```python
def load_or_create(self) -> DigestTimesData
```

最終ダイジェスト生成時刻を読み込む。存在しなければテンプレートから初期化。

| 戻り値 | 説明 |
|--------|------|
| `DigestTimesData` | レベル別の最終処理情報 |

**DigestTimesData構造**:
```python
{
    "weekly": {"timestamp": "2025-11-28T12:00:00", "last_processed": 5},
    "monthly": {"timestamp": "", "last_processed": None},
    # ... 全8レベル
}
```

---

#### extract_file_numbers()

```python
def extract_file_numbers(self, level: str, input_files: Optional[List[str]]) -> List[str]
```

ファイル名から連番を抽出（プレフィックス付き、ゼロ埋め維持）。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `level` | `str` | ダイジェストレベル（将来の拡張用） |
| `input_files` | `Optional[List[str]]` | ファイル名のリスト |

| 戻り値 | 説明 |
|--------|------|
| `List[str]` | 抽出・フォーマットされた連番リスト（無効な入力は空リスト） |

**使用例**:
```python
tracker = DigestTimesTracker(config)
numbers = tracker.extract_file_numbers("weekly", ["L00001_xxx.txt", "L00005_yyy.txt"])
# numbers: ["L00001", "L00005"]
```

---

#### save()

```python
def save(self, level: str, input_files: Optional[List[str]] = None) -> None
```

最終生成時刻と最新処理済みファイル番号を保存。

| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `level` | `str` | - | ダイジェストレベル |
| `input_files` | `Optional[List[str]]` | `None` | 処理したファイル名のリスト |

**動作フロー**:
1. 既存データを読み込み
2. `input_files`から最後のファイル番号を抽出
3. 現在時刻とともに保存

**保存形式**:
```python
{
    "weekly": {
        "timestamp": "2025-11-28T12:00:00",
        "last_processed": 5  # 最後に処理したファイル番号（int）
    }
}
```

**使用例**:
```python
tracker = DigestTimesTracker(config)
tracker.save("weekly", ["L00001_xxx.txt", "L00002_yyy.txt", "L00005_zzz.txt"])
# last_processed = 5
```

---

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
