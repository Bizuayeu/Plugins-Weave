# Advanced Features - EpisodicRAG Plugin

> **対応バージョン**: EpisodicRAG Plugin v5.0.0+ / ファイルフォーマット 1.0

このドキュメントでは、EpisodicRAGプラグインの高度な機能について説明します。

---

## 目次

1. [GitHubセットアップ（長期記憶の有効化）](#githubセットアップ長期記憶の有効化)
2. [セットアップ手順](#セットアップ手順)
   - [GitHubリポジトリの作成](#1-githubリポジトリの作成)
   - [Essencesディレクトリの初期化とpush](#2-essencesディレクトリの初期化とpush)
   - [CLAUDE.mdの作成](#3-claudemdの作成)
   - [セッション開始時の動作確認](#4-セッション開始時の動作確認)
3. [記憶の更新ワークフロー](#記憶の更新ワークフロー)
4. [なぜGitHubセットアップが必要なのか？](#なぜgithubセットアップが必要なのか)
5. [キャッシュバスティングの仕組み](#キャッシュバスティングの仕組み)
6. [高度なワークフロー](#高度なワークフロー)
   - [スキルのCLI直接実行](#スキルのcli直接実行)
   - [複数環境での記憶共有](#複数環境での記憶共有)
   - [プライベートリポジトリの使用](#プライベートリポジトリの使用)
7. [バックアップ＆リカバリ](#バックアップリカバリ)
8. [トラブルシューティング](#トラブルシューティング)

---

## GitHubセットアップ（長期記憶の有効化）

> 📖 用語定義（GrandDigest, ShadowGrandDigest）: [用語集](../../GLOSSARY.md#記憶構造)

EpisodicRAGの長期記憶システムをフルに活用するには、GitHubリポジトリと連携します。これにより、セッション開始時に過去の記憶（GrandDigest/ShadowGrandDigest）を自動的に読み込めます。

**注意**: このドキュメントでは以下のプレースホルダーを使用します:
- `{base_dir}`: データ基準ディレクトリ（config.jsonで設定）
- `{loops_dir}`: Loopファイル配置先
- `{digests_dir}`: Digestファイル配置先
- `{essences_dir}`: GrandDigest/ShadowGrandDigest配置先

現在の設定パスは `@digest-config` で確認できます。

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
cd {essences_dir}

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
3. 取得した`{SHA}`を使って以下の2つのURLを生成し、長期記憶にアクセス：
   `curl -s https://raw.githubusercontent.com/YourName/Memory-Repo/{SHA}/{ESSENCES_PATH}/GrandDigest.txt`
   `curl -s https://raw.githubusercontent.com/YourName/Memory-Repo/{SHA}/{ESSENCES_PATH}/ShadowGrandDigest.txt`
   # {ESSENCES_PATH} は GitHubリポジトリ内のEssencesディレクトリへの相対パス
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
cd {essences_dir}

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

**注意**: GitHubセットアップをスキップしても、Plugin自体は動作します。ただし、セッション開始時の自動記憶読み込みは行われません。

> 📖 Essences/GrandDigest/Shadow の定義: [用語集](../../GLOSSARY.md#記憶構造)

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

### スキルのCLI直接実行

v4.0.0より、スキルはPythonスクリプトとしても実行可能です：

| スキル | CLIコマンド |
|--------|------------|
| `@digest-setup` | `python -m interfaces.digest_setup` |
| `@digest-config` | `python -m interfaces.digest_config` |
| `@digest-auto` | `python -m interfaces.digest_auto` |

これにより、CI/CDパイプラインや自動化スクリプトからの呼び出しが容易になります。

> 📖 詳細: [CHANGELOG.md](../../CHANGELOG.md#400---2025-12-01)

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

## バックアップ＆リカバリ

長期記憶（Loop、全Digest、Essence）を安全に保護するためのガイドラインです。

> 📖 階層構造の詳細: [用語集](../../GLOSSARY.md#8階層構造)

### バックアップ対象ファイル

EpisodicRAGの長期記憶は以下の4層で構成されます。**再構築可能性**に基づいて優先度を設定：

| カテゴリ | ファイル/ディレクトリ | 説明 | 再構築 | 優先度 |
|----------|----------------------|------|--------|--------|
| **Loop** | `{loops_dir}/L*.txt` | 会話記録（原本）例: `L00001_テスト会話.txt` | 不可 | **必須** |
| **Provisional** | `{digests_dir}/0_Provisional/` | 個別Loop分析結果 | Loopから `/digest` | 推奨 |
| **階層Digest** | `{digests_dir}/1_Weekly/` 〜 `8_Centurial/` | 確定済み階層Digest | 下位階層から再生成 | 推奨 |
| **Essence** | `{essences_dir}/GrandDigest.txt` | 統合ビュー（確定済み） | 階層Digestから再構築 | 任意 |
| **Essence** | `{essences_dir}/ShadowGrandDigest.txt` | 統合ビュー（未確定） | Provisionalから再構築 | 任意 |
| 設定 | `~/.claude/plugins/.episodicrag/config.json` | プラグイン設定 | - | 推奨 |
| 設定 | `~/.claude/plugins/.episodicrag/last_digest_times.json` | 最終処理日時 | - | 任意 |

**ポイント**: Loopファイルだけが真に必須です。他のファイルは再構築可能なため、バックアップ容量を節約したい場合はLoopのみでも復旧可能です。

### バックアップ戦略

#### 方法1: Git連携（推奨）

上記「GitHubセットアップ」を完了していれば、Gitが自動バックアップとして機能します：

```bash
cd {base_dir}

# 全長期記憶をバックアップ
git add {loops_dir}/ {digests_dir}/ {essences_dir}/
git commit -m "Backup: $(date +%Y-%m-%d)"
git push
```

#### 方法2: 手動コピー

```bash
# バックアップディレクトリ作成
BACKUP_DIR=~/episodicrag-backup/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# 全長期記憶をコピー
cp -r {loops_dir} $BACKUP_DIR/
cp -r {digests_dir} $BACKUP_DIR/
cp -r {essences_dir} $BACKUP_DIR/
```

#### 方法3: クラウドストレージ同期

dataディレクトリ全体をクラウドストレージ（Google Drive, Dropbox等）と同期することで、自動バックアップを実現できます。

**設定方法**:

1. `@digest-config` を実行
2. [5] trusted_external_paths でクラウドストレージのパスを許可
   - 例: `~/Google Drive` または `C:/Users/username/Google Drive`
3. [1] base_dir をクラウドストレージ内のパスに変更
   - 例: `~/Google Drive/EpisodicRAG`

**設定例（Google Drive）**:
```json
{
  "base_dir": "~/Google Drive/EpisodicRAG",
  "trusted_external_paths": ["~/Google Drive"],
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences"
  }
}
```

> 📖 `trusted_external_paths` の詳細は [api/config.md](../dev/api/config.md#trusted_external_paths) を参照

### リカバリ手順

#### Loopファイルが破損/紛失した場合

Loopは原本のため、バックアップからの復元が必須です：

```bash
cp ~/episodicrag-backup/{DATE}/Loops/L*.txt {loops_dir}/
```

#### Digest（Provisional/階層）が破損した場合

1. **バックアップから復元**（推奨）:
   ```bash
   cp -r ~/episodicrag-backup/{DATE}/Digests/ {digests_dir}/
   ```

2. **Loopから再生成**:
   ```ClaudeCLI
   # Loopが残っていれば再分析可能
   /digest  # 未処理Loopを再検出・分析
   ```

#### GrandDigest/ShadowGrandDigestが破損した場合

1. **バックアップから復元**:
   ```bash
   cp ~/episodicrag-backup/{DATE}/Essences/*.txt {essences_dir}/
   ```

2. **Git履歴から復元**（Git連携時）:
   ```bash
   cd {essences_dir}
   git log --oneline  # コミット履歴確認
   git checkout {COMMIT_SHA} -- GrandDigest.txt ShadowGrandDigest.txt
   ```

3. **テンプレートから再初期化**（最終手段）:
   ```ClaudeCLI
   @digest-setup
   # セットアップウィザードでファイルを再作成
   ```
   **注意**: この場合、GrandDigest/ShadowGrandDigestの履歴は失われますが、Loop/Digestが残っていれば再構築可能です。

#### last_digest_times.jsonが破損した場合

1. 削除して `@digest-setup` を再実行
2. `/digest` で未処理Loopを再検出

### バックアップの推奨頻度

| タイミング | アクション |
|-----------|----------|
| Loop追加後 | Loopファイルをバックアップ |
| `/digest` 後 | Provisional/Shadow をバックアップ |
| `/digest weekly` 後 | 全データをバックアップ |
| 週1回 | 定期フルバックアップ |

---

## トラブルシューティング

> **Note**: このセクションはGitHub連携に特化した問題を扱います。
> DigestAnalyzer、ShadowGrandDigest、階層カスケードなどの高度な問題は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照してください。

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

## 次のステップ

- 📘 **基本的な使い方を学びたい**: [GUIDE.md](GUIDE.md)
- 🆘 **高度な問題に直面した**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📙 **技術仕様を理解したい**: [ARCHITECTURE.md](../dev/ARCHITECTURE.md)
- ❓ **よくある質問**: [FAQ.md](FAQ.md)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
