# Infrastructure層 API

外部関心事（ファイルI/O、ロギング）。

> **対象読者**: AIエージェント（Claude Code）、人間開発者
> **想定ユースケース**: ファイル操作、ロギング、設定ファイル読み込みの実装時

> 📖 用語・共通概念は [用語集](../../../GLOSSARY.md) を参照

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
    ConfigLoader, PathResolver, load_config,
    # パス検証 (v4.1.0+)
    PathValidatorChain, TrustedExternalPathValidator,
    ValidationContext, ValidationResult,
    # 永続化パス (v5.2.0+)
    get_persistent_config_dir, get_config_path,
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
- [パス検証](#パス検証infrastructureconfigpath_validatorspy-v410) - PathValidatorChain *(v4.1.0+)*
- [永続化パス](#永続化パスinfrastructureconfigpersistent_pathpy-v520) - get_persistent_config_dir() *(v5.2.0+)*
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

ハンドラーの出力先は UTF-8 で構成される（`_utf8_safe_stream()`）。Windows の
cmd.exe / PowerShell はリダイレクト・パイプ時に既定で cp932 を使うため、
em-dash「—」(U+2014) 等 cp932 に存在しない文字が `UnicodeEncodeError`
（`--- Logging error ---`）を引き起こしていた。バイナリバッファを持つ stream は
UTF-8 の `TextIOWrapper` で包み直される（handler-local な差し替えで、
`sys.stdout` 自体は変更しない）。バッファを持たない stream（StringIO 等）は
そのまま使われる。

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

> **v5.3.0変更**: `find_plugin_root()` は廃止されました。設定ファイルの場所は `get_persistent_config_dir()` で取得します。

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
    def __init__(self, config: ConfigData): ...
    def resolve_path(self, key: str) -> Path: ...
    @property
    def base_dir(self) -> Path: ...
    @property
    def loops_path(self) -> Path: ...
    @property
    def digests_path(self) -> Path: ...
    @property
    def essences_path(self) -> Path: ...
    def get_identity_file_path(self) -> Optional[Path]: ...
```

> **v5.3.0変更**: `plugin_root` パラメータは廃止されました。`base_dir` は絶対パス必須です。

**セキュリティ**: `trusted_external_paths` 設定で外部パスアクセスを制限。

```python
from infrastructure.config import PathResolver, ConfigLoader, get_config_path

config_path = get_config_path()
loader = ConfigLoader(config_path)
resolver = PathResolver(loader.load())

loops = resolver.loops_path  # 絶対パス
```

---

## パス検証（infrastructure/config/path_validators.py） *(v4.1.0+)*

Chain of Responsibility パターンによるパス検証。PathResolverの内部バリデーションを独立モジュール化。

> 📖 Chain of Responsibility パターン - [DESIGN_DECISIONS.md](../DESIGN_DECISIONS.md) 参照

### ValidationContext

検証に必要なコンテキスト情報を保持。

```python
@dataclass(frozen=True)
class ValidationContext:
    """パス検証のコンテキスト"""
    resolved_path: Path          # 解決済みパス
    base_dir: Path               # 基準ディレクトリ
    trusted_paths: List[Path]    # 信頼済み外部パス
    original_value: str          # 元の設定値
```

> **v5.3.0変更**: `plugin_root` は `base_dir` に変更されました。

### ValidationResult

検証結果を表すデータクラス。

```python
@dataclass(frozen=True)
class ValidationResult:
    """検証結果"""
    is_valid: bool               # 検証成功/失敗
    message: Optional[str] = None  # エラーメッセージ（失敗時）
```

### PathValidator（抽象基底クラス）

```python
class PathValidator(ABC):
    """パス検証の抽象基底クラス"""

    @abstractmethod
    def validate(self, context: ValidationContext) -> ValidationResult: ...

    def set_next(self, validator: "PathValidator") -> "PathValidator": ...
```

### TrustedExternalPathValidator

パスが信頼済み外部パス内にあるかを検証。

```python
class TrustedExternalPathValidator(PathValidator):
    """trusted_external_paths内のパスを許可"""

    def validate(self, context: ValidationContext) -> ValidationResult
```

### PathValidatorChain

複数のバリデータをチェーン化するファサード。

```python
class PathValidatorChain:
    """パス検証のChain of Responsibility"""

    @classmethod
    def create_default_chain(cls) -> "PathValidatorChain": ...

    def validate(self, context: ValidationContext) -> ValidationResult: ...
```

**使用例**:

```python
from infrastructure.config.path_validators import (
    PathValidatorChain, ValidationContext
)

# デフォルトチェーンを作成
chain = PathValidatorChain.create_default_chain()

# 検証コンテキストを作成
context = ValidationContext(
    resolved_path=Path("/some/path").resolve(),
    base_dir=Path("~/.claude/plugins/.episodicrag").expanduser().resolve(),
    trusted_paths=[Path("/trusted/external").resolve()],
    original_value="/some/path"
)

# 検証実行
result = chain.validate(context)
if not result.is_valid:
    raise ConfigError(result.message)
```

---

## 永続化パス（infrastructure/config/persistent_path.py） *(v5.2.0+)*

Claude Codeのプラグイン自動更新に影響されない永続化ディレクトリを提供。

> **背景**: Claude Codeはプラグイン更新時に`~/.claude/plugins/marketplaces/`を削除→再cloneするため、`.gitignore`に含まれるファイル（config.json等）が消失する問題を解決。

### get_persistent_config_dir()

```python
def get_persistent_config_dir() -> Path
```

永続化設定ディレクトリを取得（なければ作成）。

**戻り値**: `~/.claude/plugins/.episodicrag/` のパス

**特徴**:
- ディレクトリが存在しない場合は自動的に作成される
- このディレクトリはClaude Codeのauto-update対象外
- 環境変数`EPISODICRAG_CONFIG_DIR`で上書き可能（テスト用）

**使用例**:

```python
from infrastructure.config.persistent_path import get_persistent_config_dir

config_dir = get_persistent_config_dir()
config_file = config_dir / "config.json"
last_digest_file = config_dir / "last_digest_times.json"
```

**テスト時の使用**:

```bash
# 環境変数で一時ディレクトリを指定
EPISODICRAG_CONFIG_DIR=/tmp/test_config pytest ...
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
> **v4.1.0 更新**: PathValidatorChain（Chain of Responsibility）が追加されました。
> **v5.0.0 更新**: LEVEL_CONFIGにloop層が追加されました（9レベル化）。
> **v5.2.0 更新**: `get_persistent_config_dir()` が追加されました。config.jsonとlast_digest_times.jsonが永続化パス（`~/.claude/plugins/.episodicrag/`）に移動し、`find_plugin_root()` は廃止されました。`plugin_root` パラメータの削除により、`base_dir` は絶対パス必須になりました。

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
