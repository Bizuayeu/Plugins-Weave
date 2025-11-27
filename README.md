# EpisodicRAG Plugin

階層的記憶・ダイジェスト生成システム（8 層 100 年、完全自己完結版）

![EpisodicRAG Plugin](EpisodicRAG.png)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 概要

EpisodicRAG は、会話ログ（Loop ファイル）を階層的にダイジェスト化し、長期記憶として構造化・継承するシステムです。8 階層（Weekly → Centurial、約 108 年分）の記憶を自動管理します。

### 主な特徴

- **階層的記憶管理**: 8 階層（週次～世紀）の自動ダイジェスト生成
- **まだらボケ回避**: 未処理 Loop の即座検出で記憶の断片化を防止
- **セッション間継承**: GitHub 経由で長期記憶を次セッションへ引き継ぎ
- **完全自己完結**: プラグイン内にすべてのデータを保持（既存プロジェクト統合も可）

---

## ドキュメントナビゲーション

| あなたは... | 読むべきドキュメント |
|------------|---------------------|
| 🚀 **初めて使う** | [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.md) → [GLOSSARY](EpisodicRAG/docs/GLOSSARY.md) |
| 📘 **日常的に使う** | [GUIDE](EpisodicRAG/docs/user/GUIDE.md) |
| ❓ **問題が発生した** | [FAQ](EpisodicRAG/docs/user/FAQ.md) → [TROUBLESHOOTING](EpisodicRAG/docs/user/TROUBLESHOOTING.md) |
| 🛠️ **開発に参加する** | [CONTRIBUTING](EpisodicRAG/CONTRIBUTING.md) → [ARCHITECTURE](EpisodicRAG/docs/dev/ARCHITECTURE.md) |
| 🤖 **AI/Claude 仕様** | [AI Spec Hub](EpisodicRAG/docs/README.md) |

---

## クイックインストール

```bash
# 1. マーケットプレイス追加
/marketplace add https://github.com/Bizuayeu/Plugins-Weave

# 2. プラグインインストール
/plugin install EpisodicRAG-Plugin@Plugins-Weave

# 3. 初期セットアップ（対話形式）
@digest-setup
```

詳細なセットアップ手順は [QUICKSTART.md](EpisodicRAG/docs/user/QUICKSTART.md) を参照してください。

---

## 基本的な使い方

### 記憶定着サイクル

```
Loop追加 → /digest → Loop追加 → /digest → ...
```

この原則を守ることで、AI は全ての Loop を記憶できます。

### 主なコマンド

| コマンド | 説明 |
|---------|------|
| `/digest` | 新規 Loop 検出と分析 |
| `/digest weekly` | Weekly Digest 確定 |
| `@digest-auto` | システム状態確認と推奨アクション |
| `@digest-setup` | 初期セットアップ |
| `@digest-config` | 設定変更 |

詳細は [GUIDE.md](EpisodicRAG/docs/user/GUIDE.md) を参照してください。

---

## 8 階層構造

| 階層 | 期間目安 |
|------|---------|
| Weekly | ~1 週間 |
| Monthly | ~1 ヶ月 |
| Quarterly | ~3 ヶ月 |
| Annual | ~1 年 |
| Triennial | ~3 年 |
| Decadal | ~10 年 |
| Multi-decadal | ~30 年 |
| Centurial | ~100 年 |

> 📖 完全な階層テーブルは [GLOSSARY.md](EpisodicRAG/docs/GLOSSARY.md#8階層構造) を参照

---

## セッション間で記憶を引き継ぐ

GitHub 連携により、セッション終了後も長期記憶を保持・継承できます。

→ [ADVANCED.md](EpisodicRAG/docs/user/ADVANCED.md)

---

## ライセンス

**MIT License** - 詳細は [LICENSE](LICENSE) を参照

### 特許

**特願 2025-198943** - 階層的記憶・ダイジェスト生成システム

- 個人・非商用利用: MIT ライセンスの範囲で自由に利用可能
- 商用利用: 特許権との関係について事前にご相談ください

---

## 作者

Weave @ EpisodicRAG

---
