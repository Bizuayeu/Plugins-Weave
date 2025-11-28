# Contributing to EpisodicRAG Plugin

EpisodicRAGプラグインの開発に興味を持っていただき、ありがとうございます！

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
7. [ドキュメント](#ドキュメント)
8. [サポート](#サポート)

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
    │   ├── plugin.json
    │   ├── config.template.json
    │   ├── last_digest_times.template.json
    │   ├── GrandDigest.template.txt
    │   └── ShadowGrandDigest.template.txt
    ├── agents/
    ├── commands/
    ├── docs/
    ├── scripts/
    │   └── test/
    ├── skills/
    │   └── shared/
    ├── CHANGELOG.md
    └── CONTRIBUTING.md
```

`marketplace.json`は既に配置済みです（リポジトリに含まれています）。

#### 2. ローカルマーケットプレイスの登録

Claude Codeで以下を実行：

```bash
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

```bash
/plugin install EpisodicRAG-Plugin@Plugins-Weave
```

**成功時の出力**:
```text
✅ Plugin 'EpisodicRAG-Plugin' installed successfully
```

#### 4. 初期セットアップ

```bash
@digest-setup
```

対話形式で設定を行います。

#### 5. 動作確認

```bash
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

```text
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
python scripts/config.py --show-paths
```

**出力例**:
```text
Plugin Root: [Your Project]/plugins-weave/EpisodicRAG
Config File: [Your Project]/plugins-weave/EpisodicRAG/.claude-plugin/config.json
Loops Path: [Your Project]/plugins-weave/EpisodicRAG/data/Loops
Digests Path: [Your Project]/plugins-weave/EpisodicRAG/data/Digests
Essences Path: [Your Project]/plugins-weave/EpisodicRAG/data/Essences
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

### config.py - 設定管理

すべてのパス情報を管理し、Plugin自己完結性を保証します。

```bash
# パス情報表示
python scripts/config.py --show-paths

# 設定JSON出力
python scripts/config.py
```

### generate_digest_auto.sh - 自動Digest生成

階層的Digestを自動生成します。

```bash
bash scripts/generate_digest_auto.sh
```

---

## Clean Architecture（4層構造）

v2.0.0 より、`scripts/` は Clean Architecture（4層構造）を採用しています。

> 📖 **詳細仕様**: 層構造・依存関係ルール・推奨インポートパスは [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md#clean-architecture) を参照

### 新機能追加時のガイド

| 追加する機能 | 配置先 |
|-------------|--------|
| 定数・型定義・例外 | `domain/` |
| ファイルI/O・ロギング | `infrastructure/` |
| ビジネスロジック | `application/` |
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

### ユニット/統合テスト実行

> 📊 最新のテスト数は [CI バッジ](https://github.com/Bizuayeu/Plugins-Weave/actions) を参照してください。

```bash
cd plugins-weave/EpisodicRAG/scripts

# 全テスト実行（pytest）- 推奨
python -m pytest test/ -v

# unittest形式
python -m unittest discover -s test -v

# 層別インポート確認
python -c "from domain import LEVEL_CONFIG, __version__; print(__version__)"
python -c "from infrastructure import load_json; print('OK')"
python -c "from application import ShadowGrandDigestManager; print('OK')"
python -c "from interfaces import DigestFinalizerFromShadow; print('OK')"
```

### テスト構成

`scripts/test/` にユニット/インテグレーションテストがあります。

#### ファイル命名規則

| パターン | テスト対象 |
|---------|-----------|
| `test_{module}.py` | 単一モジュールのユニットテスト |
| `test_{package}_{class}.py` | パッケージ内クラスのテスト |
| `test_path_integration.py` | パス解決の統合テスト |

#### 主要テストファイル（層別）

| 層 | テストファイル |
|----|---------------|
| Domain | `test_validators.py`, `test_helpers.py` |
| Infrastructure | `test_json_repository.py`, `test_file_scanner.py` |
| Application | `test_shadow_*.py`, `test_grand_digest.py`, `test_digest_*.py`, `test_cascade_processor.py` |
| Interfaces | `test_finalize_from_shadow.py`, `test_save_provisional_digest.py`, `test_interface_helpers.py` |
| Config | `test_config.py`, `test_path_integration.py` |

#### テスト実行（追加オプション）

```bash
cd scripts

# 層別テスト
python -m pytest test/test_validators.py test/test_helpers.py -v  # Domain
python -m pytest test/test_shadow_*.py -v                         # Shadow関連

# カバレッジ付き
python -m pytest test/ --cov=. --cov-report=term-missing
```

### 手動テスト

変更を加えた後は、必ず以下をテストしてください：

1. 基本的なコマンド（`/digest`, `@digest-auto`）
2. スキル（`@digest-setup`, `@digest-config`）
3. エージェント（`@DigestAnalyzer`）
4. 階層的Digest生成フロー

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

### バージョン管理

#### Single Source of Truth (SSoT)

バージョン情報は `scripts/domain/version.py` の `__version__` が唯一の真実です。

```python
# scripts/domain/version.py
__version__ = "2.3.0"  # ← ここを更新
```

#### バージョン同期対象

| ファイル | フィールド | 備考 |
|---------|-----------|------|
| `scripts/domain/version.py` | `__version__` | SSoT（ここを更新） |
| `.claude-plugin/plugin.json` | `version` | 手動同期 |
| `pyproject.toml` | `version` | 手動同期 |

#### pre-commitによる自動チェック

コミット時に `check_version.py` が自動実行され、3箇所のバージョンが一致しているか検証されます。

```bash
# 手動でチェック
python scripts/check_version.py
```

不一致がある場合はコミットがブロックされます。

#### ドキュメントヘッダーのバージョン

一部ドキュメント（ARCHITECTURE.md, API_REFERENCE.md, TROUBLESHOOTING.md）にはバージョンヘッダーがあります：

```markdown
> **対応バージョン**: EpisodicRAG Plugin v2.x.x+ / ファイルフォーマット 1.0
```

これらは**メジャー/マイナーバージョン変更時のみ更新**してください（パッチバージョンは更新不要）。

---

## サポート

質問や問題がある場合は、GitHub Issuesで報告してください。

ご協力ありがとうございます！

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
