# Advanced Features - EpisodicRAG Plugin

このドキュメントでは、EpisodicRAGプラグインの高度な機能について説明します。

---

## 目次

1. [GitHubセットアップ（長期記憶の有効化）](#githubセットアップ長期記憶の有効化)
2. [セットアップ手順](#セットアップ手順)
   - [GitHubリポジトリの作成](#1-githubリポジトリの作成)
   - [Essencesディレクトリの初期化とpush](#2-essencesディレクトリの初期化とpush)
   - [CLAUDE.mdテンプレートの配置](#3-claudemdテンプレートの配置)
   - [セッション開始時の動作確認](#4-セッション開始時の動作確認)
3. [記憶の更新ワークフロー](#記憶の更新ワークフロー)
4. [なぜGitHubセットアップが必要なのか？](#なぜgithubセットアップが必要なのか)
5. [キャッシュバスティングの仕組み](#キャッシュバスティングの仕組み)
6. [高度なワークフロー](#高度なワークフロー)
7. [トラブルシューティング](#トラブルシューティング)

---

## GitHubセットアップ（長期記憶の有効化）

EpisodicRAGの長期記憶システムをフルに活用するには、GitHubリポジトリと連携します。これにより、セッション開始時に過去の記憶（GrandDigest/ShadowGrandDigest）を自動的に読み込めます。

**注意**: このドキュメントでは例として開発環境のパス `plugins-weave/EpisodicRAG` を使用していますが、実際のプラグインインストール場所は環境により異なります。現在の設定パスは `@digest-config` で確認できます。

### 前提条件

- GitHubアカウント
- Git CLI
- （オプション）GitHub CLI (`gh`)

---

## セットアップ手順

### 1. GitHubリポジトリの作成

```bash
# GitHub CLIを使う場合
gh repo create your-memory-repo --public --description "EpisodicRAG Long-term Memory"

# または、GitHubウェブUIで新規リポジトリを作成
```

### 2. Essencesディレクトリの初期化とpush

```bash
cd plugins-weave/EpisodicRAG/data/Essences

# Gitリポジトリとして初期化
git init
git add GrandDigest.txt ShadowGrandDigest.txt
git commit -m "Initial commit: EpisodicRAG memory initialization"

# GitHubリポジトリにpush
git remote add origin https://github.com/{GITHUB_USER}/{GITHUB_REPO}.git
git branch -M main
git push -u origin main
```

**注意**: `{GITHUB_USER}` と `{GITHUB_REPO}` は実際の値に置き換えてください。

### 3. CLAUDE.mdの作成

```bash
# プロジェクトルートに移動
cd ../../../..

# .claudeディレクトリを作成（存在しない場合）
mkdir -p .claude

# .claude/CLAUDE.mdを作成し、以下の内容を記述
# - {GITHUB_USER} → あなたのGitHubユーザー名
# - {GITHUB_REPO} → リポジトリ名
# - {ESSENCES_PATH} → GitHubリポジトリ内のEssencesディレクトリへの相対パス
```

**CLAUDE.mdの記述例** (`{GITHUB_USER}=YourName`, `{GITHUB_REPO}=Memory-Repo`):

```markdown
## セッション開始時の必須動作
1. プロジェクトナレッジに格納された `*.md` を確認
2. ユーザーに以下のURLを提示し、最新の`{SHA}`の取得を依頼：
   `https://api.github.com/repos/YourName/Memory-Repo/git/refs/heads/main`
   # キャッシュバスティングのため、ユーザーから`{SHA}`を受け取る
3. 取得した`{SHA}`を使って以下の2つのURLを生成し、ユーザーに提示：
   `https://raw.githubusercontent.com/YourName/Memory-Repo/{SHA}/{ESSENCES_PATH}/GrandDigest.txt`
   `https://raw.githubusercontent.com/YourName/Memory-Repo/{SHA}/{ESSENCES_PATH}/ShadowGrandDigest.txt`
   # {ESSENCES_PATH} は GitHubリポジトリ内のEssencesディレクトリへの相対パス
4. ユーザーから2つのURLの`web_fetch`承認を取得し、長期記憶にアクセス
```

### 4. セッション開始時の動作確認

**Claude Code / VSCode Extensionの場合:**

Claude Codeを再起動し、新しいセッションを開始すると、`.claude/CLAUDE.md` の指示に従って以下のプロトコルが自動的に実行されます：

1. 最新のSHA取得URLを提示
2. ユーザーからSHAを取得
3. 記憶URLを生成（GrandDigest.txt, ShadowGrandDigest.txt）
4. web_fetchで長期記憶を読み込み

**WebChatの場合:**

WebChatではプロジェクトナレッジが自動読み込みされないため、以下のいずれかの方法を使用します：

**方法A: プロジェクトファイルとしてアップロード（推奨）**

```bash
# プロジェクトルートで実行
# CLAUDE.md を作成し、上記の「セッション開始時の必須動作」セクションを記述
# プレースホルダーを実際の値に置き換える
vi CLAUDE.md
```

セッション開始時に`CLAUDE.md`をプロジェクトファイルとしてアップロードします。

**方法B: セッション開始時にコピペ**

上記の「セッション開始時の必須動作」セクションを、毎セッション開始時にWebChatにコピペします（非効率的なため非推奨）。

---

## 記憶の更新ワークフロー

新しいダイジェストを生成した後、GitHubに記憶を更新します：

```bash
# 新しいダイジェストを生成後
cd plugins-weave/EpisodicRAG/data/Essences

# 変更をコミット
git add GrandDigest.txt ShadowGrandDigest.txt
git commit -m "Update: New digest generated (Weekly/Monthly/etc.)"
git push

# 次回セッション開始時に最新の記憶が自動的に読み込まれます
```

---

## なぜGitHubセットアップが必要なのか？

- **長期記憶の継続性**: セッション間で記憶を引き継ぐため
- **キャッシュバスティング**: 常に最新の記憶を参照するため
- **バックアップ**: 記憶の喪失を防ぐため
- **複数環境での共有**: 異なるデバイス・プロジェクトで同じ記憶を使用するため

**注意**: GitHubセットアップをスキップしても、Plugin自体は動作します（完全自己完結）。ただし、セッション開始時の自動記憶読み込みは行われません。

---

## キャッシュバスティングの仕組み

Claude CodeのWebFetchは、同じURLに対してキャッシュを保持する場合があります。これを回避するため、毎セッション最新のSHAを取得し、URLに含めることで、常に最新の記憶を参照できます。

### キャッシュバスティングのフロー

1. ユーザーがSHA取得URLにアクセス（ブラウザまたはcurl）
2. 最新コミットのSHAを取得
3. SHAを含むrawファイルURLを生成
4. Claude CodeがWebFetchで最新の記憶を読み込み

これにより、記憶の更新が即座にセッションに反映されます。

---

## 高度なワークフロー

### 複数環境での記憶共有

同じGitHubリポジトリを複数のプロジェクトで参照することで、環境をまたいで記憶を共有できます：

1. プロジェクトA: 開発環境（MacBook）
2. プロジェクトB: 本番環境（Linux Server）
3. プロジェクトC: 移動環境（Windows Laptop）

すべてのプロジェクトで同じ`{GITHUB_USER}/{GITHUB_REPO}`を参照すれば、記憶が統一されます。

### プライベートリポジトリの使用

プライベートリポジトリを使用する場合：

```bash
# GitHub Personal Access Tokenを使用
git remote set-url origin https://{TOKEN}@github.com/{USER}/{REPO}.git

# またはSSH
git remote set-url origin git@github.com:{USER}/{REPO}.git
```

WebFetchでのアクセスには、プライベートリポジトリのraw URLに認証が必要になる場合があります。パブリックリポジトリの使用を推奨します（記憶は個人情報を含まないため）。

---

## トラブルシューティング

### SHAが古いままになる

キャッシュの問題でSHAが更新されない場合：

```bash
# ブラウザのキャッシュクリア
# またはcurlで直接取得
curl https://api.github.com/repos/{USER}/{REPO}/git/refs/heads/main
```

### WebFetchが失敗する

- GitHubリポジトリがpublicか確認
- raw URLのフォーマットが正しいか確認
- SHAが正しいか確認

### 記憶が反映されない

- `GrandDigest.txt`, `ShadowGrandDigest.txt`が正しくpushされているか確認
- GitHub上でファイルの内容を直接確認
- CLAUDE.mdのプレースホルダーが正しく置き換えられているか確認

---

詳細な技術仕様については [ARCHITECTURE.md](ARCHITECTURE.md) を参照してください。

---

*Last Updated: 2025-11-27*
*Version: 1.1.2*
