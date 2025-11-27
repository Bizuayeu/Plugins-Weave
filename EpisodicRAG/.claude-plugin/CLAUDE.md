# CLAUDE.md - EpisodicRAG Plugin

このファイルは、Claude CodeがEpisodicRAGプラグインを開発・操作する際のガイドラインです。

---

## プロジェクト概要

EpisodicRAGは、会話ログ（Loopファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。8階層（Weekly → Centurial、約108年分）の記憶を自動管理します。

**バージョン**: 1.1.7+
**ファイルフォーマット**: 1.0

---

## ディレクトリ構造

```
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

以下の概念は `skills/shared/_common-concepts.md` で定義されています。他のドキュメントでは**参照リンク**を使用してください：

| 概念 | SSoTの場所 | 参照形式 |
|------|-----------|---------|
| まだらボケ | `_common-concepts.md#まだらボケとは` | `> 📖 詳細: [_common-concepts.md](../skills/shared/_common-concepts.md#まだらボケとは)` |
| 記憶定着サイクル | `_common-concepts.md#記憶定着サイクル` | 同上 |
| 階層的カスケード | `_common-concepts.md#階層的カスケード` | 同上 |

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

1. **概念の追加・変更**: まず `skills/shared/_common-concepts.md` を更新
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
| API仕様 | `docs/API_REFERENCE.md` |
| アーキテクチャ | `docs/ARCHITECTURE.md` |
| トラブルシューティング | `docs/TROUBLESHOOTING.md` |
| 用語集 | `docs/GLOSSARY.md` |
| 開発者ガイド | `CONTRIBUTING.md` |

---

## 注意事項

### やってはいけないこと

- `_common-concepts.md` の内容を他のファイルに**コピー**する（参照リンクを使用）
- `config.py` をバイパスしてパスを直接指定する
- テストを無効化してコミットする

### 推奨事項

- 新機能は `CHANGELOG.md` に記録
- 3回試行して失敗したら別のアプローチを検討
- 既存パターンに従う（CONTRIBUTING.md参照）

---

*このファイルは EpisodicRAG Plugin v1.1.7+ に対応しています。*
