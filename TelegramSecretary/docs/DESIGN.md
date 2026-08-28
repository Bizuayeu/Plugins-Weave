# TelegramSecretary 設計正典（DESIGN）

設計の **why** を集約する。役割分担 — **DESIGN**=なぜこの設計か / **STRUCTURE**=どこに何を置くか。

## 目次

- [1. 設計原則](#1-設計原則)
- [2. アーキテクチャ（Clean Architecture 4層）](#2-アーキテクチャclean-architecture-4層)
  - [三世界分類との対応](#三世界分類との対応)
- [3. データアーキテクチャ（管理表 + Identities）](#3-データアーキテクチャ管理表--identities)
  - [3.1 二系統のデータ](#31-二系統のデータ)
  - [3.2 なぜ SSoT = Private JSON か](#32-なぜ-ssot--private-json-か)
  - [3.3 なぜテンプレート/データ分離か（配布可能性の核心）](#33-なぜテンプレートデータ分離か配布可能性の核心)
  - [3.4 なぜ CRUD はエージェント主体 + `/telegram-secretary` ラップか](#34-なぜ-crud-はエージェント主体--telegram-secretary-ラップか)
  - [3.5 なぜ肥大化対策が管理表ごとに違うか（発火判断は重要度の世界）](#35-なぜ肥大化対策が管理表ごとに違うか発火判断は重要度の世界)
  - [3.6 なぜ管理表を git で永続化するか（揮発/永続分離）](#36-なぜ管理表を-git-で永続化するか揮発永続分離)
  - [3.7 なぜ WAL（Write-Ahead Log）で言行一致を保証するか（consistency vs durability）★WAL 設計根拠 SSoT](#37-なぜ-walwrite-ahead-logで言行一致を保証するかconsistency-vs-durabilitywal-設計根拠-ssot)
  - [3.8 なぜ管理表を足すのが 1 行で済むか（abilities 4 表目・subjects 8 表目）](#38-なぜ管理表を足すのが-1-行で済むかabilities-4-表目subjects-8-表目)
  - [3.9 なぜ outbound（proactive-send）に WAL 再送を足すのか（offset 安全網の無い経路の冪等性）★再送方針 SSoT](#39-なぜ-outboundproactive-sendに-wal-再送を足すのかoffset-安全網の無い経路の冪等性再送方針-ssot)
  - [3.10 なぜ artifacts を成果物層として持つか（決定論の管理表と分ける理由）](#310-なぜ-artifacts-を成果物層として持つか決定論の管理表と分ける理由)
  - [3.11 なぜ P×A 直交2軸で役割が進化するか（PROFILE/GOALS/STEPS・データ駆動判定・占術スキル接続）](#311-なぜ-pa-直交2軸で役割が進化するかprofilegoalsstepsデータ駆動判定占術スキル接続)
  - [3.12 なぜ起動時ロードは orientation ダイジェストか（沈黙失敗と上流配置）★起動時オリエンテーション SSoT](#312-なぜ起動時ロードは-orientation-ダイジェストか沈黙失敗と上流配置起動時オリエンテーション-ssot)
- [4. Scope: 公式 plugin（/channels）との差分と採否](#4-scope-公式-pluginchannelsとの差分と採否)
  - [構造的要約](#構造的要約)
  - [今後の判断指針](#今後の判断指針)

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

- **管理表（8 表）**: `INDIVIDUALS`（関係者）/ `TASKS`（依頼進捗）/ `KNOWLEDGE`（対応知の蓄積、判例DB的）の事実データ3表 + `SUBJECTS`（主題の語彙表＝KNOWLEDGE を引く軸、§3.8）+ `ABILITIES`（秘書が行使できる能力カタログ、§3.8）+ `PROFILE`（人物理解＝P軸）/ `GOALS`（目標＝A軸）/ `STEPS`（逆算ステップ）の役割進化3表（§3.11）
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
| **TASKS** | 日付 Archive（done / cancelled が N 日経過） | 閉じたタスクは「過去ログ」が自然。時系列で流れる |
| **INDIVIDUALS** | 日付 Archive（blocked + 長期非接触） | 離脱者は稀に過去ログ化 |
| **KNOWLEDGE** | **カテゴリ分割**（Archive せず） | 知識は**蓄積が本質**（判例DBは古いから捨てない）。肥大化は category 単位のシャード分割で解く |
| **ABILITIES** | **カテゴリ分割**（Archive せず、KNOWLEDGE と同型） | 能力カタログも蓄積が本質（捨てない）。分割の単位・キーは必要時にエージェントが定義（§3.2 の JSON 柔軟性） |
| **SUBJECTS** | 分割も Archive もしない（`status=deprecated` で廃止） | 語彙表は**件数が増えない設計**（増やすより育てる）。消すと過去レコードの主題が読めなくなるため、退場は削除でなく status |

**蓄積の肥大化と digest の肥大化は別の問題**（上表は前者）。後者——起動時 orientation の出力が育って退避圏に入る——には**表ごとの処方**で対処し、v1.10.0 で 8 表すべてに処方が付いた（**表と処方の対応は §3.12 の 8 行表が SSoT**。下表は蓄積側の表と並べるための対応）：

| 管理表 | digest 側の絞り | 当たる先 |
|---|---|---|
| **KNOWLEDGE** | `--knowledge-latest` / `--knowledge-category` / `--knowledge-subject` | 索引行の件数（`content` は元から載らない） |
| **TASKS** | `--notes-tail` / `--tasks-latest` | active の notes 末尾 / 一行要約の件数 |
| **PROFILE** | `--profile-cap` | `content`（v1.9.0） |
| **ABILITIES** | `--abilities-cap` | `guidance`（v1.9.0） |
| **INDIVIDUALS** | `--individuals-cap` | `identity.context_notes`（v1.9.0） |
| **GOALS** | `--goals-cap` | `notes`（v1.10.0） |
| **STEPS** | `--steps-latest` | 索引行の件数（v1.10.0。`notes` は元から載らない） |
| **SUBJECTS** | 件数絞りは持たない（索引化で有界、v1.10.0） | `note` 列の幅（主題を選ぶ一覧ゆえ母数は減らさない） |

cap が当たるのは**表の支配的長文フィールド 1 つだけ**で、レコードの JSON 構造は壊さない——丸めても個票は `get --key` で全文が引ける、という読み筋を温存するため。丸めの規約（UTF-8 バイト・文字境界・マーカーは幅の内側・非正は全捨て）は幅ノブと共通（§3.12）。

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

**registry_dir は独立 git 作業ツリー（worktree）であること**（worktree provisioning 3層・2026-06-05 インシデント恒久対策、本項が SSoT）:

`registry_dir` を Private dev リポの**サブディレクトリ**（例 `<PRIVATE_REPO>/TelegramSecretary/registry`）に置くと2つの欠陥が同時に出る——起動時 fetch の `checkout -B` が**親リポ全体のブランチを切替えて dev ツリーを破壊**（欠陥2）、かつ cloud routine の fresh clone では registry_dir が不在で `cwd=registry_dir` の git が `OSError`（欠陥1）。結果、**4管理表が空のまま「記憶なし」稼働**する事故が起きた（T0002 誤答・grant 未ロード）。registry_dir を**独立した第二 worktree**にして3層で根治する：

- **層1（根治）** `bootstrap.sh`: `registry_dir` を Private リポの第二 worktree として冪等 provisioning（`git worktree add -B <branch> <registry_dir> origin/<branch>`、既存なら `checkout -B origin/<branch>` でリフレッシュ）。常に `origin/<branch>` 強制＝SSoT は origin、古いローカルブランチを掴まない。失敗は `_ts_die` せず継続し層3 が警告（graceful）
- **層2（防御）** `GitCliAdapter.fetch_checkout`: `checkout -B` の**前に** `rev-parse --show-toplevel == registry_dir` を検証、不一致なら `RegistryWorktreeError`（`GitSyncError` サブクラス）で停止＝親リポ誤爆を構造的に禁止
- **層3（可観測）** `run_registry_fetch`: fetch 失敗時に「EMPTY tables＝記憶なし稼働」を WARNING 出力（exit code 不変、principal 一報は ROUTINE_PROMPT へ委譲）＝沈黙の空表稼働を可視化

固定ブランチ `claude/ts-registry` は **registry 専用 orphan ブランチ**として **root 直下に registry 関連のみ**——全管理表（`individuals/ tasks/ knowledge/ subjects/ abilities/ profile/ goals/ steps/`）＋ `wal/`（言行一致の機構ログ、§3.7）＋ `artifacts/`（秘書の成果物層、§3.10）——を持つ（旧: Private 全ツリー＋`TelegramSecretary/registry/` ネスト → 新: フラット）。これで第二 worktree が registry だけを最小展開し dev ツリーと干渉しない。**方式B（単一 worktree）**を Stage 1 spike で確定し、本番稼働（post-fix の cloud run が provisioning→fetch→write→push を完走）で実証済み。

> 設計の背骨は §2「決定論コア + エージェント判断の分離」の踏襲: git 操作（commit/push/rebase/fetch）は決定論の世界（コード・テスト可能）、「何を残すか」の判断は重要度の世界（エージェント）。

> **cloud routine harness の作業ブランチについて**: cloud routine は session ごとに `<registry_branch>-<ランダム SUFFIX>`（例 `claude/ts-registry-AbCdE`）の作業ブランチをローカルに自動生成する。一方 registry_sync は `git push HEAD:<registry_branch>`（SUFFIX なし）で固定ブランチへ直接 push するため、管理表は常に1本（`registry_branch`）へ集約される。**harness 作業ブランチは commit が乗った時だけ GitHub に push される**ので、registry_cli 以外で git commit しない限り（＝作業ブランチが空のまま）リモートに残骸は生じない。`<registry_branch>-XXXXX` がリモートに増えていたら、それは session 中に registry_cli を通さない手動 commit が乗ったサイン——削除は手動掃除（`gh api -X DELETE .../git/refs/heads/<branch>`）で足り、毎 session の常設削除処理は要らない。

### 3.7 なぜ WAL（Write-Ahead Log）で言行一致を保証するか（consistency vs durability）★WAL 設計根拠 SSoT

§3.6 の registry 永続化は push が **best-effort**（一時失敗は次回再送）。これは durability（データを失わない）には十分だが、**consistency（対外的な約束と内部状態の一致）には穴がある**: 秘書が「登録しました」と返信した後にコンテナが強制終了され push が漏れると、「言ったのに registry に無い」言行不一致が起きうる。これは冗長化でなく**順序**（WAL）で解く。

- **先行書込**: 内部状態の変更を約束する返信の**前に**、intent を WAL ログ（`registry_dir/wal/WAL.jsonl`、registry と同一固定ブランチ）へ追記し push する
- **must-succeed push（送信前ゲート）**: WAL ログ push は redo のソースゆえ best-effort では不可。push 成功まで send-reply を打たない＝**push できないなら約束もしない**（矛盾が表面化する前に止まる）。registry の add 自体は従来どおり best-effort（漏れても redo される側）
- **起動時 redo**: 次回起動で WAL の pending（registry に無いやり残し）を registry へ upsert（key 冪等）。registry-sync（fetch）の**後**に置き最新 registry で照合。**返信は再送しない**——送信前クラッシュ分は offset 再取得が再処理を担う（役割分担: offset=メッセージ再処理、WAL=送信後の registry 漏れ専任）。※この「返信は再送しない」は **inbound 返信に固有の前提**であり、offset 安全網を持たない proactive-send（能動 push）にはそのまま適用できない。outbound 経路にだけ WAL 再送を足す整合的拡張は §3.9 を参照。redo が registry へ書く前に、payload は次項の関門を通る
- **検証は一つ、書き込み口はどれも同じ関門を通る（v1.11.0）**: registry への書き込み口は `add` / `import` / `wal-redo` の三口で、これに WAL の入口 `wal-append` を足した**四つが `registry_cli.canonical_record` 一つを呼ぶ**——未知トップレベルキー・語彙外 subject・許可集合外 category を弾き、値オブジェクトを通した正準形（`from_dict` → `to_dict`）を返す同一の関門である。検証を口ごとに書けば、口を増やすたびに「そこだけ緩い」抜け道が増える。WAL は must-succeed push で remote へ出る**片道の口**ゆえ、不正を redo まで持ち越すと「push 済みなのに永久に反映されない intent」が残る——入口で弾けば運用者はその場で書き直せる（`wal-append` は exit 2 で、ログを書く前に止まる）。読み側（`list` / `get` / `orientation`）は従来どおり fail-open のまま（write / read の非対称は §3.8）
- **dead は未履行の約束の記録であって redo ソースではない（v1.11.0）**: `wal-redo` の検証で落ちた pending は registry へ書かず `status=dead` へ隔離し、理由（例外型名＋メッセージ先頭を既存の topic 幅で切り詰め＝payload の値を残さない）を添える。dead を**再検証しない**のは、それが redo の入力ではなく「果たされていない約束がここに在る」という記録だからである。exit は 0 のまま（起動経路を止めない）で、残存する dead は毎起動 stderr へ 1 行ずつ出る。出口は二つ——同じ key の正しい `add` が入れば `settle` が done 化する（自己治癒）か、履行しないと決めたなら `wal-drop --kind --key` で畳む。**pending を落とす口は作らない**（果たされていない約束を黙って捨てる操作を持たせない。秘書倫理としての SSoT は SecretaryRole の「言行一致」）
- **二重役割**: ログは WAL（整合性＝pending redo）と短期記憶（直近 24h の会話文脈、起動時に読む）を兼ねる。保持は状態ごとに違う——**pending は無条件保持**（redo ソース）、**dead も無条件保持**（期限を置かず、上記の二つの出口でだけ消える）、**done だけ**が起動時チェックポイントで 24h 掃除（ローテーションを終了処理に依存させない＝強制終了で飛ばない）
- **守備範囲は key の存在であって内容ではない（★誤解しやすい境界）**: `reconcile` / `settle` の判定は `(kind, key)` が registry にあるかだけで、payload の中身は見ない。ゆえに**既存レコードの内容更新——例えば既にある tasks の `notes` への追記——は WAL では守れない**。intent を積んでも key は既に在るので redo の対象にならず、それどころか `settle` が「registry に在る」を根拠に done 化する＝**反映されていないのに反映済みに見える**（偽陽性）。WAL が塞ぐのは「約束したレコードが存在しない」穴だけで、「約束した内容が入っていない」穴は塞がない。後者に冗長も再送も効かず、順序——送信と記録を同じ手順の内側で連続させる——でしか塞げない（秘書倫理としての SSoT は SecretaryRole の「言行一致」）

> consistency と durability は別問題: durability の穴は冗長で塞ぐが、ここでの穴は「同一障害ドメイン（同じ git push）に冗長を足しても共倒れ」ゆえ順序で塞ぐ。設計の背骨は §2 の踏襲——WAL の純粋ロジック（reconcile/settle/checkpoint/quarantine）は Domain、push/redo の順序遵守は ROUTINE_PROMPT（従属度の世界）、git 操作は決定論。`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。

### 3.8 なぜ管理表を足すのが 1 行で済むか（abilities 4 表目・subjects 8 表目）

表を足す判断は 2 度あり、どちらも同じ骨格で通った——テーブル駆動の `REGISTRY_SPEC` に 1 行、値オブジェクトを 1 つ。以下は各表の追加理由（なぜその表が要るか）と、そこから引き出された一般則（何をコードに置き、何をデータに置くか）。

#### abilities（能力カタログ、4 表目）——データ層での能力拡張

individuals/tasks/knowledge が「事実データ」（誰と・何を頼まれ・どう判断したか）であるのに対し、`abilities` は秘書が**行使できる能力（スキル）のカタログ**——「何ができるか」を担う第4の管理表。各レコードは発動シグナル（`trigger`）・スキル実体への相対パス（`skill_path`）・起動ガイダンス（`guidance`）を持ち、秘書は応答前に `abilities list` で「この依頼に使える能力があるか」を引き、該当すれば外部スキル（例: 占術鑑定）を行使する。

- **なぜ registry 4表目か（同格）**: 能力も「秘書が判断して蓄積し、参照する」点で事実データ3表と同型。テーブル駆動の `_REGISTRY_SPEC` に1種別 + `Ability` 値オブジェクトを足すだけで CRUD・検証・git 永続化・起動時 fetch が付く（§2「決定論コア + エージェント判断の分離」をそのまま継承）。read 配線は ROUTINE_PROMPT の4表オリエンテーションで「応答前に引く」運用として明示
- **なぜ WAL 対象か**: WAL（§3.7）は「『登録しました』と相手に約束した返信」と内部状態の consistency を守る機構。abilities の `add` も「『○○できます』と能力を相手に宣言する返信」を伴いうる——宣言したのに push 漏れで ABILITIES に無ければ、次の器は「できると言ったのに登録されていない」言行不一致に陥る。individuals/tasks/knowledge と同型ゆえ、4表すべてを一様に WAL 保護対象とする（`_WAL_KINDS` は `_REGISTRY_SPEC` 全種別）。永続化は §3.6 の git sync が durability を、WAL が consistency を担う
- **なぜデータ層で能力拡張か（本質）**: 能力を ROUTINE_PROMPT（手順骨格＝稼働 body）でなく ABILITIES.json（データ）に置くことで、**稼働 body を触らずに能力を追加できる**。read 配線を一度通せば、以後の能力追加は Private の ABILITIES.json 更新（git push）だけで済み、cloud routine の prompt body 再登録（`RemoteTrigger update` の罠を踏むリスク）が不要になる。三世界分類で言えば、手順骨格（従属度の世界＝ROUTINE_PROMPT）は安定させ、可変の能力カタログを決定論の世界（データ）へ逃がす設計
- **配布可能性（母集団スコープ）**: 配布 template（`ABILITIES.template.json`）には具体能力を焼かず空で配る。運用固有の能力（例: 占術スキル連携）は Private の実 ABILITIES.json に置く——§3.3 のテンプレート/データ分離を能力にも適用
- **能力の自己追記ガード**: 秘書が能力を `add` するのは**実在を確認したスキルに限る**（不確実・未検証の能力は宣言しない＝存在しない能力をカタログに書くハルシネーションの防止）

#### subjects（主題語彙、8 表目）——閉じた語彙はコード、開いた語彙はデータ

`SUBJECTS` は主題（馬・建設・製造…）の語彙表で、`KNOWLEDGE.subjects[]` の照合先。abilities が「何ができるか」を持つのに対し、subjects が持つのは**知識を引く軸**そのものである。

- **なぜ category（コード）と subjects（データ）を分けるか（設計核）**: `category`（認識の型：observation / research / …）は**閉じた語彙**——増えないことに意味があり、増殖と綴り揺れこそが v1.8.0 で許可集合検証を入れた理由。対して主題は**開いた語彙**——扱う領域が増えれば増える。これをコードの定数に置くと、主題を 1 つ増やすたびに deploy が要る。**閉じた語彙はコード（frozenset）、開いた語彙はデータ（管理表）**、が分岐の判定基準。両者は直交する軸なので、同じ知見が「observation（型）× 馬（主題）」の両方から引ける
- **なぜ topic の接頭辞規約（`[主題] 本文`）を捨てたか**: v1.8.0 は主題軸を `topic` 文字列の接頭辞で持つ規約（コード変更ゼロ）を提案していたが、規約は**強制されないぶん揺れる**（付け忘れ・表記ゆれ・遡及付与の未完了が混在しても誰も気づかない）。フィールドに分けて語彙表と照合すれば、範囲外は書き込み口で弾ける——検証できない規約より、検証できるデータ構造を採る
- **なぜ status=deprecated で退場させるか**: 語彙の削除は過去レコードの主題を読めなくする（照合先が消えるだけでなく、その主題で引けなくなる）。`deprecated` は**新規付与だけを止める**——既存レコードの読み出しは壊さない。「消さずに止める」は archive 方針（§3.5）と同じ思想
- **なぜ照合の純関数を Domain に置き、データ供給を Interface にするか**: 語彙はデータゆえ Domain 定数にできないが、「与えられた語彙集合に対して範囲外を列挙する」判定はビジネスルールである。`invalid_subjects(subjects, active_ids)` を Domain の純関数に置き、SUBJECTS を読んで渡すのは Interface（`registry_cli`）が担う——依存は内向きのまま、判定は引数だけでテストできる
- **なぜ書き込み口だけを fail-closed にするか（write / read の非対称）**: `add` / `import` はトップレベルの未知キーを exit 2 で弾く（キー名を stderr に出す）。従来 `from_dict` は既知キーだけを転記するため、typo（`subjects` → `subject`）は**例外にならず沈黙して消えていた**——「登録したのに無い」を後から探させる形。対して read 経路（`list` / `get` / `orientation`）は警告どまりに留める——read に同じ検証を入れると、未知キーを 1 つ持つレコードがあるだけで list が全滅する（v1.8.0 の category 検証が読み取り経路で発火して起きた形）。**前方互換は read に残し、fail-closed は write に置く**。v1.11.0 でこの fail-closed は WAL の入口（`wal-append`）と redo（`wal-redo`）にも広がり、書き込み側は四口とも同じ検証関門を共有する（§3.7）——read の fail-open はそのまま
- **配線コストの実証**: subjects の CRUD・WAL kind・orientation の表順・subparser はすべて `REGISTRY_SPEC` の 1 行と `Config.subjects_path` だけで生えた（表名の列挙は `main.py` / `wal_cli` とも `REGISTRY_SPEC` 導出ゆえ、表を足すための改修はゼロ）。§3.8 が abilities で主張した「テーブル駆動なら 4 表目は 1 行」は、8 表目でも成り立っている

### 3.9 なぜ outbound（proactive-send）に WAL 再送を足すのか（offset 安全網の無い経路の冪等性）★再送方針 SSoT

秘書は基本 inbound（受信→返信）だが、口頭での権限 grant（例: 自由時間の付与）により **outbound（能動 push＝proactive-send）** も担う（能力境界の SSoT は SecretaryRole）。pull 口（getUpdates）に push を足すことで対話チャネルが双方向化する。この outbound 経路は、§3.7 が前提にした冪等性の安全網（offset）を構造的に持たないため、WAL 再送の扱いが inbound と異なる。本節を **再送方針の SSoT** とし、他ドキュメント（SKILL / ROUTINE_PROMPT / CHANGELOG）は要約 + 本節へのポインタに留める。

- **なぜ offset 非干渉が不変条件か**: `ProactiveSend` は `SendReply` から `OffsetStore` 依存と offset advance を除いた姉妹 UseCase。offset は **inbound 専用の既読台帳**ゆえ、outbound がこれに触れると「advance して未読 inbound を取りこぼす」事故が起きうる。依存に持たない（提供する手段が無い）ことで構造的に封じる——壊しようがない設計。lease 検証→添付検証→送信→lease renew の順序と「送信失敗時は据え置き」不変条件は `SendReply` から継承する
- **なぜ §3.7 を破壊しない整合的拡張か（論証核）**: §3.7 が「WAL は送信後の registry 漏れ専任、**返信は再送しない**」と言えたのは、**inbound 返信には offset という安全網がある**ため——`update_id` を advance しなければ次回 cron の getUpdates が同じメッセージを再取得し、自然に再送される。ところが proactive-send は inbound に紐づかない＝**トリガとなる `update_id` が存在しない**＝offset 安全網が構造的に無い。送信前にクラッシュすれば、その「送ろうとした意図」は二度と再現されない。よって outbound では **WAL 再送が唯一の冪等性保証**になる。§3.7 を覆すのではなく「offset 安全網の無い経路にだけ WAL 再送を足す」——前提（安全網の有無）が違うから処方が違う、という整合的拡張である（§3.7 inbound の結論はそのまま保つ）
- **happy-path settle（成功送信は再送しない）**: `proactive-send` は送信成功直後に当該 outbound intent を done 化する（`domain.wal.settle_outbound` / `SettleOutboundIntent` / `run_wal_settle_outbound`）。これにより**正常送信した分は次回 redo の対象から外れる**——redo が再送するのは「送信成功と done 記録の間でクラッシュした真の中断分」だけになる。registry kind が registry 照合（reconcile/settle）で done 化するのと対称に、外部真実源を持たない outbound は**送信者自身が created_at 直指定で done 化**する。これを欠くと「成功送信が毎起動で複製され、複製に偽の障害謝罪が乗る」（happy-path settle の欠落＝v1.2.1 までの不具合、§ Changelog 1.2.2 で修正）
- **なぜ冪等性は at-least-once か（exactly-once を追わない）**: 買える保証は at-least-once。happy-path settle 後もなお「送信成功↔done 記録」の窓でクラッシュすれば重複しうるが（既に届いている／done だけ落ちた状態）、これを技術（TTL / content-hash dedup / 二相コミット）で潰さず、**再送時に元の送信予定時刻＋中立プレフィックス**（`[<created_at>] にお送りしようとした内容を、念のためお届けします（既に届いていたらご容赦ください）`）を本文頭に付して「受け手の混乱」を**社会レイヤで無害化**する。プレフィックスは**障害原因を断定しない**——再送が起きる窓では送信済み/未送信のどちらもあり得るため、どちらでも偽にならない文言にする（「システムが落ちていた」と断定すると、実際は届いている成功ケースで偽の謝罪になる）。鮮度の判断（古い push を今受け取ってよいか）は人間に委ね、policy をコードに持たない（§3.6/§3.7 の決定論コア + エージェント判断の踏襲）
- **なぜ再送→即 done か（無限再送ループの防止）**: outbound kind は registry key を持たない（reconcile/settle の照合経路に乗らない）ため、redo は独立ループで「（happy-path settle 後に残った）pending を1回だけ再送 → 即 `mark_done`」する。done 化を再送と同一トランザクション内に置くことで、次回起動でその intent が再び pending として拾われない＝無限再送を防ぐ。TTL（鮮度切れ破棄）を持たないのはこのため——再送回数を1回に固定すれば TTL なしでも暴発しない。`wal-append --kind outbound` は registry key が無いので `created_at` をキーにし（`chat_id` 必須）、送信成功時の settle と中断時の再送の両方がこの created_at で当該 intent を指す
- **送信前ゲートと PII 範囲**: outbound の WAL ライフサイクル（`append`(pending)→`push`(must-succeed)→送信→`settle`(done)→`push`(best-effort)）は **`proactive-send` コマンドが内包**する（created_at を内部生成し settle キーに使う＝エージェントが key を受け渡す手順依存を排し、done 化を手順遵守に依存させない）。push できなければ送信もしない（§3.7 の送信前ゲートを共有）。registry_sync 無効時は WAL を素通りし送信のみ（後方互換）。WAL payload は送信本文 + 添付パス + chat_id + reply_to に限り、会話本文全体は載せない（SECURITY §7 の PII 範囲に準ずる）

> 設計の背骨は §2 / §3.7 の踏襲——WAL の純粋ロジック（reconcile/settle/checkpoint と outbound の二分）は Domain・UseCase、push/redo の順序遵守と「親性ゲートで何を能動送信するか」の判断は ROUTINE_PROMPT（従属度の世界）、git 操作と送信は決定論。`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。

### 3.10 なぜ artifacts を成果物層として持つか（決定論の管理表と分ける理由）

管理表（8表、§3.1–3.8/§3.11）は **決定論の世界**——`_REGISTRY_SPEC` 駆動の CRUD・スキーマ検証・WAL 保護を持つ構造化データ。対して `artifacts/` は秘書が生成する**非定型の成果物**（レビュー・章稿・レポート等）を置く層で、**重要度の世界**に属する。同じ `registry_dir` 配下に同居するが、性質が異なるため設計を分ける。

- **なぜ CRUD/WAL/スキーマを持たせないか（本質）**: 成果物は「どう構造化するか」自体が秘書の判断（重要度の世界）。固定スキーマや CRUD subcommand を与えると、管理表の決定論性に成果物の非定型性が混入する。`artifacts/` は **場所（`registry_dir/artifacts/`）と git 永続対象であること**だけを標準化し、ファイル構成・命名・索引（INDEX 等）は秘書に委ねる——実例として `mba50` は「章別 md ＋ INDEX」→「単一 JSON マスター」と形を変えており、**スキーマレスこそが要件**であることを示す。§3.5「情報の持ち方は情報の主体が決める」・§2 三世界分類の踏襲
- **なぜ永続か**: 成果物は蓄積が本質（過去の成果物は資産）。§3.6 の git 永続（orphan ブランチ `claude/ts-registry`）に、全管理表・`wal/` と並べて `artifacts/` を載せる。揮発してよい `state_dir` とは永続要件が正反対
- **なぜ backup はツリー同期か（ファイル固定でない）**: 管理表9点（8表＋WAL）が「単一ファイルの状態 SSoT」ゆえ固定列挙でコピーするのに対し、`artifacts/` はファイルが増減する成果物層ゆえ **ディレクトリ単位のツリー同期**（`/ts-registry-backup` が `ls-tree -r` で全ファイル列挙・`rm -rf` で stale 削除も反映）。配布先に `artifacts/` が無ければ空ループ＝no-op（母集団スコープ安全）
- **配布可能性（母集団スコープ）**: 配布 template には成果物実体を焼かない（§3.3）。`artifacts/` は実運用で自然に育つ Private 層であり、public（配布物）には「**層が在る**」ことだけを記述する——個人利用の初日から成果物が registry_dir 配下に蓄積される構造を標準化しておく

- **規約付き用途を置いてよい範囲（`handoff/`）**: 申し送りブロック `artifacts/handoff/<UTC日時>_<session_id>.md`（§3.12）は、この層に置く**最初の規約付き用途**である。それでも標準化するのは「置き場（`artifacts/handoff/`）と命名の辞書順ソート可能性」だけで、スキーマも CRUD subcommand も与えない——`orientation` はファイル名で新しい順に選び、頭から cap 字で丸めるだけで、**中身を解釈しない**。書き込みは秘書の `Write`、送出は既存 sync 経路を薄く呼ぶ `artifacts-sync` の二手（新規 git コードを書かない）。「置き場と命名」は決定論に載せてよく、「何を書くか」は重要度の世界に残す——この線が引ける限り、規約付き用途は §3.10 の境界を侵さない

> 設計の背骨は §2「決定論コア + エージェント判断の分離」の踏襲: 管理表は決定論（コードがスキーマ・CRUD を持つ）、artifacts は重要度の世界（置き場と永続だけ与え、中身は判断主体に委ねる）。この層の境界が「構造化管理表」と「成果物」を取り違えないための背骨。

### 3.11 なぜ P×A 直交2軸で役割が進化するか（PROFILE/GOALS/STEPS・データ駆動判定・占術スキル接続）

秘書の役割拡張を「パーソナライズ（P）」と「伴走（A）」の**直交する2機能軸**として持ち、その組み合わせで役割名を導出する——秘書（P✗A✗）／執事（P✓A✗）／コーチ（P✗A✓）／守護霊（P✓A✓）。機能の実体は3表の追加（PROFILE=P軸データ、GOALS/STEPS=A軸データ）であり、役割は**フラグではなくデータの状態**から立ち上がる。

- **なぜ直交2軸か（一枚岩のコーチング機能にしない）**: 「相手を深く知る」（P）と「目標へ並走する」（A）は独立に価値を持つ——深く知るが指図しない執事も、内面に踏み込まず目標だけ追うコーチも、それぞれ実在の人間像に対応する。一枚岩の「コーチング機能 on/off」では、この中間状態が表現できず、利用者は全部入りか無しかの二択を迫られる。直交分解により、**預けるものを利用者が選べる**（占いだけ・目標だけ・両方）
- **なぜ役割判定をデータ駆動（決定論）にするか**: P = 「PROFILE に subject=principal が1件以上」、A = 「GOALS に status=active が1件以上」を `derive_role` 純関数（Domain）が計算し、`role-status` subcommand が JSON で返す。LLM に「あなたは守護霊ですか」と聞かない——**役割の自称はハルシネーションの温床**（できない能力の宣言と同型）であり、判定をコードに置けば4象限の単体テストが書ける（Testability 最優先、§2 の分離の踏襲）。「どの役割か」はコード、「どう演じるか」は SecretaryRole ガイダンス（重要度の世界）
- **なぜ卒業が起きる設計か**: 全目標が achieved/abandoned になると A 軸が降り、守護霊→執事へ自然に戻る。これは仕様——伴走は預かりものであり、変容を見届けたら手を離す。目標を増やせば再びコーチ/守護霊に戻る（可逆）
- **なぜ3表か（TASKS と混ぜない・GOALS と STEPS を分ける）**: TASKS は**他者起点の依頼**（相手がいて応答義務がある）、STEPS は**目標起点の自発アクション**（親が GOAL で、義務ではなく約束）——意味論が異なるため混ぜない。GOALS と STEPS を分けるのは進捗の粒度（goal は月次・step は日次）と肥大化速度（step は done が高速に溜まる）が異なるため。`goal_id` 必須は値オブジェクト検証が担う
- **Archive 方針（§3.5 の管理表ごとの肥大化対策の適用)**: PROFILE = 蓄積優先（人物理解は捨てる対象ではなく対話で精緻化される）／GOALS = closed_at 起点の日付 Archive（TASKS と同型）／STEPS = 親 GOAL の Archive に連動（孤児ステップを残さない）
- **占術スキル（P軸聴取経路①）の接続**: 占術スキルの接続は ABILITIES 経由（`skill_path` に Expertises 実体を登録、§3.8 の自己追記ガードは実在 Read 確認で充足）。配布版 ShioriSecretary では同スキルをリポ同梱して配布物単体で実在検証可能にしている
- **なぜ JSON 占いをパーサーで固定しないか**: 占術 JSON の読み解きは重要度の世界の仕事（情報の持ち方は情報の主体が決める、§3.5/§3.10 と同根）。スキーマをコードに固定すると外部サイトの形式変更で壊れる——LLM 解釈に委ねることで robustness と「どの占術サイトでも受けられる」汎用性を同時に得る

> 設計の背骨は §2 / §3.8 の踏襲——役割判定・3表 CRUD・WAL は決定論（`REGISTRY_SPEC` に3エントリ足すだけで全機構が付く）、役割の演じ方・占術の解釈・伴走の温度は重要度の世界（SecretaryRole）、起動時の orientation ダイジェスト（§3.12）は従属度の世界（ROUTINE_PROMPT）。

### 3.12 なぜ起動時ロードは orientation ダイジェストか（沈黙失敗と上流配置）★起動時オリエンテーション SSoT

起動時オリエンテーションは `orientation` サブコマンドの**絞り込みダイジェスト一撃**で行う。表を並べて `list` する旧手順は、registry が育つと必ず壊れる構造だった。

- **沈黙失敗の機序（なぜ「重い」ではなく「壊れる」か）**: 表を並べた出力が肥大すると（実測: knowledge 943KB/187 件・tasks 741KB/8 件——支配項は 1 レコードの notes 165K 字、合計 1.6MB）、ハーネスが出力を persisted-output へ退避する。コマンドは **exit 0 で成功**し、ログにも異常が出ず、しかし**データはコンテキストに載っていない**。エージェントは「思い出した」と誤認したまま稼働し、登録済みのタスク・方針を取りこぼす。失敗が観測面に現れないため自己修正が働かず、17 枠にわたり再発した。**エラーで止まる失敗より、成功を装う失敗の方が高くつく**
- **なぜ knowledge への記録では直らないか（上流配置の原則）**: 「一括ロードするな」を knowledge に書いても効かない——その knowledge を読むのが、まさに失敗するステップだからである。**手順 X の失敗を防ぐ知識は、X より上流に置かなければならない**。本件で有効な置き場は稼働 body に限られる: `bootstrap.sh` のログ（Step 2）→ `ROUTINE_PROMPT` Step 5 → `orientation` の CLI そのもの。データ層（管理表）は下流ゆえ、この種の防止知識を預けてはならない
- **出力の有界性（なぜサイズが読めるか）**: ダイジェストは全文でなく**射影**であり、出力量は概ね

  ```
  小表全文（individuals/abilities/profile/goals）
      ※ v1.9.0 以降 individuals / abilities / profile、v1.10.0 以降 goals も cap で頭打ちにできる
    + subjects 件数 × 索引行（note は topic_width で丸め、v1.10.0）
    + steps 件数（steps_latest で頭打ち可、v1.10.0）× 索引行
    + tasks 件数（tasks_latest で頭打ち可）× 一行要約
    + active タスク数 × notes_tail(4000B)
    + knowledge 件数（category / subject / latest で絞り可）× topic_width(120B)
    + handoff_latest(3 件) × handoff_cap(8000B)
  ```

  で抑えられる。**支配項だった「notes 総長」と「knowledge content 総量」が式から消えている**ことが本質——レコードが太っても出力は太らない。**幅の単位は UTF-8 バイト**（v1.7.0 で是正）——退避の閾値がバイトである以上、幅を字数で数えると日本語 1 字≈2.47 バイト（orientation_datafit_20260809 実測）の分だけ実効幅が膨らみ、実データで既定のまま 99,037 バイトを出して沈黙失敗が再発した。**数値は不変のまま単位だけを是正**してある——v1.5.0 の校正意図（notes 末尾に 3,000–4,000 字の申し送りが堆積する／topic は識別可能な幅で足りる）は「1 字＝1 バイト」の世界で立てた見積りゆえ、バイトとして読み直せばそのまま生きる（120B≈48.6 字・4000B≈1,619 字、日本語主体データでの出力見積は 55KB 圏）。丸めは文字境界で止め、マーカー（"…"＝3 バイト）は幅の内側に置く。handoff の 2 値は実測からの外挿ゆえ仮置きで、いずれも CLI オプションで上書きできる（`handoff_latest` は件数＝単位是正の外）
- **サイズの自己申告（有界式が実データで守られているかを毎枠測る）**: 上の式は**設計上の主張**であって、実データで閾値の内側に収まっているかは測らないと分からない——現に v1.7.0 の見積（55KB 圏）は実測 72.7KB と外れていた。そこで `orientation` は実行のたび digest の総バイトを stderr へ 1 行 `orientation digest: N bytes` として申告し、`ORIENTATION_WARNING_BYTES`（25,600＝実測境界 25〜39KB 圏の安全側下限、仮置き）超では退避の可能性と絞りオプションを添える。**閾値未満でも黙らない**のが要点で、安全側で黙る計器は「exit 0 なのに載っていない」を観測させないまま通す（`_warn_if_oversized` との非対称は意図的）。stdout と exit code は不変（fail-open）＝退行リスクを持ち込まず「気づけない」だけを潰す。この計器があるので、以後の校正は実測を根拠に自走できる
- **なぜ `list` を消さず警告に留めるか**: `list` は個別調査・運用時に正当な用途を持つ。禁止（exit 変更）は既存経路の退行リスクを生むため、200KB 超で stderr に一行警告する **fail-open**（stdout・exit 0 は不変）とし、「沈黙」を「声」に変えるだけに留める。深掘りの正規ルートは `get --key`（個票）であり、表全体を舐める必要はない
- **handoff のブロック境界＝枠（なぜ notes 追記をやめるか）**: 申し送りを tasks の `notes` に追記する運用は、1 レコードを線形に伸ばし続け、上記の支配項そのものを育てる。切り取り（notes_tail）は時間を買うだけで成長構造を変えない。そこで申し送りを `artifacts/handoff/<UTC日時>_<session_id>.md` のブロックへ分離した——**セッション枠がそのまま境界**になり、1 ブロックは枠の長さで自然に有界、古いブロックは読まれないだけで消えない（append-only 台帳の不可侵性を保ったまま、読む量だけを切る）。命名が UTC 日時始まりなのは、辞書順降順＝新しい順を成立させるためで、**標準化するのは置き場と命名だけ**（中身は解釈しない、§3.10）
- **移行の可逆性**: orientation は legacy な notes 堆積も読み続ける（active タスクのみ・末尾 notes_tail 字）。handoff へ移行しても既存 notes は書き換えず、tail は自然に縮む一方——既存データの移設・破壊を伴わない
- **非再帰読み＝archive の契約（暗黙挙動でなく契約）**: orientation が見るのは `handoff/` **直下の `*.md` だけ**——サブディレクトリと非 .md は読まない。これは `glob("*.md")` の偶然ではなく退行テストで固定した契約であり、`handoff/archive/` はこの契約が作る**読み筋の外**として成立する。将来「再帰で読む」改修が入れば卒業の受け皿が静かに壊れるため、テスト側に置いた（文書だけの約束にしない）
- **卒業（`handoff-archive`）**: 消化を終えたブロックを**指名して** `handoff/archive/` へ mv し、既存 sync 経路で送る（git は rename として拾う＝履歴が切れない）。全件検証→全件移動で部分成功を作らない（不在・パス成分・archive 側の同名既存は何も動かさず exit 2）。**`--before <date>` のような一括掃除は持たない**——消化を経ない機械的 archive は原トレースの意図しない退場を招く。何を卒業させるかは重要度の世界（ROUTINE_PROMPT 手順 11 の自由時間）、移動と読み筋は決定論の世界
- **卒業すると参照の解決先が二箇所になる（辿る側の規律）**: notes や knowledge に書かれた handoff への参照は**ファイル名だけ**（`20260814T111500Z_session-xxxxxxxx.md`）でディレクトリ成分を持たない。名前は不変だが場所は動くので、卒業後の解決先は「`handoff/` 直下 → `handoff/archive/`」の二箇所になる。**直下に無い＝失われた、ではない**——archive まで見てから判定する。参照側にパスを焼き込んで解決する手もあるが、それは卒業のたびに全参照を書き換えることになる（名前で引ける利点を捨てる）ので採らない。**orientation に載らないこと（読み筋の外）とファイルが無いことは別**、を混同しないための規律
- **カテゴリ絞り（`--knowledge-category`）**: 上式の `knowledge 件数 × topic_width` 項を category 完全一致で絞って落とす。絞って見えなくなった分は見出しの `N of M` に残る（サイレントに減らさない＝沈黙失敗を新しい形で作らない）。絞りのキーが §3.5「KNOWLEDGE はカテゴリ分割（archive せず蓄積）」と同じ category なのは意図的で、物理シャード分割の閾値に達する前から同じ軸で読める
- **件数絞り（`--knowledge-latest`）**: 同じ項を**新しい順 N 件**で頭打ちにする（id は日付順に振られるため id の大きい方が新しい——`pick_latest_handoffs` の名前降順と同じ読み筋）。母数の開示は category 絞りと同じ規約で、見出しに `latest N of M` が載る。**選ぶのは新しい順、並べるのは id 昇順のまま**——索引の読み方（不変の規約）は変えず、母数だけを減らす。この捻れは並べ替えではなく**読み方の開示**で解き、latest 指定時のみ見出しに `newest last`（末尾が最新）を加える（未指定の見出しは不変＝既定出力の byte 同一互換を保つ）。`--knowledge-category` と併用すると**絞ってから latest**（M は category 絞り後の件数）で、逆順だと「新しい N 件に該当 category が無ければ 0 件」になり絞りの意味が壊れる。既定は未指定＝全件（後方互換）であり、ROUTINE_PROMPT Step 5 の投入値は v1.8.0 で**仮置き（200）から実測校正値へ**替わった（実測表と選定理由は CHANGELOG v1.8.0 / v1.9.0）
- **主題絞り（`--knowledge-subject`）と索引の主題併記**: 同じ項を subjects の**要素一致**で絞る（category 絞りと同型。母数開示・該当 0 件でも exit 0＝絞りは観測であって検証ではない）。絞りの順は **category → subject → latest**——latest を先に効かせると「新しい N 件に該当主題が無ければ 0 件」になり絞りの意味が壊れる（category との併用理由と同じ）。索引行は `id | subjects | topic` の 3 列で、主題は `/` 連結・未設定は `-`（列が消えると読み手が桁をずらして誤読する）。**併記列は topic_width の外側**に置く——主題を足したせいで topic の丸め幅が縮むと、索引の読める量が主題の付き方で揺れる
- **蓋の無い表への上限ノブ（案A、v1.9.0）**: 下の「絞れない床」が示すとおり、v1.8.0 の 4 ノブは knowledge 索引・notes 末尾・handoff 本文の 3 項にしか効かず、床（小表全文＋tasks 一行要約）には手が届かなかった。`--profile-cap` / `--individuals-cap` / `--abilities-cap` / `--tasks-latest` は**この床を初めて可動域に入れる**。cap が当たるのは表の支配的長文フィールド 1 つ（`content` / `identity.context_notes` / `guidance`）だけで、丸めの規約は既存 `_truncate` をそのまま使う（新しい丸め処理を書かない＝読み手が表ごとに切れ方を覚えずに済む）。**既定は未指定＝全文**（非破壊）で、見出しに `full, <field path> cap N bytes` として開示する
- **絞れない床（校正で動かせる部分が増えた）**: v1.8.0 で全ノブを最小に振っても残った **11,629 バイト**は、小表の全文（individuals / abilities / **profile 6,417B** / goals / steps）と tasks の一行要約だった——25,600 の目標に対し床だけで 45%。v1.9.0 は subjects 表が加わって床が **13,847 バイト**へ上がる一方、案A のノブを最小に振ると床は **6,919 バイト**（目標の 27%）まで下がる。**C（主題軸）が床を押し上げ、A（上限ノブ）が床を掘り下げる**——A を C の前提条件として同版に入れたのはこのため（実測は CHANGELOG v1.9.0）。**v1.10.0 で「蓋の無い表」は消えた**——subjects / steps を索引化し goals に cap を掛けたので、8 表すべてが可動域に入り、床は「表の件数 × 索引行」まで縮む（実測は CHANGELOG v1.10.0）
- **表の性質が処方を決める（8 表の処方一覧）★SSoT**: 蓋の掛け方は表ごとの気分ではなく、**1 レコードが長いのか／レコード数が増えるのか**で決まる。前者には cap（支配的長文フィールド 1 つだけを丸める）、後者には索引または件数絞り（行あたりを最小化し、母数は見出しで開示する）。新しい表が生えたら、この二択のどちらかに必ず入れる——どちらでもない表は「蓋の無い表」であり、育ったときに沈黙失敗を再発させる側になる。

  | 表 | 処方 | 根拠 |
  |---|---|---|
  | individuals | cap（`identity.context_notes`、`--individuals-cap`） | 1 レコードが長い |
  | tasks | 一行要約＋`--tasks-latest`（notes は絞った集合に連動） | 件数が増える |
  | knowledge | `id \| subjects \| topic` 索引＋絞り 3 種（category / subject / latest） | 件数が増える |
  | subjects | 索引（`id \| label \| aliases \| status \| note`、件数絞りは付けない） | `subjects add` で語彙を育てるのが正規ワークフロー＝件数が増える。ただし「どの主題で引くか」を選ぶ一覧ゆえ母数は減らせない——絞るのは行あたりの重さだけ |
  | abilities | cap（`guidance`、`--abilities-cap`） | 1 レコードが長い（`trigger` / `skill_path` は発動判断に要るので丸めない） |
  | profile | cap（`content`、`--profile-cap`） | 1 レコードが長い（principal 1 件） |
  | goals | cap（`notes`、`--goals-cap`） | 件数は少なく本文が長い |
  | steps | 索引（`id \| goal_id \| seq \| status \| title`）＋`--steps-latest` | 目標からの逆算単位ゆえ設計上 `done` が高速に溜まる＝件数が増える |

  実装上、この表は 2 箇所に写っている——`_CAP_FIELDS`（cap 側 4 表への経路の写像）と `_table_section` の分岐（索引側 4 表）。**「既定は全文」の分岐に残るのは cap 側 4 表**（individuals / abilities / profile / goals）で、`_CAP_FIELDS` のキー集合とちょうど一致する。subjects に cap でなく索引を採ったのは、cap が 1 レコードの長さにしか効かず語彙の件数成長に無力だから——全文 JSON は `created_at` / `updated_at` という**この用途で価値ゼロの数十バイト**を毎レコード運ぶ
- **category の許可集合（なぜ読み取り経路で弾くか）**: `category` は**認識の型**の軸であり、許可集合 10 種（`observation` / `research` / `harness` / `domain-insight` / `analysis` / `design` / `method` / `philosophy` / `business` / `decision`）に閉じる。旧実装の `d.get("category", "general")` は範囲外を**沈黙のうちに生成する fail-open** で、これが分類の増殖と綴り揺れの温床だった——上の「絞り」は category を軸に効くので、軸が揺れれば絞り自体が壊れる。検証は値オブジェクトの `__post_init__` に置く＝**読み取り経路でも発火する**ため、範囲外を含む既存データは `list` / `orientation` ごと exit 2 で落ちる（v1.8.0 の破壊的変更。移行手順は CHANGELOG v1.8.0）。主題（馬・建設 等）の軸は **knowledge の `subjects[]`**（v1.9.0）が担い、二軸を混ぜない——語彙は SUBJECTS 表が持ち、範囲外は書き込み口で弾ける（§3.8。v1.8.0 が置いた `topic` の接頭辞規約は、検証できない規約ゆえ v1.9.0 で廃止した）

> 消化（handoff → knowledge への結晶化）と卒業（archive）のサイクルは v1.6.0 で載った。分離（第一段）が「読む量を切る」だったのに対し、消化と卒業は**母数そのものを減らす**——選択（何を結晶化し、何を卒業させるか）＝α は秘書の判断に残し、移動と読み筋だけをコードが持つ（§2 の踏襲）。

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
