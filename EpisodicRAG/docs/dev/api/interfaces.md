[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Interfaces

# Interfaces層 API

外部からのエントリーポイント。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number
```

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

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
