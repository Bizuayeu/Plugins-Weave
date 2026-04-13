---
name: context-preload
description: ContextPreloader管理・セットアップ
---

# /context-preload

ContextPreloaderの管理コマンド。ソースの追加・削除・テスト・プロファイル管理を行う。

## 実行フロー

**このコマンドが呼ばれたら、必ず最初にステータスチェックを実行すること。**

```bash
cd plugins-weave/ContextPreloader
python -m scripts status
```

| `ready` | 対応 |
|---------|------|
| `true` | → [管理フロー](#管理フロー)へ |
| `false` | → [セットアップ](#セットアップ)を開始 |

## セットアップ

`ready: false` の場合、不足コンポーネントを順に構築する。
TodoWriteで該当ステップのみリスト化して実行。

### Step 1: config作成（`config.ok` が `false`）

ユーザーに読み込みたいファイル/URLを確認し、sourcesに追加:

```bash
mkdir -p ~/.claude/plugins/.contextpreloader/profiles
python -m scripts add --path "/path/to/file" --label "Label"
```

指定なしの場合はテンプレートを配置:
```bash
cp plugins-weave/ContextPreloader/.claude-plugin/sources.template.json ~/.claude/plugins/.contextpreloader/sources.json
```

### Step 1.5: mode設定（任意）

合計10KB超のソースがある場合、reference modeを推奨:
- `sources.json` の `settings.mode` を `"reference"` に変更
- 各ソースに `description` と `priority`（`critical`/`high`/`normal`/`low`）を追加

### Step 2: プロファイル作成（任意）

プロジェクト別に分けたい場合、プロファイル名を聞いて `profiles/{name}.json` を作成。

### Step 3: hook配置（`hook.ok` が `false`）

```bash
cp plugins-weave/ContextPreloader/hooks/context_preloader.py ~/.claude/hooks/
```

### Step 4: settings.json更新（`settings.ok` が `false`）

プロジェクトの `.claude/settings.json` に SessionStart hook を追加（既存hooksとマージ）:

```json
"command": "python \"~/.claude/hooks/context_preloader.py\""
```

プロファイルありの場合は `--profile NAME` を追加。

### Step 5: 動作確認

```bash
python -m scripts status
python -m scripts test
```

## 管理フロー

### `--profile` の動作

| コマンド | 対象 |
|---------|------|
| `python -m scripts` | グローバル (`sources.json`) のみ |
| `python -m scripts --profile NAME` | グローバル + プロファイル をマージ |

CLIコマンドも同様。hookの `--profile` と合わせること。

### Usage

- `/context-preload` - ステータス表示
- `/context-preload add <path>` - ソースを対話的に追加
- `/context-preload remove <id>` - ソースを削除
- `/context-preload test` - 全ソースのアクセステスト
- `/context-preload profiles` - プロファイル一覧
- `/context-preload setup` - 初期セットアップ

### Implementation

```bash
cd plugins-weave/ContextPreloader
python -m scripts list                        # ソース一覧
python -m scripts test                        # テスト
python -m scripts profiles                    # プロファイル一覧
python -m scripts add --path P --label L      # 追加
python -m scripts remove --id ID              # 削除
```

## Output Mode

| mode | 動作 | 用途 |
|------|------|------|
| `"inline"` (default) | ファイル内容を全文stdout出力 | 小さいファイル向け |
| `"reference"` | パス・説明・優先度のみ出力 | 大きいファイル向け（hook stdout制限回避） |

### 出力例（reference mode）

```
=== ContextPreloader: Session Context ===
Read the following files using the Read tool before responding to the user.

1. [CRITICAL] GrandDigest (Long-term Memory Summary)
   Path: C:/Users/anyth/DEV/homunculus/Weave/Identities/GrandDigest.txt
   8層階層的長期記憶ダイジェスト（週次〜世紀）
```
