---
name: digest-config
description: EpisodicRAG設定変更（対話的）
---

# digest-config - 設定変更スキル

EpisodicRAG プラグインの設定を対話的に変更するスキルです。

## 用語説明

- **plugin_root**: プラグインのインストール先（`.claude-plugin/config.json` が存在するディレクトリ）
- **base_dir**: データ配置の基準ディレクトリ（plugin_root からの相対パスで指定）
- **paths**: 各データディレクトリ（base_dir からの相対パスで指定）

## 設定変更フロー

### 1. 設定ファイル読み込み

```python
from pathlib import Path
import json
import sys

# プラグインルート検出
plugin_root = Path("{PLUGIN_ROOT}")  # 実際のパスに調整
# 例: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
config_file = plugin_root / ".claude-plugin" / "config.json"

if not config_file.exists():
    print("❌ 設定ファイルが見つかりません")
    print("")
    print("初回セットアップを実行してください:")
    print("@digest-setup セットアップを実行")
    sys.exit(1)

# 設定読み込み
with open(config_file, 'r', encoding='utf-8') as f:
    config_data = json.load(f)
```

### 2. 現在の設定表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 現在の設定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Base Directory (plugin_rootからの相対パス):
  🔧 base_dir: .

Paths (base_dirからの相対パス):
  📂 loops_dir: data/Loops
  📂 digests_dir: data/Digests
  📂 essences_dir: data/Essences
  📄 identity_file_path: null

Thresholds:
  - weekly: 5
  - monthly: 5
  - quarterly: 3
  - annual: 4
  - triennial: 3
  - decadal: 3
  - multi_decadal: 3
  - centurial: 4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. 変更項目選択

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ 何を変更しますか？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Base directory（パス解決の基準）
[2] Paths（ディレクトリパス）
[3] Identity file（外部参照ファイル）
[4] Thresholds（生成条件）
[5] キャンセル（変更なし）

選択 (1/2/3/4/5):
```

### 4. Base directory 変更（選択肢 1）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Base directory設定の変更
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

base_dirは、すべてのパス解決の基準となるディレクトリです。
プラグインルートからの相対パスで指定します。

現在の設定: .
解決後の絶対パス: {PLUGIN_ROOT}  # 実際のインストール先パス

設定例:
  "." - プラグインルート自身（デフォルト、自己完結）
  "../../.." - 3階層上（例: DEVルート基準）
  "../.." - 2階層上

新しい相対パスを入力してください:
```

#### Base directory 変更の入力

```python
# 現在の値を表示
current_value = config_data.get("base_dir", ".")
plugin_root = Path(__file__).resolve().parent.parent  # プラグインルート

# 現在の解決後パスを計算
current_resolved = (plugin_root / current_value).resolve()

print(f"\n現在の設定: {current_value}")
print(f"解決後の絶対パス: {current_resolved}")
print("")
print("新しい相対パスを入力してください（プラグインルートからの相対パス）:")
print("例:")
print("  . (プラグインルート自身)")
print("  ../../.. (3階層上)")
print("  ../.. (2階層上)")
print("")

new_value = input("新しいパス [Enter でキャンセル]: ")

if new_value == "":
    print("変更をキャンセルしました")
    sys.exit(0)

# パスのバリデーション（解決後の絶対パスを計算）
new_resolved = (plugin_root / new_value).resolve()

# パスの存在確認
if not new_resolved.exists():
    print(f"⚠️ 指定されたパスが存在しません: {new_resolved}")
    create_it = input("このパスを使用しますか？ (y/N): ")
    if create_it.lower() != 'y':
        print("❌ 変更をキャンセルしました")
        sys.exit(1)

# 確認表示
print(f"\n変更プレビュー:")
print(f"  base_dir: {current_value} → {new_value}")
print(f"  解決後: {current_resolved}")
print(f"       → {new_resolved}")
print("")

confirm = input("この変更を適用しますか？ (y/N): ")
if confirm.lower() != 'y':
    print("変更をキャンセルしました")
    sys.exit(0)

# 設定更新
config_data["base_dir"] = new_value
print(f"✅ base_dir を更新しました: {current_value} → {new_value}")
```

### 5. パス変更（選択肢 2）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 パス設定の変更
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

どのパスを変更しますか？

[1] loops_dir (Loopファイルの配置先)
    現在: data/Loops

[2] digests_dir (Digest出力先)
    現在: data/Digests

[3] essences_dir (GrandDigest配置先)
    現在: data/Essences

[4] キャンセル

選択 (1/2/3/4):
```

#### パス変更の入力

```python
# 例: loops_dir を変更
current_value = config_data["paths"]["loops_dir"]
print(f"\n現在の値: {current_value}")
print("新しいパスを入力してください（相対パスはプラグインルート基準）:")
print("例:")
print("  - data/Loops (デフォルト、プラグイン内)")
print("  - ../../../EpisodicRAG/Loops (既存プロジェクト共有)")
print("")

new_value = input("新しいパス [Enter でキャンセル]: ")

if new_value == "":
    print("変更をキャンセルしました")
    sys.exit(0)

# パスのバリデーション
new_path = Path(new_value)
if not new_path.is_absolute():
    # 相対パスの場合、プラグインルート基準で解決
    new_path = plugin_root / new_value

# パスの存在確認
if not new_path.exists():
    print(f"⚠️ 指定されたパスが存在しません: {new_path}")
    create_it = input("ディレクトリを作成しますか？ (y/N): ")
    if create_it.lower() == 'y':
        new_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ ディレクトリを作成しました")
    else:
        print("❌ 変更をキャンセルしました")
        sys.exit(1)

# 設定更新
config_data["paths"]["essences_dir"] = new_value
print(f"✅ essences_dir を更新しました: {current_value} → {new_value}")
```

### 6. Threshold 変更（選択肢 4）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ Threshold設定の変更
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

どの階層のthresholdを変更しますか？

[1] weekly: 5
[2] monthly: 5
[3] quarterly: 3
[4] annual: 4
[5] triennial: 3
[6] decadal: 3
[7] multi_decadal: 3
[8] centurial: 4
[9] すべてカスタマイズ
[0] キャンセル

選択 (1-9/0):
```

#### Threshold 変更の入力

```python
# 例: weekly_threshold を変更
threshold_key = "weekly_threshold"
current_value = config_data["levels"][threshold_key]

print(f"\n現在の値: {current_value}")
print("新しい値を入力してください（1以上の整数）:")
print("")
print("推奨値:")
print("  - Weekly: 5-7 (約1週間分)")
print("  - Monthly: 4-5 (約1ヶ月分)")
print("  - Quarterly: 3 (四半期)")
print("  - Annual: 4 (年)")
print("")

while True:
    new_value_str = input(f"新しい値 [Enter でキャンセル]: ")

    if new_value_str == "":
        print("変更をキャンセルしました")
        sys.exit(0)

    try:
        new_value = int(new_value_str)
        if new_value < 1:
            print("❌ 1以上の値を入力してください")
            continue
        break
    except ValueError:
        print("❌ 数値を入力してください")

# 設定更新
config_data["levels"][threshold_key] = new_value
print(f"✅ {threshold_key} を更新しました: {current_value} → {new_value}")
```

#### すべてカスタマイズ（選択肢 9）

```python
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("⚙️ すべてのThresholdをカスタマイズ")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

threshold_keys = [
    "weekly_threshold",
    "monthly_threshold",
    "quarterly_threshold",
    "annual_threshold",
    "triennial_threshold",
    "decadal_threshold",
    "multi_decadal_threshold",
    "centurial_threshold"
]

for threshold_key in threshold_keys:
    level_name = threshold_key.replace("_threshold", "").title()
    current_value = config_data["levels"][threshold_key]

    while True:
        new_value_str = input(f"{level_name} [{current_value}]: ")

        if new_value_str == "":
            # デフォルト値を使用
            break

        try:
            new_value = int(new_value_str)
            if new_value < 1:
                print("  ❌ 1以上の値を入力してください")
                continue
            config_data["levels"][threshold_key] = new_value
            print(f"  ✅ {level_name}: {current_value} → {new_value}")
            break
        except ValueError:
            print("  ❌ 数値を入力してください")
```

### 7. Identity file 変更（選択肢 3）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Identity file設定の変更
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Identity.mdは、AIの自己認識やプロジェクト固有の
文脈情報を含むファイルです（オプション）。

現在の設定: null

[1] パスを指定
[2] 設定を削除（nullに戻す）
[3] キャンセル

選択 (1/2/3):
```

#### Identity file パス入力

```python
# 選択肢1: パスを指定
print("\nIdentity.mdファイルのパスを入力してください:")
print("（相対パスはプラグインルート基準）")
print("")
print("例:")
print("  - ../../../Identities/WeaveIdentity.md")
print("  - /absolute/path/to/Identity.md")
print("")

new_path_str = input("パス [Enter でキャンセル]: ")

if new_path_str == "":
    print("変更をキャンセルしました")
    sys.exit(0)

# パス存在確認
new_path = Path(new_path_str)
if not new_path.is_absolute():
    new_path = plugin_root / new_path_str

if not new_path.exists():
    print(f"⚠️ 指定されたファイルが見つかりません: {new_path}")
    print("パスを確認してください")
    sys.exit(1)

# 設定更新
config_data["paths"]["identity_file_path"] = new_path_str
print(f"✅ identity_file_path を更新しました: {new_path_str}")

# 選択肢2: 設定を削除
config_data["paths"]["identity_file_path"] = None
print(f"✅ identity_file_path を削除しました（null に設定）")
```

### 8. 設定ファイル更新

変更を設定ファイルに保存します：

```python
# 設定ファイル書き込み
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✅ 設定を保存しました")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
```

### 9. 変更内容の確認

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 更新後の設定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Base Directory (plugin_rootからの相対パス):
  🔧 base_dir: ../../.. (変更されました)

Paths (base_dirからの相対パス):
  📂 loops_dir: data/Loops
  📂 digests_dir: data/Digests
  📂 essences_dir: data/Essences
  📄 identity_file_path: ../../../Identities/WeaveIdentity.md

Thresholds:
  - weekly: 7 (変更されました)
  - monthly: 5
  - quarterly: 3
  - annual: 4
  - triennial: 3
  - decadal: 3
  - multi_decadal: 3
  - centurial: 4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ℹ️ 次回の `/digest` から新しい設定が適用されます
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 設定変更の即座反映

設定変更後、config.py は次回の読み込み時に自動的に新しい設定を読み込みます。

**注意**: 既に生成済みのダイジェストには影響しません。新しい設定は、次回の `/digest` 実行時から適用されます。

## 実装時の注意事項

> 📖 共通の実装ガイドラインは [_implementation-notes.md](../shared/_implementation-notes.md) を参照してください。

### 本スキル固有の注意点

## バリデーション

### パスのバリデーション

```python
def validate_path(path_str, plugin_root, must_exist=False):
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

### Threshold のバリデーション

```python
def validate_threshold(value):
    """Thresholdのバリデーション"""
    try:
        int_value = int(value)
        if int_value < 1:
            raise ValueError("Thresholdは1以上である必要があります")
        return int_value
    except ValueError:
        raise ValueError("Thresholdは整数である必要があります")
```

## エラーハンドリング

```python
# 設定ファイルが存在しない
if not config_file.exists():
    print("❌ 設定ファイルが見つかりません")
    print("@digest-setup を実行してください")
    sys.exit(1)

# JSON読み込みエラー
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
except json.JSONDecodeError:
    print("❌ 設定ファイルが破損しています")
    print("@digest-setup で再セットアップしてください")
    sys.exit(1)

# 設定ファイル書き込みエラー
try:
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f"❌ 設定ファイルの保存に失敗しました: {e}")
    sys.exit(1)
```

## スキルの自律判断

このスキルは**自律的には起動しません**。必ずユーザーの明示的な呼び出しが必要です。

理由：

- 設定変更はユーザーの意図を確認する必要がある
- 誤った設定変更を防ぐため
- 対話的な UI が必要

## 使用例

### 例 1: weekly threshold を変更

```
@digest-config weekly threshold を 7 に変更
```

→ 対話的に weekly_threshold を 7 に変更

### 例 2: Loop ディレクトリを変更

```
@digest-config Loopディレクトリを既存プロジェクトと共有したい
```

→ 対話的に loops_dir を変更

### 例 3: 設定全体を確認

```
@digest-config 設定を確認
```

→ 現在の設定を表示（変更なし）

---

**このスキルは、EpisodicRAG プラグインの設定を対話的に変更します ⚙️**

---

