# EpisodicRAG AI Specification Hub

[![Version](https://img.shields.io/badge/version-5.2.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)

AI/Claudeエージェント向けの技術仕様ハブです。

> 📖 ドキュメント一覧: [INDEX.md](../INDEX.md) - 全ドキュメントへのナビゲーション
>
> 📖 ユーザー向けドキュメント: [プロジェクト README](../README.md)
>
> 📖 開発参加ガイド: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 目次

- [プラグイン構造](#プラグイン構造)
- [v5.0.0 Breaking Changes](#v500-breaking-changes)
- [v4.0.0 Breaking Changes](#v400-breaking-changes)
- [Command Specifications](#command-specifications)
- [Skill Specifications](#skill-specifications)
- [Agent Specifications](#agent-specifications)
- [Quick Reference](#quick-reference)
- [Learning Resources](#learning-resources)
- [Developer Documentation](#developer-documentation)
- [Documentation Map](#documentation-map)

---

## プラグイン構造

設定ファイルとデータは `~/.claude/plugins/.episodicrag/` に保存されます（プラグイン更新時も保持）。

> 📖 ディレクトリ構成: [ARCHITECTURE.md](dev/ARCHITECTURE.md#ディレクトリ構成)
>
> 📖 設定項目詳細: [config.md](dev/api/config.md)

---

## v5.0.0 Breaking Changes

### プラグインルート自動検出
`/digest` 実行時の `config.json` 検出エラーを防止。
任意のディレクトリから `/digest` を実行可能に。

### Loopレベル追加
`last_digest_times.json` に Loop 層を追加。
全レベル（Loop含む）で最新の `/digest` 対象を把握可能に。

### シェルスクリプト廃止
対話型プロセスを md ファイルに一本化（可読性向上、読み飛ばし防止）。

> 📖 詳細: [CHANGELOG.md](../CHANGELOG.md#500---2025-12-05)

---

## v4.0.0 Breaking Changes

### Config層の再編成
インポートパスが変更されました:
- **旧**: `scripts/config.py` (単一モジュール)
- **新**: `domain/config/`, `infrastructure/config/`, `application/config/` (3層)

### スキルのCLI化
スキル経由に加え、直接実行が可能に:
```bash
python -m interfaces.digest_setup
python -m interfaces.digest_config
python -m interfaces.digest_auto
```

> 📖 詳細: [CHANGELOG.md](../CHANGELOG.md#400---2025-12-01)

---

## Command Specifications

| コマンド | 仕様書 | 概要 |
|---------|--------|------|
| `/digest` | [digest.md](../commands/digest.md) | 新規 Loop 検出・分析・階層確定 |

---

## Skill Specifications

| スキル | 仕様書 | 概要 |
|--------|--------|------|
| `@digest-setup` | [SKILL.md](../skills/digest-setup/SKILL.md) | 初期セットアップ（対話的） |
| `@digest-config` | [SKILL.md](../skills/digest-config/SKILL.md) | 設定変更（対話的） |
| `@digest-auto` | [SKILL.md](../skills/digest-auto/SKILL.md) | システム診断・推奨アクション |

---

## Agent Specifications

| エージェント | 仕様書 | 概要 |
|-------------|--------|------|
| DigestAnalyzer | [digest-analyzer.md](../agents/digest-analyzer.md) | Loop/Digest 並列分析 |

---

## Shared Concepts

> 📖 用語・共通概念は [EpisodicRAG/GLOSSARY.md](../GLOSSARY.md) を参照
>
> 📖 設計思想・哲学は [CONCEPT.md](../CONCEPT.md) を参照

---

## Quick Reference

### コマンド

```text
/digest              # 新規Loop検出と分析
/digest weekly       # Weekly Digest確定
/digest monthly      # Monthly Digest確定
/digest quarterly    # Quarterly Digest確定
# ... (annual, triennial, decadal, multi_decadal, centurial)
```

### スキル

```text
@digest-setup        # 初期セットアップ
@digest-config       # 設定変更
@digest-auto         # システム状態確認
```

---

## Learning Resources

| 目的 | ドキュメント |
|------|-------------|
| 学習パス | [LEARNING_PATH.md](dev/LEARNING_PATH.md) |
| 設計判断 | [DESIGN_DECISIONS.md](dev/DESIGN_DECISIONS.md) |

---

## Developer Documentation

| 目的 | ドキュメント | 概要 |
|------|-------------|------|
| 技術アーキテクチャ | [ARCHITECTURE.md](dev/ARCHITECTURE.md) | Clean Architecture・データフロー・ファイル形式 |
| API仕様 | [API_REFERENCE.md](dev/API_REFERENCE.md) | Python API リファレンス |
| 実装パターン | [_implementation-notes.md](../skills/shared/_implementation-notes.md) | スキル・コマンド・エージェント実装の共通ガイドライン |
| エラーリカバリー | [ERROR_RECOVERY_PATTERNS.md](dev/ERROR_RECOVERY_PATTERNS.md) | エラーハンドリングパターン |

### Layer API Details

| Layer | Document | 概要 |
|-------|----------|------|
| Domain | [domain.md](dev/api/domain.md) | 定数・型・例外・ファイル命名 |
| Domain/Config | 同上 | 設定定数・型バリデーション |
| Infrastructure | [infrastructure.md](dev/api/infrastructure.md) | JSON操作・ファイルスキャン・ロギング |
| Infrastructure/Config | 同上 | ファイルI/O・パス解決 |
| Application | [application.md](dev/api/application.md) | Shadow管理・GrandDigest・Finalize処理 |
| Application/Config | 同上 | DigestConfig Facade・サービスクラス |
| Interfaces | [interfaces.md](dev/api/interfaces.md) | DigestFinalizer・ProvisionalSaver・CLI |
| Config (統合) | [config.md](dev/api/config.md) | config.json仕様・統合API |

---

## Documentation Map

```text
docs/
├── README.md                  ← 現在地
├── user/                      ← ユーザー向け
│   ├── QUICKSTART.md (.en)    # 5分スタート
│   ├── GUIDE.md               # 基本ガイド
│   ├── ADVANCED.md            # 高度な使い方
│   ├── CHEATSHEET.md (.en)    # 早見表
│   ├── FAQ.md                 # よくある質問
│   └── TROUBLESHOOTING.md     # トラブル解決
│
└── dev/                       ← 開発者向け
    ├── ARCHITECTURE.md        # 技術仕様
    ├── API_REFERENCE.md       # API仕様
    ├── DESIGN_DECISIONS.md    # 設計判断
    ├── LEARNING_PATH.md       # 学習パス
    ├── ERROR_RECOVERY_PATTERNS.md  # エラーリカバリー
    └── api/                   # Layer別詳細
        ├── domain.md
        ├── infrastructure.md
        ├── application.md
        ├── interfaces.md
        └── config.md
```

---

## Related Links

- [プロジェクト README](../README.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [CHANGELOG.md](../CHANGELOG.md) - 変更履歴
- [GitHub Repository](https://github.com/Bizuayeu/Plugins-Weave)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
