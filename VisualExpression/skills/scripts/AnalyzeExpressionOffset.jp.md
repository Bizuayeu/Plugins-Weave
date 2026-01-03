# AnalyzeExpressionOffset

[English](AnalyzeExpressionOffset.md) | 日本語

表情グリッド画像を分析し、最適な切り抜きオフセットを決定するためのメタスクリプト。

## 目次

- [概要](#概要)
- [使用方法](#使用方法)
- [分析手順](#分析手順)
- [出力形式](#出力形式)
- [分析例](#分析例)
- [MakeExpressionJsonとの統合](#makeexpressionjsonとの統合)
- [注意事項](#注意事項)

---

## 概要

このスクリプトにより、Claude（Weave）が表情グリッド画像を視覚的に分析し、
各表情をセルの幾何学的中心ではなく「表情の視覚的中心」で切り抜くための
オフセット設定を出力できます。

---

## 使用方法

1. このファイルと表情グリッド画像をClaudeに渡す
2. Claudeが各セルの表情位置を分析
3. Claudeがオフセット設定JSONを出力
4. `MakeExpressionJson/main.py --offsets` でJSONを使用

---

## 分析手順

### グリッドレイアウト

入力画像は4行×5列のグリッド（20表情）：
- 各セル: 300×300ピクセル
- 総画像サイズ: 1500×1200ピクセル
- 出力サイズ: 280×280ピクセル（10pxマージンで中心切り抜き）

### 表情コードマッピング

| 位置 | Col 1 (Basic) | Col 2 (Emotion) | Col 3 (Negative) | Col 4 (Anxiety) | Col 5 (Special) |
|------|---------------|-----------------|------------------|-----------------|-----------------|
| Row 1 | normal | joy | anger | anxiety | sleepy |
| Row 2 | smile | elation | sadness | fear | cynical |
| Row 3 | focus | surprise | rage | upset | defeated |
| Row 4 | diverge | calm | disgust | worry | dreamy |

### 視覚的分析プロセス

各表情セルについて：

1. **顔の中心を特定**
   - 両目の中間点（または同等の顔面特徴点）を見つける
   - これが「表情の中心」

2. **セル中心との比較**
   - セルの幾何学的中心: 各300×300セル内で(150, 150)
   - 表情の中心がずれている原因：
     - キャラクターのポーズ変化
     - 頭の傾きや回転
     - 芸術的な非対称性

3. **オフセットを計算**
   - オフセットX = (表情中心のX座標) - 150
   - オフセットY = (表情中心のY座標) - 150
   - 正のX = 表情が中心より右 → 切り抜きを右にずらす
   - 正のY = 表情が中心より下 → 切り抜きを下にずらす

### オフセットガイドライン

- **小さなオフセット (±1-5px)**: 微調整、わずかな変動に一般的
- **中程度のオフセット (±6-15px)**: 顕著なずれ、動的なポーズで典型的
- **大きなオフセット (±16-20px)**: 推奨最大値; これより大きい場合は生成の問題を示唆
- **ゼロオフセット**: 表情が完全に中央; `{}` を使用またはJSONから省略

---

## 出力形式

### JSON構造

```json
{
  "offsets": {
    "normal": {"x": 0, "y": -3},
    "smile": {"x": 2, "y": 0},
    "joy": {"x": -5, "y": 2},
    "anger": {"x": 0, "y": 0}
  },
  "analysis_notes": "ほとんどの表情は中央揃え。joyが左にずれていたため+5補正を適用。",
  "recommended_regenerate": []
}
```

### フィールド説明

| フィールド | 説明 |
|-----------|------|
| `offsets` | 表情コード → {x, y} オフセットペアの辞書 |
| `offsets.{code}.x` | 水平オフセット（ピクセル、正=右） |
| `offsets.{code}.y` | 垂直オフセット（ピクセル、正=下） |
| `analysis_notes` | 分析に関するオプションのメモ |
| `recommended_regenerate` | 再生成を推奨する表情コードのリスト |

### 省略ルール

- ゼロオフセット（完全に中央）の表情は省略可能
- すべての表情が中央の場合: `{"offsets": {}}`

---

## 分析例

### サンプル対話

```
User: [表情グリッド画像を添付] この表情グリッドを分析して、切り抜きオフセットを決定してください。

Claude: 各表情セルを最適な切り抜きのために分析します。

**分析結果:**

グリッドを見ると：
- Row 1-2: 表情はよく中央揃えされています
- Row 3: 一部の表情で顔がやや上にあります（focus/rageの頭の傾き）
- Row 4: dreamy表情がわずかに右に傾いています

**オフセット設定:**

{
  "offsets": {
    "focus": {"x": 0, "y": -5},
    "rage": {"x": 0, "y": -3},
    "dreamy": {"x": 4, "y": 0}
  },
  "analysis_notes": "ほとんどの表情は中央揃え。Focus/rageは頭が上向き。Dreamyは右に傾斜。",
  "recommended_regenerate": []
}

このJSONをコピーして以下で使用：
python main.py grid_image.png --offsets offsets.json
```

---

## MakeExpressionJsonとの統合

### コマンドライン使用法

```bash
# オフセットJSONをファイルに保存
echo '{"offsets": {"focus": {"x": 0, "y": -5}}}' > offsets.json

# オフセット付きで実行
python main.py grid_image.png --offsets offsets.json --output ./output/
```

### プログラム的使用法

```python
from usecases.image_splitter import ImageSplitter

offsets = {
    "focus": {"x": 0, "y": -5},
    "rage": {"x": 0, "y": -3},
    "dreamy": {"x": 4, "y": 0}
}

splitter = ImageSplitter(offsets=offsets)
results = splitter.split_from_file("grid_image.png")
```

---

## 注意事項

1. **精度**: オフセットはピクセル単位; ±1-2pxの調整は通常知覚できない
2. **一貫性**: 類似したポーズの表情には類似したオフセットを適用
3. **限界**: 推奨最大オフセットは±20px; より大きい値はセルの再生成が必要なことを示唆
4. **CHIBI表情**: Specialカラムの Row 3-4 は異なるプロポーションの場合あり; 適宜調整

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
