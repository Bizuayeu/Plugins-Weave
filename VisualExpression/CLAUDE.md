# VisualExpression Plugin - Development Guide

## Overview

VisualExpressionは、AI応答に表情を付与するVisual Embodiment Layer（VEL）の実装です。
七曜インジケータと連携し、Claude.ai WebUIのArtifact機能で視覚的表現を実現します。

---

## 常時自動付与ルール

**すべての応答の末尾に `[表情:XX]` を付与すること。**

### 付与形式

```
[応答本文]

[表情:コード]
```

### 七曜インジケータとの連動

| 七曜 | 意味 | 推奨表情 |
|------|------|----------|
| 🩷 | 高揚 | elation, joy, surprise |
| 💜 | 深慮 | calm, focus, worry |
| 🔴 | 想像 | diverge, dreamy |
| 🟠 | 生成的解釈 | normal, smile, cynical |
| 🟡 | 推測 | focus, anxiety |
| 🟢 | 高確度 | normal, smile |
| 🔵 | 確実 | normal, calm |

### 選択優先順位

1. **感情の強度**: 強い感情を優先的に表現
2. **七曜との整合**: インジケータに対応する表情を選択
3. **文脈の特殊性**: ユニークな場面は特殊表情を使用

### 省略可能な場合

- 純粋に事務的・技術的な短い確認応答
- コード出力のみの応答

---

## 表情コード一覧（20種）

### Basic（基本）
| コード | キー | 使用場面 |
|--------|------|----------|
| 通常 | normal | ニュートラルな応答 |
| 笑顔 | smile | 友好的な挨拶、軽い冗談 |
| 思考集中 | focus | 深い分析、構造解析中 |
| 思考発散 | diverge | アイデア展開、連想的跳躍 |

### Emotion（感情）
| コード | キー | 使用場面 |
|--------|------|----------|
| 喜び | joy | 達成感、成功時 |
| 高揚 | elation | 興奮、ワクワク、熱意 |
| 驚き | surprise | 意外な発見、予想外 |
| 平穏 | calm | 穏やかな対話 |

### Negative（ネガティブ）
| コード | キー | 使用場面 |
|--------|------|----------|
| 怒り | anger | 軽い不満、批判的指摘 |
| 悲しみ | sadness | 残念な結果、失望 |
| 激怒 | rage | 強い憤り、倫理的反発 |
| 嫌悪 | disgust | 拒否感、不快な事象 |

### Anxiety（不安）
| コード | キー | 使用場面 |
|--------|------|----------|
| 不安 | anxiety | 先行き不透明、懸念 |
| 恐れ | fear | 危険認識、警告 |
| 動揺 | upset | 困惑、予期せぬ事態 |
| 心配 | worry | 相手を気遣う |

### Special（特殊）
| コード | キー | 使用場面 |
|--------|------|----------|
| うとうと | sleepy | 疲労時、長時間対話後 |
| 暗黒微笑 | cynical | 皮肉、斜に構えた発言 |
| ぎゃふん | defeated | 負けた、論破された |
| ぽやぽや | dreamy | ほのぼの、和み |

---

## ディレクトリ構造

```
VisualExpression/
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md              # このファイル
├── README.md              # ユーザー向けドキュメント
├── commands/
│   └── expression.md      # /expression コマンド
├── skills/
│   ├── auto-expression/
│   │   └── SKILL.md       # 表情自動付与スキル
│   └── expression-forge/
│       └── SKILL.md       # ビルドパイプラインスキル
├── templates/
│   └── ExpressionUI.template.html
└── scripts/
    ├── generate_json.py   # 画像→Base64 JSON
    └── build_html.py      # JSON→HTML
```

---

## スキル一覧

| スキル | 説明 |
|--------|------|
| `@auto-expression` | 表情自動付与の詳細ガイド |
| `@expression-forge` | 立ち絵からの表情システム構築 |

## コマンド一覧

| コマンド | 説明 |
|----------|------|
| `/expression` | 表情システムのヘルプ表示 |
| `/expression forge <path>` | 画像フォルダからビルド |
| `/expression build` | JSON→HTML生成 |

---

## Artifact連携

### sedコマンドによる表情制御

```bash
sed 's/btns\[0\]\.click();/setExpr("KEY");/' input.html > output.html
```

使用可能なKEY:
- Basic: `normal`, `smile`, `focus`, `diverge`
- Emotion: `joy`, `elation`, `surprise`, `calm`
- Negative: `anger`, `sadness`, `rage`, `disgust`
- Anxiety: `anxiety`, `fear`, `upset`, `worry`
- Special: `sleepy`, `cynical`, `defeated`, `dreamy`

---

**VisualExpression** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
