# Changelog

すべての主要な変更をこのファイルに記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [1.2.0] - 2026-06-04 — 能動 push（proactive-send）

### Added

- **`proactive-send` サブコマンド（秘書による能動 outbound）** — 受信への返信（`send-reply`）に対し、inbound に紐づかない能動送信を担う双方向化。`SendReply` から `OffsetStore` 依存と offset advance を除いた姉妹 UseCase で、**offset 非干渉**（offset は inbound 専用の既読台帳ゆえ依存に持たない＝「advance して未読 inbound を取りこぼす」事故を構造的に封じる）。lease 検証→添付検証→送信→lease renew の不変条件は send-reply から継承。引数は `--chat-id`（必須）/ `--text-file`（必須）/ `--owner` / `--file`（複数可）/ `--reply-to` で、**`--update-id` は持たない**（send-reply との差分）。exit code は send-reply と同一（0/1/2/3/4）。能力境界（秘書は基本 inbound、口頭 grant で outbound）は SecretaryRole、再送の冪等性設計は DESIGN §3.9 が SSoT。
- **`wal-redo` の outbound 再送（言行一致の outbound 版）** — proactive-send は inbound に紐づかず offset の安全網が無いため、WAL 再送が唯一の冪等性保証になる。起動時に outbound kind の pending を **1回だけ再送**（本文頭に元送信予定時刻＋謝罪プレフィックスを付す）して即 `mark_done` する（再送→即 done で無限再送ループを防ぐ。TTL も content-hash dedup も持たない）。買える保証は at-least-once で、重複は技術で潰さず「受け手の混乱」を社会レイヤで無害化する設計（DESIGN §3.9）。`wal-append --kind outbound`（`chat_id` 必須）で先行書込。

### Changed

- **`wal-redo` 契約を「outbound kind に限り再送する」へ拡張** — 従来「返信は再送しない」（registry kind の redo 専任）だった契約を、entries を registry kind と outbound kind に二分する形へ拡張。**registry kind は不変**（reconcile→upsert→settle、送信前クラッシュ分は offset 再取得が担うため再送しない）で、outbound kind のみ独立ループで1回再送する。`wal-append --kind` の choices に `outbound` を追加。

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
