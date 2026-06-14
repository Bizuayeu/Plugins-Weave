---
name: dream-defrag
description: auto-memory の引く dream（GC）。MEMORY.md の横断重複統合・上位層DRY・完了卒業・index lean 化
---

# /dream-defrag - 引く dream（auto-memory の GC）

Claude Code auto-memory（`MEMORY.md` + `memory/*.md`）を剪定するコマンドです。
`/digest` Step 11 の Auto-dream が「**足す dream**」（additive enrichment）なのに対し、
本コマンドは「**引く dream**」（global・reductive な GC）を担い、両者で記憶定着の二相を成します。

memory-dream の 4 フェーズのうち **③Dedup & Resolve と ④Prune & Index** のみを実行します
（①Mine・②Consolidate は Step 11 の責務）。

## 目次

- [用語説明](#用語説明)
- [重要な注意事項](#重要な注意事項)
- [基本的な使い方](#基本的な使い方)
- [実行フロー](#実行フロー)
- [4 スコープの判断手順](#4-スコープの判断手順)

---

## 用語説明

> 📖 用語・共通概念は [用語集](../GLOSSARY.md) を参照（**dream の二相**・**DEFRAG_THRESHOLD** を含む）

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

### 2. 安全要件（最重要）

> **auto-memory ファイルは git 非追跡です。** `/digest` が扱う GrandDigest 等と違い、
> revert できません。**剪定の前に必ず snapshot を作成すること。**

- snapshot 成功を確認するまで、ファイルの削除・統合に進まない
- 剪定は**非破壊フロー**で行う: **snapshot → 候補提示 → ユーザー裁可 → 適用**
- エントリの削除・統合を**黙って実行しない**。必ず候補表を提示し、承認を得てから適用する

### 3. 判断と決定論の分離

- **決定論（スクリプト）**: 件数集計（`scan`）・バックアップ（`snapshot`）・索引同期（`rebuild-index`）
- **判断（Claude）**: 何を重複・卒業・上位層DRY 違反と見て剪定するか
- スクリプトは剪定候補を自動生成しない。候補の検出と確定は Claude が行う

### 4. UIメッセージ出力

> **UIメッセージ出力時は必ずコードブロックで囲むこと！**
> VSCode拡張では単一改行が空白に変換されるため、対話型メッセージは三連バッククォートで囲む必要があります。

> 📖 共通の実装ガイドラインは [_implementation-notes.md](../skills/shared/_implementation-notes.md) を参照してください。

---

## 基本的な使い方

```ClaudeCLI
/dream-defrag
```

メモリ件数が `DEFRAG_THRESHOLD`（50）を超えたときに推奨されます。
auto-memory が無効な環境では自動的にスキップされます。

---

## 実行フロー

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items for /dream-defrag:
1. 件数診断 - dream_defrag scan を実行し threshold 超過を確認
2. 早期終了判定 - no_memory または閾値未満なら案内して終了
3. スナップショット作成 - dream_defrag snapshot（剪定適用より前の必須バックアップ）
4. メモリ読み込み・候補判断 - 関連 memory を Read し 4 スコープの剪定候補を判断
5. 候補提示・ユーザー裁可 - 候補表を提示し、適用可否の承認を得る
6. 剪定適用 - 承認された統合・削除を Edit / rm で適用（卒業は降格に限定）
7. 索引同期 - dream_defrag rebuild-index で MEMORY.md をディスク現存に同期
8. 完了サマリ - 件数の前後と snapshot パスを提示
```

### 各ステップの概要

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | 件数診断 | `python -m interfaces.dream_defrag scan` |
| 2 | 早期終了判定 | scan 出力の `status` / `over_threshold` を参照 |
| 3 | スナップショット作成 | `python -m interfaces.dream_defrag snapshot` |
| 4 | メモリ読み込み・候補判断 | scan 出力の所在から Read、Claude が剪定候補を判断 |
| 5 | 候補提示・ユーザー裁可 | 候補表を提示し承認を取得 |
| 6 | 剪定適用 | Edit（統合）/ Bash rm（削除）。卒業は index 降格に限定 |
| 7 | 索引同期 | `python -m interfaces.dream_defrag rebuild-index` |
| 8 | 完了サマリ | scan を再実行し件数の前後を提示 |

### 各ステップの詳細

#### Step 1: 件数診断

**実行ディレクトリ**: `{plugin_root}/scripts`

```bash
python -m interfaces.dream_defrag scan
```

**出力から確認する項目**:
- `status`: `ok` / `no_memory` / `error`
- `file_count`: memory ファイル数（MEMORY.md 自体は除く）
- `over_threshold`: `file_count > 50` なら `true`
- `memory_dir`: memory ディレクトリの絶対パス

---

#### Step 2: 早期終了判定

**判定ロジック**:
- `status == "no_memory"` → auto-memory 無効環境。スキップして終了
- `status == "error"` → エラー内容を提示して終了
- `over_threshold == false` → 閾値未満。剪定は任意（下記で続行確認）

**閾値未満時の対話例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ℹ️ メモリ件数は閾値未満です
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

現在: 42 件 / 閾値: 50 件

まだ剪定の必要はありません。それでも実行しますか？
  [y] 続行（任意剪定）
  [n] 終了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

#### Step 3: スナップショット作成（必須）

**実行ディレクトリ**: `{plugin_root}/scripts`

```bash
python -m interfaces.dream_defrag snapshot
```

**出力**:
- `snapshot_path`: 作成されたバックアップの絶対パス（走査対象 dir の外＝永続化 dir 配下）

> ⚠️ **このステップの成功を確認してから Step 6 の適用に進むこと。** snapshot が失敗した場合（`status != "ok"`）は剪定に進まず、ユーザーに報告する。

---

#### Step 4: メモリ読み込み・候補判断

Step 1 の `memory_dir` と `MEMORY.md` を起点に、関連 memory ファイルを Read し、
[4 スコープの判断手順](#4-スコープの判断手順)に従って剪定候補を判断する。

**判断の出力形**（候補1件）:
- `kind`: `dedup` / `upper_dry` / `graduate`
- `targets`: 対象ファイル名
- `reason`: なぜ剪定候補か

---

#### Step 5: 候補提示・ユーザー裁可

判断した候補を**表で提示**し、適用の可否を確認する。**承認なしに適用しない。**

**候補提示の例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧹 剪定候補（snapshot 済: <snapshot_path>）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[dedup] 統合
  - project_telegram_secretary.md + project_secretary_plugin_port.md
    → 1 件へ統合（重複する稼働状況の記述）

[upper_dry] 削除
  - feedback_git_push_bypass.md
    → WeaveSupplement が定義済みのルールの再掲

[graduate] 降格
  - project_private_consolidation.md（✅完了）
    → EpisodicRAG に記録済みを確認 → index から降格

適用してよいですか？
  [y] 適用   [n] 中断   [e] 個別に選ぶ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

#### Step 6: 剪定適用

承認された候補のみ適用する:
- **dedup**: 生き残りファイルを Edit で統合（他方の固有情報を吸収）→ 不要ファイルを `rm`
- **upper_dry**: 上位層が定めるルールの再掲を Edit で除去（エントリ全体が再掲なら `rm`）
- **graduate**: 完了プロジェクトを `rm`（**下記の卒業条件を満たす場合のみ**）

> **卒業（graduate）の境界**: dream-defrag は **MEMORY.md live index からの降格**までを担い、
> **EpisodicRAG（Loops/Digests）への実記録は行わない**（記憶層は不可侵）。
> 削除する完了プロジェクトの本体史が EpisodicRAG に**まだ無い**場合は、削除せずフラグし、
> 「先に `/digest` 系で記録してから卒業」を案内する。

---

#### Step 7: 索引同期

**実行ディレクトリ**: `{plugin_root}/scripts`

```bash
# まずプレビュー（書き込まない）
python -m interfaces.dream_defrag rebuild-index --preview

# 問題なければ適用
python -m interfaces.dream_defrag rebuild-index
```

`rebuild-index` は **ディスクから消えた memory ファイルのエントリ行を MEMORY.md から落とす**
決定論的同期です。生き残りエントリの one-liner 説明は verbatim 保持されます
（Step 6 で `rm` 済みのファイルが索引からも消える）。

---

#### Step 8: 完了サマリ

`scan` を再実行し、件数の前後・適用した剪定・snapshot パスを提示する。

**完了サマリの例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ dream-defrag 完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

件数: 57 → 49 件
  統合(dedup): 2 件 → 1 件
  削除(upper_dry): 1 件
  降格(graduate): 3 件

バックアップ: <snapshot_path>
（気に入らなければ snapshot から復元できます）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4 スコープの判断手順

剪定は次の 4 観点で判断する。**いずれも「何を剪定するか」は Claude の判断**であり、
スクリプトは候補を自動生成しない。

### ① 横断 dedup（エントリ間の重複統合）

- **見るもの**: scan 出力の `memory_files[*].frontmatter.description` と `MEMORY.md` の one-liner
- **判断**: 同一トピックを複数ファイルが重複して扱っていないか（例: 同一プロジェクトの複数エントリ）
- **適用**: 最も情報量の多いファイルへ Edit で統合し、他方の固有情報だけ吸収 → 重複ファイルを `rm`

### ② 上位層 DRY（上位ルールの再掲を削除）

- **見るもの**: memory の内容と、上位層（`WeaveSupplement.md` / `CLAUDE.md` 等）が既に定めるルール
- **判断**: 上位層が定義済みのルールを memory が再掲していないか（**上位が定めるルールを下位で再掲しない**）
- **適用**: 再掲部分を Edit で除去。エントリ全体が再掲なら `rm`
- **注意**: 上位層の参照元パスは環境依存。決め打ちせず、文脈から該当ファイルを Read で特定する

### ③ 完了卒業（graduate）

- **見るもの**: `project` 種別エントリのうち完了マーク（✅完了 等）のもの
- **判断**: その完了プロジェクトの本体史が EpisodicRAG（GrandDigest/Loops）に記録済みか
- **適用**:
  - 記録済み → `rm`（index からの降格。本体史は EpisodicRAG に残る）
  - 未記録 → **削除せずフラグ**し「先に `/digest` 系で記録」を案内（記憶層は不可侵）

### ④ index lean 化

- **見るもの**: `MEMORY.md` の冗長な節・完了済みで価値の無い記述
- **判断**: 索引が「思い出す助け」として lean か
- **適用**: Step 6 の削除後、`rebuild-index` で索引をディスク現存に同期（決定論）

---

## セットアップ・関連

| 対象 | 用途 | 詳細 |
|------|------|------|
| `/digest` Step 11 | 足す dream（additive enrichment） | [commands/digest.md](./digest.md) |
| `@digest-auto` | システム状態診断 | [digest-auto SKILL.md](../skills/digest-auto/SKILL.md) |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
