# EpisodicRAG AI Specification Hub

Claude/AI エージェント向けの技術仕様ハブです。

> 📖 **ユーザー向けドキュメント**は [プロジェクト README](../README.md) を参照してください。

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

## Shared Concepts (SSoT)

AI エージェントが参照すべき共通概念の Single Source of Truth:

| 概念 | SSoT ファイル |
|------|--------------|
| まだらボケ・記憶定着サイクル | [_common-concepts.md](../skills/shared/_common-concepts.md) |
| 実装ガイドライン | [_implementation-notes.md](../skills/shared/_implementation-notes.md) |
| 8 層階層構造 | [GLOSSARY.md](GLOSSARY.md#8階層構造) |
| DigestConfig API | [API_REFERENCE.md](API_REFERENCE.md) |
| ファイル形式仕様 | [ARCHITECTURE.md](ARCHITECTURE.md) |

---

## Quick Reference

### コマンド

```bash
/digest              # 新規Loop検出と分析
/digest weekly       # Weekly Digest確定
/digest monthly      # Monthly Digest確定
/digest quarterly    # Quarterly Digest確定
# ... (annual, triennial, decadal, multi_decadal, centurial)
```

### スキル

```bash
@digest-setup        # 初期セットアップ
@digest-config       # 設定変更
@digest-auto         # システム状態確認
```

---

## User Documentation

| ドキュメント | 対象 | 概要 |
|-------------|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 新規ユーザー | 5 分で始める |
| [GUIDE.md](GUIDE.md) | 一般ユーザー | 詳細ガイド |
| [GLOSSARY.md](GLOSSARY.md) | 全員 | 用語集 |
| [FAQ.md](FAQ.md) | 問題解決 | よくある質問 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 問題解決 | 詳細トラブルシューティング |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 開発者 | 技術仕様 |
| [ADVANCED.md](ADVANCED.md) | 上級者 | GitHub 連携 |
| [API_REFERENCE.md](API_REFERENCE.md) | 開発者 | API リファレンス |

---

## Related Links

- [プロジェクト README](../README.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [GitHub Repository](https://github.com/Bizuayeu/Plugins-Weave)

---
