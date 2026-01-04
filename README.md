[English](README.en.md) | 日本語

# Plugins-Weave

Claude Code プラグインマーケットプレイス

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## プラグイン一覧

| プラグイン | 説明 |
|-----------|------|
| [EpisodicRAG](EpisodicRAG/) | 階層的記憶・ダイジェスト生成システム（8層100年） |
| [EmailingEssay](EmailingEssay/) | AI駆動エッセイ配信システム |
| [VisualExpression](VisualExpression/) | 表情表現システム |

---

## インストール

### 1. マーケットプレイス追加

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Weave
```

### 2. プラグインインストール

```ClaudeCLI
# EpisodicRAG（長期記憶管理）
/plugin install EpisodicRAG-Plugin@Plugins-Weave

# EmailingEssay（エッセイ配信）
/plugin install EmailingEssay-Plugin@Plugins-Weave

# VisualExpression（表情表現）
/plugin install VisualExpression-Plugin@Plugins-Weave
```

---

## 各プラグインの詳細

### EpisodicRAG

階層的記憶・ダイジェスト生成システム。会話ログ（Loopファイル）を8階層（Weekly→Centurial、約108年分）で自動管理します。

- [クイックスタート](EpisodicRAG/docs/user/QUICKSTART.md)
- [用語集](EpisodicRAG/GLOSSARY.md)
- [詳細README](EpisodicRAG/README.md)

### EmailingEssay

AI駆動のエッセイ配信プラグイン。省察から生まれるプロアクティブなコミュニケーションを実現します。

- [README](EmailingEssay/README.md)
- [セットアップ](EmailingEssay/SETUP.md)

### VisualExpression

AIペルソナ向け表情表現システム。感情に基づく表情切り替えを提供します。

- [README](VisualExpression/README.md)

---

## ライセンス

**MIT License** - 詳細は [LICENSE](LICENSE) を参照

---
**Plugins-Weave** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
