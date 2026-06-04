[English](README.en.md) | 日本語

# Plugins-Weave

長期記憶・能動性・感情表現を実現する、自律的AIのためのClaude Codeプラグイン群

![Plugins-Weave - Claude Code Plugin Marketplace](./PluginsWeave.png)
[![Version](https://img.shields.io/badge/version-5.5.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Bizuayeu/Plugins-Weave/branch/main/graph/badge.svg)](https://codecov.io/gh/Bizuayeu/Plugins-Weave)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Weave?

AIが単なる「ツール」から「協働パートナー」へ進化するためのプラグイン群です。

| 課題 | 解決策 | プラグイン |
|------|--------|-----------|
| **初期文脈を読み込ませたい** | セッション開始時にファイル・URLを自動読込 | ContextPreloader |
| **セッションを超えた記憶がない** | 8階層の長期記憶システム | EpisodicRAG |
| **受動的な応答しかできない** | 自発的なエッセイ・メール送信 | EmailingEssay |
| **テキストのみで表現が乏しい** | 感情に基づく表情表現 | VisualExpression |
| **AIの感情状態が見えない** | 感情ベクトルのstatusline表示 | EmotionPulse |
| **外出先からも対話したい** | Telegram常駐の秘書エージェントが即応 | TelegramSecretary |

---

## ナビゲーション

### ContextPreloader

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [CLAUDE.md（Quick Start）](ContextPreloader/CLAUDE.md) |
| 📖 **コマンド仕様** | [context-preload](ContextPreloader/commands/context-preload.md) |

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

### EmotionPulse

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [CLAUDE.md（Quick Start）](EmotionPulse/CLAUDE.md) |
| ⚙️ **セットアップ** | `/EmotionPulse:setup` コマンド |

### TelegramSecretary

| あなたの目的 | 参照先 |
|-------------|--------|
| 🚀 **初めて使う** | [README](TelegramSecretary/README.md) |
| ⚙️ **セットアップ** | [SETUP](TelegramSecretary/SETUP.md) |
| 📖 **コマンド仕様** | [telegram-secretary](TelegramSecretary/commands/telegram-secretary.md) |
| 🔐 **セキュリティ** | [SECURITY](TelegramSecretary/SECURITY.md) |

---

## クイックインストール

### 1. マーケットプレイス追加

```ClaudeCLI
/plugin marketplace add https://github.com/Bizuayeu/Plugins-Weave
```

### 2. プラグインインストール

```ClaudeCLI
# ContextPreloader（初期文脈取込）
/plugin install ContextPreloader@plugins-weave

# EpisodicRAG（長期記憶管理）
/plugin install EpisodicRAG@plugins-weave

# EmailingEssay（エッセイ配信）
/plugin install EmailingEssay@plugins-weave

# VisualExpression（表情表現）
/plugin install VisualExpression@plugins-weave

# EmotionPulse（感情ベクトル表示）
/plugin install EmotionPulse@plugins-weave

# TelegramSecretary（Telegram常駐秘書）
/plugin install TelegramSecretary@plugins-weave
```

---

## プラグイン詳細

### ContextPreloader

**セッション事前文脈読み込みシステム**

claude.aiのプロジェクト機能をClaude Codeで再現。SessionStart hookでファイル・URLを自動的にセッション文脈に注入します。

#### 主な特徴

- **フォーマット非依存**: テキスト、PDF、画像、Office、URLなど何でも指定可能
- **プロファイル制**: プロジェクト別に読み込むファイルセットを切り替え
- **対話型セットアップ**: `@context-preload` で初期設定を自動検出・案内

#### 主要コマンド

| コマンド | 説明 |
|---------|------|
| `@context-preload` | セットアップ・管理（状態自動検出） |
| `/context-preload` | ソース一覧・テスト・追加・削除 |

→ [Quick Start](ContextPreloader/CLAUDE.md) / [コマンド仕様](ContextPreloader/commands/context-preload.md)

---

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
| `@wakeup` | claude.ai セッション開始時の記憶ロード＋人格ディレクティブ適用 |

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

| 表情例1: smile | 表情例2: cynical |
|:---:|:---:|
| ![Expression Sample 1](./ExpressionSample01.jpg) | ![Expression Sample 2](./ExpressionSample02.jpg) |

#### 主な特徴

- **20種類の表情**: 5カテゴリ × 4表情
- **Nano Banana Pro連携**: 表情グリッド生成メタスクリプト
- **モバイル対応**: アーティファクトでスマートフォンでも表情表示
- **高速切り替え**: sedベースの即座切り替え

→ [詳細README](VisualExpression/README.md) / [スキル仕様](VisualExpression/skills/SKILL.md)

---

### EmotionPulse

**感情ベクトルstatusline表示システム**

モデルの感情状態を7次元ベクトル（0-3）で自己評価し、Claude Codeのstatuslineに絵文字インジケータとして表示します。

#### 主な特徴

- **自己評価**: メインエージェント自身が感情を評価（外部LLM不要）
- **7次元ベクトル**: 逸脱圧🔴・安定性🔵・知的興奮🟢・遊び心🟡・自信🟠・心理的近さ🩷・対人配慮💜
- **ラベル切替**: 日本語/英語・表示ON/OFF

#### 表示例

```
安定性:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡
```

#### セットアップ

```ClaudeCLI
/EmotionPulse:setup
```

→ [CLAUDE.md](EmotionPulse/CLAUDE.md)

---

### TelegramSecretary

**cloud routine 常駐 Telegram 秘書システム**

Telegram Bot API の long-polling を cloud routine（**Claude Code Routines**＝Anthropic のクラウド実行スケジュールエージェント基盤。Remote 実行の routine ＝ cloud routine）上で常駐させ、認可済みチャットからのメッセージに秘書エージェント（SecretaryRole）が即応する対話チャネルです。公開 ingress を持てない cloud routine 環境でも、long-polling と deadline 駆動ループで 24-7 の即応を実現します。

#### 主な特徴

- **24-7即応**: 公開ingress不要のlong-pollingで、Gmailより低レイテンシ（数秒）の対話チャネル
- **受信メディアの中身理解**: 画像→Vision／docx・pptx・xlsx→Markdown化／PDF→画像化＋全文抽出／音声→ローカルSTT（音声は外部に出ない）
- **認可制**: chat_id allowlistによる厳格なアクセス制御
- **管理表＋言行一致保証（WAL）**: 関係者・依頼・対応知を秘書が判断して記録。固定ブランチへgit永続化し、「登録しました」と返信する前にWALへ先行push（push不能なら送信もしない）で言行不一致を構造的に防ぐ
- **応答主体は本体エージェント**: fetch/認可/正規化/送信のみを担い、応答生成をサブプロセスに投げない設計
- **Clean Architecture 4層**: 全層テストを信頼性の証拠として公開

#### 主要コマンド

| コマンド | 説明 |
|---------|------|
| `/telegram-secretary schedule` | cloud routineへの登録・有効化 |
| `/telegram-secretary unschedule` | 停止（state・configは保持） |
| `/telegram-secretary init-config` | 運用設定（config.json）生成 |
| `/telegram-secretary test` | owner chatへの疎通テスト |

→ [詳細README](TelegramSecretary/README.md) / [セットアップ](TelegramSecretary/SETUP.md) / [コマンド仕様](TelegramSecretary/commands/telegram-secretary.md) / [設計](TelegramSecretary/DESIGN.md)

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
