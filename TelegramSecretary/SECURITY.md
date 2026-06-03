# SECURITY: TelegramSecretary

> **方針**: 本ドキュメントは **SSoT を意図的に例外化**し、網羅性を優先する。配布物として単体で読んで穴が無いことが最優先のため、他ドキュメント（DESIGN / 上位 `SECURITY.md`）と内容が重複してもよい。配布時にセキュリティの穴があることの方が、重複より遥かに有害。
>
> 凡例 — ✅ 実装済み（テスト有） / 📋 計画（未実装） / ⚠️ 運用上の注意

## 脅威モデル概観

TelegramSecretary は **cloud routine（＝ Claude Code Routines のクラウド実行）上で常駐し、外部（Telegram）からのメッセージを受けて エージェント が応答する**。攻撃面は以下:

1. **未認可の第三者**が bot にメッセージを送る → 認可で遮断
2. **受信本文によるプロンプトインジェクション** → フェンシング＋フラグ
3. **bot token・secrets の漏洩** → env 限定＋ログ redact
4. **応答経由の内部情報漏洩** → 出力スキャン
5. **巨大/悪意あるメディアによる DoS・ディスク圧迫** → size 上限＋retention
6. **並走セッションによる二重応答・データ競合** → lease
7. **関係者情報・人格データ（PII）の流出**（特に配布時）→ Private 分離
8. **配布されたコードに個人データが焼き込まれる** → テンプレート/データ分離

## 1. 認可（Authorization）✅

- **chat_id allowlist**（`AUTHORIZED_CHATS`）— 認証（authn）と認可（authz）を区別し、IDOR を防ぐ。未認可 chat の update は **Domain 層で破棄**し、エージェント に渡さない（`domain/authorization.py`、`FetchAuthorizedUpdates`）
- 認可は emit より前。エージェント は認可済みデータしか見ない
- ⚠️ allowlist は env で管理。chat_id の発見は鶏卵問題ゆえ初回のみ手動（README 参照）

## 2. プロンプトインジェクション対策 ✅（フラグ）/ ⚠️（フェンシング運用）

- **injection フラグ**（`flag_injection`）— role override / system prompt 抽出 / credentials 要求を検知し `injection_flags` に記録。**ブロックせずフラグ化**し、判断は エージェント に委ねる（偽陽性回避）
- **プロンプトフェンシング** — 受信本文は XML タグで隔離し「データとして扱え」と明示してから エージェント に渡す（ROUTINE_PROMPT に明記、エージェント 側の運用責務）
- ⚠️ injection_flags が非空なら エージェント は警戒を強める（内容を疑い、必要なら無視）

## 3. secrets 管理 ✅

- **bot token は env のみ**（`TELEGRAM_BOT_TOKEN`）。コード・コミット・ログに置かない
- **token 込み URL のログ秘匿** — `/bot<TOKEN>/...` や `/file/bot<TOKEN>/...` の TOKEN を例外メッセージ・stderr・ログに残さない。`raise ... from None` で例外 chain を切る（`api_gateway` 全送受信経路 + `media_downloader`、token redact テストで検証）
- network error 経路（全 send/fetch 共通）も token 込み URL を redact する（red テストで token 混入を実証してから対処）
- ⚠️ **schedule 登録時の秘匿** — `/telegram-secretary schedule` で cloud routine を登録する際、bot token / authorized chats は **Environment に注入**し、`RemoteTrigger` の body（events の prompt body / session_context）や commit に焼かない（`environment_id` で参照）。秘匿値を body に入れると trigger 設定・実行ログに残存する

## 4. 出力漏洩防止 ⚠️（エージェント 運用責務）

- **出力漏洩スキャン** — 返信に token / env名 / system prompt / **絶対パス**が混入していないか、send-reply 前に エージェント が確認
- **添付生成物の漏洩スキャン** — 送り返す md/docx/画像/PDF にも機密が混入していないか確認。コードはバイナリ中身まで検査しない＝エージェントの判断責務
- **transcript の漏洩スキャン** — 音声内の機密（パスワード読み上げ等）が transcript 経由で emit に乗る可能性、スキャン対象に含める

## 5. 受信メディアの安全性 ✅

- **size 上限（DoS 防御）** — `MEDIA_MAX_SIZE_BYTES`（既定 20MB）超過は download せず skip + flag。超大ファイルでのディスク圧迫を防ぐ
- **retention 自動削除** — `MEDIA_RETENTION_HOURS`（既定 24h）経過した media を `cleanup_media_dir` で削除。機密書類の長期残存を防ぐ
- **mime は自己申告として扱う** — Telegram 申告の mime_type を信頼せず、親プロセスのエージェントが `Read`/render 結果を真とする（rename 攻撃対策）
- **render 寛容性の認識** — markitdown は garbage でも何か返す。rendered_text が意味あるテキストかは エージェント が判断（最終防御は エージェント 層）
- **PDF / 音声のローカル完結** — pdfplumber/pypdfium2（PDF）・Moonshine（音声）はいずれもローカル処理で、ファイルが外部に出ない。将来 Whisper API 等の外部送信 STT に切替時は「音声が第三者に渡る」プライバシー判断を別途必須化
- **音声中間ファイルの不在** — PyAV はメモリ内で 16kHz mono float へデコードし、ffmpeg 中間 wav をディスクに書かない（機密 voice の中間生成物が残存しない）
- **送信添付の上限** — `OUTBOUND_MAX_SIZE_BYTES`（既定 50MB）超過は送信前に `AttachmentTooLarge` で弾く（誤送信・コスト事故防止）

## 6. 並走制御（Lease）✅

- **heartbeat + TTL リースロック** — 並走セッションの二重応答・offset 競合を構造的に防止。新セッションは heartbeat が新鮮なら起動拒否、stale なら奪取（crash 自己治癒と両立）
- **SendReply の owner 二重検証** — 送信前に lease を再 load し owner 一致を確認（CLI 層 + UseCase 層の二重防御）

## 7. 管理表・人格データ（PII）の保護 📋（計画）

- **Private 分離が第一防御** — INDIVIDUALS（関係者の honorific/context_notes/taboo_topics）・TASKS・KNOWLEDGE・Identities はすべて Private リポ。public（配布物）には実体を置かない
- **context_notes / taboo_topics に PII 前提** — 関係者の自由記述に個人情報が入る前提で、Private リポのアクセス権限を最小化
- **shared_with 境界**（複数チャネル併用時）— 関係者間の情報共有は `identity.shared_with` の明示許可制。未承認の relay は拒否し、`<OWNER>`（principal）に承認伺い
- **principal / associate の権限分離** — 管理系操作（approve/block/edit 等）は principal（`<OWNER>`）起源のみ
- **git 永続化のセキュリティ**（`registry_sync` 有効時）— 管理表は **Private リポの固定ブランチ**（`registry_branch`）へ push し、public（配布物）には実体を置かない。git 認証（PAT 等）は env / cloud routine Environment に注入し、コミット・ログ・prompt body に焼かない。commit 対象は `registry_dir` 配下の管理表ファイルのみ（人格・秘匿の混入を構造的に排除）。force 不使用ゆえ外部更新を破壊しない
- **WAL ログの PII 範囲**（`registry_sync` 有効時）— WAL ログ（`registry_dir/wal/WAL.jsonl`）の各 intent payload は **registry へ add するレコードと同一**（individuals/tasks/knowledge の構造化レコード）ゆえ、registry を超える PII 範囲の拡大は無い（**会話本文全体はログに載せない**）。同じ Private リポ固定ブランチに置かれ、commit 対象も `registry_dir` 配下に限定。done 化後は起動時チェックポイントで 24h 掃除（pending は redo まで保持）。WAL push も registry と同じ git 認証経路ゆえ、秘匿の扱いは上記と同一

## 8. 配布時の責任分界 ⚠️

プラグインとして配布する際の境界:

| プラグインが**持つ**（public） | ユーザーが**各自持つ**（Private） |
|---|---|
| コード（scripts）・ドキュメント | 自分の bot token・chat allowlist |
| 管理表/Identities の**雛型**（templates/） | 管理表の**実データ**・秘書人格の実体 |
| デフォルト値・スキーマ | 関係者情報・依頼・知識（PII） |

- **配布物に個人データを焼き込まない**ことが最大の配布セキュリティ要件。テンプレート/データ分離（DESIGN §3.3）はセキュリティ機構でもある
- ⚠️ ユーザーは自分の token を BotFather から取得し、自分の Private に state を持つ。プラグインは雛型と決定論ロジックのみ提供

## 9. レート制限 📋（未実装、設計要件）

- chat_id 単位 sliding window でコスト暴走 & DoS を防御（設計要件）。現状未実装、必要性が顕在化した時点で UseCase 層に追加

## 配布前チェックリスト

- [ ] public ツリーに実 token / chat_id / 関係者情報 / 人格実体が混入していないか（grep 検査）
- [ ] `templates/` は雛型のみで実データを含まないか
- [ ] `.gitignore` に開発専用ディレクトリ（`docs/devlog/`・`LineBridge/` 等）と `state/`（実データ）が入っているか
- [ ] token redact テストが green か（network error 経路含む）
- [ ] injection_flags / 出力漏洩スキャンの運用が ROUTINE_PROMPT に明記されているか
- [ ] 配布ドキュメントに固有名（人格名・運用主体名・組織名・ローカル絶対パス）が残っていないか（grep 検査）
- [ ] プレースホルダ（`<AGENT_NAME>` / `<OWNER>` / `<ORGANIZATION>` / `<REPO_ROOT>` / `<PRIVATE_DIR>` / `<INSTALL_DIR>`）が規約どおり使われているか（[STRUCTURE.md](./STRUCTURE.md)）

## ルート `SECURITY.md` との関係

上位の `<REPO_ROOT>/SECURITY.md`（エージェント本体の汎用応答指針：拒否スタイル・内部情報秘匿・プロンプトインジェクション一般）は ROUTINE_PROMPT Step 0 がロードする。本ファイルは **TelegramSecretary というスキルのセキュリティ機構**を網羅する。両者は層が異なり、配布物としては本ファイルが単体完結する。
