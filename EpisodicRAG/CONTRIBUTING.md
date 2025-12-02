[English](CONTRIBUTING.en.md) | 日本語

# Contributing to EpisodicRAG Plugin

EpisodicRAGプラグインの開発に興味を持っていただき、ありがとうございます！

> **AIエージェント向け**: [.claude-plugin/CLAUDE.md](.claude-plugin/CLAUDE.md) を参照してください。

> **対応バージョン**: EpisodicRAG Plugin（[version.py](scripts/domain/version.py) 参照）

このドキュメントでは、開発環境のセットアップ方法、コード変更のテスト方法、プルリクエストの作成方法について説明します。

---

## 目次

1. [開発環境のセットアップ](#開発環境のセットアップ)
2. [インストール方法](#インストール方法)
   - [パターンA: ローカルマーケットプレイス経由（推奨）](#パターンa-ローカルマーケットプレイス経由推奨)
   - [パターンB: 手動セットアップ（従来の方法）](#パターンb-手動セットアップ従来の方法)
3. [スクリプトの手動実行](#スクリプトの手動実行)
4. [プルリクエストの作成](#プルリクエストの作成)
5. [コーディング規約](#コーディング規約)
6. [テスト](#テスト)
7. [開発ツール](#開発ツール-v410) - フッターチェッカー、リンクチェッカー *(v4.1.0+)*
8. [ドキュメント](#ドキュメント)
9. [サポート](#サポート)

---

## 開発環境のセットアップ

### 前提条件

- Python 3.x
- Bash（Git Bash / WSL）
- Claude Code環境

---

## インストール方法

開発中のプラグインをテストする方法は2つあります。

### パターンA: ローカルマーケットプレイス経由（推奨）

**概要**: Claude Codeの`/plugin install`コマンドを使ってローカルプラグインをインストールします。実際のマーケットプレイス配布と同じフローでテストできます。

#### 1. ディレクトリ構造の確認

```text
plugins-weave/
├── .claude-plugin/                     # マーケットプレイス設定
│   └── marketplace.json
└── EpisodicRAG/                        # プラグイン本体
    ├── .claude-plugin/
    │   ├── CLAUDE.md                   # AIエージェント向け指示
    │   ├── plugin.json
    │   ├── config.template.json
    │   ├── last_digest_times.template.json
    │   ├── GrandDigest.template.txt
    │   └── ShadowGrandDigest.template.txt
    ├── agents/
    ├── commands/
    ├── docs/
    ├── scripts/                        # Clean Architecture（4層）
    │   ├── domain/                     # コアビジネスロジック
    │   │   └── config/                 # 設定定数・バリデーション
    │   ├── infrastructure/             # 外部関心事（I/O）
    │   │   └── config/                 # 設定ファイルI/O
    │   ├── application/                # ユースケース
    │   │   └── config/                 # DigestConfig（Facade）
    │   ├── interfaces/                 # エントリーポイント
    │   └── test/
    ├── skills/
    │   └── shared/
    ├── pyproject.toml
    ├── README.md / README.en.md
    ├── CHANGELOG.md / CHANGELOG.en.md
    └── CONTRIBUTING.md / CONTRIBUTING.en.md
```

> 📖 **詳細なディレクトリ構造**: [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md#ディレクトリ構成)

`marketplace.json`は既に配置済みです（リポジトリに含まれています）。

#### 2. ローカルマーケットプレイスの登録

Claude Codeで以下を実行：

```ClaudeCLI
# 相対パスの場合
/marketplace add ./plugins-weave

# または絶対パスの場合
/marketplace add C:\Users\anyth\DEV\plugins-weave
```

**成功時の出力**:
```text
✅ Marketplace 'Plugins-Weave' added successfully
```

#### 3. プラグインのインストール

```ClaudeCLI
/plugin install EpisodicRAG-Plugin@Plugins-Weave
```

**成功時の出力**:
```text
✅ Plugin 'EpisodicRAG-Plugin' installed successfully
```

#### 4. 初期セットアップ

```ClaudeCLI
@digest-setup
```

対話形式で設定を行います。

#### 5. 動作確認

```ClaudeCLI
@digest-auto
```

**期待される出力**:
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG システム状態
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

#### 6. 開発イテレーション（コード変更後）

プラグインのコードを修正した後、以下で再テスト：

```ClaudeCLI
# 1. アンインストール
/plugin uninstall EpisodicRAG-Plugin@Plugins-Weave

# 2. 再インストール
/plugin install EpisodicRAG-Plugin@Plugins-Weave

# 3. セットアップ（必要に応じて）
@digest-setup

# 4. 動作確認
@digest-auto
```

**メリット**:
- 実際のマーケットプレイス配布フローと同じテスト環境
- `/plugin install`コマンドで簡単にインストール・アンインストール
- バージョン管理が容易

---

### パターンB: 手動セットアップ（従来の方法）

**概要**: プラグインディレクトリを直接操作する従来の方法です。

#### 1. セットアップスクリプト実行

```bash
cd plugins-weave/EpisodicRAG
bash scripts/setup.sh
```

#### 2. 設定確認

```bash
python -m interfaces.digest_setup check
```

**出力例**:
```json
{
  "status": "configured",
  "config_exists": true,
  "directories_exist": true,
  "config_file": "[Your Project]/plugins-weave/EpisodicRAG/.claude-plugin/config.json",
  "message": "Setup already completed"
}
```

（identity_file_pathを設定している場合は "Identity File:" 行も表示されます）

**メリット**:
- シンプル（マーケットプレイス登録不要）
- 既存のワークフローと同じ

**デメリット**:
- マーケットプレイス配布時の動作と異なる可能性
- インストール・アンインストールが手動

---

**推奨**: 開発中は**パターンA（ローカルマーケットプレイス）** を使用し、マーケットプレイス配布時の動作を確認しながら開発してください。

---

## スクリプトの手動実行

プラグインの内部スクリプトを直接実行することも可能です（デバッグ用）。

### config_cli.py - 設定管理（v4.0.0+）

すべてのパス情報を管理し、Plugin自己完結性を保証します。

```bash
cd plugins-weave/EpisodicRAG/scripts

# パス情報表示
python -m interfaces.config_cli --show-paths

# 設定JSON出力
python -m interfaces.config_cli
```

### スキルのCLI直接実行（v4.0.0+）

スキルはPythonスクリプトとして直接実行可能です（デバッグ用）:

```bash
cd plugins-weave/EpisodicRAG/scripts

# @digest-setup 相当
python -m interfaces.digest_setup

# @digest-config 相当
python -m interfaces.digest_config

# @digest-auto 相当
python -m interfaces.digest_auto
```

> **Note**: スキル経由の使用（`@digest-setup` 等）も引き続き可能です。

### generate_digest_auto.sh - 自動Digest生成

階層的Digestを自動生成します。

```bash
bash scripts/generate_digest_auto.sh
```

---

## Clean Architecture（4層構造）

v2.0.0 より、`scripts/` は Clean Architecture（4層構造）を採用しています。

> 📖 **詳細仕様**: 層構造・依存関係ルール・推奨インポートパスは [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md#clean-architecture) を参照
>
> 📖 **アーキテクチャ選択理由**: [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md)

**v4.0.0での変更**: 設定管理機能（config）は各層のサブディレクトリに分散配置されています:
- `domain/config/` - 設定定数、バリデーションヘルパー
- `infrastructure/config/` - 設定ファイルI/O、パス解決
- `application/config/` - DigestConfig（Facade）、サービスクラス

### 新機能追加時のガイド

| 追加する機能 | 配置先 |
|-------------|--------|
| 定数・型定義・例外 | `domain/` |
| 設定関連の定数・バリデーション | `domain/config/` |
| ファイルI/O・ロギング | `infrastructure/` |
| 設定ファイル読み込み・パス解決 | `infrastructure/config/` |
| ビジネスロジック | `application/` |
| 設定管理サービス（Facade） | `application/config/` |
| 外部エントリーポイント | `interfaces/` |

---

## プルリクエストの作成

1. このリポジトリをフォーク
2. 新しいブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

### コミットメッセージ

明確で簡潔なコミットメッセージを心がけてください：

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント更新
- `refactor:` リファクタリング
- `test:` テスト追加・修正

---

## コーディング規約

- Python: PEP 8に準拠
- Bash: ShellCheckで検証
- Markdown: 明確で簡潔な記述

---

## テスト

> 📖 **テスト詳細**: テストディレクトリ構造・実行方法は [scripts/README.md](scripts/README.md#tests) を参照

### クイックスタート

```bash
cd plugins-weave/EpisodicRAG/scripts

# 全テスト実行
python -m pytest test/ -v

# 層別テスト実行
python -m pytest test/domain_tests/ -v
python -m pytest test/config_tests/ -v
```

### 手動テスト

変更を加えた後は、必ず以下をテストしてください：

1. 基本的なコマンド（`/digest`, `@digest-auto`）
2. スキル（`@digest-setup`, `@digest-config`）
3. エージェント（`@DigestAnalyzer`）
4. 階層的Digest生成フロー

---

## 開発ツール *(v4.1.0+)*

`scripts/tools/` ディレクトリには、ドキュメントの品質管理ツールが含まれています。

### フッターチェッカー（check_footer.py）

各ドキュメントのフッターが `_footer.md` で定義された形式と一致しているかを検証します。

```bash
cd plugins-weave/EpisodicRAG/scripts

# チェック実行
python -m tools.check_footer

# 自動修正
python -m tools.check_footer --fix

# サマリーのみ表示
python -m tools.check_footer --quiet
```

**出力例**:
```text
Checking files in: docs/

OK (3):
  docs/README.md
  docs/dev/ARCHITECTURE.md
  docs/dev/DESIGN_DECISIONS.md

MISSING (1):
  docs/user/NEW_FILE.md

MISMATCH (1):
  docs/user/OLD_FILE.md

Summary: 3 OK, 1 MISSING, 1 MISMATCH
```

### リンクチェッカー（link_checker.py）

Markdownファイル内の相対リンク、アンカーリンク、複合リンクを検証します。

```bash
cd plugins-weave/EpisodicRAG/scripts

# 検証実行
python -m tools.link_checker ../docs

# 詳細出力
python -m tools.link_checker ../docs --verbose

# JSON出力（CI/CD用）
python -m tools.link_checker ../docs --json
```

**出力例**:
```text
Checking: docs/dev/ARCHITECTURE.md

BROKEN LINKS:
  Line 42: [config.md](./config.md)
    File not found: docs/dev/config.md
    Suggestion: Did you mean docs/dev/api/config.md?

  Line 85: [#invalid-anchor](#invalid-anchor)
    Anchor not found in document

Summary: 2 broken links in 1 file
```

**機能**:
- 相対リンク（`./file.md`, `../file.md`）の検証
- アンカーリンク（`#section`）の検証
- 複合リンク（`file.md#section`）の検証
- 壊れたリンクの修正案提示
- JSON出力（CI/CD統合用）

---

## 開発環境での注意事項

### インストールテスト時の環境混在

開発環境とインストール済プラグインが同じマシンに存在する場合、以下に注意してください：

**問題**: `@digest-setup`等を実行すると、開発フォルダに設定ファイルが作成される可能性があります

**確認方法**:
```bash
cd plugins-weave/EpisodicRAG
git status
```
```text
# 期待: "nothing to commit, working tree clean"
```

**ベストプラクティス**:

1. **インストール後は必ずgit statusで確認**
2. **設定ファイルは開発フォルダにコミットしない**
3. **設定の編集はインストール済プラグイン側で行う**
   - インストール先: `~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/`

詳細は[TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md#開発環境とインストール環境の混在)を参照してください。

---

## ドキュメント

コードの変更に伴い、必要に応じてドキュメントを更新してください：

- README.md - 一般ユーザー向け
- CONTRIBUTING.md - このファイル
- docs/ - 詳細ドキュメント

### Single Source of Truth (SSoT) 原則

**SSoT（Single Source of Truth）** とは、同じ情報を複数箇所に書かず、正規の定義場所を1つに定めて参照する原則です。変更時のメンテナンス負荷を軽減し、不整合を防止します。

#### ドキュメントのSSoT

| 情報 | SSoT（正規の定義場所） | 参照方法 |
|------|----------------------|----------|
| 用語・概念定義 | [README.md](README.md)（用語集） | `> 📖 詳細: [用語集](../../README.md#セクション名)` |
| フッター | `_footer.md` | 各ドキュメント末尾で統一 |
| 設定仕様 | [api/config.md](docs/dev/api/config.md) | リンクで参照 |

#### バージョンのSSoT

バージョン情報は `.claude-plugin/plugin.json` の `version` フィールドが唯一の真実（SSoT）です。

```json
// .claude-plugin/plugin.json
{
  "name": "EpisodicRAG-Plugin",
  "version": "x.y.z",  // ← ここがSSoT - 実際の値は plugin.json を参照
  ...
}
```

| ファイル | フィールド | 同期方法 |
|---------|-----------|----------|
| `.claude-plugin/plugin.json` | `version` | **SSoT**（ここが起点） |
| `pyproject.toml` | `version` | 手動同期 |
| `../.claude-plugin/marketplace.json` | `plugins[].version` | 手動同期 |
| `CHANGELOG.md` | `## [x.x.x]` | 手動同期 |
| `../README.md` / `../README.en.md` | バージョンバッジ | 手動同期 |
| `scripts/domain/version.py` | `__version__` | **自動**（動的読み込み） |

> 📊 これらの同期は `scripts/test/domain_tests/test_version.py` のテストで検証されます。

**動的読み込みの仕組み**:

`scripts/domain/version.py` は `plugin.json` からバージョンを動的に読み込みます：

```python
from domain import __version__
print(__version__)  # plugin.json の version が表示される
```

### リリース手順

バージョン更新時は以下の**5ファイル**を更新:

1. `.claude-plugin/plugin.json` - `version` フィールドを更新（SSoT）
2. `pyproject.toml` - `version` を同じ値に更新
3. `../.claude-plugin/marketplace.json` - `plugins[0].version` を同じ値に更新
4. `CHANGELOG.md` - 新しいセクション `## [x.x.x] - YYYY-MM-DD` を追加
5. `../README.md` と `../README.en.md` - バージョンバッジを更新

```bash
# 動作確認（テストで全ファイルの同期を検証）
cd scripts
python -m pytest test/domain_tests/test_version.py -v
```

### ドキュメントヘッダーのバージョン

一部ドキュメント（ARCHITECTURE.md, API_REFERENCE.md, TROUBLESHOOTING.md）にはバージョンヘッダーがあります：

```markdown
> **対応バージョン**: EpisodicRAG Plugin（[version.py](scripts/domain/version.py) 参照）/ ファイルフォーマット 1.0
```

**推奨**: 動的参照形式（`[version.py](...) 参照`）を使用し、手動更新を不要にしてください。

---

## Documentation Sync Process

### Bilingual Documentation Policy

EpisodicRAGプラグインは日本語を主言語とし、主要ドキュメントの英語版を提供しています。

1. **Primary Language**: Japanese (日本語)
2. **Secondary Language**: English

> **翻訳方針**: 主要ドキュメント（README, CHANGELOG, CONTRIBUTING, QUICKSTART, CHEATSHEET）のみ英語版を維持します。その他のドキュメントは日本語のみとし、翻訳の維持コストを抑えます。

### Currently Synced Files

| Japanese | English | Status |
|----------|---------|--------|
| `../README.md` | `../README.en.md` | ✅ Synced |
| `README.md` | `README.en.md` | ✅ Synced |
| `CHANGELOG.md` | `CHANGELOG.en.md` | ✅ Synced |
| `CONTRIBUTING.md` | `CONTRIBUTING.en.md` | ✅ Synced |
| `docs/user/QUICKSTART.md` | `docs/user/QUICKSTART.en.md` | ✅ Synced |
| `docs/user/CHEATSHEET.md` | `docs/user/CHEATSHEET.en.md` | ✅ Synced |

### Sync Workflow

日本語ドキュメントを更新した場合、対応する英語ドキュメントも同期してください。

1. **Edit Japanese version first** - 日本語版を先に編集
2. **Update English version** - 同じPR内で英語版を更新
3. **Add sync header** - 英語ファイルの先頭にヘッダーを追加:
   ```markdown
   <!-- Last synced: YYYY-MM-DD -->
   ```

### Adding New Translations

新しい英語翻訳を追加する場合:

1. Copy structure from Japanese version（日本語版の構造をコピー）
2. Translate content maintaining formatting（フォーマットを維持して翻訳）
3. Add sync header with date（同期ヘッダーを追加）
4. Update this table（上のテーブルを更新）

---

## サポート

質問や問題がある場合は、GitHub Issuesで報告してください。

ご協力ありがとうございます！

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
