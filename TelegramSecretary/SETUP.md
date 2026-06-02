# TelegramSecretary セットアップガイド（Cloud Routine 運用）

Telegram で 24-7 即応する秘書を Cloud Routine 上に常駐させるための、**迷わず動かす**ための手順書。claude.ai の GUI と Telegram アプリ内でほぼ完結します。

> 仕様の SSoT は [SKILL.md](./skills/telegram-secretary/SKILL.md)、起動手順の詳細は [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md)、配置規約は [STRUCTURE.md](./STRUCTURE.md)、ローカル動作確認は [README.md](./README.md)。本書はそれらの上に立つ「運用開始の順路」です。

## 全体像

```
① Bot 作成 → ② chat_id 取得 → ③ プラグイン配置 → ④ 秘書人格 → ⑤ config
   → ⑥ Cloud Routine 登録 → ⑦ Environment 設定（GUI）→ ⑧ テスト起動
```

秘書の応答は親エージェント本人が起草し、本スキルは fetch / 認可 / 正規化 / 送信のみを担います。**秘匿（bot token・chat_id）は Cloud Routine の Environment に注入**し、コードやリポジトリには焼き込みません。

## 必要なもの

- **Telegram アカウント**
- **Claude Code（Cloud Routine が使える環境）**
- **リポジトリ（最小1つ・原則 Private）** — Cloud Routine が clone する。エージェント人格（`Identities/`）を含むため、**原則は1つの非公開リポにまとめる**のが素直。役割で2つに分けることもできる:
  - **基本設定**（`<BASE_REPO>`）— 本スキル `Expertises/TelegramSecretary/`・エージェント人格 `Identities/`・`SECURITY.md`
  - **非公開データ**（`<PRIVATE_DIR>`）— 秘書人格 `SecretaryRole.md` と運用 state
  > **1つの非公開リポにまとめる**のが基本（`<BASE_REPO>`＝`<PRIVATE_DIR>`、sources 1つ、cwd＝リポルート）。汎用スキル等**一部を公開したい場合のみ** 2 分割（sources 複数、各リポ名ディレクトリ並列・cwd＝親）。**人格（`Identities/`）の公開は必須ではない**——Weave が基本設定リポを公開しているのは人格論を公開する方針ゆえの例外的対応で、一般には人格ごと Private が原則。

## 手順

### ① Telegram Bot を作る

1. Telegram で **@BotFather** に話しかける
2. `/newbot` → bot の表示名とユーザー名を決める
3. 返ってくる **token**（`123456789:ABC-DEF...` の形式）を控える ← これが `TELEGRAM_BOT_TOKEN`

### ② 自分の chat_id を知る

1. Telegram で **@userinfobot** に話しかける
2. 返ってくる数値 **Id**（例 `123456789`）を控える ← これを `TELEGRAM_SECRETARY_AUTHORIZED_CHATS` に入れる

> **token と chat_id は別物です。** token は bot の鍵（BotFather 発行）、chat_id はあなた個人の宛先（@userinfobot で判明）。個人 DM では `chat_id = user_id`。

### ③ プラグインを配置

marketplace からインストール、または基本設定リポの `Expertises/TelegramSecretary/` に配置します。**Cloud Routine は基本設定リポを fresh clone する**ので、`Expertises/TelegramSecretary/`（コード一式）が基本設定リポにコミットされていることが必要です。

### ④ 秘書人格を用意（SecretaryRole.md）

雛型 [`templates/SecretaryRole.template.md`](./templates/SecretaryRole.template.md) をコピーし、**非公開リポの `Identities/SecretaryRole.md`** として、秘書の固有名・対応原則・触れない話題などを定義します（人格は個人資産ゆえ非公開リポに置き、配布物には焼き込みません）。

### ⑤ config.json を生成

```
/telegram-secretary init-config --session-duration-sec <秒> --agent-name <人格名> --private-dir <Private パス>
```

- `--session-duration-sec`: 1セッションの長さ（1〜86400 秒）
- `--agent-name`: 基本設定リポの `Identities/<agent_name>Identity.md` を解決する名前
- `--private-dir`: cwd（2リポ親）起点での非公開リポのパス（例 `<PRIVATE_REPO>/TelegramSecretary`）

> config.json は**基本設定リポの `Expertises/TelegramSecretary/config.json` に置き、Cloud Routine が fresh clone で読めるようコミット**します（秘匿を含まない運用設定ゆえコミット可）。配布リポでは `.gitignore` 対象なので、運用リポ側で明示追跡してください。

### ⑥ Cloud Routine に登録

```
/telegram-secretary schedule
```

- routine 本体（cron＋prompt body＋sources）を作成します
- **sources は基本設定＋非公開**（分けるなら2つ、1リポにまとめるなら1つ）
- prompt body 内の `<BASE_REPO>` / `<PRIVATE_DIR>` は schedule が自動で実リポ名に置換します（手置換不要）

> **`environment_id` は後から差し替え可能**です。先に routine を作っておき、次の ⑦ で環境を整えてから紐付ける流れが、一般には迷いにくくおすすめです。

### ⑦ Environment を設定（claude.ai GUI）

claude.ai の Code → Environments で：

- **環境変数**:
  - `TELEGRAM_BOT_TOKEN` = ① の token
  - `TELEGRAM_SECRETARY_AUTHORIZED_CHATS` = `[② の chat_id]`（JSON 整数配列。例 `[123456789]`）
- **network policy（egress 許可）**: **`api.telegram.org` を許可** ← これが無いと起動時に `host_not_allowed` で止まります
- 作成した Environment を routine に紐付け（GUI、または `/telegram-secretary schedule` の再実行で `environment_id` を指定）

### ⑧ テスト起動

- **手動起動**: routine を `run` で即実行（cron を待たずにテストできる）
- **Telegram で bot に1通送る** → 数秒で返信が返れば**導通完了**（egress・即応・パス解決がすべて OK）
- 返らない場合は claude.ai の実行履歴で停止した Step を確認（下記トラブルシューティング）

## 勤務帯の設計（cron ＋ duration）

時計はコードに持たせず、**cron（起動タイミング）＋ `session_duration_sec`（各回の長さ）** で表現します：

| 運用 | cron（UTC） | session_duration_sec |
|---|---|---|
| 24 時間常駐 | 1日1回（例 `1 15 * * *` ＝ JST 0:01） | 実行上限内の最大（例 `86340`） |
| 平日 9–17 時 | `0 0-7 * * 1-5`（JST 9–16 時 ＝ UTC 0–7 時） | `3600`〜`7200` |

> **cron は UTC**。JST から 9 時間引きます（JST 9:00 = UTC 0:00）。1セッションの実行上限はプラットフォーム依存です——上限を超える長さを指定しても途中で終了し、次の cron が lease / offset の冪等性で継続します（隙間メッセージは Telegram の ~24h 保持で取りこぼしません）。

## トラブルシューティング

| 症状 | 原因 | 対応 |
|---|---|---|
| `host_not_allowed`（Step 3） | egress 未開通 | network policy に `api.telegram.org` を追加 |
| exit 2（config invalid） | config.json 欠損 or env 欠損 | `show-config` で確認 → `init-config` 再生成、Environment の token/chats を確認 |
| exit 3（auth failed） | bot token 不正 | BotFather で token を確認・再生成 |
| exit 4（lease conflict） | 他セッションが保持中 | 自己治癒の正常動作（重複起動防止）。放置でよい |
| Step 0 でパス解決失敗 | 2リポ配置の不整合 | sources に基本設定リポ＋非公開リポの両方があるか、config の `private_dir` が cwd 親起点か確認 |
| 返信が返らない | egress or 認可 | chat_id が `AUTHORIZED_CHATS` に入っているか、`api.telegram.org` egress が通っているか |

## 参照

- 仕様 SSoT: [SKILL.md](./skills/telegram-secretary/SKILL.md)
- 起動手順: [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md)
- 構造地図: [STRUCTURE.md](./STRUCTURE.md)
- セキュリティ正典: [SECURITY.md](./SECURITY.md)
- ローカル動作確認: [README.md](./README.md)
