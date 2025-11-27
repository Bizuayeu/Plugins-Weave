[Docs](../README.md) > ARCHITECTURE

# Architecture - EpisodicRAG Plugin

このドキュメントでは、EpisodicRAGプラグインの技術仕様とアーキテクチャについて説明します。

> **対応バージョン**: EpisodicRAG Plugin v2.0.0+ / ファイルフォーマット 1.0

---

## 目次

1. [ディレクトリ構成](#ディレクトリ構成)
2. [Clean Architecture](#clean-architecture)
3. [データフロー](#データフロー)
4. [パス解決の仕組み](#パス解決の仕組み)
5. [技術仕様](#技術仕様)
6. [テスト](#テスト)
7. [セキュリティとプライバシー](#セキュリティとプライバシー)
8. [パフォーマンス](#パフォーマンス)
9. [拡張性](#拡張性)
10. [次のステップ](#次のステップ)

---

## ディレクトリ構成

### Plugin構造（完全自己完結）

```
~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/
├── .claude-plugin/
│   ├── config.json                      # 設定ファイル（@digest-setupで生成）
│   ├── config.template.json             # 設定テンプレート
│   ├── last_digest_times.template.json  # Digest時刻テンプレート
│   ├── GrandDigest.template.txt         # GrandDigest初期化テンプレート
│   ├── ShadowGrandDigest.template.txt   # Shadow初期化テンプレート
│   └── plugin.json                      # Plugin メタデータ
├── agents/
│   └── digest-analyzer.md               # DigestAnalyzerエージェント
├── skills/
│   ├── digest-auto/SKILL.md             # システム状態確認スキル
│   ├── digest-setup/SKILL.md            # 初期セットアップスキル
│   ├── digest-config/SKILL.md           # 設定変更スキル
│   └── shared/                          # 共通コンポーネント
│       ├── _common-concepts.md          # 共通概念（まだらボケ等）
│       └── _implementation-notes.md     # 実装ノート
├── commands/
│   └── digest.md                        # /digest コマンド
├── scripts/                             # Clean Architecture実装
│   ├── domain/                          # コアビジネスロジック（最内層）
│   ├── infrastructure/                  # 外部関心事
│   ├── application/                     # ユースケース
│   ├── interfaces/                      # エントリーポイント
│   ├── config.py                        # 設定管理クラス
│   └── test/                            # テスト（407テスト）
├── data/                                # Plugin内データ（@digest-setupで作成）
│   ├── Loops/                           # Loopファイル配置先
│   ├── Digests/                         # Digest出力先
│   │   ├── 1_Weekly/
│   │   │   ├── W0001_タイトル.txt       # RegularDigest
│   │   │   └── Provisional/             # 次回確定用
│   │   ├── 2_Monthly/ ... 8_Centurial/  # 同様の構造
│   │   └── (各階層にProvisional/あり)
│   └── Essences/                        # GrandDigest配置先
│       ├── GrandDigest.txt
│       └── ShadowGrandDigest.txt
├── docs/                                # ドキュメント
└── CHANGELOG.md                         # 変更履歴
```

---

## Clean Architecture

v2.0.0 より、Clean Architecture（4層構造）を採用しています。

### 層構造

```
scripts/
├── domain/                          # コアビジネスロジック（最内層）
│   ├── __init__.py                  # 公開API
│   ├── types.py                     # TypedDict定義
│   ├── exceptions.py                # ドメイン例外
│   ├── constants.py                 # LEVEL_CONFIG等
│   ├── version.py                   # バージョン
│   └── file_naming.py               # ファイル命名ユーティリティ
│
├── infrastructure/                  # 外部関心事
│   ├── __init__.py                  # 公開API
│   ├── json_repository.py           # JSON操作
│   ├── file_scanner.py              # ファイル検出
│   └── logging_config.py            # ロギング設定
│
├── application/                     # ユースケース
│   ├── __init__.py                  # 公開API（全コンポーネント）
│   ├── validators.py                # バリデーション
│   ├── tracking/                    # 時間追跡
│   │   └── digest_times.py          # DigestTimesTracker
│   ├── shadow/                      # Shadow管理
│   │   ├── template.py              # ShadowTemplate
│   │   ├── file_detector.py         # FileDetector
│   │   ├── shadow_io.py             # ShadowIO
│   │   └── shadow_updater.py        # ShadowUpdater
│   ├── grand/                       # GrandDigest
│   │   ├── grand_digest.py          # GrandDigestManager
│   │   └── shadow_grand_digest.py   # ShadowGrandDigestManager
│   └── finalize/                    # Finalize
│       ├── shadow_validator.py      # ShadowValidator
│       ├── provisional_loader.py    # ProvisionalLoader
│       ├── digest_builder.py        # RegularDigestBuilder
│       └── persistence.py           # DigestPersistence
│
├── interfaces/                      # エントリーポイント
│   ├── __init__.py                  # 公開API
│   ├── finalize_from_shadow.py      # DigestFinalizerFromShadow
│   ├── save_provisional_digest.py   # ProvisionalDigestSaver
│   └── interface_helpers.py         # sanitize_filename, get_next_digest_number
│
└── config.py                        # DigestConfig クラス
```

### 依存関係ルール

```
domain/           ← 何にも依存しない
    ↑
infrastructure/   ← domain/ のみ
    ↑
application/      ← domain/ + infrastructure/
    ↑
interfaces/       ← application/
```

### 推奨インポートパス

```python
# Domain層（定数・型・例外）
from domain import LEVEL_CONFIG, __version__, ValidationError
from domain.file_naming import extract_file_number, format_digest_number

# Infrastructure層（外部I/O）
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files

# Application層（ビジネスロジック）
from application.shadow import ShadowTemplate, ShadowUpdater
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from application.validators import validate_dict, is_valid_list

# Interfaces層（エントリーポイント）
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number

# 設定（DigestConfigクラス）
from config import DigestConfig
```

---

## データフロー

### 1. Loop検出フロー

```
新しいLoopファイル配置
  ↓
/digest コマンド実行
  ↓
ShadowGrandDigest.weeklyにプレースホルダー追加
  ↓
DigestAnalyzerで並列分析
  ↓ (long版)
ShadowGrandDigest.txt更新（digestフィールド埋め込み）
  ↓ (short版)
Provisional Digest保存（次階層用individual）
```

### 2. Digest確定フロー

```
thresholdを満たすファイル蓄積
  ↓
/digest <type> コマンド実行
  ↓
ShadowGrandDigest.<type> 内容確認
  ↓
プレースホルダー判定
  ├─ 未分析 → DigestAnalyzer並列起動
  └─ 分析済 → タイトル提案へスキップ
  ↓
タイトル提案と確定
  ↓
DigestFinalizerFromShadow 実行
  ↓
RegularDigest作成（Narrative + Operational）
  ├─ overall_digest（Shadowからコピー）
  └─ individual_digests（Provisionalマージ）
  ↓
GrandDigest.txt更新
  ↓
次階層Shadowカスケード
  ↓
Provisionalクリーンアップ
  ↓
ShadowGrandDigest.<type> 初期化
```

### 3. 階層的カスケード

> SSoT: [_common-concepts.md](../skills/shared/_common-concepts.md#階層的カスケード)

```
Loop (5個) → Weekly Digest
  ↓ (5個蓄積)
Weekly (5個) → Monthly Digest
  ↓ (3個蓄積)
Monthly (3個) → Quarterly Digest
  ↓ (4個蓄積)
Quarterly (4個) → Annual Digest
  ↓ (3個蓄積)
Annual (3個) → Triennial Digest
  ↓ (3個蓄積)
Triennial (3個) → Decadal Digest
  ↓ (3個蓄積)
Decadal (3個) → Multi-decadal Digest
  ↓ (4個蓄積)
Multi-decadal (4個) → Centurial Digest
```

---

## パス解決の仕組み

### config.pyの役割

`scripts/config.py`は、すべてのパス設定を一元管理し、Plugin自己完結性を保証します。

```python
class DigestConfig:
    def __init__(self, plugin_root: Optional[Path] = None):
        if plugin_root is None:
            plugin_root = self._find_plugin_root()
        self.plugin_root = plugin_root
        self.config_file = self.plugin_root / ".claude-plugin" / "config.json"
        self.config = self.load_config()
        self.base_dir = self._resolve_base_dir()

    def _resolve_base_dir(self):
        base_dir_setting = self.config.get("base_dir", ".")
        return (self.plugin_root / base_dir_setting).resolve()

    def resolve_path(self, key):
        rel_path = self.config["paths"][key]
        return (self.base_dir / rel_path).resolve()

    # 主要プロパティ
    @property
    def loops_path(self) -> Path: ...      # Loopファイル配置先
    @property
    def digests_path(self) -> Path: ...    # Digest出力先
    @property
    def essences_path(self) -> Path: ...   # GrandDigest配置先
```

### パス解決の例

**設定:**
```json
{
  "base_dir": "../../..",
  "paths": {
    "loops_dir": "homunculus/Weave/EpisodicRAG/Loops"
  }
}
```

**解決:**
```
plugin_root = ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
base_dir = plugin_root / ../../.. = /Users/username/DEV
loops_path = base_dir / homunculus/Weave/EpisodicRAG/Loops
           = /Users/username/DEV/homunculus/Weave/EpisodicRAG/Loops
```

---

## 技術仕様

### ファイル形式

> **Note**: 各ファイル形式の詳細なAPI仕様は [API_REFERENCE.md](API_REFERENCE.md) を参照してください。

#### GrandDigest.txt

確定済みダイジェストの集約ファイル。各レベルの`overall_digest`のみを保持します。

```json
{
  "metadata": {
    "last_updated": "2025-11-22T00:00:00",
    "version": "1.0"
  },
  "major_digests": {
    "weekly": {
      "overall_digest": {
        "timestamp": "2025-11-22T00:00:00",
        "source_files": ["Loop0001_xxx.txt", "Loop0002_xxx.txt", ...],
        "digest_type": "技術探求",
        "keywords": ["キーワード1", "キーワード2", ...],
        "abstract": "全体統合分析（2400文字程度）...",
        "impression": "所感・展望（800文字程度）..."
      }
    },
    ...
  }
}
```

#### ShadowGrandDigest.txt

未確定（下書き）のダイジェスト。プレースホルダー（`<!-- PLACEHOLDER ... -->`）は未分析状態を示します。

#### Provisional Digest

DigestAnalyzerが生成した個別ダイジェストの中間ファイル（JSON形式）。

#### last_digest_times.json

各レベルの最終処理ファイルを追跡する状態ファイル。

---

## テスト

### 実行方法

```bash
cd scripts

# 全テスト実行（pytest）
python -m pytest test/ -v

# unittest形式
python -m unittest discover -s test -v
```

### テスト構成

| カテゴリ | ファイル数 | テスト数 |
|----------|-----------|---------|
| Domain層 | 1 | 5 |
| Infrastructure層 | 2 | 15 |
| Application層 | 12 | 180+ |
| Interfaces層 | 3 | 40+ |
| Integration | 2 | 60+ |

**合計**: **407テスト**

---

## セキュリティとプライバシー

- **ローカルファイルシステムのみ使用**: ネットワーク通信なし
- **GitHub連携は任意**: オプション機能（高度な使い方）
- **データの完全なユーザー管理**: すべてのデータはユーザーの管理下に保存
- **設定ファイルの自己完結**: Plugin内に完全に配置

---

## パフォーマンス

- **軽量なPythonスクリプト**: 最小限の依存関係
- **効率的なファイルI/O**: JSON形式での高速読み書き
- **並列処理対応**: DigestAnalyzer複数起動による高速分析
- **大量データ対応**: 100+ Loopファイルでもスムーズに動作

---

## 拡張性

### 新しい階層の追加

`config.json`に新しいthresholdを追加し、`LEVEL_CONFIG`（`domain/constants.py`）を更新することで、9階層目以降を追加可能です。

### カスタムエージェント

DigestAnalyzerエージェントをベースに、カスタム分析ロジックを実装可能です。

---

## 次のステップ

- **基本的な使い方**: [GUIDE.md](../user/GUIDE.md)
- **GitHub連携の設定**: [ADVANCED.md](../user/ADVANCED.md)
- **トラブルシューティング**: [TROUBLESHOOTING.md](../user/TROUBLESHOOTING.md)
- **API リファレンス**: [API_REFERENCE.md](API_REFERENCE.md)

---
