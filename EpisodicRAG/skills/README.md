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
| [_common-concepts.md](shared/_common-concepts.md) | まだらボケ概念定義（SSoT） |
| [_implementation-notes.md](shared/_implementation-notes.md) | 実装ガイドライン |

---

## See Also

- [GUIDE.md](../docs/GUIDE.md) - スキルの詳しい使い方
- [GLOSSARY.md](../docs/GLOSSARY.md) - 用語集

---

*Last Updated: 2025-11-27*
*Version: 1.1.2*
