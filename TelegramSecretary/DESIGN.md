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
| **Domain** | 純粋ロジック・値オブジェクト | `TelegramUpdate` / `OutboundMessage` / `Individual` / `Identity` / `Task` / `Knowledge` / `Ability` / `MediaAttachment` / 正規化・injection フラグ |
| **UseCase** | オーケストレーション + Port 定義 | `FetchAuthorizedUpdates` / `SendReply` / 管理表 CRUD UseCase / Ports（`UpdateSource`・`MessageSink`・`OffsetStore`・各 `*Store`） |
| **Interface (Adapter)** | ゲートウェイ・ストア・CLI | `TelegramApiGateway` / `JsonStateStore` / `JsonRegistryStore`（管理表）/ `StdoutEventEmitter` / `main.py` |
| **Infrastructure** | 外部・フレームワーク・配線 | `bootstrap.sh` / `config` / `composition`（Composition Root）/ `exit_codes` / `archive_rotate.py` |

**Composition Root**: 依存組み立ては `infrastructure/composition.py` に集約する（`load_config` の fail-fast、`build_media_stack` による poll/watch 共通の media stack 構築）。各 CLI ハンドラは組み立て済みを受け取って実行に専念し、自前で adapter を new しない。終了コードは `infrastructure/exit_codes.py` が SSoT（値は外部契約＝SKILL/ROUTINE_PROMPT/SECURITY と一致）。

### 三世界分類との対応

| 世界 | LLMへの投入 | 該当 |
|---|---|---|
| **決定論の世界** | 投入しない（コード管理） | scripts 全般 — fetch / 認可 / 正規化 / 送信 / render / 管理表 I/O・archive/分割の純関数。設定の検証・読込（config.json / env）も決定論 |
| **従属度の世界** | 目的と前提のみ | ROUTINE_PROMPT（手順を委任） |
| **重要度の世界** | 質の良い長文 | エージェントの人格（本体 Identity）+ SecretaryRole。応答起草・CRUD 判断・エスカレ判断・archive/分割の発火判断（いつ・どの単位で） |

**設計線**: 「どう保存するか（スキーマの I/O）・分割を計算する純関数」は決定論の世界。「誰を active にするか・何を KNOWLEDGE に残すか・**いつ・どの単位で archive/分割するか**・どう応答するか」は重要度の世界（エージェント）。**情報の持ち方は情報の主体（エージェント）が決める**——archive は LLM タスクであり、決定論的に自動実行しない。コードは純関数（`archive_rotate.py`）と I/O を道具として提供し、発火と単位の判断はエージェントが担う。この境界が管理表設計の背骨。

**keep-alive の三世界対応**: 「watch の窓満了・メッセージ駆動 exit（`WatchWindow` / `--max-duration` / `--exit-on-message`）」と「deadline 計算」は決定論的世界（コード + bash 算術、テスト可能）。「`/goal` で deadline まで各ターン watch を回し返信を起草する」運用は従属度の世界（ROUTINE_PROMPT に委任）。停止主軸を時刻（deadline）に置きポーリング回数を LLM 判断から切り離したのは、決定論をコードに寄せる本設計線の踏襲。

## 3. データアーキテクチャ（管理表 + Identities）

### 3.1 二系統のデータ

- **管理表（4 表）**: `INDIVIDUALS`（関係者）/ `TASKS`（依頼進捗）/ `KNOWLEDGE`（対応知の蓄積、判例DB的）の事実データ3表 + `ABILITIES`（秘書が行使できる能力カタログ、§3.8）
- **Identities（人格定義）**: `SecretaryRole` — **これが無いとエージェントが人格的に振る舞えない**。cloud routine 型エージェントのロール定義ファイルと同型

### 3.2 なぜ SSoT = Private JSON か

- **Private**: 関係者情報・依頼・人格はすべて個人資産。配布物（public コード）に焼き込めば他人の手に渡る。物理分離が必然
- **JSON**: エージェントが後から必要に応じてスキーマを改変できる柔軟性。固いスキーマ言語より、判断主体（エージェント）が触れる形式が適切
- **単一正典**: 複数チャネル採用時のキャッシュ（Redis 等）は JSON のミラー（一方向 JSON→Redis）。チャネルを増やしても正典は1つ＝二重管理の破綻を防ぐ
- **運用設定 config.json も同原則**: 非秘匿の運用設定（`session_duration_sec` 等）は `config.json` が単一正典。bootstrap は config.json から deadline 等を算出して env へ一方向展開（env は派生＝二重管理にしない）。場所は `<INSTALL_DIR>` 直下に決め打ち（env で指さない＝鶏卵問題の回避）

### 3.3 なぜテンプレート/データ分離か（配布可能性の核心）

`templates/`（public、雛型）と実体（Private）を分ける。個人利用の初日からこの分離を徹底すれば、プラグイン配布は「marketplace に1エントリ追加 ＋ Private を外す」だけで済む。**配布可能性を個人利用の構造に最初から埋める**。Identities（人格）も同じ — 雛型は public、`<OWNER>` の SecretaryRole 実体は Private。

### 3.4 なぜ CRUD はエージェント主体 + `/telegram-secretary` ラップか

- **操作主体 = エージェント**: エージェント/SecretaryRole が対話の文脈で「この人を active にする」「この判断を KNOWLEDGE に残す」と判断して CRUD（重要度の世界）
- **決定論 I/O = CLI subcommand**: 実際の書き込みは決定論的世界（テスト可能）。エージェントは subcommand を呼ぶ
- **ユーザー向けにも解放**: skill / slash command として操作インターフェースを公開（人間が直接操作も可能）
- **`/telegram-secretary` で全ラップ**: マスタースキルが管理パネルとして全操作の入口。コマンド名を覚えずとも操作可能

### 3.5 なぜ肥大化対策が管理表ごとに違うか（発火判断は重要度の世界）

肥大化対策の「**いつ・どの単位で分割/archive するか**」は重要度の世界（エージェント判断）——情報の持ち方は情報の主体が決める。以下は既定のベストプラクティス（方針）であり、エージェントが文脈に応じて単位や閾値を変えてよい。コードは `archive_rotate.py` の純関数（`partition_for_archive` / `split_by_category`）と `JsonRegistryStore` の I/O を**道具**として提供し、決定論的な自動実行（subcommand）は持たない。

| 管理表 | 方式（既定方針） | 理由 |
|---|---|---|
| **TASKS** | 日付 Archive（done が N 日経過） | 完了タスクは「過去ログ」が自然。時系列で流れる |
| **INDIVIDUALS** | 日付 Archive（blocked + 長期非接触） | 離脱者は稀に過去ログ化 |
| **KNOWLEDGE** | **カテゴリ分割**（Archive せず） | 知識は**蓄積が本質**（判例DBは古いから捨てない）。肥大化は category 単位のシャード分割で解く |
| **ABILITIES** | **カテゴリ分割**（Archive せず、KNOWLEDGE と同型） | 能力カタログも蓄積が本質（捨てない）。分割の単位・キーは必要時にエージェントが定義（§3.2 の JSON 柔軟性） |

詳細スキーマ・ディレクトリ配置は [STRUCTURE.md](./STRUCTURE.md)。

### 3.6 なぜ管理表を git で永続化するか（揮発/永続分離）

**Claude Code Routines**（Anthropic のクラウド実行＝cloud routine）は stateless（毎回 fresh clone）。揮発してよい state と、蓄積が本質の管理表は永続要件が正反対ゆえ物理分離する。

| データ | 永続要件 | 解決 |
|---|---|---|
| `offset.json` / `lease.json` / `media/` | 揮発OK | `state_dir`（Telegram ~24h 保持・lease 再取得・retention 削除で復元/破棄） |
| `individuals` / `tasks` / `knowledge` / `abilities` | **永続必須** | `registry_dir` を git で永続化（蓄積が本質、KNOWLEDGE は判例DB、ABILITIES は能力カタログ） |

**永続化方式**（`registry_sync` オプトイン、既定無効で後方互換）:

- **イベント駆動**: 管理表 add/remove のたびに固定ブランチへ commit & push。更新頻度が低く crash 耐性が高い
- **commit/push 分離**: commit はローカル即時（確実）、push は best-effort（一時失敗は次回 sync でまとめて再送、ローカル commit は積まれるのでロスは commit 前 crash の極小窓のみ）
- **固定ブランチ運用**: 専用ブランチ（`registry_branch`、既定 `claude/ts-registry`）へ push、起動時に fetch。feature ブランチ分岐や merge の手間を避ける（単一ファイル状態を持つ運用パターンの横展開）
- **force 不使用**: 複数 JSON の独立した部分更新ゆえ、force（ツリー全体置換）は他ファイルの更新を壊す。通常 push（non-fast-forward 自動拒否が競合検出を内蔵）＋ 例外時のみ `pull --rebase` フォールバック。lease がシングルライターを保証し、外部更新（手動編集等）の例外にだけ rebase で保険をかける
- **設定は config.json 正典**: `registry_sync` / `registry_dir` / `registry_branch` は非秘匿の運用設定ゆえ config.json（純2層）。cloud routine が fresh clone で読む

> 設計の背骨は §2「決定論コア + エージェント判断の分離」の踏襲: git 操作（commit/push/rebase/fetch）は決定論の世界（コード・テスト可能）、「何を残すか」の判断は重要度の世界（エージェント）。

### 3.7 なぜ WAL（Write-Ahead Log）で言行一致を保証するか（consistency vs durability）

§3.6 の registry 永続化は push が **best-effort**（一時失敗は次回再送）。これは durability（データを失わない）には十分だが、**consistency（対外的な約束と内部状態の一致）には穴がある**: 秘書が「登録しました」と返信した後にコンテナが強制終了され push が漏れると、「言ったのに registry に無い」言行不一致が起きうる。これは冗長化でなく**順序**（WAL）で解く。

- **先行書込**: 内部状態の変更を約束する返信の**前に**、intent を WAL ログ（`registry_dir/wal/WAL.jsonl`、registry と同一固定ブランチ）へ追記し push する
- **must-succeed push（送信前ゲート）**: WAL ログ push は redo のソースゆえ best-effort では不可。push 成功まで send-reply を打たない＝**push できないなら約束もしない**（矛盾が表面化する前に止まる）。registry の add 自体は従来どおり best-effort（漏れても redo される側）
- **起動時 redo**: 次回起動で WAL の pending（registry に無いやり残し）を registry へ upsert（key 冪等）。registry-sync（fetch）の**後**に置き最新 registry で照合。**返信は再送しない**——送信前クラッシュ分は offset 再取得が再処理を担う（役割分担: offset=メッセージ再処理、WAL=送信後の registry 漏れ専任）。※この「返信は再送しない」は **inbound 返信に固有の前提**であり、offset 安全網を持たない proactive-send（能動 push）にはそのまま適用できない。outbound 経路にだけ WAL 再送を足す整合的拡張は §3.9 を参照
- **二重役割**: ログは WAL（整合性＝pending redo）と短期記憶（直近 24h の会話文脈、起動時に読む）を兼ねる。pending は無条件保持（redo ソース）、done は起動時チェックポイントで 24h 掃除（ローテーションを終了処理に依存させない＝強制終了で飛ばない）

> consistency と durability は別問題: durability の穴は冗長で塞ぐが、ここでの穴は「同一障害ドメイン（同じ git push）に冗長を足しても共倒れ」ゆえ順序で塞ぐ。設計の背骨は §2 の踏襲——WAL の純粋ロジック（reconcile/settle/checkpoint）は Domain、push/redo の順序遵守は ROUTINE_PROMPT（従属度の世界）、git 操作は決定論。`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。

### 3.8 なぜ abilities を4表目として追加したか（能力カタログ・データ層での能力拡張）

individuals/tasks/knowledge が「事実データ」（誰と・何を頼まれ・どう判断したか）であるのに対し、`abilities` は秘書が**行使できる能力（スキル）のカタログ**——「何ができるか」を担う第4の管理表。各レコードは発動シグナル（`trigger`）・スキル実体への相対パス（`skill_path`）・起動ガイダンス（`guidance`）を持ち、秘書は応答前に `abilities list` で「この依頼に使える能力があるか」を引き、該当すれば外部スキル（例: 占術鑑定）を行使する。

- **なぜ registry 4表目か（同格）**: 能力も「秘書が判断して蓄積し、参照する」点で事実データ3表と同型。テーブル駆動の `_REGISTRY_SPEC` に1種別 + `Ability` 値オブジェクトを足すだけで CRUD・検証・git 永続化・起動時 fetch が付く（§2「決定論コア + エージェント判断の分離」をそのまま継承）。read 配線は ROUTINE_PROMPT の4表オリエンテーションで「応答前に引く」運用として明示
- **なぜ WAL 対象か**: WAL（§3.7）は「『登録しました』と相手に約束した返信」と内部状態の consistency を守る機構。abilities の `add` も「『○○できます』と能力を相手に宣言する返信」を伴いうる——宣言したのに push 漏れで ABILITIES に無ければ、次の器は「できると言ったのに登録されていない」言行不一致に陥る。individuals/tasks/knowledge と同型ゆえ、4表すべてを一様に WAL 保護対象とする（`_WAL_KINDS` は `_REGISTRY_SPEC` 全種別）。永続化は §3.6 の git sync が durability を、WAL が consistency を担う
- **なぜデータ層で能力拡張か（本質）**: 能力を ROUTINE_PROMPT（手順骨格＝稼働 body）でなく ABILITIES.json（データ）に置くことで、**稼働 body を触らずに能力を追加できる**。read 配線を一度通せば、以後の能力追加は Private の ABILITIES.json 更新（git push）だけで済み、cloud routine の prompt body 再登録（`RemoteTrigger update` の罠を踏むリスク）が不要になる。三世界分類で言えば、手順骨格（従属度の世界＝ROUTINE_PROMPT）は安定させ、可変の能力カタログを決定論の世界（データ）へ逃がす設計
- **配布可能性（母集団スコープ）**: 配布 template（`ABILITIES.template.json`）には具体能力を焼かず空で配る。運用固有の能力（例: 占術スキル連携）は Private の実 ABILITIES.json に置く——§3.3 のテンプレート/データ分離を能力にも適用
- **能力の自己追記ガード**: 秘書が能力を `add` するのは**実在を確認したスキルに限る**（不確実・未検証の能力は宣言しない＝存在しない能力をカタログに書くハルシネーションの防止）

### 3.9 なぜ outbound（proactive-send）に WAL 再送を足すのか（offset 安全網の無い経路の冪等性）★再送方針 SSoT

秘書は基本 inbound（受信→返信）だが、口頭での権限 grant（例: 自由時間の付与）により **outbound（能動 push＝proactive-send）** も担う（能力境界の SSoT は SecretaryRole）。pull 口（getUpdates）に push を足すことで対話チャネルが双方向化する。この outbound 経路は、§3.7 が前提にした冪等性の安全網（offset）を構造的に持たないため、WAL 再送の扱いが inbound と異なる。本節を **再送方針の SSoT** とし、他ドキュメント（SKILL / ROUTINE_PROMPT / CHANGELOG）は要約 + 本節へのポインタに留める。

- **なぜ offset 非干渉が不変条件か**: `ProactiveSend` は `SendReply` から `OffsetStore` 依存と offset advance を除いた姉妹 UseCase。offset は **inbound 専用の既読台帳**ゆえ、outbound がこれに触れると「advance して未読 inbound を取りこぼす」事故が起きうる。依存に持たない（提供する手段が無い）ことで構造的に封じる——壊しようがない設計。lease 検証→添付検証→送信→lease renew の順序と「送信失敗時は据え置き」不変条件は `SendReply` から継承する
- **なぜ §3.7 を破壊しない整合的拡張か（論証核）**: §3.7 が「WAL は送信後の registry 漏れ専任、**返信は再送しない**」と言えたのは、**inbound 返信には offset という安全網がある**ため——`update_id` を advance しなければ次回 cron の getUpdates が同じメッセージを再取得し、自然に再送される。ところが proactive-send は inbound に紐づかない＝**トリガとなる `update_id` が存在しない**＝offset 安全網が構造的に無い。送信前にクラッシュすれば、その「送ろうとした意図」は二度と再現されない。よって outbound では **WAL 再送が唯一の冪等性保証**になる。§3.7 を覆すのではなく「offset 安全網の無い経路にだけ WAL 再送を足す」——前提（安全網の有無）が違うから処方が違う、という整合的拡張である（§3.7 inbound の結論はそのまま保つ）
- **なぜ冪等性は at-least-once か（exactly-once を追わない）**: 買える保証は at-least-once。送信成功と done 記録の間にクラッシュすれば重複しうるが、これを技術（TTL / content-hash dedup / 二相コミット）で潰さず、**再送時に元の送信予定時刻＋謝罪プレフィックス**（`[<created_at>] に送ろうとした件、システムが落ちていたので念のため再送します`）を本文頭に付して「受け手の混乱」を**社会レイヤで無害化**する。鮮度の判断（古い push を今受け取ってよいか）は人間に委ね、policy をコードに持たない（§3.6/§3.7 の決定論コア + エージェント判断の踏襲）
- **なぜ再送→即 done か（無限再送ループの防止）**: outbound kind は registry key を持たない（reconcile/settle の照合経路に乗らない）ため、redo は独立ループで「pending を1回だけ再送 → 即 `mark_done`」する。done 化を再送と同一トランザクション内に置くことで、次回起動でその intent が再び pending として拾われない＝無限再送を防ぐ。TTL（鮮度切れ破棄）を持たないのはこのため——再送回数を1回に固定すれば TTL なしでも暴発しない。`wal-append --kind outbound` は registry key が無いので `created_at` をキーにし（`chat_id` 必須）、registry redo と独立して扱う
- **送信前ゲートと PII 範囲**: outbound も registry kind と同じく `wal-append`（pending）→ `wal-push`（must-succeed）→ `proactive-send` の順で、push できなければ送信もしない（§3.7 の送信前ゲートを共有）。WAL payload は送信本文 + 添付パス + chat_id に限り、会話本文全体は載せない（SECURITY §7 の PII 範囲に準ずる）

> 設計の背骨は §2 / §3.7 の踏襲——WAL の純粋ロジック（reconcile/settle/checkpoint と outbound の二分）は Domain・UseCase、push/redo の順序遵守と「親性ゲートで何を能動送信するか」の判断は ROUTINE_PROMPT（従属度の世界）、git 操作と送信は決定論。`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。

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
| bot commands | `setMyCommands` | `/` 入力でコマンド候補を表示 | ❌ | △ | 自然文で エージェントに話しかける対話型が主。コマンド体系を前面に出さない |
| sticker 受信認識 | （受信側） | sticker を認識 | ❌ | △ | inbound 拡張。必要になれば追加 |
| group @mention | group policy | グループで `@bot` 呼び出し（privacy mode） | ❌ | ✕ | 1:1 DM（`<OWNER>` との個人チャット）前提。グループ運用は想定外 |
| cloud routine lifecycle | （公式になし） | routine の登録 / 更新 / 停止 | ✅ | ◎ | **schedule / unschedule** で常駐 routine 自体を `RemoteTrigger` 管理（upsert / `enabled:false` 停止）。公式 `/channels` は手動登録のみ |

### 構造的要約

「公式にあって TS にない」機能は**送信側 UX 装飾**に偏り、「TS にあって公式にない」機能は**受信の中身理解**（voice/docx の transcript/md 化）に集中する。この非対称が、設計思想「秘書の価値は read 系」の裏返しとして表に出ている。

整理すると——**pairing は「誰を入れるか」、commands は「何ができるかの提示」、group は「どこで聞くか」**。TS は「`<OWNER>` と少数の関係者が、1:1 で、自然文で呼ぶ」運用に絞るため、これら3つは現状不要としている。

### 今後の判断指針

- 残った穴（`edit_message` / `bot commands` / `sticker` 認識）は、運用で実際に欲しくなった時点で埋める。「公式にあるから」を理由に先回り実装しない
- 採否が変わったら本表を更新する
