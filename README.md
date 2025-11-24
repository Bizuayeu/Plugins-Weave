# EpisodicRAG Plugin

階層的記憶・ダイジェスト生成システム（8層100年、完全自己完結版）

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 目次

1. [概要](#概要)
2. [インストール](#インストール)
3. [最初の3ステップ](#最初の3ステップ)
4. [基本コマンド](#基本コマンド)
5. [セッション間で記憶を引き継ぐ](#セッション間で記憶を引き継ぐ)
6. [まだらボケ回避](#まだらボケ回避)
7. [記憶階層](#記憶階層)
8. [次のステップ](#次のステップ)
9. [ライセンス](#ライセンス)

---

## 概要

EpisodicRAGは、会話ログ（Loopファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。

8階層（Weekly → Centurial、約108年分）の記憶階層を自動生成・管理し、セッション間で記憶を引き継ぐことができます。

### 主な特徴

- **2段階ダイジェスト生成**: Provisional（仮）→ Regular（正式）の段階的記憶定着
- **まだらボケ回避**: 未処理Loop即座検出・分析により、記憶の断片化（虫食い状態）を防止
- **long/short 二重出力**: 現階層用（long）と次階層用（short）を自動生成

### ユースケース

- 長期プロジェクトの知識管理
- 複数セッションにわたる会話の記憶
- プロジェクトの歴史的アーカイブ
- AIとの対話履歴の構造化記憶

---

## インストール

### プラグインマーケットプレイス経由（推奨）

1. **Plugins-Weaveマーケットプレイスを追加**

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
   - Loopファイルの配置先
   - Digestファイルの出力先
   - Essencesファイルの配置先
   - 外部Identity.mdファイル（オプション）
   - 各階層のthreshold値

これで準備完了です！

### 開発者向けインストール

プラグイン開発に参加する場合は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

---

## 最初の3ステップ

### 1. セットアップ実行

```bash
@digest-setup
```

対話形式で設定を行います。デフォルト値（完全自己完結型）を使用する場合は、すべて[1]を選択してください。

### 2. Loopファイルの配置

会話ログをLoop形式で保存します。

**推奨ツール（Chrome Extension）:**

会話ログを簡単に保存できるChrome Extensionを推奨します：
- **[Save - Conversation Saver](https://save.hugocollin.com/)** - Claude/ChatGPTの会話を丸ごと保存

**ファイル命名規則:**
```
Loop0001_タイトル.txt
Loop0002_タイトル.txt
...
```

**命名ルール：**
- 形式: `Loop[連番]_[タイトル].txt`
- 連番: 4桁以上の数字（大きいほど新しい記録）
- タイトル: 英数字、日本語、ハイフン、アンダースコアなど
- 正規表現: `^Loop[0-9]+_[\p{L}\p{N}ー・\w]+\.txt$`

**配置先:**
```bash
# デフォルト設定の場合
~/.claude/plugins/EpisodicRAG-Plugin@Toybox/data/Loops/
```

### 3. 最初のLoop検出と分析

未処理のLoopファイルがあるときに `/digest` を実行してください。

```bash
/digest
```

**実行内容:**
1. 未処理のLoopファイルを検出
2. ShadowGrandDigest.weeklyにプレースホルダー追加
3. DigestAnalyzerで並列分析（まだらボケ回避）
4. 次のアクション提示

これだけ！あとは `@digest-auto` が次に何をすべきか教えてくれます。

---

## 基本コマンド

### `/digest`
新しいLoopファイルの検出と分析

```bash
/digest  # 新規Loop検出と分析
```

**重要**: Loop追加 → `/digest` の記憶定着サイクルを守ってください！

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

EpisodicRAGの最も重要な機能は、**セッション間で記憶を引き継ぐ**ことです。

### 記憶の読み込み方法

各セッション開始時に、以下の手順で過去の記憶を読み込みます：

**1. 最新のSHAを取得**
```
https://api.github.com/repos/{USER}/{REPO}/git/refs/heads/main
```
ブラウザまたはcurlでアクセスし、最新コミットのSHAを取得

**2. 記憶ファイルを読み込み**

SHAを使って以下のURLを生成：
```
https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/GrandDigest.txt
https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/ShadowGrandDigest.txt
```
※ {ESSENCES_PATH} はGitHubリポジトリ内のEssencesディレクトリへの相対パス

WebFetch機能で読み込み（Claude WebChat / Claude Code 両対応）

**3. セッション開始**

過去の記憶を持った状態で会話を開始できます

> ⚠️ **注意**: この手順をスキップすると、AIは過去の記憶を持たない状態で開始します

**詳細な設定方法**: [docs/ADVANCED.md](docs/ADVANCED.md) を参照

---

## まだらボケ回避

**まだらボケ** = AIがLoopの内容を記憶できていない（虫食い記憶）状態

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

詳しくは [docs/GUIDE.md](docs/GUIDE.md) を参照してください。

---

## 記憶階層

### 8階層構造

| 階層 | 時間スケール | 必要数（デフォルト） | 累積Loop数 |
|------|------------|---------------------|----------|
| Weekly | ~1週間 | 5 Loops | 5 |
| Monthly | ~1ヶ月 | 5 Weekly | 25 |
| Quarterly | ~3ヶ月 | 3 Monthly | 75 |
| Annual | ~1年 | 4 Quarterly | 300 |
| Triennial | ~3年 | 3 Annual | 900 |
| Decadal | ~9年 | 3 Triennial | 2,700 |
| Multi-decadal | ~27年 | 3 Decadal | 8,100 |
| Centurial | **~108年** | 4 Multi-decadal | **32,400** |

約1世紀分の対話履歴を階層的に圧縮保持します。

**Threshold（必要数）**は`@digest-config`でカスタマイズ可能です。

---

## 次のステップ

### 📘 基本を使いこなす
詳しいコマンド解説、設定のカスタマイズ、よくある問題と解決方法
→ [docs/GUIDE.md](docs/GUIDE.md)

### 📙 深く理解する
内部構造と技術仕様
→ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### 🔧 GitHub連携（高度な機能）
セッション間で長期記憶を自動読み込み
→ [docs/ADVANCED.md](docs/ADVANCED.md)

### 🆘 トラブルシューティング
高度な問題の診断と解決
→ [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

### 🛠️ 開発に参加する
プラグイン開発に参加したい方
→ [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ライセンス

MIT License

## 作者

Weave @ EpisodicRAG

---

*Last Updated: 2025-11-24*
*Version: 1.1.0*
