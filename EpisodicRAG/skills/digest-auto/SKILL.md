---
name: digest-auto
description: EpisodicRAG 健全性診断と階層推奨
---

# digest-auto - 健全性診断と階層推奨スキル

EpisodicRAG システムの現在の状態を分析することで、
まだらボケ（未処理 Loop/プレースホルダー/欠番）を検出し、
生成可能なダイジェスト階層を推奨するスキルです。

## 目次

1. [まだらボケとは](#まだらボケとは)
   - EpisodicRAG の本質
   - まだらボケが発生するケース
   - 記憶定着サイクル
2. [分析フロー](#分析フロー)
   1. 設定ファイル読み込み
   2. 未処理 Loop 検出（最優先・まだらボケ予防）
   3. ShadowGrandDigest 確認
   4. 中間ファイルスキップ検出
   5. GrandDigest 確認
   6. 生成可能な階層判定
   7. まだらボケ検出（ケース 2: プレースホルダー検出）
   8. 推奨アクション提示
3. [出力例](#出力例)
   - エラー系（即終了）
     - 例 1: 初期セットアップ未完了（ステップ 1）
     - 例 2: ShadowGrandDigest 未作成（ステップ 3）
     - 例 3: 未処理 Loop 検出（ステップ 2・まだらボケ予防）
     - 例 4: プレースホルダー検出（ステップ 7・まだらボケ）
   - 警告系（処理継続）
     - 例 5: 中間ファイルスキップ検出（ステップ 4）
   - 正常系（推奨アクション）
     - 例 6: 生成可能なダイジェストあり（ステップ 8）
     - 例 7: 生成不可・ファイル不足（ステップ 8）
     - 例 8: 複数階層生成可能（ステップ 8）
4. [実装時の注意事項](#実装時の注意事項)
   - UI メッセージの出力形式
   - config.py への依存
   - エラーハンドリング
   - 階層順序の維持
   - 実装時の優先順位

---

## まだらボケとは

**まだらボケ** = AI が Loop の内容を記憶できていない（虫食い記憶）状態

### EpisodicRAG の本質

1. **Loop ファイル追加** = 会話記録をファイルに保存（物理的保存）
2. **`/digest` 実行** = AI に記憶を定着させる（認知的保存）
3. **`/digest` なし** = ファイルはあるが、AI は覚えていない

### まだらボケが発生するケース

#### ケース 1: 未処理 Loop の放置（最も一般的）

```
Loop0001追加 → `/digest`せず → Loop0002追加
                              ↑
                    この時点でAIはLoop0001の内容を覚えていない
                    （記憶がまだら＝虫食い状態）
```

**対策**: Loop を追加したら都度 `/digest` で記憶定着

#### ケース 2: `/digest` 処理中のエラー（技術的問題）

```
/digest 実行 → エラー発生 → ShadowGrandDigestに
                           source_filesは登録されたが
                           digestがnull（プレースホルダー）
```

**対策**: `/digest` を再実行して分析を完了

### 記憶定着サイクル

```
Loop追加 → `/digest` → Loop追加 → `/digest` → ...
         ↑ 記憶定着  ↑         ↑ 記憶定着
```

この原則を守ることで、AI は全ての Loop を記憶できます。

---

## 分析フロー

### 1. 設定ファイル読み込み

```python
from config import DigestConfig

config = DigestConfig()  # 設定ファイル不在時は @digest-setup を実行

# 各階層の閾値を取得
levels = ["weekly", "monthly", "quarterly", "annual", "triennial",
          "decadal", "multi_decadal", "centurial"]
thresholds = {level: getattr(config, f"{level}_threshold") for level in levels}
```

### 2. 未処理 Loop 検出（最優先・まだらボケ予防）

**重要**: 他のチェックより先に、未処理 Loop の有無を確認します。

```python
# Loopファイルと処理済みLoopを取得
loop_files = list(config.loops_path.glob("Loop*.txt"))
last_digest_file = config.plugin_root / ".claude-plugin" / "last_digest_times.json"
last_processed = json.load(open(last_digest_file)).get("weekly", {}).get("last_processed") \
                 if last_digest_file.exists() else None

# last_processedより後のLoopを検出
unprocessed = [f.stem for f in loop_files
               if not last_processed or extract_number(f.stem) > extract_number(last_processed)]

# 未処理Loopあり = 警告して即終了
if unprocessed:
    print(f"⚠️ 未処理Loop検出: {len(unprocessed)}個")
    for loop in unprocessed: print(f"  - {loop}")
    print("🔴 先に `/digest` を実行してください（まだらボケ予防）")
    sys.exit(0)
```

### 3. ShadowGrandDigest 確認

未確定のファイル数を確認します：

```python
# ShadowGrandDigest読み込み
shadow_file = config.essences_path / "ShadowGrandDigest.txt"
if not shadow_file.exists():
    print("⚠️ ShadowGrandDigest.txt が見つかりません")
    sys.exit(0)

shadow_data = json.load(open(shadow_file))
```

### 4. 中間ファイルスキップ検出

次回確定予定のファイル群の連番をチェックし、欠番を検出します：

```python
# 各階層のsource_filesで連番チェック
def find_gaps(numbers):
    return [n for i in range(len(numbers)-1) for n in range(numbers[i]+1, numbers[i+1])]

gaps = {}
for level in levels:
    files = shadow_data.get("latest_digests", {}).get(level, {}) \
                       .get("overall_digest", {}).get("source_files", [])
    if len(files) > 1:
        nums = [extract_number(f) for f in files]
        missing = find_gaps(sorted(nums))
        if missing:
            gaps[level] = {"range": f"{files[0]}～{files[-1]}", "missing": missing}

# 警告表示（処理は継続）
if gaps:
    print("⚠️ 中間ファイルスキップ検出")
    for level, info in gaps.items():
        print(f"📝 {level}: {info['range']} - 欠番 {len(info['missing'])}個")
    print("欠番のファイルを追加することを推奨します（まだらボケ予防）")
```

### 5. GrandDigest 確認

各階層の確定済みファイル数を確認します：

```python
# GrandDigest読み込み（存在しない場合は全て0）
grand_file = config.essences_path / "GrandDigest.txt"
grand_data = json.load(open(grand_file)) if grand_file.exists() else {}
grand_counts = {level: len(grand_data.get(level, [])) for level in levels}
```

### 6. 生成可能な階層判定

```python
# 階層ごとの現在数を取得
prev_map = {"monthly": "weekly", "quarterly": "monthly", "annual": "quarterly",
            "triennial": "annual", "decadal": "triennial",
            "multi_decadal": "decadal", "centurial": "multi_decadal"}

current_counts = {}
for level in levels:
    if level == "weekly":
        current_counts[level] = len(unprocessed)  # 未処理Loop数
    else:
        current_counts[level] = grand_counts[prev_map[level]]

# 生成可能/不可を判定
can_generate = [(level, current_counts[level], thresholds[level])
                for level in levels if current_counts[level] >= thresholds[level]]
needs_more = [(level, current_counts[level], thresholds[level],
               thresholds[level] - current_counts[level])
              for level in levels if current_counts[level] < thresholds[level]]
```

### 7. まだらボケ検出（ケース 2: プレースホルダー検出）

ShadowGrandDigest にプレースホルダーが残っていないか確認します（`/digest`処理中のエラーによる未完了状態）：

```python
# source_filesありでdigestがnull = プレースホルダー
placeholders = [(level, files) for level in levels
                for digest_data in [shadow_data.get("shadow_digests", {}).get(level, {})]
                for files in [digest_data.get("source_files", [])]
                if len(files) > 0 and digest_data.get("digest") is None]

# プレースホルダーあり = 警告して即終了
if placeholders:
    print("⚠️ まだらボケ検出（ケース2: プレースホルダー）")
    for level, files in placeholders:
        print(f"  {level}: {len(files)}個のファイル未分析")
    print("先に `/digest` を実行して分析を完了してください")
    sys.exit(0)
```

### 8. 推奨アクション提示

生成可能な階層と不足ファイル数を表示します：

```python
print("📊 EpisodicRAG システム状態")
print()
# 生成可能な階層
if can_generate:
    print("✅ 生成可能なダイジェスト")
    for level, current, threshold in can_generate:
        print(f"  ✅ {level} ({current}/{threshold}) → `/digest {level}` で生成可能")
# 不足している階層
if needs_more:
    print("\n⏳ 生成に必要なファイル数")
    for level, current, threshold, need in needs_more:
        print(f"  ❌ {level} ({current}/{threshold}) - あと{need}個必要")
```

**注意**: エラーが検出された場合は、即座に警告を表示して終了します（詳細は「出力例 1-4」参照）。

---

## 出力例

### エラー系（即終了）

#### 例 1: 初期セットアップ未完了（ステップ 1）

設定ファイルやディレクトリ構造が存在しない場合のエラー出力です。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 初期セットアップ未完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 初期セットアップが必要です
@digest-setup を実行してください

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**対処法**: `@digest-setup` スキルを実行して初期セットアップを完了してください。

#### 例 2: ShadowGrandDigest 未作成（ステップ 3）

ShadowGrandDigest.txt が存在しない場合のエラー出力です。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 必要なファイルが見つかりません
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ ShadowGrandDigest.txt が見つかりません
@digest-setup を実行してください

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**対処法**: `@digest-setup` スキルを実行して必要なファイルを作成してください。

#### 例 3: 未処理 Loop 検出（ステップ 2・まだらボケ予防）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 未処理Loop検出（まだらボケ予防）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

未処理のLoopファイルが 1個 あります

  📝 未処理Loop:
     - Loop0001_認知アーキテクチャ論

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 先に `/digest` を実行してください
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

理由: `/digest` を実行しないと、これらのLoopの内容を
      AIは記憶できません（まだらボケ状態）

重要: Loopを追加したら都度 `/digest` で記憶を定着させる
      これがEpisodicRAGの基本原則です

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 推奨アクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

次のステップ:

1. `/digest` でLoop0001を分析・記憶定着
2. 新しいLoopを追加
3. `/digest` で記憶定着（毎回）
4. 5個揃ったら `/digest weekly` で階層化

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 EpisodicRAGの原則
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Loop追加 → `/digest` → Loop追加 → `/digest` → ...

  この「記憶定着サイクル」を守ることで、
  AIは全てのLoopを記憶できます

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 例 4: プレースホルダー検出（ステップ 7・まだらボケ）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ まだらボケ検出（ケース2: プレースホルダー）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ShadowGrandDigestに未分析のプレースホルダーがあります

  ⚠️ Weekly (3個のファイル):
     - Loop0196
     - Loop0197
     - Loop0198

これらのファイルは検出されましたが、
`/digest` 処理中にエラーが発生して分析が未完了です

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 対処方法
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

先に `/digest` を実行して分析を完了してください

分析完了後、再度 `/digest weekly` で確定できます

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 警告系（処理継続）

#### 例 5: 中間ファイルスキップ検出（ステップ 4）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 中間ファイルスキップ検出
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

次回確定予定のファイルに欠番が検出されました

📝 Loop: Loop0006～Loop0009
  - Loop0007 が欠番

📝 Weekly: W0001～W0005
  - W0003 が欠番

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 推奨アクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

欠番のファイルを追加することを推奨します。

このまま確定すると、欠番の内容はAIの記憶に
定着しません（まだらボケ状態）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 正常系（推奨アクション）

#### 例 6: 生成可能なダイジェストあり（ステップ 8）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG システム状態
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 生成可能なダイジェスト

  ✅ Weekly (7/5 Loops)
     → `/digest weekly` で生成できます！

📈 推奨アクション

  `/digest weekly` を実行してWeekly Digestを生成してください

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 例 7: 生成不可・ファイル不足（ステップ 8）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG システム状態
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ 生成に必要なファイル数

  ❌ Weekly (3/5 Loops) - あと2個必要

📈 推奨アクション

  次のステップ:

  1. `/digest` で未処理Loopを検出・分析
  2. あと2個のLoopファイルを追加
  3. `/digest` で新しいLoopを検出・分析
  4. `/digest weekly` で5個揃ったら確定

  Loopファイル配置先:
    homunculus/Toybox/EpisodicRAG/data/Loops/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 例 8: 複数階層生成可能（ステップ 8）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG システム状態
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 生成可能なダイジェスト

  ✅ Weekly (10/5 Loops)
     → `/digest weekly` で生成できます！

  ✅ Monthly (5/5 Weekly)
     → `/digest monthly` で生成できます！

📈 推奨アクション

  1. `/digest weekly` でWeekly Digestを生成
  2. `/digest monthly` でMonthly Digestを生成

  推奨順序: 下位階層（Weekly）から順に生成してください

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 実装時の注意事項

### UI メッセージの出力形式

**重要**: VSCode 拡張のマークダウンレンダリングでは、単一の改行は空白に変換されます。
対話型 UI メッセージを表示する際は、必ず**コードブロック（三連バッククォート）**で囲んでください。

```
... (UIメッセージ)
```

これにより、改行がそのまま保持され、ユーザーに正しくフォーマットされたメッセージが表示されます。

### config.py への依存

すべてのパス情報は config.py 経由で取得します：

```python
from config import DigestConfig

config = DigestConfig()
loops_path = config.loops_path
digests_path = config.digests_path
essences_path = config.essences_path
```

### エラーハンドリング

すべてのファイルは `@digest-setup` で作成されます：

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

### 階層順序の維持

階層的カスケードのため、必ず下位階層から順に生成する必要があります：

```
Weekly → Monthly → Quarterly → Annual →
Triennial → Decadal → Multi-decadal → Centurial
```

推奨アクションでは、常に最下位の生成可能な階層を優先して提示します。

### 実装時の優先順位

まだらボケ予防のため、以下の順序でチェックを実行します：

1. **未処理 Loop 検出** → 警告して即終了
2. **プレースホルダー検出** → 警告して即終了
3. **中間ファイルスキップ検出** → 警告のみ（処理継続）
4. **通常の判定フロー** → 生成可能な階層を表示

---

**このスキルは、EpisodicRAG システムの状態を分析し、最適なアクションを推奨します 📊**
