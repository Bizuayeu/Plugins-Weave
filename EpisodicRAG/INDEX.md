[English](INDEX.en.md) | 日本語

# ドキュメント一覧

EpisodicRAGプラグインの全ドキュメントへのナビゲーション。

## 読者別ガイド

| 読者 | 最初に読むべき | 次に読むべき |
|------|--------------|-------------|
| 初めての方 | [QUICKSTART](docs/user/QUICKSTART.md) | [GUIDE](docs/user/GUIDE.md) |
| 日常利用 | [CHEATSHEET](docs/user/CHEATSHEET.md) | [FAQ](docs/user/FAQ.md) |
| トラブル時 | [TROUBLESHOOTING](docs/user/TROUBLESHOOTING.md) | [FAQ](docs/user/FAQ.md) |
| 開発者 | [ARCHITECTURE](docs/dev/ARCHITECTURE.md) | [API_REFERENCE](docs/dev/API_REFERENCE.md) |
| AI (Claude) | [CLAUDE.md](.claude/CLAUDE.md) | [技術仕様ハブ](docs/README.md) |

---

## ユーザー向け (`docs/user/`)

| ファイル | 説明 | 英語版 |
|---------|------|-------|
| [QUICKSTART.md](docs/user/QUICKSTART.md) | 5分クイックスタート | [EN](docs/user/QUICKSTART.en.md) |
| [GUIDE.md](docs/user/GUIDE.md) | 基本操作ガイド | - |
| [ADVANCED.md](docs/user/ADVANCED.md) | 高度な使い方 | - |
| [CHEATSHEET.md](docs/user/CHEATSHEET.md) | コマンド早見表 | [EN](docs/user/CHEATSHEET.en.md) |
| [FAQ.md](docs/user/FAQ.md) | よくある質問 | - |
| [TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md) | トラブルシューティング | - |

---

## 開発者向け (`docs/dev/`)

| ファイル | 説明 |
|---------|------|
| [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md) | システム設計・ディレクトリ構成 |
| [API_REFERENCE.md](docs/dev/API_REFERENCE.md) | DigestConfig API |
| [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) | 設計判断の理由 |
| [LEARNING_PATH.md](docs/dev/LEARNING_PATH.md) | 学習パス |
| [ERROR_RECOVERY_PATTERNS.md](docs/dev/ERROR_RECOVERY_PATTERNS.md) | エラー処理パターン |

### Layer別API (`docs/dev/api/`)

| ファイル | Layer |
|---------|-------|
| [domain.md](docs/dev/api/domain.md) | 定数・型・例外 |
| [infrastructure.md](docs/dev/api/infrastructure.md) | JSON操作・ファイルI/O |
| [application.md](docs/dev/api/application.md) | Facade・ユースケース |
| [interfaces.md](docs/dev/api/interfaces.md) | CLI・エントリーポイント |
| [config.md](docs/dev/api/config.md) | 設定API |

---

## 仕様書

### コマンド (`commands/`)

| コマンド | ファイル |
|---------|---------|
| `/digest` | [digest.md](commands/digest.md) |

### スキル (`skills/`)

| スキル | ファイル |
|--------|---------|
| `@digest-setup` | [SKILL.md](skills/digest-setup/SKILL.md) |
| `@digest-config` | [SKILL.md](skills/digest-config/SKILL.md) |
| `@digest-auto` | [SKILL.md](skills/digest-auto/SKILL.md) |

### エージェント (`agents/`)

| エージェント | ファイル |
|------------|---------|
| DigestAnalyzer | [digest-analyzer.md](agents/digest-analyzer.md) |

---

## プロジェクト情報

| ファイル | 説明 | 英語版 |
|---------|------|-------|
| [GLOSSARY.md](GLOSSARY.md) | 用語集・リファレンス | [EN](GLOSSARY.en.md) |
| [CONCEPT.md](CONCEPT.md) | 設計思想 | [EN](CONCEPT.en.md) |
| [CHANGELOG.md](CHANGELOG.md) | 変更履歴 | [EN](CHANGELOG.en.md) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 開発参加ガイド | [EN](CONTRIBUTING.en.md) |

---

## その他

| ファイル | 説明 |
|---------|------|
| [scripts/README.md](scripts/README.md) | Pythonスクリプト概要 |
| [scripts/test/TESTING.md](scripts/test/TESTING.md) | テスト実行ガイド |
| [skills/shared/_implementation-notes.md](skills/shared/_implementation-notes.md) | 実装ガイドライン（SSoT） |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
