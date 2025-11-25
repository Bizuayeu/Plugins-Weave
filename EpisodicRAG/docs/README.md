# EpisodicRAG Documentation

EpisodicRAGプラグインのドキュメントハブです。目的に応じて適切なドキュメントを参照してください。

---

## For Users（ユーザー向け）

| ドキュメント | 説明 |
|-------------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5分で始めるクイックスタート |
| [GUIDE.md](GUIDE.md) | 詳細なユーザーガイド |
| [GLOSSARY.md](GLOSSARY.md) | 用語集 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | トラブルシューティング |

**推奨順序**: QUICKSTART → GUIDE → TROUBLESHOOTING（必要時）

---

## For Developers（開発者向け）

| ドキュメント | 説明 |
|-------------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 技術仕様・アーキテクチャ |
| [ADVANCED.md](ADVANCED.md) | GitHub連携・高度な機能 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 開発参加ガイド |

---

## For AI（Claude向け仕様書）

### コマンド仕様
| ファイル | 説明 |
|---------|------|
| [../commands/digest.md](../commands/digest.md) | `/digest` コマンド仕様 |

### スキル仕様
| ファイル | 説明 |
|---------|------|
| [../skills/digest-setup/SKILL.md](../skills/digest-setup/SKILL.md) | `@digest-setup` スキル仕様 |
| [../skills/digest-config/SKILL.md](../skills/digest-config/SKILL.md) | `@digest-config` スキル仕様 |
| [../skills/digest-auto/SKILL.md](../skills/digest-auto/SKILL.md) | `@digest-auto` スキル仕様 |

### エージェント仕様
| ファイル | 説明 |
|---------|------|
| [../agents/digest-analyzer.md](../agents/digest-analyzer.md) | DigestAnalyzerエージェント仕様 |

---

## クイックリファレンス

### コマンド一覧

```bash
/digest              # 新規Loop検出と分析
/digest weekly       # Weekly Digest確定
/digest monthly      # Monthly Digest確定
/digest quarterly    # Quarterly Digest確定
```

### スキル一覧

```bash
@digest-setup        # 初期セットアップ
@digest-config       # 設定変更
@digest-auto         # システム状態確認
```

---

## 関連リンク

- [プロジェクトREADME](../README.md)
- [GitHub Repository](https://github.com/Bizuayeu/Plugins-Weave)

---

*Last Updated: 2025-11-25*
*Version: 1.1.0*
