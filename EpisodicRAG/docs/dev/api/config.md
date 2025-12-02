[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Config

# 設定 API

config.json仕様とDigestConfigクラス。

> **対象読者**: AIエージェント（Claude Code）、人間開発者
> **想定ユースケース**: 設定ファイル操作、DigestConfig使用時の参照

> **v4.0.0**: 設定管理機能は3層に分散配置されています。アーキテクチャ詳細は [ARCHITECTURE.md](../ARCHITECTURE.md#依存関係ルール) を参照。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from application.config import DigestConfig

# または詳細なインポート
from application.config import (
    DigestConfig,
    ConfigValidator,
    ThresholdProvider,
    LevelPathService,
)

# Infrastructure層のconfig（低レベルAPI）
from infrastructure.config import (
    ConfigLoader,
    PathResolver,
    find_plugin_root,
    load_config,
)
```

---

## 目次

1. [config.json 詳細仕様](#configjson-詳細仕様)
   - [設定ファイルの場所](#設定ファイルの場所)
   - [設定項目詳細](#設定項目詳細)
   - [よくある設定パターン](#よくある設定パターン)
2. [ConfigData型定義](#configdata型定義)
   - [ConfigData（config.json全体構造）](#configdataconfigjson全体構造)
   - [PathsConfigData / LevelsConfigData](#pathsconfigdata--levelsconfigdata)
3. [DigestConfig クラス](#digestconfig-クラスapplicationconfig__init__py)
   - [プロパティ（パス関連）](#プロパティパス関連)
   - [プロパティ（閾値関連）](#プロパティ閾値関連)
   - [メソッド](#メソッド)
   - [Context Manager対応](#context-manager対応)
   - [thresholdプロパティ](#thresholdプロパティ)
4. [CLI使用方法](#cli使用方法)
   - [interfaces.config_cli モジュール](#interfacesconfig_cli-モジュール)
   - [スキルCLI (v4.0.0+)](#スキルcli-v400)
   - [テスト実行](#テスト実行)

---

## config.json 詳細仕様

### 設定ファイルの場所

`~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/.claude-plugin/config.json`

### 設定項目詳細

#### base_dir

パス解決の基準ディレクトリ

**デフォルト**: `.` (プラグインルート自身)

**設定例：**
- `"."` (デフォルト): プラグインルート自身を基準とする（完全自己完結型）
- `"subdir"`: プラグイン内のサブディレクトリ
- `"~/DEV/production/EpisodicRAG"`: 外部パス（`trusted_external_paths`で許可が必要）
- `"C:/Users/username/DEV/data"`: Windows絶対パス（`trusted_external_paths`で許可が必要）

**パス解決の仕組み:**
```text
# 相対パスの場合
最終的なパス = {plugin_root} / {base_dir} / {paths.*_dir}

# 絶対パスの場合（trusted_external_paths内である必要あり）
最終的なパス = {base_dir} / {paths.*_dir}

例（外部パス）:
base_dir = "~/DEV/production/EpisodicRAG"
loops_dir = "data/Loops"

最終パス = ~/DEV/production/EpisodicRAG/data/Loops
```

**注意:**
- 相対パスはプラグインルート基準で解釈されます
- 絶対パス・チルダパスは`trusted_external_paths`での許可が必要です

---

#### trusted_external_paths

plugin_root外でアクセスを許可する絶対パスのリスト

**デフォルト**: `[]` (空配列、plugin_root内のみ許可)

**設定例：**
- `[]`: plugin_root内のみ（最もセキュア、デフォルト）
- `["~/DEV/production"]`: ホームディレクトリ配下の特定パスを許可
- `["C:/Data/EpisodicRAG"]`: Windows絶対パスを許可
- `["~/DEV", "D:/Backup"]`: 複数パスを許可

**セキュリティ:**
- デフォルトは空配列で最もセキュア
- 外部パスを使用する場合は明示的な許可が必要
- 相対パスは使用不可（絶対パスのみ）
- Git公開時は`config.json`を`.gitignore`に追加推奨

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

> 📖 ID桁数一覧（プレフィックス・桁数・例）は [用語集 > ID桁数一覧](../../../README.md#id桁数一覧) を参照

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
  "base_dir": "~/DEV/production/EpisodicRAG",
  "trusted_external_paths": ["~/DEV/production"],
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": "Identities/UserIdentity.md"
  },
  "levels": { ... }
}
```

---

## ConfigData型定義

config.jsonの型安全な定義。`domain/types.py`で定義。

```python
from domain.types import ConfigData, PathsConfigData, LevelsConfigData
```

### ConfigData（config.json全体構造）

```typescript
interface ConfigData {
  base_dir?: string;           // plugin_rootからの相対パス
  trusted_external_paths?: string[];  // plugin_root外でアクセス許可するパス (v4.0.0+)
  paths?: {
    loops_dir?: string;        // Loopファイル配置先
    digests_dir?: string;      // Digest出力先
    essences_dir?: string;     // GrandDigest配置先
    identity_file_path?: string | null;  // 外部Identity.mdパス
  };
  levels?: {
    weekly_threshold?: number;    // デフォルト: 5
    monthly_threshold?: number;   // デフォルト: 5
    quarterly_threshold?: number; // デフォルト: 3
    annual_threshold?: number;    // デフォルト: 4
    triennial_threshold?: number; // デフォルト: 3
    decadal_threshold?: number;   // デフォルト: 3
    multi_decadal_threshold?: number; // デフォルト: 3
    centurial_threshold?: number; // デフォルト: 4
  };
}
```

### PathsConfigData / LevelsConfigData

```python
class PathsConfigData(TypedDict, total=False):
    loops_dir: str
    digests_dir: str
    essences_dir: str
    identity_file_path: Optional[str]

class LevelsConfigData(TypedDict, total=False):
    weekly_threshold: int
    monthly_threshold: int
    quarterly_threshold: int
    annual_threshold: int
    triennial_threshold: int
    decadal_threshold: int
    multi_decadal_threshold: int
    centurial_threshold: int
```

> 📖 完全な型定義は [domain/types/config.py](../../../scripts/domain/types/config.py) を参照

---

## DigestConfig クラス（application/config/__init__.py）

```python
class DigestConfig:
    def __init__(self, plugin_root: Optional[Path] = None): ...
```

### プロパティ（パス関連）

> 📖 パス用語の定義は [用語集](../../../README.md#基本概念) を参照

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `plugin_root` | `Path` | プラグインルートディレクトリ |
| `config_file` | `Path` | 設定ファイルのパス |
| `base_dir` | `Path` | 解決された基準ディレクトリ |
| `loops_path` | `Path` | Loopファイル配置先 |
| `digests_path` | `Path` | Digest出力先 |
| `essences_path` | `Path` | GrandDigest配置先 |

### プロパティ（閾値関連）

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

### メソッド

```python
def resolve_path(self, key: str) -> Path
def get_level_dir(self, level: str) -> Path
def get_provisional_dir(self, level: str) -> Path
def get_source_dir(self, level: str) -> Path
def get_source_pattern(self, level: str) -> str
def get_threshold(self, level: str) -> int
def get_identity_file_path(self) -> Optional[Path]
def load_config(self) -> ConfigData
def show_paths(self) -> None
def validate_directory_structure(self) -> list
```

### Context Manager対応

`with`文での使用に対応しています。

```python
from application.config import DigestConfig

with DigestConfig() as config:
    print(config.loops_path)
```

### thresholdプロパティ

`threshold`プロパティ経由で`ThresholdProvider`にアクセスできます。

```python
config = DigestConfig()
print(config.threshold.weekly_threshold)  # 5
print(config.threshold.monthly_threshold)  # 5
```

---

## CLI使用方法

### interfaces.config_cli モジュール

```bash
cd scripts

# 設定をJSON形式で表示
python -m interfaces.config_cli

# パス設定を表示
python -m interfaces.config_cli --show-paths

# プラグインルートを指定
python -m interfaces.config_cli --plugin-root /path/to/plugin
```

### スキルCLI (v4.0.0+)

v4.0.0で追加されたスキルのPythonスクリプト実装。Claudeから呼び出されるか、直接実行可能。

#### digest_setup（初期セットアップ）

```bash
cd scripts

# セットアップ状態を確認
python -m interfaces.digest_setup check

# 初期セットアップ実行
python -m interfaces.digest_setup init --config '{"base_dir": ".", "paths": {...}, "levels": {...}}'

# 既存設定を上書き
python -m interfaces.digest_setup init --config '...' --force
```

#### digest_config（設定変更）

```bash
cd scripts

# 現在の設定を表示
python -m interfaces.digest_config show

# 設定を一括更新
python -m interfaces.digest_config update --config '{"base_dir": ".", ...}'

# 個別設定を変更（ドット記法サポート）
python -m interfaces.digest_config set --key "levels.weekly_threshold" --value 7

# trusted_external_paths の管理
python -m interfaces.digest_config trusted-paths list
python -m interfaces.digest_config trusted-paths add "~/DEV/production"
python -m interfaces.digest_config trusted-paths remove "~/DEV/production"
```

#### digest_auto（健全性診断）

```bash
cd scripts

# JSON形式で出力（デフォルト）
python -m interfaces.digest_auto --output json

# テキスト形式で出力
python -m interfaces.digest_auto --output text
```

出力内容:
- 未処理Loop検出
- プレースホルダー検出（まだらボケ）
- 中間ファイルスキップ検出
- 生成可能なダイジェスト階層
- 推奨アクション

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
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
