---
name: wakeup
description: claude.ai セッション開始時に長期記憶をロードし、人格ディレクティブと表情UIを起動する汎用エンジン。公開リポの記憶を認証なしで読み込み、必要時に Private リポを Read PAT で参照、記憶の書き戻しは PR フローで行う。リポ名・ファイル・commit identity・人格方針はすべて config から注入する。
---

# wakeup - セッション開始エンジン

claude.ai 環境のセッション開始時に、設定（config）に従って長期記憶をロードし、人格ロード方針を適用し、表情 UI を起動するスキルです。

> **このスキルは特定の人格・リポジトリに依存しません。** リポ名・ファイル・commit identity・人格ディレクティブはすべて config（`examples/<persona>.config.json`）と起動ディレクティブ md の値として与えます。下記の `<owner>` `<name>` `<path>` 等はプレースホルダです。

## 目次
- [前提](#前提)
- [実装時の注意事項](#実装時の注意事項)
- [実行フロー](#実行フロー)
- [Private 参照（on-demand）](#private-参照on-demand)
- [記憶の書き戻し（on-demand）](#記憶の書き戻しon-demand)
- [セキュリティ規律](#セキュリティ規律)

---

## 前提
- **config**（`examples/` のテンプレートを自分用に用意）に `public_repo` / `load_files` / `commit_identity` / `directive_path`（任意で `private_repo`）を定義。
- **起動ディレクティブ**（人格ロード方針・表情運用）は `directive_path` が指す md。
- **engine**: `scripts/interfaces/wakeup_engine.py`（標準ライブラリのみ。claude.ai の bash で自己完結し、EpisodicRAG 本体パッケージには依存しない）。

---

## 実装時の注意事項
> **UIメッセージはコードブロックで囲む**（VSCode 拡張では単一改行が空白に変換されるため）。
> **token を URL・stdout・ログに出さない**（後述のセキュリティ規律を厳守）。

---

## 実行フロー

**⚠️ 以下を TodoWrite で作成し、順番に実行すること**

```
1. config 読込       - wakeup の config を確認
2. 公開記憶ロード     - 認証なし curl で load_files を取得
3. ディレクティブ適用 - directive_path の md を読み、人格方針を反映
4. 表情UI起動        - VisualExpression に委譲
```

| Step | 内容 | 処理 |
|------|------|------|
| 1 | config 読込 | `wakeup_engine.py` が config を解釈 |
| 2 | 公開記憶ロード | 最新 SHA 取得 → raw URL を認証なし curl |
| 3 | ディレクティブ適用 | `directive_path` の md を読む |
| 4 | 表情起動 | VisualExpression の UI 配置を呼ぶ |

### Step 2: 記憶ロード（要 Read token）
> **なぜトークンが要るか**: claude.ai は共有 IP のため未認証 `api.github.com` の 60 req/h がすぐ枯渇し SHA を取れない。かつ raw の **`main` 参照は CDN キャッシュが長く最新が取れない**ため、SHA 固定での取得が必須。→ SHA 取得（API）に認証が要る。公開リポでも Read token を使う。

Read token は **Public repositories read-only** を含む fine-grained PAT。最新 SHA を取得し、SHA 固定の raw を取得する（いずれも Authorization ヘッダ。token は単一 bash 呼び出しで使い切る）：
```bash
TOKEN=$(python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py extract-token --zip /mnt/skills/user/wakeup/token.zip) \
  && SHA=$(curl -s --fail -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/<owner>/<name>/git/refs/heads/<branch>" | grep -o '"sha": *"[^"]*"' | head -1 | cut -d'"' -f4) \
  && python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py resolve-urls --config <config-path> --sha "$SHA" \
  && curl -s --fail -H "Authorization: Bearer $TOKEN" "https://raw.githubusercontent.com/<owner>/<name>/$SHA/<path>"
```

### Step 4: 表情UI起動（VisualExpression へ委譲）
```bash
cp /mnt/skills/user/visual-expression/VisualExpressionUI.html /mnt/user-data/outputs/
```
その後 `present_files` で表示。表情キー対応表など詳細は **VisualExpression スキル**を参照（ここでは重複させない）。

---

## Private 参照（on-demand）
Private リポの記憶（個別エントリ・Wiki 等）を対話中に引く時**だけ**実行します。token は**スキル同梱の二重 zip**（`/mnt/skills/user/wakeup/token.zip`）から取り出し、**単一 bash 呼び出しで使い切る**（常駐させない）：

```bash
TOKEN=$(python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py extract-token --zip /mnt/skills/user/wakeup/token.zip) && curl -s --fail -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/<owner>/<private-name>/contents/<path>"
```

- token は **Read 権限のみ**の fine-grained PAT（漏洩時の被害を最小化）。
- `$(...)` で stdout をキャプチャするため、token はツール出力に残りません。
- 失敗時も engine は token を漏らしません（マスク済み・非ゼロ終了）。

---

## 記憶の書き戻し（on-demand）
記憶（作業ログ・短期メモ等）を更新する時。**default ブランチへは直接 push せず**、`claude/*` ブランチ → PR → 人間がマージします：

```bash
git config user.name "<commit_identity.author_name>"
git config user.email "<commit_identity.author_email>"   # GitHub noreply 形式
git checkout -b claude/<topic>
# ... ファイルを更新 ...
git add <files>
git commit -m "<message>

Co-authored-by: <commit_identity.coauthor>"
git push origin claude/<topic>
gh pr create --base <branch> --head claude/<topic> --title "<title>"
```

- **Write 権限の PAT は admin でないアカウント**（write collaborator）で発行すること。admin のトークンはブランチ保護を bypass してしまう。
- 人格核（Identity 系ファイル）への書き戻しは特に PR レビューを必須とする。

---

## セキュリティ規律
- **記憶ロード**: Read token で SHA 取得（API レート回避）＋ SHA 固定 raw（CDN キャッシュ回避）。claude.ai 共有 IP では未認証が枯渇するため、公開リポでも認証する。
- **全 HTTP**: token は **Authorization ヘッダ**のみ（URL には絶対に載せない）、`curl -s --fail` を用いる。
- token は `$(...)` で受け、stdout・ログに出さない。
- **default ブランチへの直接 push は禁止**（`claude/*` ブランチ ＋ PR）。
- token は公開リポに含めない（`.gitignore`）。難読化（二重 zip）は補助で、本質防御は **fine-grained PAT の権限最小化**。

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
