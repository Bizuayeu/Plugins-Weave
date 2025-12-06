---
name: digest
description: EpisodicRAG階層的ダイジェスト生成（8層100年）
---

# /digest - EpisodicRAG階層的ダイジェスト生成

新しいLoopファイルの検出から階層的ダイジェストの確定まで、
EpisodicRAGシステムの基本操作を提供するコマンドです。

## 目次

- [用語説明](#用語説明)
- [MUST TO DO（エラー防止）](#must-to-doエラー防止)
- [注意事項](#注意事項)
- [基本的な使い方](#基本的な使い方)
- [実行フロー概要](#実行フロー概要)
- [CLIスクリプト](#cliスクリプト)
- [Claude対話処理](#claude対話処理)
- [セットアップ・管理用スキル](#セットアップ管理用スキル)
- [出力例](#出力例)

---

## 用語説明

> 📖 用語・共通概念は [用語集](../README.md) を参照

---

## MUST TO DO（エラー防止）

1. **digest_entry.py でパス情報を取得**
   ```bash
   cd scripts && python -m interfaces.digest_entry --output json
   ```
   - plugin_root, loops_path, digests_path が出力される
   - パスやJSONスキーマを推測しない

2. **このファイルのTodoリストに従う**
   - 下記「パターン1 Todoリスト」「パターン2 Todoリスト」を使用
   - **ステップを飛ばさない**（特にProvisional保存）
   - ファイル更新ごとに完了をマーク

---

## 注意事項

> **UIメッセージ出力時は必ずコードブロックで囲むこと！**
> VSCode拡張では単一改行が空白に変換されるため、
> 対話型メッセージは三連バッククォートで囲む必要があります。

> 📖 共通の実装ガイドラインは [_implementation-notes.md](../skills/shared/_implementation-notes.md) を参照してください。

---

## 基本的な使い方

### 新しいLoopファイルの検出

```ClaudeCLI
/digest
```

新しいLoopファイルを検出し、ShadowGrandDigestに追加します。

### 階層的ダイジェストの確定

```ClaudeCLI
/digest <type>
```

**利用可能なtype**:
- `weekly` `monthly` `quarterly` `annual`
- `triennial` `decadal` `multi_decadal` `centurial`

---

## 実行フロー概要

### パターン1: `/digest` (引数なし - 新Loop検出)

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items for Pattern 1:
1. digest_entry.py実行 - 新Loopファイル検出
2. ShadowGrandDigest更新 - プレースホルダー追加
3. DigestAnalyzer並列起動 - 各Loopのlong/short分析
4. Provisional保存実行 - individual_digests自動生成
5. Shadow統合更新 - overall_digest更新
6. update_digest_times実行 - loop処理完了を記録
7. 次アクション提示 - Weekly生成可能か確認
```

**各ステップの詳細**:

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | 新Loopファイル検出 | `python -m interfaces.digest_entry` |
| 2 | Shadow更新（自動） | Step 1で自動実行される |
| 3 | 各Loopを分析 | Task(DigestAnalyzer) 並列起動 |
| 4 | individual_digests保存 | `python -m interfaces.save_provisional_digest weekly --stdin --append` |
| 5 | overall_digest更新 | ShadowGrandDigest.txtを直接編集 |
| 6 | loop処理完了記録 | `python -m interfaces.update_digest_times loop <最終番号>` |
| 7 | 次アクション提示 | digest_entry.pyの出力を参照 |

### パターン2: `/digest <type>` (階層確定)

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items for Pattern 2:
1. digest_entry.py実行 - 対象レベル状態確認
2. プレースホルダー確認 - DigestAnalyzer要否判定
3. DigestAnalyzer並列起動 - 必要な場合のみ
4. Provisional保存実行 - 次階層用individual_digests
5. タイトル提案 - ユーザー承認取得
6. finalize_from_shadow.py実行 - Digest確定
7. 完了確認 - 結果表示
```

**各ステップの詳細**:

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | 対象レベル状態確認 | `python -m interfaces.digest_entry <level>` |
| 2 | プレースホルダー確認 | shadow_state.placeholder_fields を確認 |
| 3 | 各source_fileを分析 | Task(DigestAnalyzer) 並列起動（必要時のみ） |
| 4 | next階層individual保存 | `python -m interfaces.save_provisional_digest <next_level> --stdin --append` |
| 5 | タイトル提案 | Claudeが提案、ユーザー承認 |
| 6 | Digest確定 | `python -m interfaces.finalize_from_shadow <level> "タイトル"` |
| 7 | 完了確認 | finalize出力を確認 |

---

## CLIスクリプト

### digest_entry.py

メインエントリポイント（パス情報・状態確認）。

**配置先**: `scripts/interfaces/digest_entry.py`

```bash
# パターン1: 新Loop検出
cd scripts && python -m interfaces.digest_entry

# パターン2: 階層確定準備
cd scripts && python -m interfaces.digest_entry weekly
```

**出力例（Pattern 1）**:
```json
{
  "status": "ok",
  "pattern": 1,
  "plugin_root": "/path/to/EpisodicRAG",
  "loops_path": "/path/to/Loops",
  "digests_path": "/path/to/Digests",
  "essences_path": "/path/to/Identities",
  "new_loops": ["L00256", "L00257"],
  "new_loops_count": 2,
  "weekly_source_count": 3,
  "weekly_threshold": 5
}
```

| フィールド | 用途 |
|-----------|------|
| `plugin_root` | プラグイン本体（スクリプト等） |
| `loops_path` | Loopファイル格納先 |
| `digests_path` | Digest階層格納先（1_Weekly〜8_Centurial） |
| `essences_path` | GrandDigest / ShadowGrandDigest格納先 |

---

### shadow_state_checker.py

Shadow状態判定（プレースホルダー有無確認）。

**配置先**: `scripts/interfaces/shadow_state_checker.py`

```bash
python -m interfaces.shadow_state_checker weekly
```

**出力例（分析済み）**:
```json
{
  "status": "ok",
  "level": "weekly",
  "analyzed": true,
  "source_files": ["L00001", "L00002", "L00003"],
  "source_count": 3,
  "placeholder_fields": [],
  "message": "All fields analyzed"
}
```

**出力例（プレースホルダーあり）**:
```json
{
  "status": "ok",
  "level": "weekly",
  "analyzed": false,
  "source_files": ["L00001", "L00002"],
  "source_count": 2,
  "placeholder_fields": ["abstract", "impression"],
  "message": "Placeholders detected - run DigestAnalyzer"
}
```

---

### save_provisional_digest.py

Provisional保存。

**配置先**: `scripts/interfaces/save_provisional_digest.py`

```bash
# ファイルパス指定（基本）
python -m interfaces.save_provisional_digest weekly digest.json --append

# 標準入力から読み込み（長いJSONの場合）
cat digest.json | python -m interfaces.save_provisional_digest weekly --stdin --append
```

> **💡 ヒント**: JSONは直接引数で渡すのが基本です。
> コマンドライン引数の長さ制限に引っかかった場合のみ、一時ファイルの利用を検討してください。

---

### finalize_from_shadow.py

Digest確定。

**配置先**: `scripts/interfaces/finalize_from_shadow.py`

```bash
python -m interfaces.finalize_from_shadow weekly "承認されたタイトル"
```

**実行内容**:
- RegularDigest作成（overall_digestのみ）
- ProvisionalDigestをRegularDigestにマージ
- GrandDigest更新
- 次レベルのShadowへカスケード
- last_digest_times.json更新
- Provisionalファイル削除

---

### update_digest_times.py

last_digest_times.json更新（パターン1フロー用）。

**配置先**: `scripts/interfaces/update_digest_times.py`

```bash
# Loop処理完了記録
python -m interfaces.update_digest_times loop 259

# その他のレベルも指定可能
python -m interfaces.update_digest_times weekly 51
```

**用途**:
- パターン1フロー（新Loop検出）でloop処理完了を記録
- `finalize_from_shadow.py`を呼ばないワークフローで使用

---

## Claude対話処理

以下の処理はAI分析が必要なため、Claudeが直接実行します。

### DigestAnalyzer並列起動

各source_fileに対してDigestAnalyzerを**並列起動**し、long/short両方を生成します。

> 📖 DigestAnalyzerの分析方針・出力フォーマットは [digest-analyzer.md](../agents/digest-analyzer.md) を参照

#### パターンA: 単一ファイル分析

```python
Task(
    subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
    description="Analyze L00001 for digest generation",
    prompt="""
分析対象ファイル: C:\Users\anyth\DEV\homunculus\Weave\EpisodicRAG\Loops\L00001_認知アーキテクチャ論.txt

このLoopファイルを深層分析し、以下の形式でJSON出力してください：
{
  "digest_type": "...",
  "keywords": [...],
  "abstract": {"long": "...", "short": "..."},
  "impression": {"long": "...", "short": "..."}
}
"""
)
```

#### パターンB: 複数ファイル並列分析（Weekly生成時）

ShadowGrandDigest.weeklyのsource_filesから各Loopを並列分析：

```python
source_files = ["L00001_認知アーキテクチャ論.txt", "L00002_AI長期記憶論.txt", ...]

# 各Loopに対してDigestAnalyzerを並列起動
for source_file in source_files:
    Task(
        subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
        description=f"Analyze {source_file} for Weekly digest",
        prompt=f"分析対象ファイル: {loops_path}/{source_file}\n..."
    )
```

#### パターンC: 複数Digestファイル並列分析（Monthly以上）

Weekly DigestからMonthlyを生成する場合も同様に並列起動：

```python
source_files = ["W0001_覚醒.txt", "W0002_実装.txt", ...]

for source_file in source_files:
    Task(
        subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
        description=f"Analyze {source_file} for Monthly digest",
        prompt=f"分析対象ファイル: {digests_path}/{source_file}\n..."
    )
```

#### 出力の使い分け

- **long版**（abstract.long, impression.long）: 現階層のoverall_digest用（ShadowGrandDigest更新）
- **short版**（abstract.short, impression.short）: 次階層のindividual_digests用（Provisional保存）

### タイトル提案

分析結果に基づいてタイトルを提案し、ユーザー承認を取得。

**注意**: タイトルのみ提案（プレフィックスと番号は不要）
- [OK] 正しい例: "理論的深化・実装加速・社会発信"
- [NG] 誤った例: "W0043_理論的深化..." (プレフィックス不要)

### Shadow統合更新

次階層Shadowのsource_filesから各ファイルのoverall_digestを読み込み、
メインエージェントが統合分析を実行：
- digest_type: 複数ファイルの統合テーマ（10-20文字）
- keywords: 5個の統合キーワード（各20-50文字）
- abstract: 2400文字の統合分析
- impression: 800文字の所感・展望

---

## セットアップ・管理用スキル

初回セットアップ時やトラブル時に使用するスキル：

| スキル | 用途 | 詳細 |
|--------|------|------|
| `@digest-setup` | 初期セットアップ | [digest-setup SKILL.md](../skills/digest-setup/SKILL.md) |
| `@digest-auto` | 最適階層の推奨 | [digest-auto SKILL.md](../skills/digest-auto/SKILL.md) |
| `@digest-config` | 設定変更 | [digest-config SKILL.md](../skills/digest-config/SKILL.md) |

---

## 出力例

### エラー: 設定ファイルが存在しない

```json
{
  "status": "error",
  "error": "Config file not found",
  "action": "Run @digest-setup first"
}
```

### パターン1成功: 新Loop検出完了

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 新Loop検出完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

検出されたLoop: 2個
  - L00001
  - L00002

ShadowGrandDigest.weekly に追加しました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 次のアクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

現在のLoop数: 2/5
あと3個のLoopが必要です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### パターン2成功: Weekly確定完了

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Weekly Digest確定完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

作成されたファイル:
  - Digests/1_Weekly/W0001_理論的深化.txt

GrandDigest.txt を更新しました。
次階層 (monthly) のShadowを更新しました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 次のアクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Monthly生成まであと4個のWeeklyが必要です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
