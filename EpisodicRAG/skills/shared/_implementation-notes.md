[EpisodicRAG](../../README.md) > [Skills](../README.md) > Implementation Notes

# 実装ノート（Implementation Notes）

このファイルは、スキル・コマンド実装時の共通ガイドラインを含みます。

---

## UIメッセージの出力形式

**重要**: VSCode拡張のマークダウンレンダリングでは、単一の改行は空白に変換されます。
対話型UIメッセージを表示する際は、必ず**コードブロック（三連バッククォート）**で囲んでください。

```text
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

> 📖 DigestConfigの全プロパティ・メソッドは [api/config.md](../../docs/dev/api/config.md) を参照

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

```text
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

## バリデーションパターン

### Config ファイル検証

config.json の存在確認と読み込みパターン：

```python
from pathlib import Path
import json
import sys

plugin_root = Path("{PLUGIN_ROOT}")  # 実際のパスに調整
config_file = plugin_root / ".claude-plugin" / "config.json"

# 存在確認
if not config_file.exists():
    print("❌ 設定ファイルが見つかりません")
    print("@digest-setup を実行してください")
    sys.exit(1)

# 読み込み（JSONパースエラー対応）
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
except json.JSONDecodeError:
    print("❌ 設定ファイルが破損しています")
    print("@digest-setup で再セットアップしてください")
    sys.exit(1)
```

### パス検証

相対パス/絶対パスの解決とバリデーション：

```python
def validate_path(path_str: str, plugin_root: Path, must_exist: bool = False) -> Path:
    """パスのバリデーション"""
    path = Path(path_str)

    # 相対パスの場合、プラグインルート基準で解決
    if not path.is_absolute():
        path = plugin_root / path_str

    # 存在確認（オプション）
    if must_exist and not path.exists():
        raise FileNotFoundError(f"パスが見つかりません: {path}")

    return path
```

### 閾値（Threshold）入力検証

閾値入力のバリデーションパターン：

```python
def validate_threshold(value: str) -> int:
    """閾値のバリデーション（1以上の整数）"""
    try:
        int_value = int(value)
        if int_value < 1:
            raise ValueError("閾値は1以上である必要があります")
        return int_value
    except ValueError:
        raise ValueError("閾値は整数である必要があります")

# 使用例：入力ループ
while True:
    new_value_str = input(f"新しい値 [Enter でキャンセル]: ")
    if new_value_str == "":
        print("変更をキャンセルしました")
        break
    try:
        new_value = validate_threshold(new_value_str)
        break
    except ValueError as e:
        print(f"❌ {e}")
```

---

## 共通エラーメッセージ

### Config未検出時

```text
❌ 設定ファイルが見つかりません
@digest-setup を実行してください
```

### JSON パースエラー時

```text
❌ 設定ファイルが破損しています
@digest-setup で再セットアップしてください
```

### ファイル書き込みエラー時

```python
try:
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f"❌ 設定ファイルの保存に失敗しました: {e}")
    sys.exit(1)
```

---

## 関連ドキュメント

- [用語集・リファレンス](../../README.md) - 用語定義・共通概念
- [API_REFERENCE.md](../../docs/dev/API_REFERENCE.md) - DigestConfig API
- [ARCHITECTURE.md](../../docs/dev/ARCHITECTURE.md) - 技術仕様

---

*このファイルは開発者向けの内部参照用です。*
