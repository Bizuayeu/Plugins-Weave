# CorporateStrategist アーキテクチャ

プラグインの技術構造と設計思想を説明します。

## ディレクトリ構造

```
CorporateStrategist/
├── INDEX.md                    # プラグインエントリー
├── GLOSSARY.md                 # 用語集
├── DISCLAIMER.md               # 免責事項
├── QUICKSTART.md               # クイックスタート
├── CHANGELOG.md                # 変更履歴
├── LICENSE                     # ライセンス
│
├── .claude/
│   └── CLAUDE.md               # 開発ガイドライン
│
├── shared/                     # 共有リソース
│   ├── WeaveIdentity.md        # Weave人格定義
│   └── MSP_Practice_Manual.md  # MSP実践マニュアル
│
├── skills/                     # スキル定義
│   ├── corporate-strategist/   # 統合エントリー
│   ├── business-analyzer/      # 事業分析
│   ├── personnel-developer/    # 人材開発
│   ├── legal-adviser/          # 法務助言
│   └── foresight-reader/       # 洞察獲得
│
├── scripts/                    # Pythonスクリプト
│   ├── __init__.py
│   └── interfaces/             # CLIコマンド
│       ├── __init__.py
│       ├── qcd_analyzer.py
│       ├── iching_divination.py
│       └── fortune_teller_assessment.py
│
└── docs/                       # ドキュメント
    ├── user/
    │   └── GUIDE.md
    └── dev/
        └── ARCHITECTURE.md
```

---

## 設計原則

### 1. 選択的読み込み

トークン消費を最適化するため、必要なスキルのみ読み込みます。

```
選択されたスキル → SKILL.md + CLAUDE.md を読み込み
選択されていないスキル → 読み込まない
```

### 2. kebab-case命名規則

- **ディレクトリ**: CamelCase（プラグインルートのみ）
- **ファイル/コマンド**: kebab-case

### 3. 共有リソースの一元管理

複数スキルで使用するリソースは `shared/` に配置：
- WeaveIdentity.md
- MSP_Practice_Manual.md

---

## スキル構造

各スキルは以下のファイル構成を持ちます：

```
skills/{skill-name}/
├── SKILL.md      # スキル定義（YAML front matter必須）
├── CLAUDE.md     # 実装詳細（オプション）
├── references/   # 参照資料
└── templates/    # テンプレート（該当する場合）
```

### SKILL.md フロントマター

```yaml
---
name: skill-name      # kebab-case必須
description: ...      # 簡潔な説明
---
```

---

## CLIコマンド

`scripts/interfaces/` 配下のPythonスクリプトはCLIとして実行可能：

```bash
python -m scripts.interfaces.qcd_analyzer --help
python -m scripts.interfaces.iching_divination --help
python -m scripts.interfaces.fortune_teller_assessment --help
```

### デフォルトパス

各スクリプトはデータファイルを相対パスで参照：
- `iching_divination.py` → `skills/foresight-reader/i-ching/`
- `fortune_teller_assessment.py` → `skills/foresight-reader/seimei/`

---

## 依存関係

### Python標準ライブラリのみ

外部パッケージへの依存なし：
- `json`, `pathlib`, `argparse`, `hashlib`, `base64`, `time`, `datetime`

### 将来の拡張（Phase 2）

qcd_analyzer.py で予定：
- `requests`: HTTPリクエスト
- `beautifulsoup4`: HTMLパース
- `pandas`: データ分析

---

## 関連ドキュメント

- [INDEX.md](../../INDEX.md): ドキュメント一覧
- [.claude/CLAUDE.md](../../.claude/CLAUDE.md): 開発ガイドライン

---
*CorporateStrategist Architecture Document*
