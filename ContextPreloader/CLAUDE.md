# CLAUDE.md - ContextPreloader Plugin

SessionStart hookで任意のファイル・URLを事前文脈として読み込むプラグイン。
claude.aiのプロジェクト機能をClaude Codeで再現する。

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
