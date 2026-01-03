[English](README.md) | 日本語

# VisualExpression

感情に基づく表情切り替え機能を持つ、AIペルソナ向けビジュアル表現システム。

## 目次

- [前提条件](#前提条件)
- [クイックスタート](#クイックスタート)
- [ドキュメントマップ](#ドキュメントマップ)
- [機能](#機能)
- [関連リンク](#関連リンク)

---

## 前提条件

- Python 3.10+
- Pillow 10.0+ (`pip install Pillow>=10.0`)

---

## クイックスタート

1. Nano Banana Proで表情グリッド画像を生成（`skills/scripts/MetaGenerateExpression.jp.md` 参照）
2. グリッド画像からHTMLをビルド:
   ```bash
   cd skills/scripts/MakeExpressionJson
   python main.py your_grid.png
   ```
3. 生成されたzipをclaude.aiにアップロード、またはClaude Codeプラグインとしてインストール

---

## ドキュメントマップ

| ファイル | 対象 | 内容 |
|----------|------|------|
| [README.md](README.md) | 全員 | クイックスタート（英語版） |
| [README.jp.md](README.jp.md) | 全員 | クイックスタート（このファイル） |
| [CHANGELOG.md](CHANGELOG.md) | 全員 | バージョン履歴 |
| [LICENSE](LICENSE) | 全員 | MITライセンス |
| [CLAUDE.md](CLAUDE.md) | 開発者 | 開発ガイドライン |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 開発者 | セットアップ＆貢献ガイド |
| [skills/SKILL.md](skills/SKILL.md) | ユーザー | 完全ドキュメント |
| [skills/scripts/MetaGenerateExpression.jp.md](skills/scripts/MetaGenerateExpression.jp.md) | ユーザー | Nano Banana Proプロンプト生成ガイド |
| [.claude-plugin/plugin.json](.claude-plugin/plugin.json) | 開発者 | プラグインメタデータ |

---

## 機能

- **20種類の表情バリエーション**: 5カテゴリ × 各4表情
- **Nano Banana Pro統合**: 表情グリッド生成用メタスクリプト
- **ワンクリックビルド**: グリッド画像からBase64埋め込みHTMLを生成
- **クロスプラットフォーム**: claude.aiとClaude Codeの両方で動作
- **sed ベースの切り替え**: 単一コマンドによる高速な表情変更

---

## 関連リンク

- [skills/SKILL.md](skills/SKILL.md) - 完全な使用ガイド
- [GitHub](https://github.com/Bizuayeu/Plugins-Weave) - ソースリポジトリ

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
