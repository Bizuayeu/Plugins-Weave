# Changelog

すべての主要な変更をこのファイルに記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [Unreleased]

### Changed

- **P✓A✓ 役割の呼称をアネゴ→守護霊へ** — doc・テンプレート・SecretaryRole の日本語演出層のみ。emit 値 `anego`・`derive_role` 等のコード識別子は registry 互換のため不変（doc 内は `anego＝守護霊` と注記）。v1.3.0 当時の記録は当時の呼称のまま。配布版 ShioriSecretary の「アネゴ」は不変（母集団スコープの製品ライン分岐）
- **README「役割の進化」を「できること」bullet から独立セクションへ昇格** — 機能（管理表・role-status）と用途（預けるほど秘書が育つ）の層分離、P×A を 2×2 マトリクス表で明示

## [1.3.0] - 2026-06-12 — アネゴ機能（P×A 役割進化・3表追加）

### Added

- **役割のデータ駆動進化（P×A 直交2軸、通称アネゴ機能）** — 預けたデータで秘書の顔が進化する: **秘書**（baseline）→ principal のプロファイルを預けると**執事**（P✓: 嗜好を踏まえた先回り）→ active な目標を預けると**コーチ**（A✓: 目標逆算とプロマネ巻き取り）→ 両方で**アネゴ**（P×A: 人物理解 × 伴走の両輪）。全目標達成で A 軸が降りて自然に卒業（アネゴ→執事）。判定は `derive_role` 純関数＋`role-status` subcommand（決定論）が担い、役割の演じ方のみ SecretaryRole ガイダンスに置く——LLM の役割自称ハルシネーションを構造的に排除（DESIGN §3.11）
- **管理表3表追加（4→7表）** — `PROFILE`（人物理解＝P軸。method ∈ precognitive_viewer/json_fortune/mbti/interview/observation/other、蓄積優先）／`GOALS`（目標＝A軸。category ∈ money/work/relationship/health/other の四大相談コース、closed_at 起点の日付 Archive）／`STEPS`（目標逆算ステップ。goal_id 必須・seq 順、親 GOAL 連動 Archive）。既存4表と同型の CRUD subcommand・値オブジェクト検証・git 永続化・**WAL 言行一致**が `REGISTRY_SPEC` 追加だけで自動適用（abilities 前例 §3.8 の踏襲、UseCase/Adapter 無変更）。雛型 `templates/{PROFILE,GOALS,STEPS}.template.json` を追加
- **パーソナライズ聴取3経路**（SecretaryRole「パーソナライズの聴取」） — ①ABILITIES に登録済みの占術スキル（例: PrecognitiveViewer）で鑑定 ②JSON 出力型占いサイトの紹介（例: senjutsu.jp——ブラウザ内計算・データ外部送信なし。**ユーザー自身が**取得した JSON を秘書が LLM 解釈、パーサー固定せず外部形式変更に頑健）③MBTI 等の直接聴取。いずれも本人同意のもと PROFILE へ method 付きで記録
- **伴走方針（A軸）**（SecretaryRole「伴走の方針」） — 1コースから開始（伴走密度を薄めない）、対話で目標言語化→success_criteria→target_date から STEPS へ逆算分解、起動時オリエンテーションと自由時間（grant 下）の伴走ナッジ（proactive-send 既存経路を再利用、新規送信機構なし）。健康=医療助言でなく生活習慣の伴走／お金=投資助言でなく家計行動の伴走の境界を明文化
- **`role-status` subcommand** — PROFILE/GOALS から現在の役割を JSON 1行で emit。ROUTINE_PROMPT Step 5 の起動時オリエンテーションが7表一括ロードと併せて1回叩く

### Changed

- **ROUTINE_PROMPT Step 5 を7表オリエンテーションへ拡張** — 一括ロードに profile/goals/steps と `role-status` を追加、自由時間の能動発信候補に「STEPS 期限近接の伴走ナッジ」を追加（**稼働中 routine は prompt body の再登録が必要**）
- **wal-append の `--kind` choices を `REGISTRY_SPEC` 導出へ統一** — 表追加のたびに argparse 列挙を手で増やす二重管理を解消（main.py の registry subparser 生成も同様に SSoT 導出化）
- **SECURITY §7 に PROFILE の機微 PII 項目と占術経路の PII 分界を追記** — PROFILE は本人同意前提・Private 分離、占術3経路はいずれも秘書から外部への PII 送信が構造的に発生しない

### Notes

- 占術スキルの接続は既存 ABILITIES 経由のまま（`skill_path` に Expertises 実体を登録、§3.8 の実在確認ガードで充足。配布版 ShioriSecretary には同スキルをリポ同梱）
- テスト 562 → 600。既存挙動の破壊的変更なし（minor bump）

## [1.2.3] - 2026-06-10 — 公開後フルレビューに基づく堅牢性修正と内部リファクタ

### Fixed

- **media download の通信失敗で watch が即死し、当該バッチの全メッセージが恒久消失する不具合を修正** — catch が size 超過のみで、CDN 4xx・期限切れ file_id 等の通信系例外が素通りして watch を traceback 死させていた。fetch が download 前に offset を確定するため、落ちたバッチのメッセージ（テキスト含む）は再取得不能だった。通信失敗を `skip_reason="download_failed"` へフラグ化し（「フラグ化して emit、ブロックしない」原則）、`AuthFailureError`（401）のみ伝播させる。MediaDownloader Port に失敗時契約を明文化。
- **caption が NFKC 正規化と injection フラグを素通りする非対称を修正** — text のみ正規化され caption は生のまま merge されていたため、写真＋caption（最頻の入力形）に載せた全角 injection 文にフラグが付かなかった。merge 前に caption も `normalize_input` を通す。
- **`init-config` の argparse 既定値を雛型既定 `14400` に統一** — 1.2.1 の 14400 統一スイープの取りこぼしで、フラグ省略時のみ `7200`（2h）が書かれていた。
- **CLI の未捕捉 traceback を入力不正（exit 2）へ整備** — registry add の `--json`/`--json-file` 両方未指定（TypeError）・`--json-file` 不在パス（FileNotFoundError）、`send-reply`/`proactive-send` の `--text-file` 不在、`render-pdf` の `--pages` 不正書式が、いずれも traceback で exit 1（transient の誤シグナル）に落ちていた。EXIT_CONFIG_INVALID で明示メッセージを返す。

### Changed

- **全 JSON store の save/rewrite を atomic 化（tmp + `os.replace`）** — truncate→write は書込中クラッシュ（cloud routine の約 4h 強制終了等）で WAL 全損や registry の silent wipe（破損→`[]` ロード→1件だけの表が push されリモート伝播）に至る経路だった。共有ヘルパ `adapters/atomic_io.py` へ集約し、破損フォールバック付き load も一本化。
- **lease 新規取得を排他作成（`O_CREAT|O_EXCL`）に** — load→check→save の TOCTOU で、同時 cron 起動の 2 コンテナが両方 acquire に成功し得た。新規取得経路を `try_create`（OS の排他作成）にし、勝者を構造的に 1 つへ（stale 奪取・自己更新は従来どおり）。
- **git subprocess に timeout（90s）と `GIT_TERMINAL_PROMPT=0`** — credential プロンプト待ちの永久ブロック（WAL push は送信ゲートのため秘書のターン全体が無期限停止）を遮断。`pull --rebase` 失敗時は `rebase --abort` を best-effort 実行してから raise（rebase-in-progress 放置による自己復旧不能を防止）。git stderr の URL 埋め込み認証はスクラブし、PAT がログへ漏れる残存経路を閉鎖。
- **bootstrap の registry worktree 再 provision 前にサニティチェック** — `registry_dir` 誤設定時に既存の実データディレクトリを黙って `rm -rf` しない（不在/空/registry 既知エントリのみ破壊的再 provision を許可、worktree 判定のパス比較は物理パス化で symlink 誤判定も解消）。
- **依存ピンの二重管理を解消** — heavy 依存を pyproject の `media` / `voice` extras へ分離し、bootstrap は tier に応じ `pip install -e ".[media,voice]"` を叩く形へ一本化（ピンの正典は pyproject、bootstrap は再記述しない）。pyproject に `[build-system]` / `[tool.setuptools] packages = []` / `license` を追加（editable install 基盤、ShioriSecretary からの還流）。coverage の omit から `main.py` を外し実測を可視化（95%）。
- **telegram retry の共通化と 429 ポリシー統一** — api_gateway / media_downloader の retry 重複を `http_retry.py` へ抽出。CDN 経路が 429 の Retry-After を無視して即死していたのを Bot API 経路と同じ尊重 retry に統一。到達不能コード（`last_exc`）と `DEFAULT_USER_AGENT` 二重定義も解消。
- **ffmpeg 前処理の `tolist()` 廃止** — 長尺音声で Python list 化が数 GB 級に膨らむメモリ暴発リスク。ndarray のまま transcriber へ渡す。
- **内部リファクタ（挙動不変）** — send-reply/proactive-send の lease 検証重複を `usecases/outbound.py` のヘルパへ、FS I/O を伴う添付検証を domain から usecases へ移動（domain 純粋性の回復）、main.py の subparser×handlers dict 二重管理を `set_defaults(handler=)` へ、private シンボル越境 import の解消（DI 組み立てを composition へ公開名移設）、WAL checkpoint の時系列保持（kind 別連結で崩れていた interleave 順を復元）、registry remove の domain 純関数化（`remove_by`）、config の `agent_name`/`private_dir` 型検証、`message_id` の int 防御キャスト、テストの時刻ヘルパ・fake・Config 組み立ての重複一本化、docstring の言行一致修正。

### Notes

- ShioriSecretary（配布独立リポ）公開直後のフルレビュー（domain+usecases / adapters / infrastructure+CLI / 配布物整合の4観点並列）に基づく一括修正を母体へ還流。SECURITY.md のプレースホルダ統一（`<BASE_REPO>`）・SKILL.md の `wal-append --kind outbound` 記載・config.template の `registry_remote` 項目・CHANGELOG 1.2.1 の見出し重複統合も同時適用。挙動契約の変更はなし。テスト 512 → 562（+50）。

## [1.2.2] - 2026-06-07 — proactive-send の happy-path settle（偽の障害謝罪を根治）

### Fixed

- **能動送信（proactive-send）が成功しても毎起動で複製され、複製に偽の障害謝罪が乗る不具合を修正** — `proactive-send` は送信成功後に outbound WAL を done 化しておらず（lease renew のみ）、次回起動の `wal-redo` が pending を**無条件**再送していた。outbound は registry のような外部真実源を持たず「送信済みか」を redo 時点で判別できないため、成功送信まで再送対象になり、しかも再送文面が「システムが落ちていたので…」と実際には起きていない障害を断定していた（既に届いているのに未送信を騙る二重の誤り）。DESIGN §3.9 は「送信成功と done 記録の間にクラッシュすれば重複」と happy-path settle の存在を前提にしていたが、その done 記録が実装漏れだった。
- **happy-path settle の実装** — `proactive-send` が送信成功直後に当該 outbound intent を done 化 + push する（`domain.wal.settle_outbound` / `usecases.wal.SettleOutboundIntent` / `wal_cli.run_wal_settle_outbound`）。redo が再送するのは「送信成功↔done 記録の窓でクラッシュした真の中断分」だけになり、正常送信は二度と再送されない。registry kind の冪等化（reconcile/settle）と対称な、外部真実源を持たない outbound 向けの settle。
- **謝罪プレフィックスの中立化** — 障害原因を断定する旧文言（`…に送ろうとした件、システムが落ちていたので念のため再送します`）を、送信済み/未送信のどちらでも偽にならない中立文言（`…にお送りしようとした内容を、念のためお届けします（既に届いていたらご容赦ください）`）へ変更。

### Changed

- **`proactive-send` が outbound WAL ライフサイクルを内包** — 従来エージェントが `wal-append --kind outbound`→`wal-push`→`proactive-send` の3コマンドで回していた手順を、`proactive-send` 一発に集約（内部で `append`(pending)→`push`(must-succeed 送信前ゲート)→送信→`settle`(done)→`push`(best-effort)）。created_at を内部生成して settle キーに使うことで、done 化がエージェントの手順遵守に依存しなくなった。`registry_sync` 無効時は送信のみ（後方互換）。**ROUTINE_PROMPT の outbound 送信手順を更新**（cloud routine prompt body の再登録が必要）。
- **outbound WAL payload に添付パス・reply_to を保存** — 再送時に本文だけでなく添付・スレッド先も復元する（従来は本文のみで添付が落ちていた）。SECURITY §7 の PII 範囲（本文 + 添付パス + chat_id + reply_to）内。

### Notes

- 再送方針の SSoT は DESIGN §3.9。registry kind の冪等化（reconcile/settle）と outbound kind の happy-path settle が対称に揃った。

## [1.2.1] - 2026-06-05 — cloud routine 実測 4h への整合

### Fixed

- **SETUP.md「勤務帯の設計」の 24h 常駐例を実測整合へ修正** — cloud routine コンテナの連続稼働は実測で約 4h（プラットフォーム依存・変動しうる）であり、従来例「1日1回 cron ＋ `session_duration_sec=86340`」では上限で切れた後に翌日まで沈黙し常駐にならなかった。常駐は「実測上限と同程度の枠（例 `14400`）＋ その間隔の cron 複数回（例 4h ごと＝ JST 0/4/8/12/16/20）」で実現する旨へ訂正。

### Changed

- **`session_duration_sec` の雛型既定・クイックスタート例を `14400`（4h）へ** — `config.template.json` の既定値と `init-config` 例（README / commands）を、cloud routine 実測上限（約 4h）に合わせた常駐向けの目安 `14400` に統一（従来 `7200`）。`config.template.json` のフィールド説明にも既定値の根拠を明記。
- **本番常駐例を 2h 枠から 4h 枠へ統一** — README クイックスタート注記の本番設定と ROUTINE_PROMPT の `$TS_MAX_TURNS` 算出例を実測 4h に更新（`24h≈507・2h≈42` → `24h≈507・4h≈84`）。`bootstrap.sh` のコメント算出例も同期（挙動・式は不変、例示値のみ）。`580s` 窓（1 ポーリングサイクル長）は session 枠と独立ゆえ不変。
- **`session_config.py` の `MAX_SECONDS` コメントを明確化** — `86400`（24h）は値域の妥当性ガード上限であり、プラットフォームの実セッション上限（実測 約 4h）とは別レイヤーである旨を注記（値は不変）。
- **`wal-redo` 契約を「outbound kind に限り再送する」へ拡張** — 従来「返信は再送しない」（registry kind の redo 専任）だった契約を、entries を registry kind と outbound kind に二分する形へ拡張。**registry kind は不変**（reconcile→upsert→settle、送信前クラッシュ分は offset 再取得が担うため再送しない）で、outbound kind のみ独立ループで1回再送する。`wal-append --kind` の choices に `outbound` を追加。

### Added

- **`proactive-send` サブコマンド（秘書による能動 outbound）** — 受信への返信（`send-reply`）に対し、inbound に紐づかない能動送信を担う双方向化。`SendReply` から `OffsetStore` 依存と offset advance を除いた姉妹 UseCase で、**offset 非干渉**（offset は inbound 専用の既読台帳ゆえ依存に持たない＝「advance して未読 inbound を取りこぼす」事故を構造的に封じる）。lease 検証→添付検証→送信→lease renew の不変条件は send-reply から継承。引数は `--chat-id`（必須）/ `--text-file`（必須）/ `--owner` / `--file`（複数可）/ `--reply-to` で、**`--update-id` は持たない**（send-reply との差分）。exit code は send-reply と同一（0/1/2/3/4）。能力境界（秘書は基本 inbound、口頭 grant で outbound）は SecretaryRole、再送の冪等性設計は DESIGN §3.9 が SSoT。
- **`wal-redo` の outbound 再送（言行一致の outbound 版）** — proactive-send は inbound に紐づかず offset の安全網が無いため、WAL 再送が唯一の冪等性保証になる。起動時に outbound kind の pending を **1回だけ再送**（本文頭に元送信予定時刻＋謝罪プレフィックスを付す）して即 `mark_done` する（再送→即 done で無限再送ループを防ぐ。TTL も content-hash dedup も持たない）。買える保証は at-least-once で、重複は技術で潰さず「受け手の混乱」を社会レイヤで無害化する設計（DESIGN §3.9）。`wal-append --kind outbound`（`chat_id` 必須）で先行書込。

## [1.1.0] - 2026-06-04 — 能力カタログ（abilities）

### Added

- **`abilities` 管理表（registry 4 表目、individuals/tasks/knowledge と同格）** — 秘書が行使できる能力（スキル）のカタログ。同じ CRUD（`abilities {list|get|add|remove}`）・値オブジェクト検証・`registry_sync` での git 永続化を持つ。各レコードは発動シグナル `trigger`・スキル実体パス `skill_path`・起動 `guidance` を保持し、秘書は応答前に `abilities list` で該当能力を引いて外部スキルを行使する（例: 占い依頼 → 占術スキルで鑑定書生成 → `send-reply --file`）。雛型 `templates/ABILITIES.template.json` を追加。**WAL 対象**（4 表一様、§3.8）：能力の自己追記は「『○○できます』と相手に宣言する返信」を伴いうるため、individuals/tasks/knowledge と同様に WAL 先行書込で保護する（`wal-append --kind abilities` 受理、起動時 redo も abilities を反映。宣言したのに push 漏れで未登録、の言行不一致を防ぐ）。
- **ROUTINE_PROMPT「4 表オリエンテーション」** — 手順12を拡充し、4 表（誰と・何を頼まれ・どう判断し・何ができるか）の位置付けと「溜めるだけでなく応答前に能動的に引く」運用方針、abilities の read 配線（`trigger` 該当 → `skill_path` の SKILL.md → `guidance`）を明示。能力の自己追記は実在スキルに限るガード付き（ハルシネーション防止）。

### Changed

- **配布用の一般化リファクタ（用語・テンプレート整合）** — 固有名の一括中立化で生じた末尾スペース（`エージェント␣`、56 箇所）を除去、cloud routine 表記を統一、運用固有名（PrecognitiveViewer / Expertises 等）を中立例へ置換。管理表テンプレート（INDIVIDUALS/TASKS/KNOWLEDGE）の保存先記述を `<registry_dir>` へ整合（registry_dir 分離の反映漏れ）、プレースホルダを規約（`<AGENT_NAME>`/`<OWNER>`）へ統一。コードコメントの devlog 参照（配布物に無い無効リンク）を DESIGN §3.6 へ振替。
- **registry/wal CLI の DRY 統合** — `_WAL_KINDS` を `_REGISTRY_SPEC`（SSoT）全種別から導出し二重管理を解消、`_service`/`_build_git`/`_read_json_arg` を共通利用。`wal-append --kind` の choices に abilities を追加し CLI・wal_cli・ドキュメントを整合。`_NON_FF_MARKERS` の冗長要素・テストの未使用 import を整理。
- **archive/分割の位置づけを設計整合** — 「いつ・どの単位で分割/archive するか」は重要度の世界（エージェント判断）であり決定論的に自動実行しない、と DESIGN §2/§3.5・STRUCTURE を訂正（情報の持ち方は情報の主体が決める）。`archive_rotate.py` は純関数（道具）として位置づけを明確化。

### Notes

- 能力をデータ層（Private git）に置き、**稼働 body を触らず拡張する**設計。read 配線を一度通せば、以後の能力追加は `ABILITIES.json` の Private push だけで済む（cloud routine の prompt body 再登録が不要）。配布 template には具体能力を焼かない（母集団スコープ）、運用固有の能力は Private 実データに置く。

## [1.0.0] - 2026-06-03 — 正式リリース（言行一致の WAL）

### Added

- **返信送信前の WAL 先行書込（言行一致の保証、`registry_sync` 有効時）** — registry の push 漏れで「登録しました」と返信したのに未登録、という consistency 違反をゼロにする Write-Ahead Log。内部状態の変更を約束する返信の前に intent を WAL ログ（`registry_dir/wal/WAL.jsonl`、registry と同一固定ブランチ）へ追記・push（**must-succeed**＝push 不能なら send-reply も打たない）し、起動時に未反映 intent を registry へ redo（key 冪等・**返信は再送しない**＝送信前クラッシュ分は offset 再取得が担う役割分担）。ログは直近 24h の会話文脈の短期記憶も兼ね、pending は無条件保持・done は起動時チェックポイントで 24h 掃除。新規 CLI: `wal-append` / `wal-push` / `wal-redo`。durability（冗長化）でなく consistency（言行一致）を**順序**で解く設計。

### Notes

- **0.x → 1.0.0（公開 API の安定宣言）** — 0.1.0（2026-05-26 初版）から積み上げた受信メディアの中身理解・PDF 段階処理・音声 STT・生成物の送り返し・管理表の git 永続化・WAL が出揃い、cloud routine 上の対話秘書として配布可能な完成形に到達した。SemVer に従い、CLI subcommand 群・exit code（0〜4）・config.json スキーマ・emit スキーマ（`v:2`）を公開契約として安定化する（以降の破壊的変更は major で予告）。

## [0.13.0] - 2026-06-03 — 管理表の git 永続化

### Added

- **管理表の git 永続化（`registry_sync` オプトイン、既定無効）** — 秘書が蓄積する管理表（INDIVIDUALS／TASKS／KNOWLEDGE）を固定ブランチ（`registry_branch`、既定 `claude/ts-registry`）へ永続化し、cloud routine の fresh clone を跨いで残す。更新（add/remove）のたびにイベント駆動で commit&push、起動時に `registry-sync` で fetch。commit はローカル即時・push は best-effort（一時失敗は次回 sync でまとめて再送）。複数 JSON の独立した部分更新を壊さないため **force 不使用**（通常 push の non-fast-forward 拒否で競合を検出、外部更新の例外時のみ `pull --rebase` フォールバック、lease がシングルライターを保証）。
- **`registry-sync` サブコマンド** — 起動時に固定ブランチから管理表を fetch する（`registry_sync` 有効時のみ、無効は no-op）。fetch 失敗は transient（前回ローカル状態で起動し次回再試行）。
- **registry 設定を config.json に集約** — `registry_sync` / `registry_dir` / `registry_branch`（＋ `registry_remote`）を非秘匿の運用設定として config.json（純2層）に追加、雛型 `templates/config.template.json` に反映。cloud routine 起動手順（`ROUTINE_PROMPT.md` の起動時 fetch・更新時 push・`schedule` body の書き戻し先 `outcomes`）と `SETUP.md` の設定手順も整備。

### Changed

- **管理表の保存先を揮発 state と分離** — offset/lease/media（揮発、`state_dir`）と管理表（永続、`registry_dir`）は永続要件が正反対ゆえ物理分離した。`registry_dir` 未設定時は `state_dir` にフォールバックし既存挙動を維持（後方互換）。
- **`registry_dir` のパス解決を cloud routine の実行 cwd に非依存化** — config.json の相対 `registry_dir` を `Path.resolve()`（cwd 基準）で解決すると、registry サブコマンドが skill ディレクトリを cwd として実行されるため、複数リポ並列 clone 構造では Private clone の外側（git 追跡外）の誤ったパスに解決される。bootstrap が起動時 cwd（リポジトリ親）基準で絶対化して `TELEGRAM_SECRETARY_REGISTRY_DIR` に注入し、設定読込が env を優先する方式に統一した（揮発 `state_dir` の絶対化と同型）。env 不在時は従来どおり config.json 値を解決（ローカル運用の後方互換）。

### Verified

- **registry 永続化を実機（cloud routine）で検証** — Telegram 経由でタスクを登録→詳細更新し、固定ブランチ `claude/ts-registry` への add commit 到達、`TASKS.json` の upsert 冪等（同一 id が `created_at` 保持・`updated_at` 更新で 1 レコードに畳まれる）、起動時 fetch による復元を確認。push 経路の健全性（commit が origin に到達）も併せて確認した。

## [0.12.0] - 2026-06-03

### Changed

- **`TS_MAX_TURNS` を「暴走保険」から「日次総量レートキャップ」へ役割変更（duration 連動の動的算出）** — 固定 `300`（2h セッション前提の `2h/30s≈240+バッファ`）を廃し、`session_duration_sec` から `アイドル下限(duration/POLL_SET_SEC) + 15通/h 枠` で算出（24h→約507、2h→約42）。「≈15通/h を最低保証」する天井になり、`session_duration_sec` を変えても追従する。従来は 24h 運用へ 2h 前提の 300 を流用し、活発な日に deadline 前へ早期到達する不整合があった。停止主軸は引き続き deadline（時刻）で、本キャップは日次総量の上限＝暴走保険を兼ねる（累積カウンタゆえ先食い可・毎時平準化ではない）。`TS_MAX_TURNS` を env で明示すれば従来どおり上書き可、レート定数は 15通/h 固定（`bootstrap.sh` の `_ts_msg_per_hour`）。短 duration（テスト用、約1.4h 未満）では整数除算で算出が過小/0 になり `/goal` が即停止するため floor=30 を敷く。

## [0.11.1] - 2026-06-02

### Fixed

- **ドキュメントと実装の不整合を解消** — Subcommands 表の記載漏れ（`watch --timeout` / `lease --ttl` / `poll --timeout`、いずれも実装済み）を補完。STRUCTURE.md の管理表 CRUD を実装どおり `list|get|add|remove` に修正（`update` は無く `add` が upsert）。

### Changed

- **運用設定パスを `<INSTALL_DIR>` 基準に汎用化（配置・junction 非依存）** — bootstrap が repo root を `../..`（2階層配置前提）で算出するのを廃止し、自分の物理位置から絶対解決する `INSTALL_DIR` に一本化。ROUTINE_PROMPT / SETUP / bootstrap コメントから運用固有のディレクトリ階層を除去し、`schedule` の body 生成時に `<INSTALL_DIR>` を実配置パスへ置換する手順を追加。env snapshot から派生 `TELEGRAM_SECRETARY_REPO_ROOT` を除去。

### Removed

- **未使用の `watch_loop.sh` を削除** — `/goal` が `watch` を直接呼ぶ設計（D 案）への転換で不要化していた pass-through ラッパーを除去（STRUCTURE / DESIGN / exit_codes.py の言及も整理）。

## [0.11.0] - 2026-06-02

### Added

- **plugins-weave marketplace プラグイン化** — TelegramSecretary を plugins-weave の marketplace プラグインとして配布。skill は `skills/telegram-secretary/`、スラッシュコマンドは `commands/telegram-secretary.md`、`.claude-plugin/plugin.json` を追加。
- **運用設定の単一正典化（config.json）** — 手置換が必要だったプレースホルダ（人格名・private_dir 等）を `config.json`（`<INSTALL_DIR>/config.json`、`.gitignore` 除外）に集約。雛型は `templates/config.template.json`、`init-config` で生成。ROUTINE_PROMPT の Step 0 が config.json から `agent_name`/`private_dir` を動的読込し、**prompt 本文の複製・手置換が不要**に。
- **継続時間の設定可能化（`session_duration_sec`）** — セッション枠を config.json で設定（範囲 1〜86400 秒、fail-fast）。本番（勤務帯調整）／テスト（短縮で keep-alive 高速検証）／観測（cloud routine 実行制限の実測）の三役。
- **`show-config` / `init-config` サブコマンド** — 現設定の read-only 表示（秘匿マスク、未設定でも exit 0）と config.json 生成（範囲検証 + `--force` ガード）。
- **cloud routine ライフサイクル統合（`/telegram-secretary schedule` / `unschedule`）** — 常駐 routine 自体の登録・更新・停止を skill 操作化。`schedule` は upsert（`RemoteTrigger create` or `get→modify→update` ＋ `init-config`）、`unschedule` は `enabled:false` 停止（物理削除は claude.ai UI 手動）。RemoteTrigger スキーマ罠（events v1 ネスト・session_context 全置換）の回避は内蔵 `schedule` skill を正典参照。手順 SSoT は ROUTINE_PROMPT.md。
- **ドキュメント命名統一** — ドキュメント内の旧称 `/secretary`（7 箇所）を skill 実名 `/telegram-secretary` に統一。

### Changed

- **設定を純2層に整理** — env は秘匿（bot token / authorized chats）+ state_dir のみ、非秘匿の運用設定は config.json が単一正典。`config.py` が config.json を直読み（`from_env`→`from_sources`）。`config.json` の場所は `<INSTALL_DIR>` 直下に決め打ち（env で指さない＝鶏卵問題の回避）。
- **Composition Root の導入** — 依存の組み立て点を一箇所（`infrastructure/composition.py`）に集約。設定読み込みを fail-fast 化し、`poll`/`watch` 共通のメディア処理スタック構築を統一。各 CLI ハンドラは組み立て済みの依存を受け取り、自前で生成しない。終了コードの定義も単一の正典に一本化。CLI・終了コード・出力は不変の内部リファクタ。

### Removed

- **`TS_SESSION_DURATION_SEC` の 7200 既定フォールバックを廃止** — `session_duration_sec` は config.json で必須（欠落は fail-fast）。bootstrap は config.json から duration をローカル取得して deadline 計算し、duration 設定値を env に出さない（純2層）。

## [0.10.1] - 2026-05-31

### Verified

- PDF オンデマンド抽出を実機（cloud routine）で検証。受信 PDF を自動で画像化し、エージェントが必要に応じて全文（`render-pdf --text`）や巻末ページ（`--pages`）を能動取得する流れを、テキスト PDF・スキャン PDF・多ページ・大量ページ・保持期限／出力漏洩スキャンにわたり確認。

## [0.10.0] - 2026-05-31 — PDF オンデマンド抽出

### Changed

- PDF を**常に全ページ画像化**する方式へ一本化（テキスト層の有無で経路を分けるのを廃止）。全ページ同一のスタンプや薄いテキスト層による誤判定を構造的に排除。

### Added

- `render-pdf` サブコマンド（`--text`=全ページのテキスト層を抽出／`--pages N-M`=指定ページを画像化）。受信時は先頭ページ（既定 20 枚）のみ事前画像化し、全文や上限超のページは必要時に遅延生成してトークン・ディスクを節約。

## [0.9.0] - 2026-05-30 — PDF の画像化（Vision 経路）

### Added

- 画像 PDF（スキャン・図面）を全ページ画像化し、エージェントが先頭ページから段階的に Vision 解釈。画像化（決定論・低コスト）と Vision（判断・高コスト）を分離し、`page_count` で総量を把握して必要分のみ読む。
- 画像化ページ数の上限 env（`TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES`、既定 20）を追加。

### Notes

- OCR ではなく Vision を採用（図面・写真の比重と、後続の動画キーフレーム解釈との共通基盤のため）。派生画像は保持期限クリーンアップの対象。

## [0.8.1] - 2026-05-30

### Verified

- PDF テキスト抽出を実機検証。`Read` ツールを使わずに PDF 本文へ到達できること、文字化けしやすい PDF もクリーンに抽出できること、スキャン PDF はテキスト層ゼロを正直に返すこと、偽装ファイルを厳格に弾くことを確認。

## [0.8.0] - 2026-05-30 — PDF テキスト抽出

### Added

- PDF のテキスト層を pdfplumber で抽出し、本文を `rendered_text` に載せて返す（`MediaRenderer` の第三実装）。`Read` ツールに依存せず PDF 内容へ到達。テキスト層ゼロ（スキャン PDF 等）は空文字で「読めるテキストなし」を正直に返す。

### Notes

- pdfplumber（MIT、pure-python）を採用、pymupdf（AGPL）は配布制約のため不採用。内部ライブラリは `MediaRenderer` Port で差し替え可能。

## [0.7.5] - 2026-05-30

### Verified

- 音声・動画の文字起こしを cloud routine（Linux）実機で検証。音声ライブラリの導入、各種音声／動画形式の transcript 化、無音・破損ファイルの安全な空応答、保持期限クリーンアップ、出力漏洩スキャンを確認。

### Fixed

- 音声の破損・デコード不可を「失敗」ではなく「音声なし（空 transcript）」として扱うよう統一（クラッシュせず安全側）。媒体ごとに失敗の扱いが異なる点を `render_status` の説明に明記。

## [0.7.4] - 2026-05-29

### Verified

- 常駐セッションが既定枠（約2時間）を通して生存し、強制終了の発火なく正常終了することを実機確認。

### Fixed

- 長時間ポーリングの最終サイクルが窓満了を超過し、シェルのタイムアウトで強制終了されるリスクを修正。最終サイクルの待機を残り時間に丸め、プロセスが自然終了を先に迎えるよう不変条件を保証。

## [0.7.3] - 2026-05-29

### Fixed

- cloud routine のシェルは呼び出しごとに環境変数が揮発する（カレントディレクトリのみ持続する）前提に対応。bootstrap が派生環境変数を snapshot ファイルへ書き出し、各ステップが冒頭で読み直す方式に変更。これによりリース所有者・期限変数が全呼び出しで一貫。
- 相対指定の state ディレクトリがサブシェルの `cd` で実体のないパスに化ける問題を、bootstrap 実行時に絶対パス化して固定することで解消（既定運用は不変）。

## [0.7.2] - 2026-05-29

### Changed

- 音声バンドル（STT 用ライブラリ）を任意化。メディア種別ごとに必要な依存が異なる前提で、軽量構成（ダウンロードのみ）／標準（文書対応）／音声対応の3段階に分離。`TELEGRAM_SECRETARY_BUNDLE_VOICE=false` で音声バンドルを除外可能。
- 音声 STT ライブラリのライセンスは年商規模により商用条件が変わるため、大規模運用は音声バンドル除外または代替ライブラリへの切替で対応。

## [0.7.1] - 2026-05-29

### Verified

- 前面実行の長時間ポーリングで cloud routine のコンテナが枠の間 warm 維持され、期限到達で正常終了することを実機確認。セッション内 keep-alive 方式の成立を確認。

### Fixed

- 起動時にメディア処理用の依存（文書・音声ライブラリ）を一括読み込みしてクラッシュする問題を、遅延構築に変更して解消。メディアを受けるまで重い依存を読み込まず、常駐起動が常に軽い。

## [0.7.0] - 2026-05-29 — 常駐ロングポーリング（keep-alive + 即応）

### Added

- 既定枠（約2時間）の間セッションを warm に保ちつつ、メッセージに即応する keep-alive 設計。各ターンで前面実行の `watch` を1回回し、メッセージ受信で即座に返信→再起動、無メッセージなら窓満了まで long-poll でブロック（待機コスト最小）。
- `watch` に窓満了 exit（`--max-duration`）とメッセージ受信 exit（`--exit-on-message`）を追加。停止の主軸を時刻（期限）に置き、ポーリング回数を判断から切り離す。

## [0.6.0] - 2026-05-28 — 管理表＋ドキュメント体系

### Added

- 秘書の3管理表（関係者 INDIVIDUALS／依頼 TASKS／対応知 KNOWLEDGE）を Clean Architecture 4層で構築。正典は Private な JSON、配布物はテンプレートのみ（個人データを焼き込まない＝配布可能性の担保）。
- 管理表 CRUD の CLI サブコマンド（`individuals|tasks|knowledge`）。操作主体はエージェント、書き込みは決定論的 I/O、入口は将来 `/telegram-secretary` でラップ。
- 肥大化対策：TASKS／INDIVIDUALS は日付アーカイブ、KNOWLEDGE はカテゴリ分割（知識は蓄積が本質のため捨てない）。
- 設計ドキュメント体系を整備（DESIGN／STRUCTURE／SECURITY）。

## [0.5.1] - 2026-05-27

### Fixed

- 返信スレッド機能の入力源（元メッセージ ID）が emit に含まれず、エージェントがスレッド返信に渡す値を取得できなかった設計不整合を修正。
- 送信失敗時のネットワークエラー経路で、token を含む URL が例外メッセージに漏れる経路を塞いだ（全送受信経路で統一）。

## [0.5.0] - 2026-05-27 — 生成物の送り返し

### Added

- エージェント生成物（画像・レポート・文書）を Telegram に送り返す outbound media。`send-reply --file`（複数可、画像は写真・他は文書に自動振り分け）、`--reply-to` で返信スレッド、送信前の typing インジケータ。送信添付のサイズ上限（既定 50MB）を超えると送信前に弾く。
- 送信ファイルの生成はエージェント、コードは決定論的な送信と送信前チェックのみ。

### Notes

- 「公式プラグインにあるから移植」ではなく「秘書の価値は受信の中身理解」を軸に選択的に実装。markdownv2 整形・絵文字リアクション・送信済み編集は必要時に追加する方針で見送り。

## [0.4.0] - 2026-05-27 — 音声・動画の文字起こし

### Added

- voice／audio／video をローカル STT で transcript 化し、本文として読めるようにする。音声はローカル推論で外部に送信しない（機密音声に安全）。文書 Markdown 化と同じ枠（`rendered_text`）に乗せ、emit スキーマは無変更。

### Notes

- STT ライブラリのライセンスは年商規模で商用条件が変わるため、本番商用化前に契約または代替ライブラリ（Apache-2.0 系）への切替を要する。

## [0.3.1] - 2026-05-27

### Fixed

- テスト用フィクスチャが使う書き込み系ライブラリを開発依存に明示追加。宣言された依存だけのクリーン環境でテストが再現するよう修正（開発機の偶然の状態への暗黙依存を排除）。

## [0.3.0] - 2026-05-27 — 文書ファイルの読み取り

### Added

- 文書ファイル（docx／pptx／xlsx・HTML）を Markdown 化して読み取る `MediaRenderer` 抽象を導入。受信メディアを「render してエージェントが読む」流れに一般化。
- レンダリング結果の状態（ok／passthrough／skipped／failed）を構造化。失敗は個別メディア単位でフラグ化し、全体を中断しない。

### Notes

- Markdown 化ライブラリは寛容で不正バイト列にも何か返すため、内容が意味あるテキストかの判断はエージェント側の責務（推論をコード外に出す分業）。

## [0.2.1] - 2026-05-27

### Added

- 受信メディアの保持期限クリーンアップを `watch` ループに配線（一定間隔で期限超過ファイルを自動削除）。手動実行用の `cleanup-media` サブコマンドも追加。

## [0.2.0] - 2026-05-27 — 受信メディア対応

### Added

- 写真・文書・キャプションの受信に対応。認可済みメッセージのメディアをサイズ上限内でダウンロードし、メタ情報とローカルパスを emit。キャプションは本文に統合。
- メディアのサイズ上限（既定 20MB、DoS 防御）と保持期限（既定 24時間、機密書類の長期残存防止）。ダウンロード有無を切り替える Heavy／Medium モード。
- token を含むファイル URL をログ・例外に残さない redact を多層で実装。

## [0.1.2] - 2026-05-26

### Added

- セッション ID を環境変数で統一し、`lease`／`watch`／`send-reply` が同じ所有者を共有する運用に整理（`--owner` の明示が不要に、緊急時のみ上書き）。bootstrap を source／exec 両対応に。

## [0.1.1] - 2026-05-26

### Fixed

- `watch` ループがアイドル時にリースを更新せず、無音期間に並走セッションへ奪取される設計ホールを修正（サイクル末尾で自動更新、奪取検出時は自己終了）。
- 送信前にリース所有者を再検証（二重防御）。レート制限（429）と `Retry-After` を尊重。

### Changed

- 全 Expertise のテストを信頼性の証拠として公開する方針に統一。

## [0.1.0] - 2026-05-26 — 初版

### Added

- Clean Architecture 4層で基盤を構築。認可（chat_id allowlist、IDOR 防止）、オフセットの単調増加（冪等性）、heartbeat + TTL リース（並走防止・crash 自己治癒）、入力正規化、プロンプトインジェクション検知フラグ（ブロックせず記録）。
- CLI サブコマンド（`validate-config`／`lease`／`poll`／`watch`／`send-reply`／`test`）と bootstrap スクリプト。
- 応答生成は親プロセスのエージェントが担い、コードは fetch／認可／正規化／送信のみ（推論をサブプロセスで多重起動しない設計原則）。
