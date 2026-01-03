# MetaGenerateExpression

[English](MetaGenerateExpression.md) | 日本語

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
| 肌の色 | 肌の質感・色調 | 色白, 小麦色, 褐色 |
| 髪色 | メインの髪色 | オレンジ, 金髪, 黒髪 |
| 髪型 | 長さ・スタイル | ロング, ショート, ポニーテール |

### 任意項目

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| 目の色 | 瞳の色 | キャラに合わせて自動 |
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
- Skin: [肌の色]
- Hair: [髪色], [髪型]
- Eyes: [目の色]（任意）
- Outfit: [服装]（任意）
- Accessories: [アクセサリ]（任意）

Layout: 4 rows x 5 columns grid (20 expressions total)
Each cell: 300x300 pixels (total image size: 1500x1200 pixels)
Each column = 1 category (4 expressions per category, arranged vertically)
Each cell: Same character, same pose (bust shot), different facial expression

Col 1 (Basic): neutral, smile, focused thinking, creative thinking
Col 2 (Emotion): joy, elation/excitement, surprise, calm/peaceful
Col 3 (Negative): mild anger, sadness, rage, disgust
Col 4 (Anxiety): anxiety, fear, upset/confused, worried
Col 5 (Special): [Special表情1], [Special表情2], [Special表情3] (CHIBI/deformed style), [Special表情4] (CHIBI/deformed style)

Background: [背景]
Important: Keep character appearance consistent across all expressions.
Output as a single image with all 20 expressions arranged in a 4x5 grid (4 rows, 5 columns), total size 1500x1200 pixels is MANDATORY!!!
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

3. 肌の色は？（色白、小麦色、褐色など）
User: 色白

4. 髪色と髪型を教えてください。
User: オレンジ色のロングヘア

5. 目の色は？（任意、スキップ可）
User: 琥珀色

6. 服装は？（任意、スキップ可）
User: 和服（着物）

7. アクセサリはありますか？（任意）
User: なし

8. 背景のスタイルは？（デフォルト: シンプルなグラデーション）
User: 金色のグラデーション

9. Special表情（Col 5）をカスタマイズしますか？
   デフォルト: うとうと, 暗黒微笑, ぎゃふん, ぽやぽや
   ※ Row 3,4 はCHIBIスタイルで生成されます
User: デフォルトでOK

Claude: プロンプトを生成しました。以下をNano Banana Proにコピー&ペーストしてください：

[生成されたプロンプト]
```

---

## 注意事項

1. **画像サイズ**: 生成画像は**1500×1200px**（300px × 4行 × 5列）が必須
   - 300pxセルの中心から280pxを切り抜くことで、多少の位置ズレを吸収
2. **一貫性**: Nano Bananaに「キャラクターの外見を全表情で一貫させて」と強調
3. **再生成**: 一発で完璧にならない場合は対話的に修正を依頼
4. **ウォーターマーク**: Nano Banana Proの出力には透かしが入る場合あり
5. **表情中心オフセット（オプション）**: 表情の視覚的中心がセル中心からずれている場合、
   [AnalyzeExpressionOffset.jp.md](AnalyzeExpressionOffset.jp.md) を使用してClaudeにオフセットを判定させることができます

---

## 次のステップ

生成された画像を取得したら：

### 基本的な使用法

```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid_image.png --output ./output/
```

### オフセット分析を使用する場合（オプション）

表情の位置がずれている場合は、まずClaudeに画像を分析させます：

1. `AnalyzeExpressionOffset.jp.md` と画像をClaudeに渡す
2. Claudeが出力したJSONを `offsets.json` として保存
3. オフセット付きで実行：

```bash
python main.py your_grid_image.png --offsets offsets.json --output ./output/
```

### 出力ファイル

- `ExpressionImages.json` - Base64エンコード済み画像データ
- `VisualExpressionUI.html` - 自己完結型HTML
- `VisualExpressionSkills.zip` - claude.aiアップロード用

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
