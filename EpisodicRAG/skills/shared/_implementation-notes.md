# 実装ノート（Implementation Notes）

このファイルは、スキル・コマンド実装時の共通ガイドラインを含みます。

---

## UIメッセージの出力形式

**重要**: VSCode拡張のマークダウンレンダリングでは、単一の改行は空白に変換されます。
対話型UIメッセージを表示する際は、必ず**コードブロック（三連バッククォート）**で囲んでください。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 タイトル
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

メッセージ内容

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

これにより、改行がそのまま保持され、ユーザーに正しくフォーマットされたメッセージが表示されます。

---

## config.pyへの依存

すべてのパス情報は`config.py`経由で取得します：

```python
from config import DigestConfig

config = DigestConfig()
loops_path = config.loops_path
digests_path = config.digests_path
essences_path = config.essences_path
```

> 📖 DigestConfigの全プロパティ・メソッドは [API_REFERENCE.md](../../docs/dev/API_REFERENCE.md#クラス-digestconfig) を参照

---

## エラーハンドリング

### 設定ファイル
config.jsonは `@digest-setup` で作成されます：

```python
try:
    config = DigestConfig()
except FileNotFoundError:
    print("❌ 初期セットアップが必要です")
    print("@digest-setup を実行してください")
    sys.exit(1)
```

### データファイル
GrandDigest.txt / ShadowGrandDigest.txt は `load_or_create()` パターンで自動作成されます：

```python
# マネージャークラスが自動的にテンプレートから作成
manager = ShadowGrandDigestManager(config)
data = manager.load_or_create()  # 存在しなければ作成
```

---

## 階層順序の維持

階層的カスケードのため、必ず下位階層から順に生成する必要があります：

```
Weekly → Monthly → Quarterly → Annual →
Triennial → Decadal → Multi-decadal → Centurial
```

推奨アクションでは、常に最下位の生成可能な階層を優先して提示します。

---

## 実装時の優先順位

まだらボケ予防のため、以下の順序でチェックを実行します：

1. **未処理Loop検出** → 警告して即終了
2. **プレースホルダー検出** → 警告して即終了
3. **中間ファイルスキップ検出** → 警告のみ（処理継続）
4. **通常の判定フロー** → 生成可能な階層を表示

---

## 関連ドキュメント

- [用語集・リファレンス](../../README.md) - 用語定義・共通概念
- [API_REFERENCE.md](../../docs/dev/API_REFERENCE.md) - DigestConfig API
- [ARCHITECTURE.md](../../docs/dev/ARCHITECTURE.md) - 技術仕様

---

*このファイルは開発者向けの内部参照用です。*
