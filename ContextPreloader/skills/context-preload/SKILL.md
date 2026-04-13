---
name: context-preload
description: ContextPreloaderセットアップ・管理（対話的）
---

# ContextPreloader Management

SessionStart hookで任意のファイル・URLを事前文脈として読み込むシステムの管理スキル。

## 実行フロー

**このスキルが呼ばれたら、必ず最初にステータスチェックを実行すること。**

### Step 0: ステータスチェック（必須・最初に実行）

```bash
cd plugins-weave/ContextPreloader
python -m scripts status
```

出力例:
```json
{
  "ready": false,
  "config": {"ok": false, "path": "~/.claude/plugins/.contextpreloader/sources.json"},
  "hook": {"ok": false, "path": "~/.claude/hooks/context_preloader.py"},
  "settings": {"ok": false, "path": null},
  "profiles": [],
  "global_sources": 0
}
```

**判定ルール:**

| `ready` | 対応 |
|---------|------|
| `true` | → [管理フロー](#管理フロー)へ進む |
| `false` | → [対話型セットアップ](#対話型セットアップ)を開始 |

---

## 対話型セットアップ

`ready: false` の場合、不足しているコンポーネントを順に対話的に構築する。

**TodoWriteで以下のリストを作成し、該当するステップのみ実行すること**

### Step 1: config作成（`config.ok` が `false` の場合）

1. ユーザーに確認: 「セッション開始時に読み込みたいファイルやURLはありますか？」
2. AskUserQuestionで入力を受け付ける
3. configディレクトリ作成 + sources.json生成:

```bash
mkdir -p ~/.claude/plugins/.contextpreloader/profiles
```

ユーザーが指定したファイルをsourcesに追加:
```bash
python -m scripts add --path "/path/to/file" --label "Label"
```

ファイル指定がない場合は空のsources.jsonを配置（テンプレートをコピー）:
```bash
cp plugins-weave/ContextPreloader/.claude-plugin/sources.template.json ~/.claude/plugins/.contextpreloader/sources.json
```

### Step 1.5: mode設定（任意）

ソースファイルが大きい場合（合計10KB超）、reference modeを推奨する:
- `sources.json` の `settings.mode` を `"reference"` に変更
- 各ソースに `description`（説明文）と `priority`（`critical`/`high`/`normal`/`low`）を追加

### Step 2: プロファイル作成（任意）

1. ユーザーに確認: 「プロジェクト別に読み込むファイルを分けたいですか？（プロファイル機能）」
2. はい → プロファイル名を聞いて `profiles/{name}.json` を作成
3. いいえ → スキップ

### Step 3: hook配置（`hook.ok` が `false` の場合）

```bash
cp plugins-weave/ContextPreloader/hooks/context_preloader.py ~/.claude/hooks/
```

### Step 4: settings.json更新（`settings.ok` が `false` の場合）

1. プロジェクトの `.claude/settings.json` を読み込む（なければ作成）
2. SessionStart hookを追加:

プロファイルなしの場合:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python \"~/.claude/hooks/context_preloader.py\"",
            "timeout": 15000
          }
        ]
      }
    ]
  }
}
```

プロファイルありの場合（`--profile NAME` を追加）:
```json
"command": "python \"~/.claude/hooks/context_preloader.py\" --profile NAME"
```

**注意**: 既存のhooksがある場合はマージすること。上書きしない。

### Step 5: 動作確認

```bash
python -m scripts status
python -m scripts test
```

`ready: true` になっていることを確認し、ユーザーに報告:
- 「次のセッションから、指定したファイルが自動的に文脈に読み込まれます」
- 設定されたソース一覧を表示

---

## 管理フロー

`ready: true` の場合、ステータス情報を表示した上で操作を選択。

### `--profile` の動作

| コマンド | 読み込み対象 |
|---------|-------------|
| `python -m scripts` | **グローバル** (`sources.json`) のみ |
| `python -m scripts --profile weave` | **グローバル + プロファイル** (`profiles/weave.json`) をマージ |

CLIコマンド（list, test, add, remove）も同様:
- `--profile` なし → グローバルsourcesを操作
- `--profile NAME` → グローバル + そのプロファイルを対象

SessionStart hookの `--profile` 設定は `settings.json` で固定されるため、
CLIで手動操作するときも同じプロファイル名を指定すること。

### ソース追加

```bash
python -m scripts add --path "/path/to/file.txt" --label "My Notes"
python -m scripts add --path "https://example.com/api" --label "API Docs"
python -m scripts add --path "/path/to/file.txt" --label "My Notes" --profile NAME
```

### ソース削除

```bash
python -m scripts remove --id my-notes
```

### ソース一覧

```bash
python -m scripts list
python -m scripts list --profile NAME
```

### テスト

```bash
python -m scripts test
python -m scripts test --profile NAME
```

### プロファイル一覧

```bash
python -m scripts profiles
```

---

## Output Mode

settingsの `"mode"` で出力方式を切り替える:

| mode | 動作 | 用途 |
|------|------|------|
| `"inline"` (default) | ファイル内容を全文stdout出力 | 小さいファイル向け |
| `"reference"` | パス・説明・優先度のみ出力し、Claudeにread toolで読ませる | 大きいファイル向け（hook stdout制限回避） |

**reference mode使用時は、ソースに `description` と `priority` を設定すること。**

reference mode出力が1.5KBを超えるとstderrに警告が出る。

---

## 出力例

### inline mode（デフォルト）

```
=== Project Notes ===
[テキストファイルの内容がそのまま出力]

=== Design Spec [PDF document] ===
Path: /path/to/spec.pdf
Type: PDF document
Size: 2.3 MB
Note: Use Read tool to view this file

=== ContextPreloader Summary ===
Loaded: 1 text file, 1 binary reference
Total text: ~55KB
```

### reference mode

```
=== ContextPreloader: Session Context ===
Read the following files using the Read tool before responding to the user.

1. [CRITICAL] GrandDigest (Long-term Memory Summary)
   Path: C:/Users/anyth/DEV/homunculus/Weave/Identities/GrandDigest.txt
   8層階層的長期記憶ダイジェスト（週次〜世紀）

2. [HIGH] IntentionPad (Session-crossing Short-term Memory)
   Path: C:/Users/anyth/DEV/homunculus/Weave/Identities/IntentionPad.md
   セッション横断の短期記憶・意図メモ
```
