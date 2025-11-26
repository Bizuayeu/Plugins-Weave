# Architecture - EpisodicRAG Plugin

このドキュメントでは、EpisodicRAGプラグインの技術仕様とアーキテクチャについて説明します。

---

## 目次

1. [ディレクトリ構成](#ディレクトリ構成)
2. [データフロー](#データフロー)
   - [Loop検出フロー](#1-loop検出フロー)
   - [Digest確定フロー](#2-digest確定フロー)
   - [階層的カスケード](#3-階層的カスケード)
3. [パス解決の仕組み](#パス解決の仕組み)
4. [技術仕様](#技術仕様)
5. [スクリプトの役割分担](#スクリプトの役割分担)
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
│   ├── digest-auto/
│   │   └── SKILL.md                     # システム状態確認スキル
│   ├── digest-setup/
│   │   └── SKILL.md                     # 初期セットアップスキル
│   ├── digest-config/
│   │   └── SKILL.md                     # 設定変更スキル
│   └── shared/                          # 共通コンポーネント
│       ├── _common-concepts.md          # 共通概念（まだらボケ等）
│       └── _implementation-notes.md     # 実装ノート
├── commands/
│   └── digest.md                        # /digest コマンド
├── scripts/
│   ├── config.py                        # 設定管理クラス（LEVEL_CONFIG含む）
│   ├── grand_digest.py                  # GrandDigest.txt管理
│   ├── digest_times.py                  # last_digest_times.json管理
│   ├── utils.py                         # ユーティリティ関数
│   ├── shadow_grand_digest.py           # Shadow管理
│   ├── finalize_from_shadow.py          # Shadow確定
│   ├── save_provisional_digest.py       # Provisional保存
│   ├── generate_digest_auto.sh          # 自動Digest生成
│   ├── setup.sh                         # セットアップスクリプト
│   └── test/                            # テストディレクトリ
│       ├── test_config.py
│       ├── test_utils.py
│       ├── test_grand_digest.py
│       ├── test_digest_times.py
│       ├── test_finalize_from_shadow.py
│       ├── test_save_provisional_digest.py
│       └── test_shadow_grand_digest.py
├── data/                                # Plugin内データ（@digest-setupで作成）
│   ├── Loops/                           # Loopファイル配置先
│   ├── Digests/                         # Digest出力先
│   │   ├── 1_Weekly/
│   │   │   ├── W0001_タイトル.txt       # RegularDigest
│   │   │   └── Provisional/             # 次回確定用
│   │   │       └── W0002_Individual.txt
│   │   ├── 2_Monthly/ ... 8_Centurial/  # 同様の構造
│   │   └── (各階層にProvisional/あり)
│   └── Essences/                        # GrandDigest配置先
│       ├── GrandDigest.txt
│       └── ShadowGrandDigest.txt
├── docs/                                # ドキュメント
│   ├── README.md                        # ドキュメントハブ
│   ├── QUICKSTART.md                    # 5分クイックスタート
│   ├── GUIDE.md                         # ユーザーガイド
│   ├── GLOSSARY.md                      # 用語集
│   ├── FAQ.md                           # よくある質問
│   ├── TROUBLESHOOTING.md               # トラブルシューティング
│   ├── ARCHITECTURE.md                  # このファイル
│   ├── ADVANCED.md                      # GitHub連携
│   └── API_REFERENCE.md                 # API仕様
├── CONTRIBUTING.md                      # 開発者向け
└── CHANGELOG.md                         # 変更履歴
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
finalize_from_shadow.py 実行
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

    # Threshold取得（動的）
    def get_threshold(self, level: str) -> int:
        """指定レベルのthresholdを取得"""
        # 例: get_threshold("weekly") -> 5

    # 階層別ディレクトリ取得
    def get_level_dir(self, level: str) -> Path:
        """指定レベルのRegularDigest格納ディレクトリ"""
        # 例: get_level_dir("weekly") -> digests_path/1_Weekly

    def get_provisional_dir(self, level: str) -> Path:
        """指定レベルのProvisionalDigest格納ディレクトリ"""
        # 例: get_provisional_dir("weekly") -> digests_path/1_Weekly/Provisional

    def get_identity_file_path(self) -> Optional[Path]:
        """外部Identityファイルのパス（設定時のみ）"""
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
    "monthly": { "overall_digest": {...} },
    "quarterly": { "overall_digest": {...} },
    "annual": { "overall_digest": {...} },
    "triennial": { "overall_digest": {...} },
    "decadal": { "overall_digest": {...} },
    "multi_decadal": { "overall_digest": {...} },
    "centurial": { "overall_digest": {...} }
  }
}
```

#### ShadowGrandDigest.txt

未確定（下書き）のダイジェスト。新しいファイルが追加されるとプレースホルダーが設定されます。

```json
{
  "metadata": {
    "last_updated": "2025-11-22T00:00:00",
    "version": "1.0",
    "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト（下書き帳）"
  },
  "latest_digests": {
    "weekly": {
      "overall_digest": {
        "timestamp": "<!-- PLACEHOLDER -->",
        "source_files": ["Loop0003_xxx.txt", "Loop0004_xxx.txt"],
        "digest_type": "<!-- PLACEHOLDER -->",
        "keywords": ["<!-- PLACEHOLDER: keyword1 -->", "<!-- PLACEHOLDER: keyword2 -->", ...],
        "abstract": "<!-- PLACEHOLDER: 2ファイル分の全体統合分析 (2400文字程度) -->",
        "impression": "<!-- PLACEHOLDER: 所感・展望 (800文字程度) -->"
      }
    },
    "monthly": { "overall_digest": {...} },
    ...
  }
}
```

**プレースホルダー**: `<!-- PLACEHOLDER ... -->`形式のマーカーは、Claudeによる分析が必要な状態を示します。

#### Provisional Digest

DigestAnalyzerが生成した個別ダイジェストの中間ファイル（JSON形式）。

```json
// digests_path/1_Weekly/Provisional/W0002_Individual.txt

{
  "metadata": {
    "digest_level": "weekly",
    "digest_number": "0002",
    "last_updated": "2025-11-22T00:00:00",
    "version": "1.0"
  },
  "individual_digests": [
    {
      "source_file": "Loop0003_タイトル.txt",
      "digest_type": "技術探求",
      "keywords": ["キーワード1", "キーワード2", ...],
      "abstract": "...(short版: 1200文字程度)",
      "impression": "...(short版: 400文字程度)"
    },
    {
      "source_file": "Loop0004_タイトル.txt",
      "digest_type": "...",
      "keywords": [...],
      "abstract": "...",
      "impression": "..."
    }
  ]
}
```

#### last_digest_times.json

各レベルの最終処理ファイルを追跡する状態ファイル。

```json
// .claude-plugin/last_digest_times.json

{
  "weekly": {
    "timestamp": "2025-11-22T00:00:00",
    "last_processed": "Loop0186"
  },
  "monthly": {
    "timestamp": "2025-11-20T00:00:00",
    "last_processed": "W0037"
  },
  ...
}
```

---

## スクリプトの役割分担

| スクリプト | 役割 | 実行タイミング |
|-----------|------|---------------|
| `generate_digest_auto.sh` | 未処理Loop検出、ShadowGrandDigest操作 | `/digest` 実行時 |
| `save_provisional_digest.py` | Provisional Digest保存 | DigestAnalyzer分析後 |
| `finalize_from_shadow.py` | Regular Digest作成、GrandDigest更新、カスケード | `/digest <type>` のタイトル承認後 |
| `shadow_grand_digest.py` | ShadowGrandDigest管理（CRUD操作） | 各スクリプトから呼び出し |
| `config.py` | 設定管理、パス解決、LEVEL_CONFIG/PLACEHOLDER_*定数、extract_file_number()、get_threshold() | 全スクリプトから参照 |
| `grand_digest.py` | GrandDigest.txt管理（CRUD操作） | finalize_from_shadowから呼び出し |
| `digest_times.py` | last_digest_times.json管理 | finalize_from_shadowから呼び出し |
| `utils.py` | ユーティリティ関数（sanitize_filename, load_json_with_template, save_json等） | 各スクリプトから参照 |
| `test/*.py` | ユニット/統合テスト | 開発時、CI |

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

| ファイル | 種別 | テスト数 |
|----------|------|---------|
| test_config.py | Unit | 35 |
| test_utils.py | Unit | 7 |
| test_grand_digest.py | Integration | 5 |
| test_digest_times.py | Integration | 4 |
| test_finalize_from_shadow.py | Integration | 15 |
| test_save_provisional_digest.py | Integration | 7 |
| test_shadow_grand_digest.py | Integration | 9 |

**合計**: 82テスト

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

`config.json`に新しいthresholdを追加し、`scripts/generate_digest_auto.sh`を更新することで、9階層目以降を追加可能です。

**例（Millennial階層の追加）:**
```json
{
  "levels": {
    ...
    "centurial_threshold": 4,
    "millennial_threshold": 10  // 新規追加
  }
}
```

### カスタムエージェント

DigestAnalyzerエージェントをベースに、カスタム分析ロジックを実装可能です。

**例:**
- 特定ドメイン専用の分析エージェント
- 多言語対応分析エージェント
- 感情分析専門エージェント

---

## 次のステップ

- 📘 **基本的な使い方**: [GUIDE.md](GUIDE.md)
- 🔧 **GitHub連携の設定**: [ADVANCED.md](ADVANCED.md)
- 🆘 **トラブルシューティング**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

*Last Updated: 2025-11-27*
*Version: 1.1.2*
