[Home](../README.md) > [Docs](README.md) > GLOSSARY

# 用語集 (Glossary)

EpisodicRAGプラグインで使用される専門用語の定義集です。

---

## 基本概念

### plugin_root
**定義**: プラグインのインストール先ディレクトリ

- `.claude-plugin/config.json` が存在するディレクトリ
- スキルやスクリプトはこのディレクトリを基準に動作
- 例: `C:\Users\anyth\.claude\plugins\marketplaces\Plugins-Weave\EpisodicRAG`

### base_dir
**定義**: データ配置の基準ディレクトリ

- **設定場所**: `config.json` の `base_dir` フィールド
- **形式**: plugin_root からの相対パス
- **例**: `.`（プラグイン内）、`../../../../../DEV/data`（外部）

パス解決: `plugin_root + base_dir` → 実際のデータ基準ディレクトリ

### paths
**定義**: 各データディレクトリの配置先

- **設定場所**: `config.json` の `paths` セクション
- **形式**: base_dir からの相対パス
- **含まれる設定**: `loops_dir`, `digests_dir`, `essences_dir`, `identity_file_path`

パス解決: `base_dir + paths.loops_dir` → 実際のLoopディレクトリ

### Loop
**定義**: AI との会話セッション全体を記録したテキストファイル

- **形式**: `Loop[連番]_[タイトル].txt`
- **例**: `Loop0001_認知アーキテクチャ論.txt`
- **正規表現**: `^Loop[0-9]+_[\p{L}\p{N}ー・\w]+\.txt$`
- **配置先**: `{loops_dir}/`

Loopは EpisodicRAG システムの最小単位であり、すべてのDigest生成の基礎データとなります。

### Digest
**定義**: 複数のLoopまたは下位Digestを要約・統合した階層的記録

Digestには以下の種類があります：

| 種類 | 説明 |
|------|------|
| **Individual Digest** | 単一Loop/Digestの要約 |
| **Overall Digest** | 複数Loop/Digestの統合要約 |
| **Provisional Digest** | 仮ダイジェスト（確定前の一時保存） |
| **Regular Digest** | 正式ダイジェスト（確定済み） |

### Essences
**定義**: GrandDigest と ShadowGrandDigest を格納するメタ情報ディレクトリ

- **配置先**: `{essences_dir}/`
- **含まれるファイル**:
  - `GrandDigest.txt` - 確定済み記憶
  - `ShadowGrandDigest.txt` - 未確定記憶

---

## 記憶構造

### GrandDigest
**定義**: 確定済みの長期記憶を格納するJSONファイル

- **ファイル**: `{essences_dir}/GrandDigest.txt`
- **内容**: 各階層（Weekly〜Centurial）の最新確定Digest
- **更新タイミング**: `/digest <type>` で階層を確定した時

> 📖 詳細な形式は [ARCHITECTURE.md](ARCHITECTURE.md#granddigesttxt) を参照

```json
{
  "metadata": { "last_updated": "...", "version": "1.0" },
  "major_digests": {
    "weekly": { "overall_digest": {...} },
    "monthly": { "overall_digest": {...} }
  }
}
```

### ShadowGrandDigest
**定義**: 未確定の増分ダイジェストを格納するJSONファイル

- **ファイル**: `{essences_dir}/ShadowGrandDigest.txt`
- **用途**: 新しいLoopの分析結果を一時保存し、threshold達成後にRegularに昇格
- **更新タイミング**: `/digest` で新規Loopを検出・分析した時

> 📖 詳細な形式は [ARCHITECTURE.md](ARCHITECTURE.md#shadowgranddigesttxt) を参照

```json
{
  "latest_digests": {
    "weekly": {
      "overall_digest": {
        "source_files": ["Loop0001.txt", "Loop0002.txt"],
        "keywords": ["<!-- PLACEHOLDER -->", ...],
        "abstract": "<!-- PLACEHOLDER: ... -->"
      }
    }
  }
}
```

### Provisional Digest
**定義**: 次階層用の個別ダイジェスト（一時ファイル）

- **配置先**: `{digests_dir}/{level_dir}/Provisional/`
- **形式**: `{prefix}{番号}_Individual.txt`
- **例**: `W0001_Individual.txt`
- **生存期間**: `/digest <type>` 実行時のRegularDigest確定まで

### Regular Digest
**定義**: 確定済みの正式ダイジェストファイル

- **配置先**: `{digests_dir}/{level_dir}/`
- **形式**: `{日付}_{prefix}{番号}_タイトル.txt`
- **例**: `2025-07-01_W0001_認知アーキテクチャ.txt`

---

## 8階層構造

EpisodicRAGは8つの階層で記憶を管理します（約108年分）：

| 階層 | プレフィックス | 時間スケール | デフォルト閾値 | 累積Loop数 |
|------|---------------|-------------|---------------|-----------|
| **Weekly** | W | ~1週間 | 5 Loops | 5 |
| **Monthly** | M | ~1ヶ月 | 5 Weekly | 25 |
| **Quarterly** | Q | ~3ヶ月 | 3 Monthly | 75 |
| **Annual** | A | ~1年 | 4 Quarterly | 300 |
| **Triennial** | T | ~3年 | 3 Annual | 900 |
| **Decadal** | D | ~9年 | 3 Triennial | 2,700 |
| **Multi-decadal** | MD | ~27年 | 3 Decadal | 8,100 |
| **Centurial** | C | ~108年 | 4 Multi-decadal | 32,400 |

---

## プロセス・操作

### まだらボケ
**定義**: AIがLoopの内容を記憶できていない（虫食い記憶）状態

**予防策**: `Loop追加 → /digest → Loop追加 → /digest` のサイクルを守る

> 📖 発生ケースと詳細な対策は [_common-concepts.md](../skills/shared/_common-concepts.md) を参照

### Threshold（閾値）
**定義**: 各階層のDigest生成に必要な最小ファイル数

- **設定場所**: `{plugin_root}/.claude-plugin/config.json`
- **変更方法**: `@digest-config` スキルで対話的に変更

### カスケード
**定義**: Digest確定時に上位階層へ自動的に伝播する処理

```
Weekly確定 → Monthly Shadow に追加
Monthly確定 → Quarterly Shadow に追加
...
```

### プレースホルダー
**定義**: ShadowGrandDigest内で`digest: null`となっている未分析状態

- **原因**: `/digest`処理中のエラー、または分析が未完了
- **解決方法**: `/digest`を再実行して分析を完了

---

## ファイル命名規則

### Loopファイル
```
形式: Loop[連番]_[タイトル].txt
連番: 4桁以上の数字（大きいほど新しい）
例:   Loop0001_初回セッション.txt
      Loop0186_認知アーキテクチャ論.txt
```

### Provisionalファイル
```
形式: {prefix}{番号}_Individual.txt
例:   W0001_Individual.txt
      M001_Individual.txt
```

### Regularファイル
```
形式: {日付}_{prefix}{番号}_タイトル.txt
例:   2025-07-01_W0001_認知アーキテクチャ.txt
      2025-08-15_M001_月次まとめ.txt
```

---

## コマンド・スキル

| コマンド/スキル | 説明 |
|----------------|------|
| `/digest` | 新規Loop検出と分析（まだらボケ予防） |
| `/digest <type>` | 特定階層の確定（例: `/digest weekly`） |
| `@digest-auto` | システム状態診断と推奨アクション提示 |
| `@digest-setup` | 初期セットアップ（対話的） |
| `@digest-config` | 設定変更（対話的） |

---

## 設定ファイル

### config.json
**配置**: `{plugin_root}/.claude-plugin/config.json`

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

---

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [QUICKSTART.md](QUICKSTART.md) - 5分チュートリアル
- [GUIDE.md](GUIDE.md) - ユーザーガイド
- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様

---
