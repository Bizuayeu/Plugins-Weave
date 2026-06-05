# TelegramSecretary セットアップガイド（cloud routine 運用）

Telegram で 24-7 即応する秘書を **Claude Code Routines**（Anthropic のクラウド実行スケジュールエージェント基盤。Remote 実行＝cloud routine）上に常駐させるための、**迷わず動かす**ための手順書。claude.ai の GUI と Telegram アプリ内でほぼ完結します。

> 仕様の SSoT は [SKILL.md](./skills/telegram-secretary/SKILL.md)、起動手順の詳細は [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md)、配置規約は [STRUCTURE.md](./STRUCTURE.md)、ローカル動作確認は [README.md](./README.md)。本書はそれらの上に立つ「運用開始の順路」です。

## 全体像

```
① Bot 作成 → ② chat_id 取得 → ③ プラグイン配置 → ④ 秘書人格 → ⑤ config
   → ⑥ cloud routine 登録 → ⑦ Environment 設定（GUI）→ ⑧ テスト起動
```

秘書の応答は親エージェント本人が起草し、本スキルは fetch / 認可 / 正規化 / 送信のみを担います。**秘匿（bot token・chat_id）は cloud routine の Environment に注入**し、コードやリポジトリには焼き込みません。

## 必要なもの

- **Telegram アカウント**
- **Claude Code（cloud routine が使える環境）**
- **リポジトリ（最小1つ・原則 Private）** — cloud routine が clone する。**原則は1つの非公開リポにまとめる**のが素直だが、2つに分けることもできる:
  - **基本設定**（`<BASE_REPO>`）— 本スキル `TelegramSecretary/`（`<BASE_REPO>` 内に配置、場所は任意——bootstrap が自身の位置を絶対解決）＋ 本体人格 `Identities/<agent_name>Identity.md`・`SECURITY.md`（cwd 起点で ROUTINE_PROMPT が読む位置）。スキルは Public 可。**本体人格は公開リポへの同居も・1リポ統合で非公開側への同居も両対応**——`<BASE_REPO>` は論理位置で、その実体が公開か非公開かは運用次第。
  - **非公開データ**（`<PRIVATE_DIR>`）— 秘書人格 `SecretaryRole.md` と運用 state。Private が前提。
  > **1つの非公開リポにまとめる**のが基本（`<BASE_REPO>`＝`<PRIVATE_DIR>`、sources 1つ、cwd＝リポルート）。汎用スキル等**一部を公開したい場合のみ** 2 分割（sources 複数、各リポ名ディレクトリ並列・cwd＝親）。

## 手順

### ① Telegram Bot を作る

1. Telegram で **@BotFather** に話しかける
2. `/newbot` → bot の表示名とユーザー名を決める
3. 返ってくる **token**（`123456789:ABC-DEF...` の形式）を控える ← これが `TELEGRAM_BOT_TOKEN`

### ② 自分の chat_id を知る

1. Telegram で **@userinfobot** に話しかける
2. 返ってくる数値 **Id**（例 `123456789`）を控える ← これが `TELEGRAM_SECRETARY_AUTHORIZED_CHATS`

> **token と chat_id は別物です。** token は bot の鍵（BotFather 発行）、chat_id はあなた個人の宛先（@userinfobot で判明）。個人 DM では `chat_id = user_id`。

### ③ プラグインを配置

marketplace からインストール、または基本設定リポの `TelegramSecretary/` に配置します。**cloud routine は基本設定リポを fresh clone する**ので、`TelegramSecretary/`（コード一式）が基本設定リポにコミットされていることが必要です。

### ④ 秘書人格を用意（SecretaryRole.md）

雛型 [`templates/SecretaryRole.template.md`](./templates/SecretaryRole.template.md) をコピーし、**非公開リポの `Identities/SecretaryRole.md`** として、秘書の固有名・対応原則・触れない話題などを定義します（人格は個人資産ゆえ非公開リポに置き、配布物には焼き込みません）。

### ⑤ config.json を生成

```
/telegram-secretary init-config --session-duration-sec <秒> --agent-name <人格名> --private-dir <Private パス>
```

- `--session-duration-sec`: 1セッションの長さ（1〜86400 秒）
- `--agent-name`: 基本設定リポの `Identities/<agent_name>Identity.md` を解決する名前
- `--private-dir`: cwd（2リポ親）起点での非公開リポのパス（例 `<PRIVATE_REPO>/TelegramSecretary`）

> config.json は**基本設定リポの `TelegramSecretary/config.json` に置き、cloud routine が fresh clone で読めるようコミット**します（秘匿を含まない運用設定ゆえコミット可）。配布リポでは `.gitignore` 対象なので、運用リポ側で明示追跡してください。

**管理表（関係者・依頼・対応知・能力カタログ）をリポジトリに永続化する場合**（任意・推奨）— cloud routine は毎回 fresh clone で起動し実行環境は揮発するため、秘書が蓄積した管理表を次回起動へ残すには、**リポジトリの固定ブランチ**に git 永続化します。`init-config` では生成されないので、config.json に以下を追記します（雛型は `templates/config.template.json`）:

```json
{
  "registry_sync": true,
  "registry_dir": "<PRIVATE_REPO>/TelegramSecretary/registry",
  "registry_branch": "claude/ts-registry"
}
```

- `registry_sync`: `true` で管理表を固定ブランチへ git 永続化（更新のたび commit&push＋起動時 fetch）。ローカル動作確認では `false`（git に触れない）
- `registry_dir`: 永続管理表（individuals/tasks/knowledge/abilities）の置き場。**揮発 state（offset/lease/media）の `state_dir` とは別**にし、非公開リポ配下を指す。未設定なら `state_dir` にフォールバック
- `registry_branch`: push 先の固定ブランチ（既定 `claude/ts-registry`）。`registry_remote`（既定 `origin`）と組で運用。揮発 state と分けることで「消えてよいもの」と「蓄積が本質のもの」を物理分離します

### ⑥ cloud routine に登録

```
/telegram-secretary schedule
```

- routine 本体（cron＋prompt body＋sources）を作成します
- **sources は基本設定＋非公開**（分けるなら2つ、1リポにまとめるなら1つ）
- prompt body 内の `<BASE_REPO>` / `<PRIVATE_DIR>` は schedule が自動で実リポ名に置換します（手置換不要）
- **`registry_sync` を有効にした場合**、管理表の push 先 `registry_branch`（既定 `claude/ts-registry`）が routine の書き戻し先（`outcomes`）として宣言されます。これが無いと cloud routine から管理表ブランチへ push できません（`registry_sync` 無効なら不要）

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
| 24 時間常駐 | 実測上限の間隔で複数回（例 4h ごと ＝ `0 15,19,23,3,7,11 * * *` ＝ JST 0/4/8/12/16/20 時） | 実測上限と同程度（例 `14400` ＝ 4h） |
| 平日 9–17 時 | `0 0-7 * * 1-5`（JST 9–16 時 ＝ UTC 0–7 時） | `3600`〜`7200` |

> **cron は UTC**。JST から 9 時間引きます（JST 9:00 = UTC 0:00）。**1セッションの実行上限はプラットフォーム依存**で、Claude Code Routines のコンテナは実測で約 4 時間程度（変動しうる）で終了します。常駐させたい場合は `session_duration_sec` を実測上限と同程度にし、cron をその間隔で回します——枠が上限より長くても途中で終了し、次の cron が lease / offset の冪等性で継続します（隙間メッセージは Telegram の ~24h 保持で取りこぼしません）。逆に「1日1回 cron ＋ 長大な枠（例 `86340`）」では、上限で切れた後に次の起動まで沈黙するため常駐には不向きです。

## トラブルシューティング

| 症状 | 原因 | 対応 |
|---|---|---|
| `host_not_allowed`（Step 3） | egress 未開通 | network policy に `api.telegram.org` を追加 |
| exit 2（config invalid） | config.json 欠損 or env 欠損 | `show-config` で確認 → `init-config` 再生成、Environment の token/chats を確認 |
| exit 3（auth failed） | bot token 不正 | BotFather で token を確認・再生成 |
| exit 4（lease conflict） | 他セッションが保持中 | 自己治癒の正常動作（重複起動防止）。放置でよい |
| Step 0 でパス解決失敗 | 2リポ配置の不整合 | sources に基本設定リポ＋非公開リポの両方があるか、config の `private_dir` が cwd 親起点か確認 |
| 返信が返らない | egress or 認可 | chat_id が `AUTHORIZED_CHATS` に入っているか、`api.telegram.org` egress が通っているか |
| 管理表が毎回空に戻る | `registry_sync` 無効 or `outcomes` 未配線 | config の `registry_sync:true` と `registry_dir` を確認 → `/telegram-secretary schedule` 再登録で push 先ブランチ（outcomes）を配線 |
| `registry fetch failed`（起動時） | 固定ブランチ未作成 or git 認証不足 | 初回は対象ブランチが空でも継続（前回ローカル状態で起動）。git 認証（PAT 等）が Environment にあるか確認 |

## 参照

- 仕様 SSoT: [SKILL.md](./skills/telegram-secretary/SKILL.md)
- 起動手順: [ROUTINE_PROMPT.md](./ROUTINE_PROMPT.md)
- 構造地図: [STRUCTURE.md](./STRUCTURE.md)
- セキュリティ正典: [SECURITY.md](./SECURITY.md)
- ローカル動作確認: [README.md](./README.md)
