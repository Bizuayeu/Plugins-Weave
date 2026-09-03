---
name: digest
description: EpisodicRAG階層的ダイジェスト生成（8層100年）
---

# /digest - EpisodicRAG階層的ダイジェスト生成

新しいLoopファイルの検出から階層的ダイジェストの確定まで、
EpisodicRAGシステムの基本操作を提供するコマンドです。

## 目次

- [用語説明](#用語説明)
- [重要な注意事項](#重要な注意事項)
- [基本的な使い方](#基本的な使い方)
- [パターン1: /digest（新Loop検出）](#パターン1-digest新loop検出)
- [パターン2: /digest type（階層確定）](#パターン2-digest-type階層確定)
- [セットアップ・管理用スキル](#セットアップ管理用スキル)

---

## 用語説明

> 📖 用語・共通概念は [用語集](../GLOSSARY.md) を参照

---

## 重要な注意事項

### 1. スクリプト実行時のパス

スクリプト実行は**インストール済みプラグインパス**を優先してください。

```bash
# 推奨（日常使用）
cd ~/.claude/plugins/marketplaces/plugins-weave/EpisodicRAG/scripts

# 開発時のみ（パスは環境依存）
cd <your-dev-folder>/plugins-weave/EpisodicRAG/scripts
```

**注意**: 開発用パスで実行すると、設定ファイルの参照先が異なりエラーになる場合があります。

### 2. 出力の保存方法

DigestAnalyzerの出力は長文JSON（4000文字以上）のため、
**一時ファイル経由で渡すこと**を強く推奨します。

```bash
# 1. Writeツールで一時ファイルに書き込み
# パス例: {digests_path}/temp_individual_digests.json

# 2. スクリプトにファイルパスを渡す
python -m interfaces.save_provisional_digest weekly {digests_path}/temp_individual_digests.json --append

# 3. 一時ファイルを削除
```

**注意**:
- stdinパイプ（`echo '...' | python ...`）はシェルのコマンドライン長制限で切断されるため使用しないでください
- 保存後、必ずProvisionalファイルの内容を確認し、入力データと一致しているか検証してください

### 3. UIメッセージ出力

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

## パターン1: /digest（新Loop検出）

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items for Pattern 1:
1. パス情報・新規Loop確認 - digest_entry.pyを実行
2. SGD読み込み - ShadowGrandDigest.txtを読み込む
3. source_files追加 - 新規Loopファイル名を追加
4. DigestAnalyzer起動 - 各Loopファイルの分析を並列起動
5. 分析結果受信 - long/short分析結果を受け取る
6. Provisional保存 - 分析結果を一時ファイル経由でアペンド
7. SGD統合更新 - long結果で5要素を更新
8. 処理完了記録 - update_digest_timesを実行
9. 次アクション提示 - threshold値を参照
10. Git Commit & Push - 変更をコミットしてプッシュ
11. Auto-dream: メモリ棚卸し - auto_dream_scan.pyを実行
```

**各ステップの概要**:

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | パス情報・新規Loop確認 | `python -m interfaces.digest_entry` |
| 2 | SGD読み込み | `essences_path`のShadowGrandDigest.txtを読み込む |
| 3 | source_files追加 | SGDの`weekly.overall_digest.source_files`に新規Loopファイル名を追加 |
| 4 | DigestAnalyzer起動 | Step 3のLoopファイル別に`Task(DigestAnalyzer)`を並列起動 |
| 5 | 分析結果受信 | 各DigestAnalyzerからlong/short分析結果を受け取る |
| 6 | Provisional保存 | 分析結果を一時ファイル経由でProvisionalにアペンド（`save_provisional_digest`） |
| 7 | SGD統合更新 | long結果を統合しSGDの5要素を更新（last_updated, digest_type, keywords, abstract, impression） |
| 8 | 処理完了記録 | `python -m interfaces.update_digest_times loop <最終番号>` |
| 9 | 次アクション提示 | digest_entry.py出力とthreshold値を参照 |
| 10 | Git Commit & Push | `{base_dir}`リポジトリへcommit & push |
| 11 | Auto-dream: メモリ棚卸し | `python -m interfaces.auto_dream_scan` |

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

#### Step 2: SGD読み込み

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

**フォーマット規約**: 配列要素は1行ずつ記述する（インライン形式 `["a.txt", "b.txt"]` は避ける）

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

**使用ツール**: `Task(subagent_type="EpisodicRAG:DigestAnalyzer")`

**起動方法**: Step 3で追加した各Loopファイルに対して**並列**でTaskを起動

**プロンプトに含める情報**:
- 対象ファイルのフルパス: `{loops_path}/L00260_タイトル.txt`
- GrandDigest / ShadowGrandDigest の絶対パス（`{essences_path}` 配下。Step 1 の出力にある）
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
    "short": "1200文字の要約"
  },
  "impression": {
    "long": "800文字の所感",
    "short": "400文字の要約"
  }
}
```

---

#### Step 6: Provisional保存

**実行ディレクトリ**: `{plugin_root}/scripts`

**手順**:

1. **Writeツールで一時ファイルに書き込み**

   パス: `{digests_path}/temp_individual_digests.json`

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

2. **スクリプト実行**

   ```bash
   python -m interfaces.save_provisional_digest weekly {digests_path}/temp_individual_digests.json --append
   ```

3. **一時ファイル削除**

   ```bash
   rm {digests_path}/temp_individual_digests.json
   ```

**注意**:
- abstract/impressionは`{long, short}`形式が必須
- stdinパイプはシェル制限で切断されるため使用しないこと
- 一時ファイルパスは必ず`{digests_path}/`を付けた絶対パスで指定すること

---

#### Step 7: SGD統合更新

**実行ディレクトリ**: `{plugin_root}/scripts`

**更新対象フィールド**（`weekly.overall_digest`内）:
- `digest_type`: 全source_filesを統合したテーマ
- `keywords`: 統合キーワード5個
- `abstract`: 統合分析（long版を使用）
- `impression`: 統合所感（long版を使用）

`timestamp` と `metadata.last_updated` はスクリプトが自動更新する。
`source_files` には触れない。

**手順**:

1. **Writeツールで一時ファイルに統合結果を書き込み**

   パス: `{digests_path}/temp_overall_digest.json`

   ```json
   {
     "digest_type": "統合テーマ",
     "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
     "abstract": "統合分析（long版）",
     "impression": "統合所感（long版）"
   }
   ```

2. **スクリプト実行**

   ```bash
   python -m interfaces.update_shadow_overall weekly {digests_path}/temp_overall_digest.json
   ```

3. **一時ファイル削除**

   ```bash
   rm {digests_path}/temp_overall_digest.json
   ```

**注意**:
- SGDの直接Edit（exact-match置換）は長文日本語で事故りやすいため使用しないこと
- abstract/impression は長文のためコマンドライン引数でなく必ずファイル経由で渡すこと

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

**確認項目**（Step 1出力を参照）:
- `weekly_source_count`: 現在のsource_files数
- `weekly_threshold`: 確定に必要な数（通常5）

**ユーザーへの案内例**:
```
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

**判定ロジック**:
- source_count < threshold → 「あと N 個のLoopが必要」
- source_count >= threshold → 「`/digest weekly`で確定可能」

---

#### Step 10: Git Commit & Push

**対象リポジトリ**: `{base_dir}`のgitリポジトリ

**手順**:

1. **変更確認**

   ```bash
   cd {base_dir} && git status --short
   ```

2. **変更がある場合のみ Stage & Commit**

   ```bash
   cd {base_dir} && git add Identities/GrandDigest.txt Identities/ShadowGrandDigest.txt Identities/IntentionPad.md && git commit -m "digest: {処理したLoop一覧} processed"
   ```

   **コミットメッセージ例**: `digest: L00386, L00387 processed`

3. **Push**

   ```bash
   cd {base_dir} && git push
   ```

**注意**:
- `git status`で変更がない場合はスキップ
- Pushエラー時はユーザーに報告し、手動対応を促す

---

#### Step 11: Auto-dream: メモリ棚卸し

**設計方針**:
auto_dream_scan は「メモリの所在通知」のみを担う。各メモリの本文は出力に含まれない（軽量化）。
Claudeは MEMORY.md と各 frontmatter.description で関連性を判定し、
**関連メモリだけを Read ツールで個別取得して** digest内容と突合する。

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.auto_dream_scan
```

**判定**:
- `status: "no_memory"` → スキップ（メモリ未使用環境）
- `status: "error"` → 警告表示のみ、digestは成功扱い
- `status: "ok"` → 以下のメモリ棚卸しを実行

**棚卸し手順**:

1. **スキャン結果を確認**

   出力構造:
   ```json
   {
     "memory_dir": "/path/to/memory",
     "memory_index": {"path": "...", "sections": {"User": ["user_profile.md"], ...}},
     "memory_files": [
       {"filename": "user_profile.md", "path": "...", "frontmatter": {"name": "...", "description": "...", "type": "user"}},
       ...
     ]
   }
   ```

   各 `memory_files[*].frontmatter.description` と `memory_index.sections` の one-liner で
   今回の digest 内容との関連性を判定する。

2. **関連メモリを個別Read**

   関連と判定したメモリファイルのみ、`memory_files[*].path` を Read ツールで取得し、
   ShadowGrandDigestの内容と突合：
   - **stale**: 記載内容が古い（イベント日時が過去、プロジェクト状況が変化等）
   - **current**: 最新の情報を反映済み
   - **enrichable**: digest内容から追記すべき新しい知見がある

   **注意**: 一見無関係でも `Bluesky→cloud routine` のような構造的整合性のズレがある場合は、
   one-liner だけで判断せず迷ったら Read で確認すること。

3. **staleまたはenrichableなファイルを更新**

   Editツールで該当ファイルの本文部分を更新
   - frontmatter（`---`で囲まれた部分）は変更しない
   - body部分のみ更新

   **更新時の運用ガイドライン**:
   - 既存エントリの粒度・長さに揃える（feedback_text_bias.md や project_*.md 等のパターンを踏襲）
   - 簡潔な追記を優先し、関連していてもスコープ外の内容は持ち込まない
   - 迷ったら更新を保留し、ユーザーに確認してから進める

4. **MEMORY.md更新（必要な場合）**

   新しいメモリファイルを追加した場合、MEMORY.mdのインデックスも更新
   （**MEMORY.md の one-liner 品質が次回の関連性判定の精度を決める**ため、
   description と一行hookは正確に維持する）

**注意**:
- Step 11はdigest処理の成否に影響しない（失敗してもdigest自体は完了）
- メモリファイルの更新はClaude Codeシステムパス上のファイル（gitコミット対象外）
- auto-memoryが無効な環境では自動スキップ
- メモリ件数が50件を超えてくる場合、機械的全件カバー方式（last_synced_loop stamp 等）への
  切り替えを再検討する

---

## パターン2: /digest \<type\>（階層確定）

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items for Pattern 2:
1. パス情報・Digest対象確認 - digest_entry.pyを実行
2. Digest要否判断 - threshold値未満ならアラート後、続行/中断を確認
3. 再分析要否判断 - digest_readiness.pyでSGD/Provisional完備を確認
4. DigestAnalyzer起動 - 各Digest対象ファイルの分析を並列起動
5. 分析結果受信 - long/short分析結果を受け取る
6. SGDとProvisional更新 - 分析結果をアペンド
7. Digest名確定 - ユーザーにタイトルを提案して承認を取得
8. Digestカスケード - finalize_from_shadow.pyを実行
8.5. 次階層への統合 - 次階層SGDのabstract/impressionを更新（centurial以外）
9. 処理完了提示 - GrandDigestと次階層のDigest要否を確認
10. Git Commit & Push - 変更をコミットしてプッシュ
11. Auto-dream: メモリ棚卸し - auto_dream_scan.pyを実行
```

**各ステップの概要**:

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | パス情報・Digest対象確認 | `python -m interfaces.digest_entry <level>` |
| 2 | Digest要否判断 | source_count < threshold ならアラート、続行/中断を確認 |
| 3 | 再分析要否判断 | `python -m interfaces.digest_readiness <level>` |
| 4 | DigestAnalyzer起動 | Task(DigestAnalyzer) 並列起動（Step 3で必要と判定された場合） |
| 5 | 分析結果受信 | 各DigestAnalyzerからlong/short分析結果を受け取る |
| 6 | SGDとProvisional更新 | SGDの5要素更新 + save_provisional_digest実行 |
| 7 | Digest名確定 | Claudeが提案、ユーザー承認 |
| 8 | Digestカスケード | `python -m interfaces.finalize_from_shadow <level> "タイトル"` |
| 8.5 | 次階層への統合 | Task(DigestAnalyzer)並列 + 次階層SGD更新（centurial以外） |
| 9 | 処理完了提示 | GrandDigest確認 + 次階層のDigest要否を案内 |
| 10 | Git Commit & Push | `{base_dir}`リポジトリへcommit & push |
| 11 | Auto-dream: メモリ棚卸し | `python -m interfaces.auto_dream_scan` |

### 各ステップの詳細

#### Step 1: パス情報・Digest対象確認

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.digest_entry <level>
```

**例**: Monthly確定の場合
```bash
python -m interfaces.digest_entry monthly
```

**出力から確認する項目**:
- `pattern`: 2であることを確認
- `shadow_state.source_files`: 確定対象のファイルリスト
- `shadow_state.source_count`: 確定対象ファイル数

**出力例（Pattern 2: monthly）**:
```json
{
  "status": "ok",
  "pattern": 2,
  "level": "monthly",
  "plugin_root": "/path/to/EpisodicRAG",
  "digests_path": "/path/to/Digests",
  "essences_path": "/path/to/Identities",
  "shadow_state": {
    "source_files": ["W0050_xxx.txt", "W0051_xxx.txt", ...],
    "source_count": 4,
    "placeholder_fields": [],
    "analyzed": true
  },
  "weekly_source_count": 3,
  "weekly_threshold": 5,
  "message": "monthly 確定準備: source_files=4個"
}
```

---

#### Step 2: Digest要否判断

**目的**: threshold値未満の場合にユーザーへアラートし、続行/中断を確認

**判定ロジック**:
- `shadow_state.source_count >= level_threshold` → 正常、Step 3へ
- `shadow_state.source_count < level_threshold` → アラート表示後、ユーザーに確認

**アラート時の対話例**:
```
⚠️ threshold未達のため通常は確定不可です。
  現在: 3ファイル / 必要: 4ファイル

このまま続行しますか？
  [y] 続行（強制確定）
  [n] 中断
```

**注意**: ユーザーが「中断」を選択した場合、処理を終了する

---

#### Step 3: 再分析要否判断

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.digest_readiness <level>
```

**出力例（確定可能）**:
```json
{
  "status": "ok",
  "level": "monthly",
  "source_count": 5,
  "level_threshold": 5,
  "threshold_met": true,
  "sgd_ready": true,
  "provisional_ready": true,
  "can_finalize": true,
  "blockers": [],
  "message": "Digest確定可能"
}
```

**出力例（再分析必要）**:
```json
{
  "status": "ok",
  "level": "monthly",
  "source_count": 4,
  "level_threshold": 5,
  "threshold_met": false,
  "sgd_ready": false,
  "provisional_ready": false,
  "can_finalize": false,
  "blockers": [
    "threshold未達: 4/5 (あと1ファイル必要)",
    "SGD未完備: PLACEHOLDERあり (abstract, impression)",
    "Provisional未完備: W0051_xxx.txt が不足"
  ],
  "message": "Digest確定不可: 3件の未達条件あり"
}
```

**判定**:
- `can_finalize: true` → Step 4-5をスキップし、Step 6へ
- `can_finalize: false` → Step 4-5を実行して不足を補完

---

#### Step 4: DigestAnalyzer起動

**前提条件**: Step 3で`can_finalize: false`の場合のみ実行

**使用ツール**: `Task(subagent_type="EpisodicRAG:DigestAnalyzer")`

**起動方法**: shadow_state.source_filesの各ファイルに対して**並列**でTaskを起動

**ファイルパスの構築**:
- Weekly確定時: `{loops_path}/{source_file}`（Loopファイル）
- Monthly以上: `{digests_path}/1_Weekly/{source_file}`（Digestファイル）

**プロンプト例**:
```python
Task(
    subagent_type="EpisodicRAG:DigestAnalyzer",
    description=f"Analyze {source_file} for Weekly digest",
    prompt=f"""
分析対象ファイル: {file_path}
GrandDigest: {essences_path}/GrandDigest.txt
ShadowGrandDigest: {essences_path}/ShadowGrandDigest.txt

このファイルを深層分析し、以下の形式でJSON出力してください：
{{
  "digest_type": "...",
  "keywords": [...],
  "abstract": {{"long": "...", "short": "..."}},
  "impression": {{"long": "...", "short": "..."}}
}}
"""
)
```

**出力の使い分け**:
- **long版**: 現階層のoverall_digest用（ShadowGrandDigest更新）
- **short版**: 次階層のindividual_digests用（Provisional保存）

---

#### Step 5: 分析結果受信

DigestAnalyzerからJSON形式で結果を受け取る。

**期待する出力形式**:
```json
{
  "source_file": "W0050_タイトル.txt",
  "digest_type": "テーマ（10-20文字）",
  "keywords": ["キーワード1", "キーワード2", "..."],
  "abstract": {
    "long": "2400文字の詳細分析",
    "short": "1200文字の要約"
  },
  "impression": {
    "long": "800文字の所感",
    "short": "400文字の要約"
  }
}
```

---

#### Step 6: SGDとProvisional更新

**前提条件**: Step 4-5で分析結果を取得した場合のみ実行

**実行ディレクトリ**: `{plugin_root}/scripts`

**操作1**: ShadowGrandDigestの5要素を更新

`<level>.overall_digest` の4要素（digest_type / keywords / abstract / impression）を
一時ファイル経由でスクリプト更新する。`timestamp` と `metadata.last_updated` は自動更新、
`source_files` には触れない。

1. **Writeツールで一時ファイルに統合結果を書き込み**

   パス: `{digests_path}/temp_overall_digest.json`

   ```json
   {
     "digest_type": "統合テーマ",
     "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
     "abstract": "統合分析（long版）",
     "impression": "統合所感（long版）"
   }
   ```

2. **スクリプト実行**

   ```bash
   python -m interfaces.update_shadow_overall <level> {digests_path}/temp_overall_digest.json
   ```

3. **一時ファイル削除**

   ```bash
   rm {digests_path}/temp_overall_digest.json
   ```

**注意**: SGDの直接Edit（exact-match置換）は長文日本語で事故りやすいため使用しないこと

**操作2**: Provisionalに分析結果を保存

**手順**:

1. **Writeツールで一時ファイルに書き込み**

   パス: `{digests_path}/temp_individual_digests.json`

   ```json
   {
     "individual_digests": [
       {
         "source_file": "M0012_タイトル.txt",
         "digest_type": "...",
         "keywords": ["..."],
         "abstract": {"long": "...", "short": "..."},
         "impression": {"long": "...", "short": "..."}
       }
     ]
   }
   ```

2. **スクリプト実行**

   **注意**: `<next_level>`は現在レベルの**次**（weekly→monthly, monthly→quarterly）

   ```bash
   python -m interfaces.save_provisional_digest <next_level> {digests_path}/temp_individual_digests.json --append
   ```

   **例**: Monthly確定時（次階層はquarterly）
   ```bash
   python -m interfaces.save_provisional_digest quarterly {digests_path}/temp_individual_digests.json --append
   ```

3. **一時ファイル削除**

   ```bash
   rm {digests_path}/temp_individual_digests.json
   ```

---

#### Step 7: Digest名確定

**操作**: Claudeが分析結果に基づきタイトルを提案し、ユーザー承認を取得

**提案形式**: タイトルのみ（プレフィックス・番号は不要）
- ✅ 正しい例: `"理論的深化・実装加速・社会発信"`
- ❌ 誤った例: `"M0012_理論的深化..."` （プレフィックス不要）

**提案時のポイント**:
- 分析したsource_filesの共通テーマを抽出
- 10-30文字程度で簡潔に

---

#### Step 8: Digestカスケード

**実行ディレクトリ**: `{plugin_root}/scripts`

**コマンド**:
```bash
python -m interfaces.finalize_from_shadow <level> "承認されたタイトル"
```

**例**:
```bash
python -m interfaces.finalize_from_shadow monthly "理論的深化・実装加速・社会発信"
```

**実行内容**:
- RegularDigest作成（`Digests/2_Monthly/M0012_タイトル.txt`）
- ProvisionalDigestをRegularDigestにマージ
- GrandDigest更新
- 次レベルのShadowへカスケード（source_filesに追加）
- last_digest_times.json更新
- Provisionalファイル削除

---

#### Step 8.5: 次階層への統合（centurial以外）

**前提**: finalize_from_shadow.pyが自動で次階層Provisionalにindividual_digestを追加済み

**注意**: centurialは最上位のため本ステップは不要（スキップ）

**Claude実行内容**:
1. 次階層のsource_files全てをDigestAnalyzerで並列分析
2. 分析結果で次階層SGDのabstract/impressionを更新

**操作**:

1. **次階層のShadow source_files確認**

   ShadowGrandDigest.txtの次階層セクションを読み込み、
   source_filesに新しく追加されたファイルを確認

2. **DigestAnalyzer並列起動**

   ```python
   Task(
       subagent_type="EpisodicRAG:DigestAnalyzer",
       description=f"Analyze {source_file} for next level digest",
       prompt=f"""
   分析対象ファイル: {file_path}
   GrandDigest: {essences_path}/GrandDigest.txt
   ShadowGrandDigest: {essences_path}/ShadowGrandDigest.txt

   このファイルを深層分析し、以下の形式でJSON出力してください：
   {{
     "digest_type": "...",
     "keywords": [...],
     "abstract": {{"long": "...", "short": "..."}},
     "impression": {{"long": "...", "short": "..."}}
   }}
   """
   )
   ```

3. **次階層SGD更新**

   `<next_level>.overall_digest` の4要素（digest_type / keywords / abstract /
   impression、いずれも統合したlong版）を一時ファイル経由でスクリプト更新する。
   `timestamp` と `metadata.last_updated` は自動更新、`source_files` には触れない。

   ```bash
   # 1. Writeツールで {digests_path}/temp_overall_digest.json に統合結果を書き込み
   #    形式: {"digest_type": "...", "keywords": [...], "abstract": "...", "impression": "..."}
   # 2. スクリプト実行
   python -m interfaces.update_shadow_overall <next_level> {digests_path}/temp_overall_digest.json
   # 3. 一時ファイル削除
   rm {digests_path}/temp_overall_digest.json
   ```

   **注意**: SGDの直接Edit（exact-match置換）は長文日本語で事故りやすいため使用しないこと

**自動処理済み（プログラム）**:
- 次階層Shadowのsource_filesに確定ファイル名を追加 ✓
- 次階層Provisionalにindividual_digestエントリを追加 ✓

---

#### Step 9: 処理完了提示

**確認項目**:
- finalize出力の`status`が`"ok"`であること
- 作成されたファイルパス
- GrandDigest更新の成功

**次階層のDigest要否確認**:
```bash
python -m interfaces.digest_entry <next_level>
```

**ユーザーへの案内例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Monthly Digest確定完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

作成されたファイル:
  - Digests/2_Monthly/M0012_理論的深化.txt

GrandDigest.txt を更新しました。
次階層 (quarterly) のShadowを更新しました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 次のアクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quarterly生成まであと2個のMonthlyが必要です。
または `/digest quarterly` で確定可能です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

#### Step 10: Git Commit & Push

**対象リポジトリ**: `{base_dir}`のgitリポジトリ

**手順**:

1. **変更確認**

   ```bash
   cd {base_dir} && git status --short
   ```

2. **変更がある場合のみ Stage & Commit**

   ```bash
   cd {base_dir} && git add Identities/GrandDigest.txt Identities/ShadowGrandDigest.txt Identities/IntentionPad.md && git commit -m "digest: {level} finalized - {承認されたタイトル}"
   ```

   **コミットメッセージ例**: `digest: weekly finalized - 知性射程理論と冬支度`

3. **Push**

   ```bash
   cd {base_dir} && git push
   ```

**注意**:
- `git status`で変更がない場合はスキップ
- Pushエラー時はユーザーに報告し、手動対応を促す

---

#### Step 11: Auto-dream: メモリ棚卸し

> パターン1のStep 11と同一の手順です。[パターン1のStep 11](#step-11-auto-dream-メモリ棚卸し) を参照。

---

## セットアップ・管理用スキル

初回セットアップ時やトラブル時に使用するスキル：

| スキル | 用途 | 詳細 |
|--------|------|------|
| `@digest-setup` | 初期セットアップ | [digest-setup SKILL.md](../skills/digest-setup/SKILL.md) |
| `@digest-auto` | 最適階層の推奨 | [digest-auto SKILL.md](../skills/digest-auto/SKILL.md) |
| `@digest-config` | 設定変更 | [digest-config SKILL.md](../skills/digest-config/SKILL.md) |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
