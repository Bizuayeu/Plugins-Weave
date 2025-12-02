[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Infrastructure

# Infrastructure層 API

外部関心事（ファイルI/O、ロギング）。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from infrastructure import (
    # JSON操作
    load_json, save_json, load_json_with_template, file_exists, ensure_directory,
    try_load_json, try_read_json_from_file, confirm_file_overwrite,
    # ファイルスキャン
    scan_files, get_files_by_pattern, get_max_numbered_file, filter_files_after_number, count_files,
    # ロギング
    get_logger, setup_logging, log_info, log_warning, log_error, log_debug,
    # 構造化ロギング
    StructuredLogger, get_structured_logger,
    # エラーハンドリング
    safe_file_operation, safe_cleanup, with_error_context,
    # ユーザーインタラクション
    get_default_confirm_callback,
)

# 設定管理（別サブパッケージ）
from infrastructure.config import (
    ConfigLoader, PathResolver, find_plugin_root, load_config,
)
```

---

## 目次

**ファイル操作**
- [JSON操作](#json操作infrastructurejson_repository) - 読み書き、テンプレート
- [ファイルスキャン](#ファイルスキャンinfrastructurefile_scannerpy) - 検索、フィルタ

**ロギング**
- [基本ロギング](#基本ロギングinfrastructurelogging_configpy) - `log_info()`, `log_error()` 等
- [構造化ロギング](#構造化ロギングinfrastructurestructured_loggingpy) - セマンティックログ（STATE, FILE等）

**エラー・設定・その他**
- [エラーハンドリング](#エラーハンドリングinfrastructureerror_handlingpy) - 安全なファイル操作
- [設定管理](#設定管理infrastructureconfig) - ConfigLoader, PathResolver *(v4.0.0+)*
- [ユーザーインタラクション](#ユーザーインタラクションinfrastructureuser_interactionpy) - 確認コールバック

---

## JSON操作（infrastructure/json_repository/）

> パッケージ構造: `operations.py`（基本操作）、`load_strategy.py`（Strategy Pattern）、`chained_loader.py`（Chain of Responsibility）

### load_json()

```python
def load_json(file_path: Path) -> Dict[str, Any]
```

JSONファイルを読み込む。

### save_json()

```python
def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None
```

dictをJSONファイルに保存（親ディレクトリ自動作成）。

### load_json_with_template()

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

### file_exists()

```python
def file_exists(file_path: Path) -> bool
```

ファイルが存在するかチェック。

### ensure_directory()

```python
def ensure_directory(dir_path: Path) -> None
```

ディレクトリが存在することを保証する（なければ作成）。

### try_load_json()

```python
def try_load_json(
    file_path: Path,
    default: Optional[Dict[str, Any]] = None,
    log_on_error: bool = True
) -> Optional[Dict[str, Any]]
```

JSONファイルを安全に読み込む。エラー時はデフォルト値を返す（グレースフルデグラデーション用）。

```python
# ファイルがなければ空dictを返す
data = try_load_json(path, default={})

# ファイルがなければNoneを返す
data = try_load_json(path)
if data is None:
    # 初期化処理
```

### try_read_json_from_file()

```python
def try_read_json_from_file(file_path: Path) -> Optional[Dict[str, Any]]
```

ファイルからJSON読み込みを試行（`try_load_json`のエイリアス）。

### confirm_file_overwrite()

```python
def confirm_file_overwrite(file_path: Path, force: bool = False) -> bool
```

ファイルの上書き可否を判定。既存ファイルがなければTrue、あればforceフラグに従う。

```python
# 使用例
if not confirm_file_overwrite(Path("output.txt")):
    raise FileIOError("File already exists")

# 強制上書き
confirm_file_overwrite(Path("output.txt"), force=True)  # 常にTrue
```

---

## ファイルスキャン（infrastructure/file_scanner.py）

### scan_files()

```python
def scan_files(
    directory: Path,
    pattern: str = "*.txt",
    sort: bool = True
) -> List[Path]
```

指定ディレクトリ内のファイルをスキャン。

### get_files_by_pattern()

```python
def get_files_by_pattern(
    directory: Path,
    pattern: str,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> List[Path]
```

パターンとフィルタ関数でファイルを取得。

### filter_files_after_number()

```python
def filter_files_after_number(
    files: List[Path],
    threshold: int,
    number_extractor: Callable[[str], Optional[int]]
) -> List[Path]
```

指定番号より大きいファイルのみをフィルタ。

### count_files()

```python
def count_files(directory: Path, pattern: str = "*.txt") -> int
```

パターンにマッチするファイル数をカウント。

### get_max_numbered_file()

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
    "L*.txt",
    extract_number_only
)  # 186
```

---

## 基本ロギング（infrastructure/logging_config.py）

### get_logger()

```python
def get_logger(name: str = "episodic_rag") -> logging.Logger
```

モジュールロガーを取得。

### setup_logging()

```python
def setup_logging(level: Optional[int] = None) -> logging.Logger
```

デフォルトのロギング設定をセットアップ。

### ユーティリティ関数

```python
def log_info(message: str) -> None
def log_warning(message: str) -> None
def log_error(message: str, exit_code: Optional[int] = None) -> None
def log_debug(message: str) -> None
```

環境変数でログ設定をカスタマイズ可能:
- `EPISODIC_RAG_LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR)
- `EPISODIC_RAG_LOG_FORMAT`: ログフォーマット (simple, detailed)

---

## 構造化ロギング（infrastructure/structured_logging.py）

LOG_PREFIX_* 定数を使用したボイラープレートを統合し、一貫したログ出力を提供。

### get_structured_logger()

```python
def get_structured_logger(name: str) -> StructuredLogger
```

構造化ロガーのインスタンスを取得。

```python
logger = get_structured_logger(__name__)
logger.state("cascade_update", level="weekly", count=5)
# -> [DEBUG] [STATE] cascade_update: level=weekly count=5
```

### StructuredLogger

```python
class StructuredLogger:
    def info(message: str) -> None          # 一般的な情報ログ
    def state(message: str, **context) -> None     # 状態変化のログ [STATE]
    def file_op(message: str, **context) -> None   # ファイル操作のログ [FILE]
    def validation(message: str, **context) -> None # 検証処理のログ [VALIDATE]
    def decision(message: str, **context) -> None  # 判断分岐のログ [DECISION]
```

**使用例**:

```python
logger = get_structured_logger(__name__)

# 従来のコード
log_debug(f"{LOG_PREFIX_STATE} cascade_update: level={level}, count={count}")

# 新しいコード
logger.state("cascade_update", level=level, count=count)
```

---

## エラーハンドリング（infrastructure/error_handling.py）

ファイル操作等のエラー処理を統一するユーティリティ関数。

### safe_file_operation()

```python
def safe_file_operation(
    operation: Callable[[], T],
    context: str,
    on_error: Optional[Callable[[Exception], T]] = None,
    *,
    reraise: bool = False,
) -> Optional[T]
```

ファイル操作を安全に実行するラッパー。一般的なファイルI/Oエラーをキャッチし、一貫した方法で処理する。

```python
# 基本的な使用（エラーを無視）
safe_file_operation(lambda: file_path.unlink(), "delete file")

# フォールバック付き
result = safe_file_operation(
    lambda: load_json(path),
    "load config",
    on_error=lambda e: {}
)

# エラーを再送出
safe_file_operation(
    lambda: save_json(path, data),
    "save config",
    reraise=True
)
```

### safe_cleanup()

```python
def safe_cleanup(
    cleanup_func: Callable[[], None],
    context: str,
    *,
    log_on_error: bool = True,
) -> bool
```

クリーンアップ操作を安全に実行する。エラーが発生しても処理を継続し、オプションで警告をログ出力。

```python
success = safe_cleanup(
    lambda: temp_file.unlink(),
    "remove temporary file"
)
if not success:
    print("Cleanup failed but continuing...")
```

### with_error_context()

```python
def with_error_context(
    operation: Callable[[], T],
    context: str,
    error_type: type = FileIOError,
) -> T
```

操作を実行し、エラー時にコンテキスト付きの例外を送出。

```python
data = with_error_context(
    lambda: json.load(f),
    "parsing config.json"
)
```

---

## 設定管理（infrastructure/config/）

> v4.0.0で追加。設定ファイルI/O・パス解決を担当。
> アクセス: `from infrastructure.config import ...`

### find_plugin_root()

```python
def find_plugin_root(script_path: Path) -> Path
```

起点パスからPluginルートディレクトリを検出。`.claude-plugin/config.json` が存在するディレクトリを返す。

**例外**: `FileNotFoundError` - Pluginルートが見つからない場合

### load_config()

```python
def load_config(config_file: Path) -> ConfigData
```

設定ファイルをシンプルに読み込む。キャッシュなし。

**例外**: `ConfigError` - ファイル不存在またはJSONパースエラー

### ConfigLoader

設定ファイルの読み込みとキャッシュ管理を担当するクラス。

```python
class ConfigLoader:
    def __init__(self, config_file: Path): ...
    def load(self) -> ConfigData: ...           # キャッシュ付き読み込み
    def reload(self) -> ConfigData: ...         # 強制再読み込み
    def get(self, key: str, default: Any = None) -> Any: ...
    def get_required(self, key: str) -> Any: ...  # 例外発生
    def has_key(self, key: str) -> bool: ...
    def validate_required_keys(self) -> List[str]: ...
    @property
    def is_loaded(self) -> bool: ...
```

**使用例**:

```python
from infrastructure.config import ConfigLoader

loader = ConfigLoader(Path("config.json"))
config = loader.load()
value = loader.get("key", default="default_value")
```

### PathResolver

base_dir基準のパス解決とセキュリティ検証を担当するクラス。

```python
class PathResolver:
    def __init__(self, plugin_root: Path, config: ConfigData): ...
    def resolve_path(self, key: str) -> Path: ...
    @property
    def loops_path(self) -> Path: ...
    @property
    def digests_path(self) -> Path: ...
    @property
    def essences_path(self) -> Path: ...
    def get_identity_file_path(self) -> Optional[Path]: ...
```

**セキュリティ**: `trusted_external_paths` 設定で外部パスアクセスを制限。

```python
from infrastructure.config import PathResolver, ConfigLoader, find_plugin_root

plugin_root = find_plugin_root(Path(__file__))
loader = ConfigLoader(plugin_root / "config.json")
resolver = PathResolver(plugin_root, loader.load())

loops = resolver.loops_path  # 絶対パス
```

---

## ユーザーインタラクション（infrastructure/user_interaction.py）

### get_default_confirm_callback()

```python
def get_default_confirm_callback() -> Callable[[str], bool]
```

標準入力を使用したデフォルトの確認コールバックを取得。

```python
callback = get_default_confirm_callback()
if callback("ファイルを上書きしますか？"):
    # 上書き実行
```

---

> **v4.0.0 更新**: 設定管理が `infrastructure/config/` サブパッケージとして追加されました。

---

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
