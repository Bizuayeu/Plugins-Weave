# CLAUDE.md - EpisodicRAG Plugin

このファイルは、Claude CodeがEpisodicRAGプラグインを開発・操作する際のガイドラインです。

> **人間の開発者向け**: [CONTRIBUTING.md](../CONTRIBUTING.md) を参照してください。

---

## プロジェクト概要

EpisodicRAGは、会話ログ（Loopファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。8階層（Weekly → Centurial、約108年分）の記憶を自動管理します。

**バージョン**: [version.py](../scripts/domain/version.py) 参照
**ファイルフォーマット**: 1.0

---

## ディレクトリ構造

```text
EpisodicRAG/
├── .claude-plugin/          # プラグインメタデータ・設定
├── agents/                  # AIエージェント仕様
├── commands/                # スラッシュコマンド仕様
├── docs/                    # ユーザードキュメント
├── scripts/                 # Python/Bash実装
│   └── test/                # ユニットテスト
├── skills/                  # スキル仕様
│   └── shared/              # 共有コンポーネント（SSoT）
├── CHANGELOG.md             # バージョン履歴
└── CONTRIBUTING.md          # 開発者ガイド
```

---

## Single Source of Truth (SSoT)

### 共有概念の定義

用語・共通概念は `README.md`（用語集・リファレンス）で定義されています。他のドキュメントでは**参照リンク**を使用してください：

| 概念 | SSoTの場所 | 参照形式 |
|------|-----------|---------|
| まだらボケ | `README.md#まだらボケ` | `> 📖 詳細: [用語集](../../README.md#まだらボケ)` |
| 記憶定着サイクル | `README.md#記憶定着サイクル` | 同上 |
| 8階層構造 | `README.md#8階層構造` | 同上 |
| 基本概念（パス用語） | `README.md#基本概念` | 同上 |

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
4. 動作確認: `/plugin uninstall` → `/plugin install` → `@digest-auto`

### ドキュメント変更時

1. **概念の追加・変更**: まず `README.md`（用語集・リファレンス）を更新
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

## Clean Architecture (v2.0.0+)

スクリプトは4層アーキテクチャで構成されています：

| 層 | ディレクトリ | 役割 |
|----|-------------|------|
| Domain | `scripts/domain/` | コアビジネスロジック（定数、型、例外） |
| Infrastructure | `scripts/infrastructure/` | 外部関心事（JSON操作、ファイルスキャン） |
| Application | `scripts/application/` | ユースケース（Shadow管理、GrandDigest管理） |
| Interfaces | `scripts/interfaces/` | エントリーポイント |

### 推奨インポートパス

```python
from domain import LEVEL_CONFIG, __version__
from application.validators import validate_dict
from interfaces import DigestFinalizerFromShadow
```

> ⚠️ v2.0.0でClean Architecture移行に伴い、旧インポートパス（`from validators import ...`等）は動作しません。
> 📖 詳細は [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md) を参照

---

## 主要ファイル参照

| 目的 | ファイル |
|------|---------|
| API仕様 | `docs/API_REFERENCE.md` |
| アーキテクチャ | `docs/ARCHITECTURE.md` |
| トラブルシューティング | `docs/TROUBLESHOOTING.md` |
| 用語集 | `README.md` |
| 開発者ガイド | `CONTRIBUTING.md` |

---

## 注意事項

### やってはいけないこと

- `README.md`（用語集）の内容を他のファイルに**コピー**する（参照リンクを使用）
- `config.py` をバイパスしてパスを直接指定する
- テストを無効化してコミットする

### 推奨事項

- 新機能は `CHANGELOG.md` に記録
- 3回試行して失敗したら別のアプローチを検討
- 既存パターンに従う（CONTRIBUTING.md参照）

---

*このファイルは EpisodicRAG Plugin v2.0.0+ に対応しています。*
