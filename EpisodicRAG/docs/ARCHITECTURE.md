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
6. [セキュリティとプライバシー](#セキュリティとプライバシー)
7. [パフォーマンス](#パフォーマンス)
8. [拡張性](#拡張性)
9. [次のステップ](#次のステップ)

---

## ディレクトリ構成

### Plugin構造（完全自己完結）

```
~/.claude/plugins/EpisodicRAG-Plugin@Toybox/
├── .claude-plugin/
│   ├── config.json                 # 設定ファイル（@digest-setupで生成）
│   ├── config.template.json        # 設定テンプレート
│   └── plugin.json                 # Plugin メタデータ
├── agents/
│   └── digest-analyzer.md          # DigestAnalyzerエージェント
├── skills/
│   ├── digest-auto/
│   │   └── SKILL.md                # システム状態確認スキル
│   ├── digest-setup/
│   │   └── SKILL.md                # 初期セットアップスキル
│   └── digest-config/
│       └── SKILL.md                # 設定変更スキル
├── commands/
│   └── digest.md                   # /digest コマンド
├── scripts/
│   ├── config.py                   # 設定管理クラス
│   ├── shadow_grand_digest.py      # Shadow管理
│   ├── finalize_from_shadow.py     # Shadow確定
│   ├── save_provisional_digest.py  # Provisional保存
│   └── generate_digest_auto.sh     # 自動Digest生成
├── templates/
│   ├── setup.sh                    # セットアップスクリプト
│   └── CLAUDE.md.template          # セッション開始時プロトコル
├── data/                           # Plugin内データ（@digest-setupで作成）
│   ├── Loops/                      # Loopファイル配置先
│   ├── Digests/                    # Digest出力先
│   │   ├── 1_Weekly/
│   │   ├── 2_Monthly/
│   │   ├── 3_Quarterly/
│   │   ├── 4_Annual/
│   │   ├── 5_Triennial/
│   │   ├── 6_Decadal/
│   │   ├── 7_Multi-decadal/
│   │   ├── 8_Centurial/
│   │   └── Provisional/           # 一時作業用
│   └── Essences/                   # GrandDigest配置先
│       ├── GrandDigest.txt
│       └── ShadowGrandDigest.txt
├── docs/                           # ドキュメント
│   ├── GUIDE.md                    # ユーザーガイド
│   ├── ADVANCED.md                 # GitHub連携
│   ├── ARCHITECTURE.md             # このファイル
│   └── TROUBLESHOOTING.md          # トラブルシューティング
├── README.md                       # 一般ユーザー向けドキュメント
└── CONTRIBUTING.md                 # 開発者向けドキュメント
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
    def __init__(self):
        self.plugin_root = self._find_plugin_root()
        self.config = self.load_config()
        self.base_dir = self._resolve_base_dir()

    def _resolve_base_dir(self):
        base_dir_setting = self.config.get("base_dir", ".")
        return (self.plugin_root / base_dir_setting).resolve()

    def resolve_path(self, key):
        rel_path = self.config["paths"][key]
        return (self.base_dir / rel_path).resolve()
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
plugin_root = ~/.claude/plugins/EpisodicRAG-Plugin@Toybox
base_dir = plugin_root / ../../.. = /Users/username/DEV
loops_path = base_dir / homunculus/Weave/EpisodicRAG/Loops
           = /Users/username/DEV/homunculus/Weave/EpisodicRAG/Loops
```

---

## 技術仕様

### ファイル形式

#### GrandDigest.txt

```json
{
  "metadata": {
    "last_updated": "2025-11-22T00:00:00",
    "version": "1.0"
  },
  "latest_digests": {
    "weekly": {
      "digest_name": "Weekly-2025W47",
      "overall_digest": {
        "digest_type": "...",
        "keywords": [...],
        "abstract": "...",
        "impression": "..."
      },
      "individual_digests": [
        {
          "source_file": "Loop0001_タイトル.txt",
          "digest": {
            "digest_type": "...",
            "keywords": [...],
            "abstract": "...",
            "impression": "..."
          }
        }
      ]
    },
    "monthly": { ... },
    ...
  }
}
```

#### ShadowGrandDigest.txt

```json
{
  "metadata": {
    "last_updated": "2025-11-22T00:00:00",
    "version": "1.0",
    "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト"
  },
  "shadow_digests": {
    "weekly": {
      "source_files": [
        {
          "file": "Loop0001_タイトル.txt",
          "digest": {
            "digest_type": "...",
            "keywords": [...],
            "abstract": "...",
            "impression": "..."
          }
        },
        {
          "file": "Loop0002_タイトル.txt",
          "digest": null  // プレースホルダー（未分析状態）
        }
      ],
      "overall_digest": null  // 確定前はnull
    },
    ...
  }
}
```

#### Provisional Digest

```
# Provisional/1_Weekly/W0001_Individual.txt

[Loop0001_タイトル.txt]
digest_type: ...
keywords: ...
abstract: ...（short版: 1200文字）
impression: ...（short版: 400文字）

---

[Loop0002_タイトル.txt]
digest_type: ...
keywords: ...
abstract: ...（short版: 1200文字）
impression: ...（short版: 400文字）

---
```

---

## スクリプトの役割分担

| スクリプト | 役割 | 実行タイミング |
|-----------|------|---------------|
| `generate_digest_auto.sh` | 未処理Loop検出、ShadowGrandDigest操作 | `/digest` 実行時 |
| `save_provisional_digest.py` | Provisional Digest保存 | DigestAnalyzer分析後 |
| `finalize_from_shadow.py` | Regular Digest作成、GrandDigest更新、カスケード | `/digest <type>` のタイトル承認後 |
| `shadow_grand_digest.py` | ShadowGrandDigest管理（CRUD操作） | 各スクリプトから呼び出し |
| `config.py` | 設定管理、パス解決 | 全スクリプトから参照 |

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

*Last Updated: 2025-11-24*
*Version: 1.1.0*
