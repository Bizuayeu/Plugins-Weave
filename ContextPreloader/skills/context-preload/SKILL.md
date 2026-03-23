---
name: context-preload
description: ContextPreloaderセットアップ・管理（対話的）
---

# ContextPreloader Management

SessionStart hookで任意のファイル・URLを事前文脈として読み込むシステムの管理スキル。

## 目次
1. [セットアップフロー](#セットアップフロー)
2. [管理フロー](#管理フロー)
3. [出力例](#出力例)

---

## セットアップフロー

**TodoWriteで以下のリストを作成し、順番に実行すること**

| Step | 内容 | 実行方法 |
|------|------|---------|
| 1 | 既存hook検出 | `.claude/hooks/load-identity.ps1` の存在確認 |
| 2 | ユーザーに確認 | マイグレーションするか、新規作成か |
| 3 | config作成 | `python -m scripts add --path P --label L` でソース追加 |
| 4 | hook配置 | `context_preloader.py` を `~/.claude/hooks/` にコピー |
| 5 | settings.json更新 | SessionStart hookコマンドを更新 |
| 6 | テスト | `python -m scripts test` で全ソース確認 |
| 7 | 報告 | 結果をユーザーに表示 |

### マイグレーション（load-identity.ps1から）

既存の `load-identity.ps1` が検出された場合:

1. 以下の3ファイルを `profiles/weave.json` として登録:
   - `GrandDigest.txt`
   - `ShadowGrandDigest.txt`
   - `IntentionPad.md`
2. `sources.json`（グローバル）は空で作成
3. hookコマンドを `python context_preloader.py --profile weave` に更新
4. `load-identity.ps1` → `load-identity.ps1.bak` にリネーム

---

## 管理フロー

### ソース追加

```bash
cd plugins-weave/ContextPreloader
python -m scripts add --path "/path/to/file.txt" --label "My Notes"
python -m scripts add --path "https://example.com/api" --label "API Docs"
python -m scripts add --path "/path/to/file.txt" --label "My Notes" --profile weave
```

### ソース削除

```bash
python -m scripts remove --id my-notes
```

### ソース一覧

```bash
python -m scripts list
python -m scripts list --profile weave
```

### テスト

```bash
python -m scripts test
python -m scripts test --profile weave
```

### プロファイル一覧

```bash
python -m scripts profiles
```

---

## 出力例

### hookモード出力

```
=== GrandDigest (Long-term Memory Summary) ===
[ファイル内容...]

=== Design Spec [PDF document] ===
Path: /path/to/spec.pdf
Type: PDF document
Size: 2.3 MB
Note: Use Read tool to view this file

=== API Reference [URL] ===
Source: https://docs.example.com/api
[HTMLから抽出されたテキスト...]

=== ContextPreloader Summary ===
Loaded: 1 text file, 1 URL, 1 binary reference
Total text: ~55KB
```

### テスト出力

```json
[
  {"id": "grand-digest", "path": "/path/to/GrandDigest.txt", "status": "ok"},
  {"id": "missing-file", "path": "/nonexistent/file.txt", "status": "missing"}
]
```
