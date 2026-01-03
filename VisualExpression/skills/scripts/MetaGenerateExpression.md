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
| 画風 | アートスタイル | アニメ風, 実写調, アイコン的 |
| 髪色 | メインの髪色 | オレンジ, 金髪, 黒髪 |
| 髪型 | 長さ・スタイル | ロング, ショート, ポニーテール |
| 目の色 | 瞳の色 | 琥珀色, 青, 緑 |

### 任意項目

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| 服装 | 基本の服装 | 和服, 制服, カジュアル |
| アクセサリ | 髪飾り等 | なし |
| 背景 | 背景スタイル | シンプルなグラデーション |
| Special表情カスタマイズ | 4種の特殊表情 | sleepy, cynical, defeated, dreamy |

---

## 表情コード一覧（20種）

表情コードの詳細は [SKILL.md の Expression Codes](../SKILL.md#expression-codes) を参照。

### 概要（全5カテゴリ×4表情＝20種）

| カテゴリ | 表情コード |
|----------|-----------|
| Basic | normal, smile, focus, diverge |
| Emotion | joy, elation, surprise, calm |
| Negative | anger, sadness, rage, disgust |
| Anxiety | anxiety, fear, upset, worry |
| Special | sleepy, cynical, defeated, dreamy |

※ Special カテゴリは `--special` オプションでカスタマイズ可

---

## プロンプト生成テンプレート

収集した情報から以下の形式でプロンプトを生成：

```
Create a character expression sheet for [キャラクター名].

Art style: [画風]

Character details:
- Hair: [髪色], [髪型]
- Eyes: [目の色]
- Outfit: [服装]（任意）
- Accessories: [アクセサリ]（任意）

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

2. 画風は？（アニメ風、実写調、アイコン的など）
User: アニメ風

3. 髪色と髪型を教えてください。
User: オレンジ色のロングヘア

4. 目の色は？
User: 琥珀色

5. 服装は？（任意、スキップ可）
User: 和服（着物）

6. アクセサリはありますか？（任意）
User: なし

7. 背景のスタイルは？（デフォルト: シンプルなグラデーション）
User: 金色のグラデーション

8. Special表情（Row 5）をカスタマイズしますか？
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
- `VisualExpressionSkills.zip` - claude.aiアップロード用

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
