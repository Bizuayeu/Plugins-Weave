[English](README.en.md) | 日本語

# Plugins-Weave

長期記憶・能動性・感情表現を実現する、自律的AIのためのClaude Codeプラグイン群

![Plugins-Weave - Claude Code Plugin Marketplace](./PluginsWeave.png)
[![Version](https://img.shields.io/badge/version-5.2.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Weave?

AIが単なる「ツール」から「協働パートナー」へ進化するためのプラグイン群です。

| 課題 | 解決策 | プラグイン |
|------|--------|-----------|
| **セッションを超えた記憶がない** | 8階層の長期記憶システム | EpisodicRAG |
| **受動的な応答しかできない** | 自発的なエッセイ・メール送信 | EmailingEssay |
| **テキストのみで表現が乏しい** | 感情に基づく表情表現 | VisualExpression |

---

## ナビゲーション

### EpisodicRAG

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.md) |
| 📚 **用語を調べたい** | [GLOSSARY](EpisodicRAG/GLOSSARY.md) |
| ❓ **問題を解決したい** | [FAQ](EpisodicRAG/docs/user/FAQ.md) / [TROUBLESHOOTING](EpisodicRAG/docs/user/TROUBLESHOOTING.md) |
| 🛠️ **開発に参加したい** | [CONTRIBUTING](EpisodicRAG/CONTRIBUTING.md) |

### EmailingEssay

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [SETUP](EmailingEssay/SETUP.md) |
| 💡 **コンセプトを知りたい** | [CONCEPT](EmailingEssay/CONCEPT.md) |
| 📖 **コマンド詳細** | [essay.md](EmailingEssay/commands/essay.md) |
| 🛠️ **開発に参加したい** | [CONTRIBUTING](EmailingEssay/CONTRIBUTING.md) |

### VisualExpression

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [README](VisualExpression/README.md) |
| 📖 **スキル仕様** | [SKILL](VisualExpression/skills/SKILL.md) |
| 🛠️ **開発に参加したい** | [CONTRIBUTING](VisualExpression/CONTRIBUTING.md) |

---

## クイックインストール

### 1. マーケットプレイス追加

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Weave
```

### 2. プラグインインストール

```ClaudeCLI
# EpisodicRAG（長期記憶管理）
/plugin install EpisodicRAG@Plugins-Weave

# EmailingEssay（エッセイ配信）
/plugin install EmailingEssay@Plugins-Weave

# VisualExpression（表情表現）
/plugin install VisualExpression@Plugins-Weave
```

---

## プラグイン詳細

### EpisodicRAG

**階層的記憶・ダイジェスト生成システム（8層100年）**

会話ログ（Loopファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。

#### 主な特徴

- **階層的記憶管理**: 8階層（週次～世紀）の自動ダイジェスト生成
- **まだらボケ回避**: 未処理Loopの即座検出で記憶の断片化を防止
- **セッション間継承**: GitHub経由で長期記憶を次セッションへ引き継ぎ

#### 主要コマンド

| コマンド | 説明 |
|---------|------|
| `/digest` | 新規Loop検出と分析 |
| `/digest weekly` | Weekly Digest確定 |
| `@digest-auto` | システム状態確認 |
| `@digest-setup` | 初期セットアップ |

→ [詳細README](EpisodicRAG/README.md) / [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.md) / [用語集](EpisodicRAG/GLOSSARY.md)

---

### EmailingEssay

**AI駆動エッセイ配信システム**

省察から生まれるプロアクティブなコミュニケーションを実現します。AIが自発的に考え、エッセイを執筆し、メールで届けます。

#### 主な特徴

- **深い省察**: UltraThinkを活用した深層思考
- **自発的配信**: スケジュール設定による自動送信
- **意識的な選択**: 送らないという選択も尊重

#### 主要コマンド

| コマンド | 説明 |
|---------|------|
| `/essay` | 即座に省察・出力 |
| `/essay wait <時刻>` | 指定時刻に配信 |
| `/essay schedule <頻度>` | 定期配信設定 |
| `/essay test` | メール設定テスト |

→ [詳細README](EmailingEssay/README.md) / [セットアップ](EmailingEssay/SETUP.md) / [コンセプト](EmailingEssay/CONCEPT.md)

---

### VisualExpression

**AIペルソナ向け表情表現システム**

感情に基づく表情切り替えを提供し、AIの表現力を拡張します。

| 表情例1 | 表情例2 |
|:---:|:---:|
| ![Expression Sample 1](./ExpressionSample01.jpg) | ![Expression Sample 2](./ExpressionSample02.jpg) |

#### 主な特徴

- **20種類の表情**: 5カテゴリ × 4表情
- **Nano Banana Pro連携**: 表情グリッド生成メタスクリプト
- **モバイル対応**: アーティファクトでスマートフォンでも表情表示
- **高速切り替え**: sedベースの即座切り替え

→ [詳細README](VisualExpression/README.md) / [スキル仕様](VisualExpression/skills/SKILL.md)

---

## ライセンス

**MIT License** - 詳細は [LICENSE](LICENSE) を参照

### 特許（EpisodicRAG）

**特願 2025-198943** - 階層的記憶・ダイジェスト生成システム

- 個人・非商用利用: MITライセンスの範囲で自由に利用可能
- 商用利用: 特許権との関係について事前にご相談ください

---

## サポート

- **Issues**: [GitHub Issues](https://github.com/Bizuayeu/Plugins-Weave/issues)
- **Author**: [Weave](https://note.com/weave_ai)

---
**Plugins-Weave** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
