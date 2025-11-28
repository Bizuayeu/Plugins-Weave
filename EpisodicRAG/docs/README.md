# EpisodicRAG AI Specification Hub

Claude/AI エージェント向けの技術仕様ハブです。

> 📖 **ユーザー向けドキュメント**は [プロジェクト README](../../README.md) を参照してください。

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

> 📖 用語・共通概念は [EpisodicRAG/README.md](../README.md) を参照

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

## User Documentation

| ドキュメント | 対象 | 概要 |
|-------------|------|------|
| [QUICKSTART.md](user/QUICKSTART.md) | 新規ユーザー | 5 分で始める |
| [GUIDE.md](user/GUIDE.md) | 一般ユーザー | 詳細ガイド |
| [用語集](../README.md) | 全員 | 用語・共通概念 |
| [FAQ.md](user/FAQ.md) | 問題解決 | よくある質問 |
| [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) | 問題解決 | 詳細トラブルシューティング |
| [ADVANCED.md](user/ADVANCED.md) | 上級者 | GitHub 連携 |

## Developer Documentation

| 目的 | ドキュメント | 概要 |
|------|-------------|------|
| 開発参加方法 | [CONTRIBUTING.md](../CONTRIBUTING.md) | 環境セットアップ・テスト・PR作成 |
| AI開発ガイド | [CLAUDE.md](../.claude-plugin/CLAUDE.md) | Claude Code向け開発ガイドライン |
| 技術アーキテクチャ | [ARCHITECTURE.md](dev/ARCHITECTURE.md) | Clean Architecture・データフロー |
| API仕様 | [API_REFERENCE.md](dev/API_REFERENCE.md) | Python API リファレンス |
| 実装パターン | [_implementation-notes.md](../skills/shared/_implementation-notes.md) | スキル実装の共通ガイドライン |
| エラーリカバリー | [ERROR_RECOVERY_PATTERNS.md](dev/ERROR_RECOVERY_PATTERNS.md) | エラーハンドリングパターン |

---

## Related Links

- [プロジェクト README](../../README.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [CHANGELOG.md](../CHANGELOG.md) - 変更履歴
- [GitHub Repository](https://github.com/Bizuayeu/Plugins-Weave)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
