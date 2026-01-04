[English](CHEATSHEET.en.md) | 日本語

# EpisodicRAG クイックリファレンス

1ページで主要機能を参照できるチートシートです。

## 目次

- [コマンド早見表](#コマンド早見表)
- [スキル早見表](#スキル早見表)
- [ファイル命名規則](#ファイル命名規則)
- [デフォルト閾値](#デフォルト閾値)
- [主要パス](#主要パス)
- [日常ワークフロー](#日常ワークフロー)
- [トラブル時](#トラブル時)
- [関連ドキュメント](#関連ドキュメント)

---

## コマンド早見表

| コマンド | 用途 | 使用タイミング |
|---------|------|---------------|
| `/digest` | 新規Loop検出・分析 | Loopを追加したら都度 |
| `/digest weekly` | Weekly Digest確定 | 5個のLoopが揃ったら |
| `/digest monthly` | Monthly Digest確定 | 5個のWeeklyが揃ったら |

## スキル早見表

| スキル | 用途 |
|--------|------|
| `@digest-auto` | システム状態診断・推奨アクション |
| `@digest-setup` | 初期セットアップ |
| `@digest-config` | 設定変更 |

---

## ファイル命名規則

| 種類 | プレフィックス | 桁数 | 形式 | 例 |
|------|---------------|------|------|-----|
| Loop | L | 5 | `L[5桁]_タイトル.txt` | `L00001_初回セッション.txt` |
| Weekly | W | 4 | `W[4桁]_タイトル.txt` | `W0001_週次まとめ.txt` |
| Monthly | M | 4 | `M[4桁]_タイトル.txt` | `M0001_月次まとめ.txt` |
| Quarterly | Q | 3 | `Q[3桁]_タイトル.txt` | `Q001_四半期.txt` |

---

## デフォルト閾値

| 階層 | 必要数 | 累積Loop数 |
|------|--------|-----------|
| Weekly | 5 Loops | 5 |
| Monthly | 5 Weekly | 25 |
| Quarterly | 3 Monthly | 75 |
| Annual | 4 Quarterly | 300 |

---

## 主要パス

| 項目 | パス |
|------|------|
| 設定ファイル | `~/.claude/plugins/.episodicrag/config.json` |
| Loopファイル | `{loops_dir}/` |
| Digestファイル | `{digests_dir}/` |
| GrandDigest | `{essences_dir}/GrandDigest.txt` |
| ShadowGrandDigest | `{essences_dir}/ShadowGrandDigest.txt` |

---

## 日常ワークフロー

```text
毎日:   Loop追加 → /digest
週末:   @digest-auto → /digest weekly
月末:   @digest-auto → /digest monthly
```

---

## トラブル時

1. `@digest-auto` で状態確認
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) で具体的な解決策
3. [FAQ.md](FAQ.md) で概念的な疑問

---

## 関連ドキュメント

| 目的 | ドキュメント |
|------|-------------|
| 初めての方 | [QUICKSTART.md](QUICKSTART.md) |
| 日常操作 | [GUIDE.md](GUIDE.md) |
| 高度な設定 | [ADVANCED.md](ADVANCED.md) |
| 用語集 | [GLOSSARY.md](../../GLOSSARY.md) |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
