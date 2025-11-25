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

### 主要プロパティ

| プロパティ | 説明 |
|-----------|------|
| `plugin_root` | プラグインルートディレクトリ |
| `loops_path` | Loopファイル配置先 |
| `digests_path` | Digest出力先 |
| `essences_path` | GrandDigest配置先 |
| `*_threshold` | 各階層の閾値（weekly_threshold等） |

### 主要メソッド

| メソッド | 説明 |
|---------|------|
| `get_level_dir(level)` | 階層ディレクトリ取得 |
| `get_provisional_dir(level)` | Provisionalディレクトリ取得 |
| `get_identity_file_path()` | Identityファイルパス取得 |

---

## エラーハンドリング

すべてのファイルは`@digest-setup`で作成されます：

```python
# 設定ファイル、ShadowGrandDigest、GrandDigestが存在しない場合
try:
    config = DigestConfig()
except FileNotFoundError:
    print("❌ 初期セットアップが必要です")
    print("@digest-setup を実行してください")
    sys.exit(1)

if not shadow_file.exists() or not grand_file.exists():
    print("❌ 必要なファイルが見つかりません")
    print("@digest-setup を実行してください")
    sys.exit(1)
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

*このファイルは内部参照用です。直接編集する場合は、参照元のドキュメントも確認してください。*
