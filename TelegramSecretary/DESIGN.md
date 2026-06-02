# TelegramSecretary 設計正典（DESIGN）

設計の **why** を集約する。役割分担 — **DESIGN**=なぜこの設計か / **STRUCTURE**=どこに何を置くか。

## 1. 設計原則

- **秘書＝入力理解優先**: `<OWNER>` の業務入力（voice / 写真 / 文書）の「受信＋中身理解」が一次価値
- **双方向性の最小成立**: 出力（送信）は file 送信で双方向が完成する。対話 UX 装飾は選択的
- **LLM 推論はコード外**: 応答生成・判断は親プロセスのエージェント、コードは決定論的な fetch / render / send / 管理表 I/O のみ（LLM 推論をサブプロセスで多重起動しない）
- **テンプレート/データ分離**: 配布可能性のため、コード・雛型（public）と実データ・人格（Private）を物理分離する
- **設定の純2層**: env は秘匿（bot token / authorized chats）+ state_dir のみ、非秘匿の運用設定（`session_duration_sec` / `agent_name` / `private_dir`）は `config.json` が単一正典。`config.json` は `<INSTALL_DIR>` 直下に決め打ち（env で場所を指さない＝鶏卵問題の回避）、`.gitignore` 除外で実体は配布されない。`session_duration_sec` 欠落は fail-fast（既定値を持たない）
- **決定論コア + エージェント判断の分離**: 三世界分類（重要度／従属度／決定論的の三世界）に基づき、スキーマ・I/O・archive はコード、判断はエージェント
- **加算バイアス回避**: 公式が持つ機能でも設計目的に不要なら入れない（YAGNI）。必要になった時点で埋める

## 2. アーキテクチャ（Clean Architecture 4層）

```
Infrastructure → Interface(Adapter) → UseCase → Domain
              依存方向: 外から内へのみ（Domain は外層を import しない）
```

| Layer | 責務 | 例 |
|---|---|---|
| **Domain** | 純粋ロジック・値オブジェクト | `TelegramUpdate` / `OutboundMessage` / `Individual` / `Task` / `Knowledge` / `MediaAttachment` / 正規化・injection フラグ |
| **UseCase** | オーケストレーション + Port 定義 | `FetchAuthorizedUpdates` / `SendReply` / 管理表 CRUD UseCase / Ports（`UpdateSource`・`MessageSink`・`OffsetStore`・各 `*Store`） |
| **Interface (Adapter)** | ゲートウェイ・ストア・CLI | `TelegramApiGateway` / `JsonStateStore` / `JsonRegistryStore`（管理表）/ `StdoutEventEmitter` / `main.py` |
| **Infrastructure** | 外部・フレームワーク・配線 | `bootstrap.sh` / `config` / `composition`（Composition Root）/ `exit_codes` / `archive_rotate.py` |

**Composition Root**: 依存組み立ては `infrastructure/composition.py` に集約する（`load_config` の fail-fast、`build_media_stack` による poll/watch 共通の media stack 構築）。各 CLI ハンドラは組み立て済みを受け取って実行に専念し、自前で adapter を new しない。終了コードは `infrastructure/exit_codes.py` が SSoT（値は外部契約＝SKILL/ROUTINE_PROMPT/SECURITY と一致）。

### 三世界分類との対応

| 世界 | LLMへの投入 | 該当 |
|---|---|---|
| **決定論の世界** | 投入しない（コード管理） | scripts 全般 — fetch / 認可 / 正規化 / 送信 / render / 管理表 I/O / archive・分割。設定の検証・読込（config.json / env）も決定論 |
| **従属度の世界** | 目的と前提のみ | ROUTINE_PROMPT（手順を委任） |
| **重要度の世界** | 質の良い長文 | エージェントの人格（本体 Identity）+ SecretaryRole。応答起草・CRUD 判断・エスカレ判断 |

**設計線**: 「何を保存するか（スキーマ）・どう保存するか（I/O）・いつ分割するか（archive）」は決定論の世界。「誰を active にするか・何を KNOWLEDGE に残すか・どう応答するか」は重要度の世界（エージェント）。この境界が管理表設計の背骨。

**keep-alive の三世界対応**: 「watch の窓満了・メッセージ駆動 exit（`WatchWindow` / `--max-duration` / `--exit-on-message`）」と「deadline 計算」は決定論的世界（コード + bash 算術、テスト可能）。「`/goal` で deadline まで各ターン watch を回し返信を起草する」運用は従属度の世界（ROUTINE_PROMPT に委任）。停止主軸を時刻（deadline）に置きポーリング回数を LLM 判断から切り離したのは、決定論をコードに寄せる本設計線の踏襲。

## 3. データアーキテクチャ（管理表 + Identities）

### 3.1 二系統のデータ

- **管理表（事実データ）**: `INDIVIDUALS`（関係者）/ `TASKS`（依頼進捗）/ `KNOWLEDGE`（対応知の蓄積、判例DB的）
- **Identities（人格定義）**: `SecretaryRole` — **これが無いとエージェントが人格的に振る舞えない**。Cloud Routine 型エージェントのロール定義ファイルと同型

### 3.2 なぜ SSoT = Private JSON か

- **Private**: 関係者情報・依頼・人格はすべて個人資産。配布物（public コード）に焼き込めば他人の手に渡る。物理分離が必然
- **JSON**: エージェント が後から必要に応じてスキーマを改変できる柔軟性。固いスキーマ言語より、判断主体（エージェント）が触れる形式が適切
- **単一正典**: 複数チャネル採用時のキャッシュ（Redis 等）は JSON のミラー（一方向 JSON→Redis）。チャネルを増やしても正典は1つ＝二重管理の破綻を防ぐ
- **運用設定 config.json も同原則**: 非秘匿の運用設定（`session_duration_sec` 等）は `config.json` が単一正典。bootstrap は config.json から deadline 等を算出して env へ一方向展開（env は派生＝二重管理にしない）。場所は `<INSTALL_DIR>` 直下に決め打ち（env で指さない＝鶏卵問題の回避）

### 3.3 なぜテンプレート/データ分離か（配布可能性の核心）

`templates/`（public、雛型）と実体（Private）を分ける。個人利用の初日からこの分離を徹底すれば、プラグイン配布は「marketplace に1エントリ追加 ＋ Private を外す」だけで済む。**配布可能性を個人利用の構造に最初から埋める**。Identities（人格）も同じ — 雛型は public、`<OWNER>` の SecretaryRole 実体は Private。

### 3.4 なぜ CRUD はエージェント主体 + `/telegram-secretary` ラップか

- **操作主体 = エージェント**: エージェント/SecretaryRole が対話の文脈で「この人を active にする」「この判断を KNOWLEDGE に残す」と判断して CRUD（重要度の世界）
- **決定論 I/O = CLI subcommand**: 実際の書き込みは決定論的世界（テスト可能）。エージェント は subcommand を呼ぶ
- **ユーザー向けにも解放**: skill / slash command として操作インターフェースを公開（人間が直接操作も可能）
- **`/telegram-secretary` で全ラップ**: マスタースキルが管理パネルとして全操作の入口。コマンド名を覚えずとも操作可能

### 3.5 なぜ肥大化対策が管理表ごとに違うか

| 管理表 | 方式 | 理由 |
|---|---|---|
| **TASKS** | 日付 Archive（done が N 日経過） | 完了タスクは「過去ログ」が自然。時系列で流れる |
| **INDIVIDUALS** | 日付 Archive（blocked + 長期非接触） | 離脱者は稀に過去ログ化 |
| **KNOWLEDGE** | **カテゴリ分割**（Archive せず） | 知識は**蓄積が本質**（判例DBは古いから捨てない）。肥大化は category 単位のシャード分割で解く |

詳細スキーマ・ディレクトリ配置は [STRUCTURE.md](./STRUCTURE.md)。

### 3.6 なぜ管理表を git で永続化するか（揮発/永続分離）

Cloud Routine は stateless（毎回 fresh clone）。揮発してよい state と、蓄積が本質の管理表は永続要件が正反対ゆえ物理分離する。

| データ | 永続要件 | 解決 |
|---|---|---|
| `offset.json` / `lease.json` / `media/` | 揮発OK | `state_dir`（Telegram ~24h 保持・lease 再取得・retention 削除で復元/破棄） |
| `individuals` / `tasks` / `knowledge` | **永続必須** | `registry_dir` を git で永続化（蓄積が本質、KNOWLEDGE は判例DB） |

**永続化方式**（`registry_sync` オプトイン、既定無効で後方互換）:

- **イベント駆動**: 管理表 add/remove のたびに固定ブランチへ commit & push。更新頻度が低く crash 耐性が高い
- **commit/push 分離**: commit はローカル即時（確実）、push は best-effort（一時失敗は次回 sync でまとめて再送、ローカル commit は積まれるのでロスは commit 前 crash の極小窓のみ）
- **固定ブランチ運用**: 専用ブランチ（`registry_branch`、既定 `claude/ts-registry`）へ push、起動時に fetch。feature ブランチ分岐や merge の手間を避ける（単一ファイル状態を持つ運用パターンの横展開）
- **force 不使用**: 複数 JSON の独立した部分更新ゆえ、force（ツリー全体置換）は他ファイルの更新を壊す。通常 push（non-fast-forward 自動拒否が競合検出を内蔵）＋ 例外時のみ `pull --rebase` フォールバック。lease がシングルライターを保証し、外部更新（手動編集等）の例外にだけ rebase で保険をかける
- **設定は config.json 正典**: `registry_sync` / `registry_dir` / `registry_branch` は非秘匿の運用設定ゆえ config.json（純2層）。Cloud Routine が fresh clone で読む

> 設計の背骨は §2「決定論コア + エージェント判断の分離」の踏襲: git 操作（commit/push/rebase/fetch）は決定論の世界（コード・テスト可能）、「何を残すか」の判断は重要度の世界（エージェント）。

---

## 4. Scope: 公式 plugin（/channels）との差分と採否

Claude 公式の Telegram plugin（`/channels`）と比較した機能採否の記録。**「公式にあるから移植する」ではなく、設計目的に照らして選択的に実装する**ための参照点（加算バイアスへの歯止め）。

凡例 — 実装: ✅ 済 / ❌ 未 / ❌(静的) 静的代替 ｜ 要否: ◎必須 ○有効 △低優先 ✕不要

| 機能 | 公式 tool | 用途 | TS 実装 | 要否 | 採否理由 |
|---|---|---|---|---|---|
| 画像/ファイル送信 | `reply(files)` | 生成物（図表/レポート/docx）を送り返す | ✅ | ◎ | write 系の中核。拡張子で sendPhoto / sendDocument に自動振り分け、`--file` 複数可 |
| typing インジケータ | `sendChatAction` | 応答までの数秒ラグの UX 緩和 | ✅ | ○ | stateless 軽量、`send_chat_action` を best-effort で送信前に発火 |
| reply threading | `reply_to` | どの発言への返信か明示 | ✅ | ○ | `reply_to_message_id` は Domain に既存、`--reply-to` 配線で完成（ほぼ無コスト） |
| **受信メディアの中身理解** | （公式になし） | voice/audio/video→transcript、docx/pptx/xlsx→markdown | ✅ | ◎ | **TS が公式を超越する強み**。公式は file_id forward + download 止まりで中身を読まない |
| 絵文字リアクション | `react` | 軽い ack（既読スタンプ） | ❌ | ✕ | 返信本文の UTF-8 絵文字で代替可。さらに **1:1 DM では bot が管理者になれず inbound reaction も構造的に受信不可** |
| 送信済み編集 | `edit_message` | 長時間タスクの進捗更新 | ❌ | ○ | 効用はあるが、`message_id` の状態管理を stateless 設計に持ち込むため見送り。必要なら独立追加 |
| markdownv2 整形 | `format` | 見出し / 強調 | ❌ | △ | MarkdownV2 は `_*[]()~>#+-=\|{}.!` 全エスケープ要で送信失敗リスク。後付け容易ゆえ YAGNI 保留 |
| pairing 認可 | access skill | 利用者を実行中に動的承認 | ❌(静的) | ✕ | 静的 allowlist（`AUTHORIZED_CHATS`）で十分 |
| bot commands | `setMyCommands` | `/` 入力でコマンド候補を表示 | ❌ | △ | 自然文で エージェント に話しかける対話型が主。コマンド体系を前面に出さない |
| sticker 受信認識 | （受信側） | sticker を認識 | ❌ | △ | inbound 拡張。必要になれば追加 |
| group @mention | group policy | グループで `@bot` 呼び出し（privacy mode） | ❌ | ✕ | 1:1 DM（`<OWNER>` との個人チャット）前提。グループ運用は想定外 |
| Cloud Routine lifecycle | （公式になし） | routine の登録 / 更新 / 停止 | ✅ | ◎ | **schedule / unschedule** で常駐 routine 自体を `RemoteTrigger` 管理（upsert / `enabled:false` 停止）。公式 `/channels` は手動登録のみ |

### 構造的要約

「公式にあって TS にない」機能は**送信側 UX 装飾**に偏り、「TS にあって公式にない」機能は**受信の中身理解**（voice/docx の transcript/md 化）に集中する。この非対称が、設計思想「秘書の価値は read 系」の裏返しとして表に出ている。

整理すると——**pairing は「誰を入れるか」、commands は「何ができるかの提示」、group は「どこで聞くか」**。TS は「`<OWNER>` と少数の関係者が、1:1 で、自然文で呼ぶ」運用に絞るため、これら3つは現状不要としている。

### 今後の判断指針

- 残った穴（`edit_message` / `bot commands` / `sticker` 認識）は、運用で実際に欲しくなった時点で埋める。「公式にあるから」を理由に先回り実装しない
- 採否が変わったら本表を更新する
