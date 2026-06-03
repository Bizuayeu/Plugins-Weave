# TelegramSecretary

> 📦 **設定の置き場** — 環境固有の値は `<INSTALL_DIR>/config.json`（`agent_name` / `private_dir` / `session_duration_sec` / `registry_*`、雛型 `templates/config.template.json`、`init-config` で生成）に集約します。秘匿（bot token / authorized chats）は env で注入。**運用値の手置換は不要**——人格名・private_dir は config.json、`<INSTALL_DIR>` / `<REPO_ROOT>` は bootstrap が env 解決します（`<INSTALL_DIR>`=インストール先 / `<OWNER>`=運用主体 はドキュメント上の読み替え表記）。詳細は [STRUCTURE.md](./STRUCTURE.md)。

Telegram Bot API の long-polling を **Claude Code Routines**（Anthropic のクラウド実行スケジュールエージェント基盤。Remote 実行の routine ＝ cloud routine）上で常駐させ、認可済みチャットからのメッセージに秘書エージェント（`SecretaryRole` を被った本体エージェント。人格名は config.json の `agent_name`）が即応する対話チャネル。

公開 ingress を持てない cloud routine 環境でも、long-polling と deadline 駆動ループで 24-7 の即応を実現します（`watch --exit-on-message` がメッセージ受信時に即座に exit → 返信 → 再起動）。応答は親プロセスのエージェント本人が起草し、本スキルは fetch / 認可 / 正規化 / 送信のみを担います（応答生成をサブプロセスに投げない設計）。

## アーキテクチャ

Clean Architecture 4層（Domain → UseCase → Interface → Infrastructure、依存は内向きのみ）。設計の理由は [DESIGN.md](./DESIGN.md)、ディレクトリ構造は [STRUCTURE.md](./STRUCTURE.md) を参照。

## できること

- **テキスト即応** — Gmail より低レイテンシ（数秒）で `<OWNER>` から呼べる 24-7 の対話チャネル
- **受信メディアの中身理解** — file 転送で止まらず中身を読む：
  - 画像 → Vision で解釈
  - docx / pptx / xlsx → Markdown 化
  - PDF → 全ページ画像化（Vision）＋ オンデマンドの全文テキスト / 個別ページ抽出
  - voice / audio / video → 音声を文字起こし（ローカル STT、音声が外部に出ない）
- **生成物の送り返し** — 画像・レポート等を返信に添付（reply threading、typing 表示）
- **管理表（4 表）** — 関係者（INDIVIDUALS）／依頼（TASKS）／対応知（KNOWLEDGE）／能力カタログ（ABILITIES）を秘書が判断して記録。秘書は応答前に能力カタログを引き、依頼に使えるスキルがあれば行使する。`registry_sync` 有効時は固定ブランチへ git 永続化（揮発 state と分離・イベント駆動 commit&push）
- **言行一致の保証（WAL）** — `registry_sync` 有効時、「登録しました」等の約束をする返信の前に intent を WAL ログへ先行 push（must-succeed＝push 不能なら送信もしない）し、起動時に未反映分を registry へ redo。push 漏れによる「言ったのに未登録」を構造的に防ぐ

## Quickstart（ローカル動作確認）

```powershell
cd <INSTALL_DIR>

# 依存インストール
python -m pip install -e ".[dev]"

# 環境変数（秘匿のみ＝純2層）
$env:TELEGRAM_BOT_TOKEN = "<bot-token-from-botfather>"
$env:TELEGRAM_SECRETARY_AUTHORIZED_CHATS = "[<your-chat-id>]"
$env:TELEGRAM_SECRETARY_STATE_DIR = ".\state"   # 任意（既定 ./state）

# 運用設定 config.json を生成（session_duration_sec 必須、範囲 1〜86400）
python scripts/main.py init-config --session-duration-sec 7200 --agent-name YourSecretary

# 設定検証 → 現設定の確認 → 疎通 ping → 1サイクル poll
python scripts/main.py validate-config
python scripts/main.py show-config
python scripts/main.py test --chat-id <your-chat-id>
python scripts/main.py poll --timeout 5

# deadline 駆動の常駐を試す（メッセージ受信で即応、窓満了で再起動）
python scripts/main.py lease acquire
python scripts/main.py watch --exit-on-message --max-duration 30 --timeout 5
#   → メッセージが来たサイクルで即 exit 0／無ければ 30 秒の窓満了で exit 0
#   （本番の常駐設定＝2h 枠・580s 窓は ROUTINE_PROMPT.md 参照）
python scripts/main.py lease release
```

> **chat_id の発見**（初回のみ手動）— bot に 1 通送ってから `poll` を 1 回叩き、emit JSON の `chat_id` を読んで `AUTHORIZED_CHATS` に登録します（鶏卵問題ゆえ初回だけ手動）。

## メディアの送受信

- **受信**: bot に画像 / docx / PDF / voice 等を送ると、`poll`/`watch` が中身を解釈して emit します。PDF の段階処理（先頭ページ Vision → 必要に応じ `render-pdf` で全文/個別ページ）や voice の文字起こしの詳細は [SKILL.md](./skills/telegram-secretary/SKILL.md)。
- **送信**: `send-reply --file <path>`（複数可、画像→sendPhoto・他→sendDocument に自動振り分け）。`--reply-to <message_id>` で返信スレッドを張れます。

## env vars

| Var | Required | 概要 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | BotFather から取得 |
| `TELEGRAM_SECRETARY_AUTHORIZED_CHATS` | ✅ | JSON array of int（chat_id allowlist） |
| `TELEGRAM_SECRETARY_STATE_DIR` | optional | offset/lease/media の保存先（既定 `./state`） |
| `TELEGRAM_SECRETARY_SESSION_ID` | optional | リース owner ID（省略時は uuid 自動生成）。`source bootstrap.sh` で自動 export され全コマンドで共有 |
| `TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES` | optional | 受信 media download のサイズ上限（既定 20MB）。超過は download せず skip |
| `TELEGRAM_SECRETARY_MEDIA_RETENTION_HOURS` | optional | 保存 media の保持期限（既定 24h）。超過分は自動削除 |
| `TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD` | optional | Heavy（true=既定、保存して中身理解）/ Medium（false、メタのみ）切替 |
| `TELEGRAM_SECRETARY_BUNDLE_VOICE` | optional | 音声/動画 STT を導入するか（既定 true）。`false` で音声は `skipped`（軽量化・ライセンス回避、後述） |
| `TELEGRAM_SECRETARY_OUTBOUND_MAX_SIZE_BYTES` | optional | 送信添付の上限（既定 50MB、Telegram bot API 上限）。超過は送信前に弾く |
| `TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES` | optional | PDF 受信時に事前画像化する先頭ページ数の上限（既定 20）。超過分は `render-pdf` でオンデマンド |

> **継続時間は config.json の `session_duration_sec`**（範囲 1〜86400 秒、必須）。「9-17 時勤務」のような勤務帯は cloud routine の cron（例 `0 9-16 * * 1-5`）+ duration で表現します（コードに時計を持たせない）。deadline 駆動ループの運用変数（`TS_SESSION_DEADLINE_EPOCH` / `TS_POLL_SET_SEC` / `TS_POLL_BASH_TIMEOUT_MS` / `TS_MAX_TURNS`）は `bootstrap.sh` が config.json から算出して export します。詳細は [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md)。

## Subcommands

| Command | 機能 | Exit code |
|---|---|---|
| `validate-config` | env + config.json の検証 | 0=OK, 2=設定欠損 |
| `show-config` | 現設定を read-only 表示（秘匿はマスク） | 0（未設定でも 0） |
| `init-config [--session-duration-sec] [--agent-name] [--private-dir] [--force]` | config.json を生成（範囲検証、既存は `--force` で上書き） | 0, 2=範囲外/既存 |
| `lease acquire\|renew\|release [--owner] [--ttl SEC]` | リースロック操作（並走防止、`--ttl` 既定 300） | 0, 4=conflict, 2 |
| `poll [--timeout]` | getUpdates 1サイクル、認可・正規化済み update を JSON Lines で emit | 0, 1=fetch失敗, 3=auth失敗 |
| `watch [--max-duration SEC] [--exit-on-message] [--timeout SEC] [--max-iterations N] [--cleanup-interval N] [--owner]` | 長期 long-poll ループ（サイクル毎に lease 自動 renew）。`--max-duration`=窓満了で exit 0、`--exit-on-message`=メッセージ受信サイクルで exit 0、`--timeout`=getUpdates long-poll 秒（既定 30） | 常駐 / 窓畳み |
| `send-reply --chat-id --update-id --text-file [--file ...] [--reply-to] [--owner]` | 返信送信。`--file` で添付、`--reply-to` で threading | 0, 1=送信失敗, 2=添付不正, 3=auth, 4=lease |
| `render-pdf --path (--text \| --pages N-M)` | 受信済み PDF のオンデマンド抽出（`--text`=全文テキスト / `--pages`=指定ページ画像化） | 0, 2=不在/引数不正 |
| `test --chat-id` | 疎通テスト（owner chat に ping 送信） | 0, 1, 3 |
| `cleanup-media` | retention 超過の保存 media を削除（`watch` は自動発火、手動/cron 用） | 0, 2 |
| `individuals\|tasks\|knowledge\|abilities {list\|get\|add\|remove}` | 管理表 CRUD（4 表、値オブジェクトで入力検証、不正は exit 2）。`registry_sync` 有効時は add/remove 後に commit&push | 0, 2 |
| `registry-sync` | 起動時に固定ブランチから管理表を fetch（`registry_sync` 有効時のみ、無効は no-op） | 0, 1 |
| `wal-append --kind <...> (--json\|--json-file)` / `wal-push` / `wal-redo` | WAL（言行一致）: 登録系返信の前に intent を先行 push（must-succeed）、起動時に未反映分を registry へ redo。`registry_sync` 有効時のみ | 0, 1=push失敗, 2 |

`--owner` は省略可（`source bootstrap.sh` で env 経由自動同期、緊急時の上書きにのみ使用）。

## cloud routine への登録（schedule / unschedule）

常駐 routine 自体の cloud routine 登録・更新・停止は `/telegram-secretary` の `schedule`（登録 / 有効化 / 設定上書き＝upsert）/ `unschedule`（停止＝`enabled:false`）で行います。**`RemoteTrigger` ツール手順**（CLI ではない）で、手順は [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md) の「cloud routine ライフサイクル管理」節が SSoT。秘匿は cloud routine の Environment に注入、運用設定（`session_duration_sec` 等）は `init-config`。物理削除（list から消す）のみ claude.ai UI 手動です。

## テスト

```powershell
python -m pytest scripts/tests/ -v
```

全層（Domain / UseCase / Adapter / Infrastructure / CLI）のテストを信頼性の証拠として公開しています。

## 依存とライセンス

| 依存 | 用途 | ライセンス |
|---|---|---|
| `httpx` | Telegram API 通信 | BSD |
| `markitdown[docx,pptx,xlsx]` | ドキュメント → Markdown 化 | MIT（再帰依存も MIT/BSD/Apache 系） |
| `pdfplumber` | PDF テキスト層抽出（ローカル完結） | MIT |
| `pypdfium2` + `Pillow` | PDF 画像化（ローカル完結） | BSD/Apache 系 |
| `moonshine-voice` + `av`（PyAV） | 音声 STT（ローカル推論、ffmpeg を wheel 内包） | ⚠️ 下記参照 |

> ⚠️ **moonshine のライセンス** — Community License は年商 $1M 未満のみ商用無料です。年商 $1M 以上での本番利用は Enterprise License、または `TELEGRAM_SECRETARY_BUNDLE_VOICE=false` で音声を外すか、`kotoba-whisper`（Apache-2.0）への差し替えが必要です（`MediaRenderer` Port の差し替えで対応）。
>
> 音声 STT はローカル推論のため、音声データが外部に送信されません（機密 voice メモにも安全）。

## 関連ドキュメント

- [SETUP.md](./SETUP.md) — セットアップガイド（cloud routine 運用開始の順路。はじめての方はここから）
- [SKILL.md](./skills/telegram-secretary/SKILL.md) — スキルマニフェスト（仕様の SSoT）
- [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md) — cloud routine 実行手順
- [DESIGN.md](./DESIGN.md) — 設計正典（なぜこの設計か）
- [STRUCTURE.md](./STRUCTURE.md) — 構造地図（どこに何を置くか）
- [SECURITY.md](./SECURITY.md) — セキュリティ正典（脅威モデル・配布前チェックリスト）
- [CHANGELOG.md](./CHANGELOG.md) — 変更履歴
