[EpisodicRAG](../README.md) > [Commands](README.md) > digest

---
name: digest
description: EpisodicRAG階層的ダイジェスト生成（8層100年）
---

# /digest - EpisodicRAG階層的ダイジェスト生成

> 📖 用語・共通概念は [用語集](../README.md) を参照

## 目次

- [基本的な使い方](#基本的な使い方)
- [実行時のタスク管理](#実行時のタスク管理)
- [実行フロー](#実行フロー)
  - [パターン1: /digest (引数なし)](#パターン1-digest-引数なし---新loop検出)
  - [パターン2: /digest type](#パターン2-digest-type-階層確定)
- [セットアップ・管理用スキル](#セットアップ管理用スキル初回セットアップ時またはトラブル時に使用)
- [詳細仕様](#詳細仕様)
- [実装詳細（開発者向け）](#実装詳細開発者向け)

## 基本的な使い方

### 新しいLoopファイルの検出

```bash
/digest
```

**実行内容**:
1. 新しいLoopファイルを検出
2. ShadowGrandDigest.weeklyにプレースホルダー追加
3. DigestAnalyzerで分析（long/short両方生成）
4. Provisional保存（Weekly用individual_digests自動生成）
5. ShadowGrandDigest.txt更新（long版）
6. 次のアクション提示

---

### 階層的ダイジェストの確定

```bash
/digest <type>
```

**利用可能なtype**:
- `weekly` `monthly` `quarterly` `annual`
- `triennial` `decadal` `multi_decadal` `centurial`

**実行内容**:
1. ShadowGrandDigest.<type> の内容確認
2. DigestAnalyzerでoverall分析（long版）
3. Provisional保存（次階層用individual、short版）
4. タイトル提案とユーザー承認
5. RegularDigest作成（Provisionalマージ）
6. GrandDigest更新、次階層Shadowカスケード
7. 次階層Provisional作成（short版生成）
8. 次階層Shadow統合更新（overall_digest生成）
9. 完了確認

---

## 実行時のタスク管理

**重要**: `/digest`コマンド実行時、**必ず**TodoWriteツールを使用してタスクリストを作成してから処理を開始すること。

### パターン1: `/digest` (引数なし) のタスクリスト

```python
TodoWrite({
  "todos": [
    {"content": "generate_digest_auto.sh実行", "status": "pending", "activeForm": "generate_digest_auto.sh実行中"},
    {"content": "ShadowGrandDigest更新確認", "status": "pending", "activeForm": "ShadowGrandDigest更新確認中"},
    {"content": "DigestAnalyzer並列起動", "status": "pending", "activeForm": "DigestAnalyzer並列起動中"},
    {"content": "Provisional保存実行", "status": "pending", "activeForm": "Provisional保存実行中"},
    {"content": "Shadow統合更新", "status": "pending", "activeForm": "Shadow統合更新中"},
    {"content": "次アクション提示", "status": "pending", "activeForm": "次アクション提示中"}
  ]
})
```

### パターン2: `/digest <type>` (階層確定) のタスクリスト

```python
TodoWrite({
  "todos": [
    {"content": "generate_digest_auto.sh <type>実行", "status": "pending", "activeForm": "generate_digest_auto.sh <type>実行中"},
    {"content": "ShadowGrandDigest状態確認", "status": "pending", "activeForm": "ShadowGrandDigest状態確認中"},
    {"content": "DigestAnalyzer並列起動（必要な場合）", "status": "pending", "activeForm": "DigestAnalyzer並列起動中"},
    {"content": "Provisional保存実行（必要な場合）", "status": "pending", "activeForm": "Provisional保存実行中"},
    {"content": "タイトル提案", "status": "pending", "activeForm": "タイトル提案中"},
    {"content": "finalize_from_shadow.py実行", "status": "pending", "activeForm": "finalize_from_shadow.py実行中"},
    {"content": "次階層Provisional作成", "status": "pending", "activeForm": "次階層Provisional作成中"},
    {"content": "次階層Shadow統合更新", "status": "pending", "activeForm": "次階層Shadow統合更新中"},
    {"content": "完了確認", "status": "pending", "activeForm": "完了確認中"}
  ]
})
```

**ルール**:
- 全てのタスクは等しく重要
- 各タスク完了時、必ずステータスを`completed`に更新
- タスクをスキップしないこと

---

## 実行フロー

### パターン1: `/digest` (引数なし - 新Loop検出)

このコマンドは以下の処理を自動的に実行します：

1. **generate_digest_auto.sh 実行**
```bash
cd scripts
bash generate_digest_auto.sh
```

2. **ShadowGrandDigest更新確認**
   - スクリプト出力からプレースホルダー追加を確認
   - 新しく検出されたLoopファイル数を表示

3. **DigestAnalyzer並列起動（まだらボケ回避）**
   - 各source_fileに対してDigestAnalyzerを**並列起動**
   - ShadowGrandDigest.weeklyに含まれる各Loopファイルを個別に深層分析
   - 4つのLoopであれば4つの個別分析結果を取得
   - DigestAnalyzerはlong/short両方を生成
   - ShadowGrandDigest.weeklyのプレースホルダーをlong版で置換:
     * `digest_type`: 本質的テーマ（10-20文字）
     * `keywords`: 5個のキーワード（各20-50文字）
     * `abstract`: 2400文字の全体統合分析（long版）
     * `impression`: 800文字の所感・展望（long版）

4. **DigestAnalyzer並列起動**
   - 各source_fileに対してDigestAnalyzerを**並列起動**:
     ```python
     # 各source_fileに対してDigestAnalyzerを並列起動
     analyzer_results = []
     for source_file in shadow_digest["weekly"]["overall_digest"]["source_files"]:
         result = Task(
             subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
             prompt=f"分析対象ファイル: {source_file}"
         )
         analyzer_results.append(result)
     # 結果: 4つの個別分析結果が得られる
     ```

5. **Provisional保存（individual_digests自動生成）**
   - 各DigestAnalyzerのshort版を使用してindividual_digests生成:
     ```python
     # 各分析結果からindividual_digestsを生成
     individual_digests = []
     for source_file, analysis in zip(source_files, analyzer_results):
         individual_digests.append({
             "filename": source_file,
             "timestamp": datetime.now().isoformat(),
             "digest_type": analysis["digest_type"],
             "keywords": analysis["keywords"],
             "abstract": analysis["abstract"]["short"],  # 1200文字版（個別分析）
             "impression": analysis["impression"]["short"]  # 400文字版（個別分析）
         })
     ```
   - save_provisional_digest.py実行:
     ```bash
     cd scripts
     python3 save_provisional_digest.py weekly '<individual_digests JSON>' --append
     ```
   - **--append**: 既存Provisionalファイルに追加（複数回/digestでLoopを追加する場合）
   - W{次番号}_Individual.txtファイル作成（例: W0001_Individual.txt）
   - 格納先: Provisional/1_Weekly/
   - 次のWeekly確定時（/digest weekly）に自動的にマージ

5. **ShadowGrandDigest.txt更新**
   - **統合ソース**:
     - current long: 既存のShadowGrandDigest.weekly.overall_digest
     - + new short: 新規individual_digests（手順4で保存）
   - メインエージェントが上記を統合してoverall_digest更新
   - Edit toolでShadowGrandDigest.weekly.overall_digestを更新

6. **次のアクション提示**
   - 現在のLoop数を確認
   - Weekly生成に必要な数（デフォルト5）と比較
   - 不足している場合: "あとN個のLoopが必要です"
   - 十分な場合: "`/digest weekly` で確定できます"

---

### パターン2: `/digest <type>` (階層確定)

このコマンドは以下の処理を自動的に実行します：

1. **generate_digest_auto.sh 実行**
```bash
cd scripts
bash generate_digest_auto.sh {{type}}
```

2. **ShadowGrandDigest確認と状態判定**
   - スクリプト出力からShadowGrandDigest.{{type}}の内容を確認
   - source_filesリストを取得
   - **overall_digestの状態を判定**:
     * abstract または impression に "<!-- PLACEHOLDER -->" が含まれる → **未分析状態**
     * プレースホルダーなし → **分析済み状態**

   【状態に応じた処理フロー】:

   **未分析状態の場合** → 手順3（DigestAnalyzer並列実行）を実行
   - 各source_fileに対してDigestAnalyzerを並列起動
   - long/short両方を生成
   - Provisional作成とタイトル提案を実施

   **分析済み状態の場合** → 手順3をスキップし、手順5（タイトル提案）へ直接進む
   - DigestAnalyzer起動は不要（既に完了済み）
   - Provisionalも作成済み
   - タイトル提案と finalize のみ実行

3. **DigestAnalyzer並列起動（overall分析 + 次階層用individual作成）**
   - 各source_fileに対してDigestAnalyzerを**並列起動**
   - ShadowGrandDigest.{{type}}に含まれる各ファイルを個別に深層分析
   - 5つのWeekly Digestであれば5つの個別分析結果を取得
   - DigestAnalyzerは各ファイルごとにlong/short両方を生成:
     ```python
     # 各source_fileに対してDigestAnalyzerを並列起動
     analyzer_results = []
     for source_file in shadow_digest[type]["overall_digest"]["source_files"]:
         result = Task(
             subagent_type="DigestAnalyzer",
             prompt=f"分析対象ファイル: {source_file}"
         )
         analyzer_results.append(result)
     ```
     * `digest_type`: ダイジェストタイプ（共通）
     * `keywords`: 5個のキーワード（共通）
     * `abstract.long`: 2400文字の統合分析（現階層overall用）
     * `abstract.short`: 1200文字の個別分析（次階層individual用）
     * `impression.long`: 800文字の所感・展望（現階層overall用）
     * `impression.short`: 400文字の所感・考察（次階層individual用）

   **データフロー**:
   - **現階層overall_digest**: DigestAnalyzerのlong版を使用（ShadowGrandDigest更新）
   - **次階層individual_digests**: DigestAnalyzerのshort版でProvisional作成（手順4）
   - **現階層individual_digests**: 既存Provisionalをfinalize時にマージ（手順6）

4. **Provisional保存（次階層用individual_digests自動生成）**
   - DigestAnalyzerのshort版を使用してindividual_digests生成:
     ```python
     individual_digests = []
     for source_file, analysis in zip(source_files, analyzer_results):
         individual_digests.append({
             "filename": source_file,
             "timestamp": datetime.now().isoformat(),
             "digest_type": analysis["digest_type"],
             "keywords": analysis["keywords"],
             "abstract": analysis["abstract"]["short"],  # 1200文字版
             "impression": analysis["impression"]["short"]  # 400文字版
         })
     ```
   - save_provisional_digest.py実行:
     ```bash
     cd scripts
     python3 save_provisional_digest.py {{next_level}} '<individual_digests JSON>'
     ```
   - **注**: 次階層用は新規作成なので --append なし
   - 次階層のProvisionalファイル作成:
     - weekly確定時 → M{次番号}_Individual.txt（例: M001_Individual.txt）→ Provisional/2_Monthly/
     - monthly確定時 → Q{次番号}_Individual.txt（例: Q001_Individual.txt）→ Provisional/3_Quarterly/
     - annual確定時 → T{次番号}_Individual.txt（例: T01_Individual.txt）→ Provisional/5_Triennial/
     - 以下、階層的に継続

5. **タイトル提案とoverall_digest準備**
   - **overall_digestソース**: ShadowGrandDigest.{{type}}.overall_digest
   - **処理**: そのままRegularDigest.{{type}}.overall_digestにコピー
   - メインエージェントの統合作業は不要（既にShadowで完成）
   - 分析結果に基づいてタイトル提案
   - ユーザー承認取得
   - **注意**: タイトルのみ提案（プレフィックスと番号は不要）
   - [OK] 正しい例: "理論的深化・実装加速・社会発信"
   - [NG] 誤った例: "W0043_理論的深化..." (プレフィックス不要)

6. **finalize_from_shadow.py 実行**
```bash
cd scripts
python3 finalize_from_shadow.py {{type}} "承認されたタイトル"
```
   このコマンドが実行する処理:
   - RegularDigest作成（overall_digestのみ）
   - 現階層のProvisionalDigestをRegularDigestにマージ（手順4で作成済み）
   - GrandDigest更新
   - 次レベルのShadowへカスケード
   - last_digest_times.json更新
   - Provisionalファイル削除（マージ後クリーンアップ）

7. **次階層Provisional作成**
   - 次階層Shadowのsource_filesを確認（例：monthly → W0001, W0002）
   - DigestAnalyzerを並列起動して各ファイル全体のshort版を生成:
     * 各ファイルのoverall_digest.abstractを1200文字に圧縮
     * 各ファイルのoverall_digest.impressionを400文字に圧縮
   - individual_digests JSON作成:
     ```python
     individual_digests = []
     for source_file, analysis in zip(source_files, analyzer_results):
         individual_digests.append({
             "filename": source_file,
             "timestamp": datetime.now().isoformat(),
             "digest_type": analysis["digest_type"],
             "keywords": analysis["keywords"],
             "abstract": analysis["abstract"]["short"],  # 1200文字版
             "impression": analysis["impression"]["short"]  # 400文字版
         })
     ```
   - save_provisional_digest.py実行:
     ```bash
     cd scripts
     python3 save_provisional_digest.py <next_level> '<individual_digests JSON>'
     ```
   - 次階層Provisionalファイル作成:
     - weekly確定時 → M{次番号}_Individual.txt → Provisional/2_Monthly/
     - monthly確定時 → Q{次番号}_Individual.txt → Provisional/3_Quarterly/
     - 以下、階層的に継続

8. **次階層Shadow統合更新**
   - 次階層Shadowのsource_filesから各ファイルのoverall_digestを読み込む
     * 例: W0001のoverall_digest（long版：abstract 2400文字, impression 800文字）
     * 例: W0002のoverall_digest（long版：abstract 2400文字, impression 800文字）
   - メインエージェントが統合分析を実行:
     * digest_type: 複数ファイルの統合テーマ（10-20文字）
     * keywords: 5個の統合キーワード（各20-50文字）
     * abstract: 2400文字の統合分析（次階層overall用）
     * impression: 800文字の所感・展望（次階層overall用）
   - Edit toolでShadowGrandDigest.{next_level}.overall_digestを更新
   - 注意: DigestAnalyzerは使用しない（構造的統合が必要なため、メインエージェントが直接実行）

9. **完了確認**
   - 生成されたRegularDigestファイルパスを表示
   - GrandDigest.txtの更新内容を表示
   - 次の階層生成の可能性を確認

---

## セットアップ・管理用スキル

初回セットアップ時やトラブル時に使用するスキル：

| スキル | 用途 | 詳細 |
|--------|------|------|
| `@digest-setup` | 初期セットアップ | [digest-setup SKILL.md](../skills/digest-setup/SKILL.md) |
| `@digest-auto` | 最適階層の推奨 | [digest-auto SKILL.md](../skills/digest-auto/SKILL.md) |
| `@digest-config` | 設定変更 | [digest-config SKILL.md](../skills/digest-config/SKILL.md) |

---

## 詳細仕様

**完全な仕様とプロセスフロー**:
- `scripts/generate_digest_auto.sh`
- `agents/digest-analyzer.md`
- `.claude-plugin/config.json`

**要件**:
- Claude Opus 4.5（Task tool, Subagent機能）
- Python 3.x
- Bash（Git Bash / WSL）

---

## 実装詳細（開発者向け）

### コマンド実行時の内部処理

このコマンドファイルは、Claude自身が以下のツールを使って処理を実行します：

1. **Bash tool**: スクリプト実行
   ```python
   Bash(command="cd scripts && bash generate_digest_auto.sh")
   ```

2. **Task tool**: DigestAnalyzerエージェント起動
   > 📖 DigestAnalyzerの詳細な呼び出しパターンは [digest-analyzer.md](../agents/digest-analyzer.md) を参照

3. **Edit tool**: ShadowGrandDigest.txt更新
   ```python
   Edit(
       file_path="data/Essences/ShadowGrandDigest.txt",
       old_string='PLACEHOLDER...',
       new_string='{"digest": {...}}'
   )
   ```

4. **Read tool**: 結果確認
   ```python
   Read(file_path="data/Essences/GrandDigest.txt")
   ```

### 引数の取得

コマンドに引数が渡された場合、Claudeは文脈から引数を理解して処理します：
- `/digest` → 引数なし → 新Loop検出モード
- `/digest weekly` → type="weekly" → 階層確定モード

### エラーハンドリング

設定ファイルが存在しない場合:
```text
❌ 設定ファイルが見つかりません

初回セットアップを実行してください:
@digest-setup セットアップを実行
```

---

**このコマンドは、EpisodicRAGシステムの基本操作を提供します 🟢**

---
