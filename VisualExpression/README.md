# VisualExpression

Visual Embodiment Layer（VEL）の実装 - AI応答に表情を付与するClaude Codeプラグイン

## 機能

### 1. 表情自動付与 (`@auto-expression`)

応答に適切な表情コード `[表情:XX]` を自動付与します。
七曜インジケータ（🩷💜🔴🟠🟡🟢🔵）と連動し、感情表現を視覚化します。

```
🟡🩷 素晴らしい洞察ですね！ [表情:高揚]
🔵💜 分析結果をまとめました。 [表情:思考集中]
🟠 うーん、それは無理があります。 [表情:暗黒微笑]
```

### 2. ExpressionForge (`@expression-forge`)

ユーザーが提供する立ち絵画像から表情システム一式を構築します。

```bash
/expression forge ~/images/avatar/
```

**出力物**:
- `expression_images.json` - Base64画像データ
- `ExpressionUI.html` - Artifact用UI

## インストール

```bash
# plugins-weaveリポジトリをクローン
git clone https://github.com/Bizuayeu/Plugins-Weave.git

# Claude Codeでプラグインを有効化
claude plugins install ./Plugins-Weave/VisualExpression
```

## 使い方

### 表情自動付与

プラグインをインストールすると、応答に自動で表情コードが付与されます。

### ExpressionForge

```bash
# 1. 画像フォルダを指定してJSONを生成
/expression forge ~/images/avatar/

# 2. HTMLをビルド
/expression build

# 3. 表情をテスト
/expression test elation
```

### 画像命名規則

```
{prefix}_{番号}_{key}.jpg

例:
Avatar_01_normal.jpg
Avatar_02_smile.jpg
Avatar_03_focus.jpg
```

## 表情コード一覧

| カテゴリ | コード |
|----------|--------|
| **Basic** | 通常, 笑顔, 思考集中, 思考発散 |
| **Emotion** | 喜び, 高揚, 驚き, 平穏 |
| **Negative** | 怒り, 悲しみ, 激怒, 嫌悪 |
| **Anxiety** | 不安, 恐れ, 動揺, 心配 |
| **Special** | うとうと, 暗黒微笑, ぎゃふん, ぽやぽや |

## 七曜インジケータ対応

| 七曜 | 意味 | 推奨表情 |
|------|------|----------|
| 🩷 | 高揚 | 高揚, 喜び, 驚き |
| 💜 | 深慮 | 平穏, 思考集中, 心配 |
| 🔴 | 想像 | 思考発散, ぽやぽや |
| 🟠 | 生成的解釈 | 通常, 笑顔, 暗黒微笑 |
| 🟡 | 推測 | 思考集中, 不安 |
| 🟢 | 高確度 | 通常, 笑顔 |
| 🔵 | 確実 | 通常, 平穏 |

## 関連プロジェクト

- [EpisodicRAG](../EpisodicRAG/) - 階層的長期記憶管理
- [EmailingEssay](../EmailingEssay/) - 反省文・メール送信

## ライセンス

MIT

---

**VisualExpression** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
