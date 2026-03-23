# CLAUDE.md - ContextPreloader Plugin

SessionStart hookで任意のファイル・URLを事前文脈として読み込むプラグイン。
claude.aiのプロジェクト機能をClaude Codeで再現する。

## Quick Start

### 1. config作成

`~/.claude/plugins/.contextpreloader/` に `sources.json` を配置:

```json
{
  "version": "1.0.0",
  "settings": {
    "encoding": "utf-8",
    "max_lines_per_file": 0,
    "show_summary": true,
    "url_timeout": 10
  },
  "sources": [
    {
      "id": "project-notes",
      "label": "Project Notes",
      "path": "~/projects/my-app/NOTES.md",
      "type": "auto",
      "enabled": true
    },
    {
      "id": "api-docs",
      "label": "API Reference",
      "path": "https://docs.example.com/api/v2",
      "type": "auto",
      "enabled": true
    },
    {
      "id": "design-spec",
      "label": "Design Specification",
      "path": "~/projects/my-app/docs/spec.pdf",
      "type": "auto",
      "enabled": true
    }
  ]
}
```

テンプレート: `.claude-plugin/sources.template.json`

### 2. hook配置

プラグイン同梱の `hooks/context_preloader.py` を `~/.claude/hooks/` にコピー:

```bash
cp plugins-weave/ContextPreloader/hooks/context_preloader.py ~/.claude/hooks/
```

開発時は環境変数でプラグインパスを上書き可能:
```bash
export CONTEXTPRELOADER_PLUGIN_DIR=~/DEV/plugins-weave/ContextPreloader
```

### 3. settings.json にhook登録

プロジェクトの `.claude/settings.json`:

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

プロファイルを使う場合（プロジェクト別に文脈を分ける）:

```json
"command": "python \"~/.claude/hooks/context_preloader.py\" --profile myproject"
```

### 4. プロファイル（任意）

`~/.claude/plugins/.contextpreloader/profiles/myproject.json`:

```json
{
  "sources": [
    {"id": "meeting-notes", "label": "Meeting Notes", "path": "~/Documents/meetings.md"},
    {"id": "team-wiki", "label": "Team Wiki", "path": "https://wiki.example.com/team"}
  ]
}
```

テンプレート: `.claude-plugin/profile.template.json`

### Source Type の動作

| path | type=auto | 動作 |
|------|-----------|------|
| `.txt`, `.md`, `.py` 等 | text | 内容をそのまま文脈に注入 |
| `.pdf`, `.png`, `.docx` 等 | binary | パス・サイズを表示（Read toolで閲覧） |
| `https://...` (HTML) | url | HTMLタグ除去しテキストを注入 |
| `https://...` (non-HTML) | url | URL+Content-Typeを表示 |

## Architecture

Clean Architecture 4層構造:

| 層 | ディレクトリ | 役割 |
|----|-------------|------|
| Domain | `scripts/domain/` | 純粋ロジック（モデル、定数、検出、例外） |
| Infrastructure | `scripts/infrastructure/` | 外部I/O（ファイル読込、URL取得、Config） |
| Application | `scripts/application/` | ユースケース統括（Preloader、Formatter、ProfileMerger） |
| Interfaces | `scripts/interfaces/` | エントリーポイント（hook_runner、CLI） |

依存フロー: `interfaces → application → domain` / `infrastructure → domain`

## Key Concepts

- **Source**: テキストファイル、バイナリファイル、またはURL
- **Profile**: 名前付きソースセット（プロジェクト単位の文脈分離）
- **Merge**: グローバルsources + プロファイルsourcesの二層マージ

## Data Paths

```
~/.claude/plugins/.contextpreloader/
  sources.json          # グローバル設定
  profiles/
    weave.json          # プロファイル例
```

## Development

```bash
cd plugins-weave/ContextPreloader

# テスト実行
python -m pytest scripts/tests/ -v

# hookモード（stdout出力）
python -m scripts
python -m scripts --profile weave

# CLI管理
python -m scripts list
python -m scripts add --path P --label L
python -m scripts remove --id ID
python -m scripts test
python -m scripts profiles
```
