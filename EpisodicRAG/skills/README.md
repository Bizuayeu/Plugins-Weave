[EpisodicRAG](../docs/README.md) > Skills

# Skills

AIスキル仕様書

---

## Overview

このディレクトリには、`@`で呼び出すスキルの仕様書が含まれています。

---

## Available Skills

| Skill | Description | Directory |
|-------|-------------|-----------|
| `@digest-auto` | システム状態診断と推奨アクション | [digest-auto/](digest-auto/) |
| `@digest-setup` | 初期セットアップ（対話形式） | [digest-setup/](digest-setup/) |
| `@digest-config` | 設定変更（対話形式） | [digest-config/](digest-config/) |

---

## Quick Reference

```bash
@digest-auto         # システム状態確認（まず最初に実行）
@digest-setup        # 初期セットアップ
@digest-config       # 設定変更
```

---

## Shared Components

[shared/](shared/) - 共通コンポーネント

| File | Purpose |
|------|---------|
| [_implementation-notes.md](shared/_implementation-notes.md) | 実装ガイドライン |

> 📖 共通概念（まだらボケ等）は [用語集](../README.md) を参照

---

## See Also

- [GUIDE.md](../docs/user/GUIDE.md) - スキルの詳しい使い方
- [用語集](../README.md) - 用語・共通概念

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
