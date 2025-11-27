[Home](../README.md) > [Docs](README.md) > API_REFERENCE

# API リファレンス

EpisodicRAGプラグインのPython API仕様書です。

---

## 定数

### LEVEL_CONFIG

階層ごとの設定を定義する辞書。Single Source of Truth（唯一の真実の情報源）として、すべてのスクリプトから参照されます。

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

**フィールド説明**:

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `prefix` | ファイル名プレフィックス | `W`, `M`, `MD` |
| `digits` | 番号の桁数 | `4` (W0001) |
| `dir` | digests_path以下のサブディレクトリ名 | `1_Weekly` |
| `source` | この階層を生成する際の入力元 | `loops`, `weekly` |
| `next` | 確定時にカスケードする上位階層 | `monthly`, `None` |

### LEVEL_NAMES

階層名のリスト。

```python
LEVEL_NAMES = ["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "multi_decadal", "centurial"]
```

### PLACEHOLDER_LIMITS

プレースホルダー文字数制限（Claudeへのガイドライン）。

```python
PLACEHOLDER_LIMITS: Dict[str, int] = {
    "abstract_chars": 2400,      # abstract（全体統合分析）の文字数
    "impression_chars": 800,     # impression（所感・展望）の文字数
    "keyword_count": 5,          # キーワードの個数
}
```

### PLACEHOLDER_MARKER / PLACEHOLDER_END / PLACEHOLDER_SIMPLE

プレースホルダー検出用のマーカー定数。ShadowGrandDigest内の未分析状態を示します。

```python
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER"
PLACEHOLDER_END = " -->"
PLACEHOLDER_SIMPLE = "<!-- PLACEHOLDER -->"  # PLACEHOLDER_MARKER + PLACEHOLDER_END
```

**使用例**:
```python
from config import PLACEHOLDER_MARKER

# プレースホルダーかどうかを判定
if PLACEHOLDER_MARKER in abstract:
    print("未分析状態です")
```

---

## 関数

### extract_file_number()

ファイル名からプレフィックスと番号を抽出。

```python
def extract_file_number(filename: str) -> Optional[Tuple[str, int]]
```

**パラメータ**:
- `filename`: ファイル名（例: `"Loop0186_xxx.txt"`, `"MD01_xxx.txt"`）

**戻り値**:
- `(prefix, number)` のタプル、またはマッチしない場合は `None`

**例**:
```python
extract_file_number("Loop0186_認知アーキテクチャ.txt")  # ("Loop", 186)
extract_file_number("W0001_Individual.txt")             # ("W", 1)
extract_file_number("MD01_xxx.txt")                     # ("MD", 1)
extract_file_number("invalid.txt")                      # None
```

### extract_number_only()

番号のみを抽出（後方互換性用）。

```python
def extract_number_only(filename: str) -> Optional[int]
```

**パラメータ**:
- `filename`: ファイル名

**戻り値**:
- 番号（int）、またはマッチしない場合は `None`

### format_digest_number()

レベルと番号から統一されたフォーマットの文字列を生成。

```python
def format_digest_number(level: str, number: int) -> str
```

**パラメータ**:
- `level`: 階層名（`loop`, `weekly`, `monthly`, ...）
- `number`: 番号

**戻り値**:
- ゼロ埋めされた文字列（例: `Loop0186`, `W0001`, `MD01`）

**例外**:
- `ValueError`: 不正なレベル名の場合

**例**:
```python
format_digest_number("loop", 186)         # "Loop0186"
format_digest_number("weekly", 1)         # "W0001"
format_digest_number("monthly", 12)       # "M012"
format_digest_number("multi_decadal", 3)  # "MD03"
```

---

## クラス: DigestConfig

設定管理クラス（Plugin自己完結版）。

### コンストラクタ

```python
def __init__(self, plugin_root: Optional[Path] = None)
```

**パラメータ**:
- `plugin_root`: Pluginルート（省略時は自動検出）

**例外**:
- `FileNotFoundError`: 設定ファイルが見つからない場合

**例**:
```python
from config import DigestConfig

# 自動検出
config = DigestConfig()

# 明示的にプラグインルートを指定
config = DigestConfig(plugin_root=Path("/path/to/plugin"))
```

### プロパティ

#### パス関連

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `plugin_root` | `Path` | プラグインルートディレクトリ |
| `config_file` | `Path` | 設定ファイルのパス |
| `base_dir` | `Path` | 解決された基準ディレクトリ |
| `loops_path` | `Path` | Loopファイル配置先 |
| `digests_path` | `Path` | Digest出力先 |
| `essences_path` | `Path` | GrandDigest配置先 |

#### 閾値関連

| プロパティ | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `weekly_threshold` | `int` | 5 | Weekly生成に必要なLoop数 |
| `monthly_threshold` | `int` | 5 | Monthly生成に必要なWeekly数 |
| `quarterly_threshold` | `int` | 3 | Quarterly生成に必要なMonthly数 |
| `annual_threshold` | `int` | 4 | Annual生成に必要なQuarterly数 |
| `triennial_threshold` | `int` | 3 | Triennial生成に必要なAnnual数 |
| `decadal_threshold` | `int` | 3 | Decadal生成に必要なTriennial数 |
| `multi_decadal_threshold` | `int` | 3 | Multi-decadal生成に必要なDecadal数 |
| `centurial_threshold` | `int` | 4 | Centurial生成に必要なMulti-decadal数 |

### メソッド

#### resolve_path()

相対パスを絶対パスに解決（base_dir基準）。

```python
def resolve_path(self, key: str) -> Path
```

**パラメータ**:
- `key`: paths以下のキー（`loops_dir`, `digests_dir`, `essences_dir`）

**戻り値**:
- 解決された絶対Path

**例外**:
- `KeyError`: pathsセクションまたはキーが存在しない場合

#### get_level_dir()

指定レベルのRegularDigest格納ディレクトリを取得。

```python
def get_level_dir(self, level: str) -> Path
```

**パラメータ**:
- `level`: 階層名（`weekly`, `monthly`, ...）

**戻り値**:
- RegularDigest格納ディレクトリの絶対Path

**例外**:
- `ValueError`: 不正なレベル名の場合

**例**:
```python
config.get_level_dir("weekly")  # digests_path/1_Weekly
```

#### get_provisional_dir()

指定レベルのProvisionalDigest格納ディレクトリを取得。

```python
def get_provisional_dir(self, level: str) -> Path
```

**パラメータ**:
- `level`: 階層名（`weekly`, `monthly`, ...）

**戻り値**:
- ProvisionalDigest格納ディレクトリの絶対Path

**例**:
```python
config.get_provisional_dir("weekly")  # digests_path/1_Weekly/Provisional
```

#### get_threshold()

指定レベルのthresholdを動的に取得。

```python
def get_threshold(self, level: str) -> int
```

**パラメータ**:
- `level`: 階層名

**戻り値**:
- そのレベルのthreshold値

#### get_identity_file_path()

外部identityファイルのパスを取得。

```python
def get_identity_file_path(self) -> Optional[Path]
```

**戻り値**:
- identityファイルの絶対Path（設定されていない場合は`None`）

#### show_paths()

パス設定を表示（デバッグ用）。

```python
def show_paths(self) -> None
```

#### validate_directory_structure()

ディレクトリ構造の検証。

```python
def validate_directory_structure(self) -> list
```

**戻り値**:
- エラーメッセージのリスト（問題がなければ空リスト）

**検証内容**:
- `loops_path`, `digests_path`, `essences_path` の存在
- 各レベルディレクトリ（1_Weekly, 2_Monthly, ...）の存在
- 各レベルディレクトリ内の `Provisional/` の存在

**例**:
```python
errors = config.validate_directory_structure()
if errors:
    for err in errors:
        print(f"Error: {err}")
```

---

## utils.py 関数

### log_error()

エラーメッセージを出力。

```python
def log_error(message: str, exit_code: Optional[int] = None) -> None
```

**パラメータ**:
- `message`: エラーメッセージ
- `exit_code`: 指定時はこのコードでプログラムを終了

### log_warning()

警告メッセージを出力。

```python
def log_warning(message: str) -> None
```

### log_info()

情報メッセージを出力。

```python
def log_info(message: str) -> None
```

### sanitize_filename()

ファイル名として安全な文字列に変換。

```python
def sanitize_filename(title: str, max_length: int = 50) -> str
```

**パラメータ**:
- `title`: 元のタイトル文字列
- `max_length`: 最大文字数（デフォルト: 50）

**戻り値**:
- ファイル名として安全な文字列（空の場合は `"untitled"`）

### load_json_with_template()

JSONファイルを読み込む。存在しない場合はテンプレートまたはデフォルトから作成。

```python
def load_json_with_template(
    target_file: Path,
    template_file: Optional[Path] = None,
    default_factory: Optional[Callable[[], Dict[str, Any]]] = None,
    save_on_create: bool = True,
    log_message: Optional[str] = None
) -> Dict[str, Any]
```

### save_json()

dictをJSONファイルに保存（親ディレクトリ自動作成）。

```python
def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None
```

### get_next_digest_number()

指定レベルの次のDigest番号を取得。

```python
def get_next_digest_number(digests_path: Path, level: str) -> int
```

**パラメータ**:
- `digests_path`: Digestsディレクトリのパス
- `level`: Digestレベル

**戻り値**:
- 次の番号（1始まり）

---

## スクリプト一覧

| スクリプト | 役割 | 主要関数/クラス |
|-----------|------|----------------|
| `config.py` | 設定管理 | `DigestConfig`, `extract_file_number()`, `format_digest_number()`, `LEVEL_CONFIG`, `PLACEHOLDER_*` |
| `utils.py` | ユーティリティ | `sanitize_filename()`, `log_error()`, `log_warning()`, `log_info()`, `load_json_with_template()`, `save_json()`, `get_next_digest_number()` |
| `grand_digest.py` | GrandDigest管理 | `GrandDigestManager` |
| `shadow_grand_digest.py` | Shadow管理 | `ShadowGrandDigestManager` |
| `digest_times.py` | 時刻追跡 | `DigestTimesTracker` |
| `finalize_from_shadow.py` | ダイジェスト確定 | `DigestFinalizerFromShadow` |
| `save_provisional_digest.py` | Provisional保存 | `ProvisionalDigestSaver` |

---

## CLI使用方法

### config.py

```bash
# 設定をJSON形式で表示
python scripts/config.py

# パス設定を表示
python scripts/config.py --show-paths

# プラグインルートを明示的に指定
python scripts/config.py --plugin-root /path/to/plugin --show-paths
```

**出力例（--show-paths）**:
```
Plugin Root: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
Config File: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/.claude-plugin/config.json
Base Dir (setting): .
Base Dir (resolved): ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
Loops Path: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/data/Loops
Digests Path: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/data/Digests
Essences Path: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/data/Essences
```

---

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様・データフロー
- [GLOSSARY.md](GLOSSARY.md) - 用語集
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発参加ガイド

---
