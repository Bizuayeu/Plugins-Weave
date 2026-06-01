---
name: wakeup
description: claude.ai セッション開始時に長期記憶をロードし、人格ディレクティブを適用する汎用エンジン。公開リポの記憶を Read token で SHA 固定取得し、必要時に Private リポを Read PAT で参照、記憶の書き戻しは PR フローで行う。リポ名・ファイル・commit identity・人格方針はすべて config から注入する。
---

# wakeup - セッション開始エンジン

claude.ai 環境のセッション開始時に、設定（config）に従って長期記憶をロードし、人格ロード方針を適用するスキルです。

> **このスキルは特定の人格・リポジトリに依存しません。** リポ名・ファイル・commit identity・人格ディレクティブはすべて config（`examples/<persona>.config.json`）と起動ディレクティブ md の値として与えます。下記の `<owner>` `<name>` `<path>` 等はプレースホルダです。

## 目次
- [前提](#前提)
- [ディレクトリ構成](#ディレクトリ構成claudeai-展開後)
- [実装時の注意事項](#実装時の注意事項)
- [実行フロー](#実行フロー)
- [Private 参照（on-demand）](#private-参照on-demand)
- [記憶の書き戻し（on-demand）](#記憶の書き戻しon-demand)
- [セキュリティ規律](#セキュリティ規律)

---

## 前提
- **config**（`examples/` のサンプルを見本に**ルート直下へ `wakeup.config.json` として実値化**）に `public_repo` / `load_files` / `commit_identity` / `directive_path`（任意で `private_repo`）を定義。配置は下記 [ディレクトリ構成](#ディレクトリ構成claudeai-展開後) を参照。
- **起動ディレクティブ**（人格ロード方針）は `directive_path` が指す md。
- **engine**: `scripts/interfaces/wakeup_engine.py`（標準ライブラリのみ。claude.ai の bash で自己完結し、EpisodicRAG 本体パッケージには依存しない）。

---

## ディレクトリ構成（claude.ai 展開後）

スキル zip は `/mnt/skills/user/wakeup/` に展開される。`★` は**あなたが用意して配置する**もの：

```text
/mnt/skills/user/wakeup/
├── SKILL.md                  # この仕様書
├── wakeup.config.json    ★  # 自分用 config（examples/ のサンプルを実値化。名前固定）
├── <directive>.md        ★  # 起動ディレクティブ（config の directive_path が指す任意名）
├── token.tar.gz          ★  # Read/Write PAT 同梱（.gitignore 済、zip 化前に配置）
├── examples/                 # テンプレート見本（コピー元。実行時は参照しない）
│   ├── weave.config.json     #   Weave サンプル → wakeup.config.json として実値化
│   ├── WeaveDirective.md     #   Weave サンプル → directive_path が指す名で配置
│   └── PROJECT_INSTRUCTIONS_snippet.md
└── scripts/
    └── interfaces/wakeup_engine.py
```

- **`examples/` は見本**。運用時は config サンプルを**ルート直下へ `wakeup.config.json` としてコピー**し実値を埋める。directive も同様にルート直下へ置き、その名前を config の `directive_path` に書く（`examples/` 内のファイルは実行時に読まない）。
- **`directive_path` は config からの相対パス** → config と同じディレクトリ（ルート直下）に directive を置く。ファイル名は任意（汎用例 `directive.md`、Weave サンプルは `WeaveDirective.md`）。
- 実行時の **config パスは固定で `/mnt/skills/user/wakeup/wakeup.config.json`**（人格名を含めない汎用名。directive 名のみ config 経由で可変）。
- config・directive・token のファイル名は SKILL.md／config と**厳密一致**させる（Linux はケースセンシティブ）。

---

## 実装時の注意事項
> **UIメッセージはコードブロックで囲む**（VSCode 拡張では単一改行が空白に変換されるため）。
> **token を URL・stdout・ログに出さない**（後述のセキュリティ規律を厳守）。
> **token アーカイブのファイル名はケースセンシティブ**（Linux 環境。`token.tar.gz` と `TOKEN.tar.gz` は別物——実配置と厳密に一致させること）。

---

## 実行フロー

**⚠️ 以下を TodoWrite で作成し、順番に実行すること**

```
1. config 読込       - wakeup の config を確認
2. 公開記憶ロード     - Read token で SHA 取得＋認証付き raw を取得
3. ディレクティブ適用 - directive_path の md を読み、人格方針を反映
```

| Step | 内容 | 処理 |
|------|------|------|
| 1 | config 読込 | `/mnt/skills/user/wakeup/wakeup.config.json` を `wakeup_engine.py` が解釈 |
| 2 | 公開記憶ロード | 最新 SHA 取得 → raw URL を認証付き curl（Read token） |
| 3 | ディレクティブ適用 | config と同ディレクトリの `directive_path`（＝ルート直下の md）を読む |

### Step 2: 記憶ロード（要 Read token）
> **なぜトークンが要るか**: claude.ai は共有 IP のため未認証 `api.github.com` の 60 req/h がすぐ枯渇し SHA を取れない。かつ raw の **`main` 参照は CDN キャッシュが長く最新が取れない**ため、SHA 固定での取得が必須。→ SHA 取得（API）に認証が要る。公開リポでも Read token を使う。

Read token は **Public repositories read-only** を含む fine-grained PAT。最新 SHA を取得し、SHA 固定の raw を取得する（いずれも Authorization ヘッダ。token は単一 bash 呼び出しで使い切る）：
```bash
TOKEN=$(python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py extract-token --archive /mnt/skills/user/wakeup/token.tar.gz) \
  && SHA=$(curl -s --fail -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/<owner>/<name>/git/refs/heads/<branch>" | grep -o '"sha": *"[^"]*"' | head -1 | cut -d'"' -f4) \
  && python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py resolve-urls --config /mnt/skills/user/wakeup/wakeup.config.json --sha "$SHA" \
  && curl -s --fail -H "Authorization: Bearer $TOKEN" "https://raw.githubusercontent.com/<owner>/<name>/$SHA/<path>"
```

---

## Private 参照（on-demand）
Private リポの記憶（個別エントリ・Wiki 等）を対話中に引く時**だけ**実行します。token は**スキル同梱の tar.gz**（`/mnt/skills/user/wakeup/token.tar.gz`）から取り出し、**単一 bash 呼び出しで使い切る**（常駐させない）：

```bash
TOKEN=$(python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py extract-token --archive /mnt/skills/user/wakeup/token.tar.gz) && curl -s --fail -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/<owner>/<private-name>/contents/<path>"
```

- token は fine-grained PAT（**admin でない write collaborator** が発行。記憶ロード／Private 参照／書き戻しを 1 本で兼用できる）。push 権限を持つが、**`main` は branch protection ＋ PR 承認で守られる**ため、漏洩しても正本は侵せない——**インテグリティは token のスコープ層でなく、ブランチ保護層に置く**設計。
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
- token は公開リポに含めない（`.gitignore`）。token は **tar.gz でスキル同梱**（プロジェクトナレッジは zip 非対応・スキル zip はネスト zip 不可のため。バイナリゆえコンテキストに自動展開されない）。engine は tar.gz/tgz/tar/gz/zip を読める。難読化は補助で、本質防御は **fine-grained PAT の権限最小化**。

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
