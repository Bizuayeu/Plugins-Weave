# CLAUDE.md - EpisodicRAG Plugin

このファイルは、Claude CodeがEpisodicRAGプラグインを開発・操作する際のガイドラインです。

> **人間の開発者向け**: [CONTRIBUTING.md](../CONTRIBUTING.md) を参照してください。

---

## 目次

**概要**
1. [プロジェクト概要](#プロジェクト概要)
2. [利用可能な機能](#利用可能な機能)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [永続化パス](#永続化パス-v520) *(v5.2.0+)*

**アーキテクチャ**
5. [Clean Architecture](#clean-architecture)
6. [Single Source of Truth (SSoT)](#single-source-of-truth-ssot)

**開発ガイド**
7. [開発ワークフロー](#開発ワークフロー)
8. [コーディング規約](#コーディング規約)

**リファレンス**
9. [主要ファイル参照](#主要ファイル参照)
10. [注意事項](#注意事項)

---

## プロジェクト概要

EpisodicRAGは、会話ログ（Loopファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。8階層（Weekly → Centurial、約108年分）の記憶を自動管理します。

**バージョン**: [version.py](../scripts/domain/version.py) 参照
**ファイルフォーマット**: 1.0

---

## 利用可能な機能

### コマンド

| コマンド | 用途 |
|---------|------|
| `/digest` | 新規Loop検出・分析（記憶定着） |
| `/digest weekly` | Weekly Digest確定 |
| `/digest monthly` | Monthly Digest確定 |

> 📖 詳細: [commands/digest.md](../commands/digest.md)

### スキル

| スキル | 用途 |
|--------|------|
| `@digest-auto` | システム状態診断・推奨アクション |
| `@digest-setup` | 初期セットアップ |
| `@digest-config` | 設定変更 |

### エージェント

| エージェント | 用途 |
|------------|------|
| `DigestAnalyzer` | Loop/Digestの並列分析 |

### 基本ワークフロー

```text
Loop追加 → /digest → Loop追加 → /digest → ...
```

この「記憶定着サイクル」を守ることで、AIは全てのLoopを記憶できます。

> 📖 詳細: [用語集 - 記憶定着サイクル](../GLOSSARY.md#記憶定着サイクル)

---

## ディレクトリ構成

```text
EpisodicRAG/
├── .claude-plugin/          # プラグインメタデータ・設定
├── agents/                  # AIエージェント仕様
├── commands/                # スラッシュコマンド仕様
├── docs/                    # ドキュメント
│   ├── dev/                 # 開発者向け（ARCHITECTURE, API等）
│   └── user/                # ユーザー向け（GUIDE, FAQ等）
├── scripts/                 # Python/Bash実装（Clean Architecture）
│   ├── domain/              # コアビジネスロジック
│   ├── infrastructure/      # 外部関心事
│   ├── application/         # ユースケース
│   ├── interfaces/          # エントリーポイント・CLI
│   ├── tools/               # 開発ツール (v4.1.0+)
│   └── test/                # ユニットテスト
├── skills/                  # スキル仕様
│   └── shared/              # 共有コンポーネント（SSoT）
├── CHANGELOG.md             # バージョン履歴
└── CONTRIBUTING.md          # 開発者ガイド
```

---

## 永続化パス *(v5.2.0+)*

設定ファイルとデータは**永続化パス**に保存されます。プラグイン更新時も設定は保持されます。

### デフォルトパス

```text
~/.claude/plugins/.episodicrag/
├── config.json          # 設定ファイル（必須）
├── Loops/               # Loopファイル（config.jsonで変更可）
├── Digests/             # Digestファイル（config.jsonで変更可）
└── Identities/          # Identityファイル（config.jsonで変更可）
```

### アクセス方法

```python
# 永続化パスの取得（推奨）
from infrastructure.config import get_persistent_config_dir

config_dir = get_persistent_config_dir()  # ~/.claude/plugins/.episodicrag/

# 設定ファイルパスの取得
from infrastructure.config import get_config_path

config_path = get_config_path()  # ~/.claude/plugins/.episodicrag/config.json
```

### テスト時のオーバーライド

```bash
export EPISODICRAG_CONFIG_DIR=/tmp/test-episodicrag
python -m pytest test/ -v
```

> 📖 詳細は [infrastructure.md](../docs/dev/api/infrastructure.md#永続化パスinfrastructureconfigpersistent_pathpy-v520) を参照

---

## Clean Architecture

スクリプトは4層アーキテクチャで構成されています。v4.0.0でconfig層を3つのサブレイヤーに分解しました。

| 層 | ディレクトリ | 役割 |
|----|-------------|------|
| Domain | `scripts/domain/` | コアビジネスロジック（定数、型、例外） |
| ├ config | `scripts/domain/config/` | 設定定数・バリデーション |
| Infrastructure | `scripts/infrastructure/` | 外部関心事（JSON操作、ファイルスキャン） |
| ├ config | `scripts/infrastructure/config/` | 設定ファイルI/O・パス解決 |
| Application | `scripts/application/` | ユースケース（Shadow管理、GrandDigest管理） |
| ├ config | `scripts/application/config/` | DigestConfig（Facade） |
| Interfaces | `scripts/interfaces/` | エントリーポイント・CLI |

### 推奨インポートパス

```python
# Domain層
from domain import LEVEL_CONFIG, __version__
from domain.config import REQUIRED_CONFIG_KEYS

# Infrastructure層
from infrastructure import load_json, save_json

# Domain層（バリデーション）
from domain.validators import validate_type, is_valid_dict
from application.config import DigestConfig

# Interfaces層
from interfaces import DigestFinalizerFromShadow
```

> 📖 詳細は [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md) を参照

---

## Single Source of Truth (SSoT)

### 共有概念の定義

用語・共通概念は `GLOSSARY.md`（用語集・リファレンス）で定義されています。他のドキュメントでは**参照リンク**を使用してください：

| 概念 | SSoTの場所 | 参照形式 |
|------|-----------|---------|
| まだらボケ | `GLOSSARY.md#まだらボケ` | `> 📖 詳細: [用語集](../../GLOSSARY.md#まだらボケ)` |
| 記憶定着サイクル | `GLOSSARY.md#記憶定着サイクル` | 同上 |
| 8階層構造 | `GLOSSARY.md#8階層構造` | 同上 |
| 基本概念（パス用語） | `GLOSSARY.md#基本概念` | 同上 |

### 実装ガイドライン

実装に関する共通ルールは `skills/shared/_implementation-notes.md` で定義されています：

- UIメッセージの出力形式
- config.pyへの依存
- エラーハンドリングパターン
- 階層順序の維持

---

## 開発ワークフロー

### コード変更時

1. 関連するテストを確認: `scripts/test/`
2. 変更を実装
3. テスト実行: `python -m pytest scripts/test/ -v`
4. 動作確認（以下のいずれか）:
   - スキル経由: `/plugin uninstall` → `/plugin install` → `@digest-auto`
   - CLI直接実行: `python -m interfaces.digest_auto`

### ドキュメント変更時

1. **概念の追加・変更**: まず `GLOSSARY.md`（用語集・リファレンス）を更新
2. **参照の更新**: 関連ドキュメントの参照リンクを確認
3. **breadcrumbの維持**: `docs/` 配下のファイルは breadcrumb を含める

```markdown
[Home](../README.md) > [Docs](README.md) > [ファイル名]
```

---

## コーディング規約

### Python

- PEP 8 準拠
- `DigestConfig` 経由でパス情報を取得
- `load_or_create()` パターンでデータファイル管理

### Markdown

- 日本語メイン、技術用語は英語可
- コードブロックには言語指定
- 内部リンクは相対パス

### 用語統一

| 用語 | 表記 | 説明 |
|------|------|------|
| Loop | 大文字 | 会話ログファイル |
| Digest | 大文字 | ダイジェストファイル/概念 |
| GrandDigest | スペースなし | 統合データファイル |
| ShadowGrandDigest | スペースなし | 未確定データファイル |

---

## 主要ファイル参照

| 目的 | ファイル |
|------|---------|
| ドキュメント一覧 | `INDEX.md` |
| API仕様 | `docs/dev/API_REFERENCE.md` |
| アーキテクチャ | `docs/dev/ARCHITECTURE.md` |
| トラブルシューティング | `docs/user/TROUBLESHOOTING.md` |
| 用語集 | `GLOSSARY.md` |
| 開発者ガイド | `CONTRIBUTING.md` |

---

## 注意事項

### やってはいけないこと

- `GLOSSARY.md`（用語集）の内容を他のファイルに**コピー**する（参照リンクを使用）
- `config.py` をバイパスしてパスを直接指定する
- テストを無効化してコミットする

### 推奨事項

- 新機能は `CHANGELOG.md` に記録
- 3回試行して失敗したら別のアプローチを検討
- 既存パターンに従う（CONTRIBUTING.md参照）

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
