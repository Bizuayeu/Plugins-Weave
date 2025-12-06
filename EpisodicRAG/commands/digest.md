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
1. パス情報・新規Loop確認 - digest_entry.py実行
2. SDG読み込み - ShadowGrandDigest.txtを読み込む
3. source_files追加 - 新規Loopファイル名を追加
4. DigestAnalyzer起動 - 各Loopの分析を並列起動
5. 分析結果受信 - long/short分析結果を受け取る
6. Provisional保存 - short結果をProvisionalにアペンド
7. SDG統合更新 - long結果で4要素を更新
8. 処理完了記録 - update_digest_times実行
9. 次アクション提示 - threshold値を参照
```

**各ステップの概要**:

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | パス情報・新規Loop確認 | `python -m interfaces.digest_entry` |
| 2 | SDG読み込み | `essences_path`のShadowGrandDigest.txtを読み込む |
| 3 | source_files追加 | SDGの`weekly.overall_digest.source_files`に新規Loopファイル名を追加 |
| 4 | DigestAnalyzer起動 | Step 3のLoop別に`Task(DigestAnalyzer)`を並列起動 |
| 5 | 分析結果受信 | 各DigestAnalyzerからlong/short分析結果を受け取る |
| 6 | Provisional保存 | short結果をProvisionalWeeklyにアペンド（`save_provisional_digest`） |
| 7 | SDG統合更新 | long結果を統合しSDGの4要素を更新（digest_type, keywords, abstract, impression） |
| 8 | 処理完了記録 | `python -m interfaces.update_digest_times loop <最終番号>` |
| 9 | 次アクション提示 | digest_entry.py出力とthreshold値を参照 |

### 各ステップの詳細

#### Step 1: パス情報・新規Loop確認

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.digest_entry --output json
```

**出力から確認する項目**:
- `new_loops`: 未処理のLoop番号リスト（例: `["L00260", "L00261"]`）
- `essences_path`: ShadowGrandDigest.txtの格納先
- `loops_path`: Loopファイルの格納先

**判定**:
- `new_loops_count > 0` → 新規Loop処理へ進む
- `new_loops_count == 0` → 処理不要

---

#### Step 2: SDG読み込み

**対象ファイル**: `{essences_path}/ShadowGrandDigest.txt`

**操作**: Readツールでファイル全体を読み込む

**確認ポイント**:
- `weekly.overall_digest.source_files`の現在のリスト
- 次のStepで追加するファイル名の重複がないこと

---

#### Step 3: source_files追加

**対象ファイル**: `{essences_path}/ShadowGrandDigest.txt`

**操作**: Editツールで`weekly.overall_digest.source_files`配列に新規Loopファイル名を追加

**追加形式**: `"L00260_タイトル.txt"` （フルファイル名）

**例**:
```json
"source_files": [
  "L00258_既存.txt",
  "L00259_既存.txt",
  "L00260_新規追加.txt"
]
```

---

#### Step 4: DigestAnalyzer起動

**使用ツール**: `Task(subagent_type="EpisodicRAG-Plugin:DigestAnalyzer")`

**起動方法**: Step 3で追加した各Loopに対して**並列**でTaskを起動

**プロンプトに含める情報**:
- 対象ファイルのフルパス: `{loops_path}/L00260_タイトル.txt`
- 出力形式の指示（long/short両方）

---

#### Step 5: 分析結果受信

DigestAnalyzerからJSON形式で結果を受け取る。

**期待する出力形式**:
```json
{
  "source_file": "L00260_タイトル.txt",
  "digest_type": "テーマ（10-20文字）",
  "keywords": ["キーワード1", "キーワード2", "..."],
  "abstract": {
    "long": "2400文字の詳細分析",
    "short": "300文字の要約"
  },
  "impression": {
    "long": "800文字の所感",
    "short": "100文字の要約"
  }
}
```

---

#### Step 6: Provisional保存

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.save_provisional_digest weekly --stdin --append
```

**入力**: Step 5の結果を`individual_digests`配列でラップ

```json
{
  "individual_digests": [
    {
      "source_file": "L00260_タイトル.txt",
      "digest_type": "...",
      "keywords": ["..."],
      "abstract": {"long": "...", "short": "..."},
      "impression": {"long": "...", "short": "..."}
    }
  ]
}
```

**注意**: abstract/impressionは`{long, short}`形式が必須

---

#### Step 7: SDG統合更新

**対象ファイル**: `{essences_path}/ShadowGrandDigest.txt`

**更新対象フィールド**（`weekly.overall_digest`内）:
- `digest_type`: 全source_filesを統合したテーマ
- `keywords`: 統合キーワード5個
- `abstract`: 統合分析（long版を使用）
- `impression`: 統合所感（long版を使用）

**操作**: Editツールで各フィールドを更新

---

#### Step 8: 処理完了記録

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.update_digest_times loop <最終Loop番号>
```

**例**: L00260まで処理した場合
```bash
python -m interfaces.update_digest_times loop 260
```

---

#### Step 9: 次アクション提示

**確認項目**:
- `weekly_source_count`: 現在のsource_files数
- `weekly_threshold`: 確定に必要な数（通常5）

**提示例**:
- source_count < threshold → 「あと N 個のLoopが必要」
- source_count >= threshold → 「`/digest weekly`で確定可能」

---

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

**入力JSONフォーマット**（必須形式）:

```json
{
  "individual_digests": [
    {
      "source_file": "L00260_タイトル.txt",
      "digest_type": "テーマ（10-20文字）",
      "keywords": ["キーワード1", "キーワード2", "..."],
      "abstract": {
        "long": "2400文字の詳細分析",
        "short": "300文字の要約"
      },
      "impression": {
        "long": "800文字の所感",
        "short": "100文字の要約"
      }
    }
  ]
}
```

**重要**: `abstract`と`impression`は必ず`{long, short}`形式を使用。
文字列のみの形式（`"abstract": "テキスト"`）は**エラー**になります。

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
