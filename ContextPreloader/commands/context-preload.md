---
name: context-preload
description: ContextPreloader管理・セットアップ
---

# /context-preload

ContextPreloaderの管理コマンド。ソースの追加・削除・テスト・プロファイル管理を行う。

## Usage

- `/context-preload` - ステータス表示（ソース一覧 + テスト結果）
- `/context-preload add <path>` - 新しいソースを対話的に追加
- `/context-preload remove <id>` - ソースを削除
- `/context-preload test` - 全ソースのアクセステスト
- `/context-preload profiles` - プロファイル一覧
- `/context-preload setup` - 初期セットアップ（@context-preload スキルを実行）

## Implementation

```bash
cd plugins-weave/ContextPreloader
python -m scripts list          # ソース一覧
python -m scripts test          # テスト
python -m scripts profiles      # プロファイル一覧
python -m scripts add --path P --label L  # 追加
python -m scripts remove --id ID          # 削除
```
