[API Reference](../API_REFERENCE.md) > 設定・Config

# 設定 API

config.json仕様とDigestConfigクラス。

---

## config.json 詳細仕様

> 📖 クイックリファレンスは [GUIDE.md](../../user/GUIDE.md#設定ファイル仕様クイックリファレンス) を参照

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
```text
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

## DigestConfig クラス（config/__init__.py）

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

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
