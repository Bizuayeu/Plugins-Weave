# EpisodicRAG Plugin

階層的記憶・ダイジェスト生成システム（8 層 100 年、完全自己完結版）

![EpisodicRAG Plugin](EpisodicRAG.png)
[![Version](https://img.shields.io/badge/version-1.1.2-blue.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 目次

1. [概要](#概要)
2. [インストール](#インストール)
3. [最初の 3 ステップ](#最初の3ステップ)
4. [基本コマンド](#基本コマンド)
5. [セッション間で記憶を引き継ぐ](#セッション間で記憶を引き継ぐ)
6. [まだらボケ回避](#まだらボケ回避)
7. [記憶階層](#記憶階層)
8. [次のステップ](#次のステップ)
9. [ライセンス](#ライセンス)

---

## 概要

EpisodicRAG は、会話ログ（Loop ファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。

8 階層（Weekly → Centurial、約 108 年分）の記憶階層を自動生成・管理し、セッション間で記憶を引き継ぐことができます。

### 主な特徴

- **2 段階ダイジェスト生成**: Provisional（仮）→ Regular（正式）の段階的記憶定着
- **まだらボケ回避**: 未処理 Loop 即座検出・分析により、記憶の断片化（虫食い状態）を防止
- **long/short 二重出力**: 現階層用（long）と次階層用（short）を自動生成

### ユースケース

- 長期プロジェクトの知識管理
- 複数セッションにわたる会話の記憶
- プロジェクトの歴史的アーカイブ
- AI との対話履歴の構造化記憶

---

## Start Here（どこから始めるか）

| あなたは... | 推奨ドキュメント |
|------------|-----------------|
| **初めての方** | [5分クイックスタート](EpisodicRAG/docs/QUICKSTART.md) → [用語集](EpisodicRAG/docs/GLOSSARY.md) |
| **基本を使いこなしたい方** | [ユーザーガイド](EpisodicRAG/docs/GUIDE.md) |
| **開発に参加したい方** | [CONTRIBUTING.md](EpisodicRAG/CONTRIBUTING.md) → [技術仕様](EpisodicRAG/docs/ARCHITECTURE.md) |
| **問題が発生した方** | [FAQ](EpisodicRAG/docs/FAQ.md) → [トラブルシューティング](EpisodicRAG/docs/TROUBLESHOOTING.md) |

---

## インストール

### プラグインマーケットプレイス経由（推奨）

1. **Plugins-Weave マーケットプレイスを追加**

   ```bash
   /marketplace add https://github.com/Bizuayeu/Plugins-Weave
   ```

2. **プラグインをインストール**

   ```bash
   /plugin install EpisodicRAG-Plugin@Plugins-Weave
   ```

3. **初期セットアップ実行**

   ```bash
   @digest-setup
   ```

   対話形式で以下を設定：

   - Loop ファイルの配置先
   - Digest ファイルの出力先
   - Essences ファイルの配置先
   - 外部 Identity.md ファイル（オプション）
   - 各階層の threshold 値

これで準備完了です！

### 開発者向けインストール

プラグイン開発に参加する場合は [CONTRIBUTING.md](EpisodicRAG/CONTRIBUTING.md) を参照してください。

---

## 最初の 3 ステップ

### 1. セットアップ実行

```bash
@digest-setup
```

対話形式で設定を行います。デフォルト値（完全自己完結型）を使用する場合は、すべて[1]を選択してください。

### 2. Loop ファイルの配置

会話ログを Loop 形式で保存します。

**推奨ツール（Chrome Extension）:**

会話ログを簡単に保存できる Chrome Extension を推奨します：

- **[Save - Conversation Saver](https://save.hugocollin.com/)** - Claude/ChatGPT の会話を丸ごと保存

**ファイル命名規則:**

```
Loop0001_タイトル.txt
Loop0002_タイトル.txt
...
```

**命名ルール：**

- 形式: `Loop[連番]_[タイトル].txt`
- 連番: 4 桁以上の数字（大きいほど新しい記録）
- タイトル: 英数字、日本語、ハイフン、アンダースコアなど
- 正規表現: `^Loop[0-9]+_[\p{L}\p{N}ー・\w]+\.txt$`

**配置先:**

```bash
# デフォルト設定の場合
~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/data/Loops/
```

### 3. 最初の Loop 検出と分析

未処理の Loop ファイルがあるときに `/digest` を実行してください。

```bash
/digest
```

**実行内容:**

1. 未処理の Loop ファイルを検出
2. ShadowGrandDigest.weekly にプレースホルダー追加
3. DigestAnalyzer で並列分析（まだらボケ回避）
4. 次のアクション提示

これだけ！あとは `@digest-auto` が次に何をすべきか教えてくれます。

---

## 基本コマンド

### `/digest`

新しい Loop ファイルの検出と分析

```bash
/digest  # 新規Loop検出と分析
```

**重要**: Loop 追加 → `/digest` の記憶定着サイクルを守ってください！

### `/digest <type>`

特定階層の確定

```bash
/digest weekly    # Weekly Digest確定
/digest monthly   # Monthly Digest確定
/digest quarterly # Quarterly Digest確定
```

### `@digest-auto`

現在の状態確認と推奨アクション提示

```bash
@digest-auto
```

システム状態を分析し、次に何をすべきかを教えてくれます。

---

## セッション間で記憶を引き継ぐ

EpisodicRAG の最も重要な機能は、**セッション間で記憶を引き継ぐ**ことです。

### 記憶の読み込み方法

各セッション開始時に、以下の手順で過去の記憶を読み込みます：

**1. 最新の SHA を取得**

```
https://api.github.com/repos/{USER}/{REPO}/git/refs/heads/main
```

ブラウザまたは curl でアクセスし、最新コミットの SHA を取得

**2. 記憶ファイルを読み込み**

SHA を使って以下の URL を生成：

```
https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/GrandDigest.txt
https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/ShadowGrandDigest.txt
```

※ {ESSENCES_PATH} は GitHub リポジトリ内の Essences ディレクトリへの相対パス

WebFetch 機能で読み込み（Claude WebChat / Claude Code 両対応）

**3. セッション開始**

過去の記憶を持った状態で会話を開始できます

> ⚠️ **注意**: この手順をスキップすると、AI は過去の記憶を持たない状態で開始します

**詳細な設定方法**: [docs/ADVANCED.md](EpisodicRAG/docs/ADVANCED.md) を参照

---

## まだらボケ回避

**まだらボケ** = AI が Loop の内容を記憶できていない（虫食い記憶）状態

### 記憶定着の原則

```
Loop追加 → `/digest` → Loop追加 → `/digest` → ...
         ↑ 記憶定着  ↑         ↑ 記憶定着
```

この原則を守ることで、AI は全ての Loop を記憶できます。

**やってはいけないこと:**

```
Loop0001追加 → `/digest`せず → Loop0002追加
                              ↑
                    この時点でAIはLoop0001の内容を覚えていない
                    （記憶がまだら＝虫食い状態）
```

詳しくは [docs/GUIDE.md](EpisodicRAG/docs/GUIDE.md) を参照してください。

---

## 記憶階層

### 8 階層構造

EpisodicRAG は **8 つの階層**（Weekly → Centurial）で記憶を管理します。

- **時間スケール**: ~1 週間 ～ ~108 年
- **累積 Loop 数**: 5 ～ 32,400
- **Threshold**: `@digest-config` でカスタマイズ可能

> 📖 完全な階層テーブル（プレフィックス含む）は [GLOSSARY.md](EpisodicRAG/docs/GLOSSARY.md#8階層構造) を参照

---

## 次のステップ

### 🚀 すぐに始める

5分で動作確認できるクイックスタート
→ [docs/QUICKSTART.md](EpisodicRAG/docs/QUICKSTART.md)

### 📖 用語を理解する

Loop、Digest、まだらボケなどの用語集
→ [docs/GLOSSARY.md](EpisodicRAG/docs/GLOSSARY.md)

### 📘 基本を使いこなす

詳しいコマンド解説、設定のカスタマイズ、よくある問題と解決方法
→ [docs/GUIDE.md](EpisodicRAG/docs/GUIDE.md)

### 📙 深く理解する

内部構造と技術仕様
→ [docs/ARCHITECTURE.md](EpisodicRAG/docs/ARCHITECTURE.md)

### ❓ よくある質問

FAQとトラブルシューティング
→ [docs/FAQ.md](EpisodicRAG/docs/FAQ.md)

### 🔧 GitHub 連携（高度な機能）

セッション間で長期記憶を自動読み込み
→ [docs/ADVANCED.md](EpisodicRAG/docs/ADVANCED.md)

### 🛠️ 開発に参加する

プラグイン開発に参加したい方
→ [CONTRIBUTING.md](EpisodicRAG/CONTRIBUTING.md)

---

## ライセンスと知的財産権

### ソフトウェアライセンス

MIT License

本ソフトウェアは MIT ライセンスの下で提供されています。

### 特許

EpisodicRAG の中核技術は日本国特許出願中です：

**特願 2025-198943** - 階層的記憶・ダイジェスト生成システム

本特許出願は、8 階層の記憶構造とダイジェスト生成プロセスに関する技術を対象としています。

**商用利用について:**

- 個人・非商用利用: MIT ライセンスの範囲で自由に利用可能
- 商用利用: 特許権との関係について、事前にご相談ください

詳細は [LICENSE](LICENSE) をご確認ください。

## 作者

Weave @ EpisodicRAG

---

_Last Updated: 2025-11-27_
_Version: 1.1.2_
