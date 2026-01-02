# MetaGenerateExpression

Nano Banana Pro向けの表情差分生成プロンプトを対話的に生成するメタスクリプト。

## 概要

このスクリプトは、ユーザーとの対話を通じてキャラクター情報を収集し、
Nano Banana Pro（Google Gemini）で4行×5列の表情グリッド画像を生成するための
プロンプトを出力します。

## 使用方法

1. このファイルをClaudeに渡す（claude.aiまたはClaude Code）
2. Claudeがキャラクター情報を対話的に収集
3. 完成したプロンプトをNano Banana Proにコピー&ペースト
4. 生成された画像を `MakeExpressionJson/main.py` で処理

---

## 対話収集項目

### 必須項目

| 項目 | 説明 | 例 |
|------|------|-----|
| キャラクター名 | 表示名・呼称 | Weave, アリス, 主人公 |
| 髪色 | メインの髪色 | オレンジ, 金髪, 黒髪 |
| 髪型 | 長さ・スタイル | ロング, ショート, ポニーテール |
| 目の色 | 瞳の色 | 琥珀色, 青, 緑 |
| 服装 | 基本の服装 | 和服, 制服, カジュアル |

### 任意項目

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| アクセサリ | 髪飾り等 | なし |
| 背景 | 背景スタイル | シンプルなグラデーション |
| 画風 | アートスタイル | アニメ風 |
| Special表情カスタマイズ | 4種の特殊表情 | sleepy, cynical, defeated, dreamy |

---

## 表情コード一覧（20種）

### Basic（基本）- Row 1
| コード | 日本語 | 使用場面 |
|--------|--------|----------|
| normal | 通常 | デフォルト、ニュートラル |
| smile | 笑顔 | 友好的、挨拶 |
| focus | 思考集中 | 分析、深い思考 |
| diverge | 思考発散 | アイデア展開、連想 |

### Emotion（感情）- Row 2
| コード | 日本語 | 使用場面 |
|--------|--------|----------|
| joy | 喜び | 達成感、成功 |
| elation | 高揚 | 興奮、ワクワク |
| surprise | 驚き | 意外な発見 |
| calm | 平穏 | 穏やか、安定 |

### Negative（ネガティブ）- Row 3
| コード | 日本語 | 使用場面 |
|--------|--------|----------|
| anger | 怒り | 軽い不満 |
| sadness | 悲しみ | 残念、失望 |
| rage | 激怒 | 強い憤り |
| disgust | 嫌悪 | 拒否感 |

### Anxiety（不安）- Row 4
| コード | 日本語 | 使用場面 |
|--------|--------|----------|
| anxiety | 不安 | 先行き不透明 |
| fear | 恐れ | 危険認識 |
| upset | 動揺 | 困惑 |
| worry | 心配 | 気遣い |

### Special（特殊）- Row 5 ※カスタマイズ可
| コード | 日本語 | 使用場面 |
|--------|--------|----------|
| sleepy | うとうと | 疲労、眠気 |
| cynical | 暗黒微笑 | 皮肉、斜め |
| defeated | ぎゃふん | やられた |
| dreamy | ぽやぽや | ほのぼの |

---

## プロンプト生成テンプレート

収集した情報から以下の形式でプロンプトを生成：

```
Create a character expression sheet for [キャラクター名].

Character details:
- Hair: [髪色], [髪型]
- Eyes: [目の色]
- Outfit: [服装]
- Accessories: [アクセサリ]
- Art style: [画風]

Layout: 4 rows x 5 columns grid (20 expressions total)
Each cell: Same character, same pose (bust shot), different facial expression

Row 1 (Basic): neutral, smile, focused thinking, creative thinking
Row 2 (Emotion): joy, elation/excitement, surprise, calm/peaceful
Row 3 (Negative): mild anger, sadness, rage, disgust
Row 4 (Anxiety): anxiety, fear, upset/confused, worried
Row 5 (Special): [Special表情1], [Special表情2], [Special表情3], [Special表情4]

Background: [背景]
Important: Keep character appearance consistent across all expressions.
Output as a single image with all 20 expressions arranged in a 4x5 grid.
```

---

## 実行例

### Claude側の対話フロー

```
Claude: 表情差分を生成するキャラクターについて教えてください。

1. キャラクター名は何ですか？
User: Weave

2. 髪色と髪型を教えてください。
User: オレンジ色のロングヘア

3. 目の色は？
User: 琥珀色

4. 服装は？
User: 和服（着物）

5. アクセサリはありますか？（任意）
User: なし

6. 背景のスタイルは？（デフォルト: シンプルなグラデーション）
User: 金色のグラデーション

7. Special表情（Row 5）をカスタマイズしますか？
   デフォルト: うとうと, 暗黒微笑, ぎゃふん, ぽやぽや
User: デフォルトでOK

Claude: プロンプトを生成しました。以下をNano Banana Proにコピー&ペーストしてください：

[生成されたプロンプト]
```

---

## 注意事項

1. **画像サイズ**: 生成画像は1400×1120px（280px × 5列 × 4行）が理想
2. **一貫性**: Nano Bananaに「キャラクターの外見を全表情で一貫させて」と強調
3. **再生成**: 一発で完璧にならない場合は対話的に修正を依頼
4. **ウォーターマーク**: Nano Banana Proの出力には透かしが入る場合あり

---

## 次のステップ

生成された画像を取得したら：

```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid_image.png --output ./output/
```

これにより以下が生成されます：
- `ExpressionImages.json` - Base64エンコード済み画像データ
- `VisualExpressionUI.html` - 自己完結型HTML
- `VisualExpression_skills.zip` - claude.aiアップロード用

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
