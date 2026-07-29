# Changelog

すべての主要な変更をこのファイルに記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [1.3.0] - 2026-07-29

### Added

- **plan-sdd に裁可・接続フェーズ（Phase 7）** — 計画の報告を散文で置いて自由文の応答を待つのをやめ、`AskUserQuestion` で裁可を仰ぐ。計画中の判断分岐を 1 分岐 1 設問に変換して先に置き、**最後の設問として「この計画で `/outsource` による実装に進むか」を必ず問う**（判断分岐がゼロでも常設——「過剰な質問の禁止」の唯一の例外）。承認時は `Skill` ツールで `ConsiderateCoder:outsource` を起動し、計画 → 実装をセッションを跨がずに接続する。harness に拒否された場合のフォールバックは「`/ConsiderateCoder:outsource` の手動実行を一行で案内して終了」の一段のみ——`outsource.md` を Read しての代行は重複実行と SSoT 侵食を招くため禁じる
- **outsource に上申裁可フェーズ（Phase 4 末尾、レポート生成前）** — 検収で残った上申事項を `AskUserQuestion` で一件ずつ裁可に回す（**1 設問 1 上申**、`multiSelect` は使わない——裁可は個別判断でありまとめ承認にしない）。plan-sdd の接続設問と違い**上申事項がゼロなら発火しない**条件付き（過剰な質問の禁止との整合）。裁可結果は Phase 5 レポートの `{{ESCALATIONS}}` へ `✅ 承認済み` / `↩️ 差し戻し` のステータス付きで記録し、差し戻された上申は「物証ベースの現状＋残作業」の新しいブリーフで orchestrator を同期起動し直す。器（HTML テンプレート）は「器は決定論・中身は判断」の既存設計どおり変更しない

## [1.2.4] - 2026-07-26

### Fixed

- **watchdog.sh の find 除外を `-not -path` から `-prune` へ** — `-not -path` は出力から落とすだけで node_modules への降下自体は止めないため、TypeScript リポを含む監視では find 一周が interval を超えて詰まり、watchdog が沈黙検知の用をなさなかった。マルチリポ CI 導入の実戦で顕在化（同一 5 リポで -not-path 版 60 秒超タイムアウト → -prune 版 約 2 秒）

### Added

- **watchdog.sh の複数ディレクトリ対応** — 第一引数をカンマ区切りで複数受け付ける（`watchdog.sh <dir>[,<dir>...]`）。マルチリポ委任では作業が複数リポに散り、単一 dir 監視では Stage の進行とともに監視対象がずれるため。既存の単一 dir 呼び出しは後方互換。outsource.md Phase 3b の使用例も追従

## [1.2.3] - 2026-07-25

### Changed

- **worker の既定を `model: sonnet` / `effort: max` から `model: opus` / `effort: high` へ** — フラッグシップ世代の性能向上と、廉価モデル側の特別価格期間の終了により、「実働は廉価な器で数を打つ」という前提が成り立たなくなった。器は落とさず、思考量で役割差をつける配分へ切り替える。effort が `max` でなく `high` 起点なのは、effort を上げるほどタスク外の変更（スコープ膨張）が増える傾向が実測されており、実装を担う層では dev-rules の YAGNI と正面から衝突するため
- **orchestrator の既定 effort を `medium` から `high`（API 既定と同値）へ** — `model: inherit` で器を継ぐ以上、どの世代が采配に回るかは事前に定まらない。基準線を明示して、器の当たり外れや環境側の設定に采配の質を左右されないようにする
- **README §8「モデル配分チューニング指針」を改稿** — 設計思想を「最も高い器が采配し、廉価な器が全力で手を動かす」から「三層とも器は落とさず、effort で判断の層だけ上へ振る」へ。配分根拠は `xhigh` 以上が思考を無効化できない領域であること——常時思考が効くのは書かない層、書く層では effort を上げるほどスコープが膨らむ。orchestrator の `effort:` 既定も指針へ明示（frontmatter との突き合わせ漏れの解消）。§3 の利点も「適材適所のモデル配分によるトークンコスト最適化」から「役割に応じた器と effort の配分」へ追従

## [1.2.2] - 2026-07-25

### Added

- **dev-rules の General Principles に KISS** — 「短く、正確に書く」（同じ内容ならより短い表現を採る／削れる語を削り、意味が落ちる手前で止める）を YAGNI の直後に追加。YAGNI が機能の範囲、外科的変更がファイルの範囲を押さえる一方、「同じ内容をどう書くか」の軸だけが空いていた。`Decision Priority` の `Simplicity`（4位＝競合時の順位）は不変

### Fixed

- **ネスト生成の動作要件を CLI バージョン条件付きへ訂正（v2.1.219 追従）** — 生成深さ上限の既定値（`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` 未設定・配信値なし時のフォールバック）が v2.1.219 で 1 → 3 に変わり、`/outsource` は環境変数なしで動くようになった（実機バイナリ 2.1.217 / 2.1.219 の差分で確認）。v1.2.1 で入れた「v2.1.217 以降は必須」の記述が偽になったため、README §4 をバージョン別の表へ、outsource Phase 3 を条件付き記述へ訂正。環境変数は既定値より優先されるので既存の設定は残して支障なし（worker は Agent を持たず、深さは構造的に 2 で止まる）

## [1.2.1] - 2026-07-22

### Added

- **ネストしたサブエージェント生成の動作要件を明記（CLI v2.1.217 追従）** — Claude Code v2.1.217 からサブエージェントは既定でネスト生成不可となり、orchestrator（サブエージェント）→ worker の起動が harness に拒否される。環境変数 `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`（`"2"`）が必須であることを、README §4（動作要件の正典）・outsource Phase 3（communicator の案内手順）・orchestrator の再投入規律（設定起因の拒否はリトライせず即上申）の三点に配線。なお同バージョンの同時実行サブエージェント数上限（既定 20）は、worker 同期起動運用のため影響なし

### Fixed

- **outsource.md 本文の実測日付の残存 2 箇所を除去** — v1.2.0 の Phase 3b 追記に development-only の日付（YYYY-MM-DD）が残り、構造テストの禁止トークン検査（date-like pattern）が赤のままリリースされていた。配布層の日付除去規律へ追従し、テストを green に復帰

## [1.2.0] - 2026-07-12

### Added

- **bg 起動＋ファイル watchdog による死活監視（/outsource Phase 3b）** — communicator→orchestrator の一段に限り background 起動を正式化し、同梱の `scripts/watchdog.sh`（対象リポの mtime 沈黙を検知して STALLED を 1 行発報）を Monitor で張る運用を追加。STALLED → TaskOutput 生死実測 → 静観／SendMessage 蘇生の**二段判定**を明文化（奥宮 v0.1 実装で実戦検証：stream stall 600s からの transcript 蘇生 1 回、偽陽性 2 パターン〔監視開始前の古い mtime での即発報／worker 初動の長考〕の是正を焼き込み）
- **orchestrator に stall 再開耐性の運用律** — TodoWrite 進捗表とファイル物証だけで現在地が復元できる状態を保つ（SendMessage transcript 再開で蘇生されうる前提。蘇生後は再検分を最小化し直ちに采配へ戻る）

### Changed

- outsource Phase 3 を「同期起動のみ」から「既定は同期（3a）、長丁場は bg＋watchdog（3b）」の二方式へ。worker 起動は従来どおり**常に同期のみ**（bg が許されるのは communicator→orchestrator の一段だけ）

## [1.1.3] - 2026-07-04

### Fixed

- **plan-sdd の生成テンプレートから旧 `rules/DEV.md` 参照を一掃（第三次レビュー）** — Phase 6 出力テンプレート冒頭の旧パスは、生成される全 `IMPLEMENTATION_PLAN.md` に存在しない参照を刻み続けるため「ConsiderateCoder 同梱の dev-rules 規範」表記へ修正。本文中の旧ファイル名通称「DEV.md の〜」6 箇所も dev-rules 表記へ統一し、旧 rules ファイル名（`DEV.md` / `OPS.md`）の再混入を test_stage3 の禁止トークンで恒久防止
- dig の allowed-tools から現行 harness に存在しない `TodoRead` を除去（v3.0.0 取り込み時の残骸）
- **README の preload 記述を実配線へ精密化** — `skills:` preload で注入されるのは dev-rules のみ（ops-rules は常時注入せず、`/plan-sdd` が計画へ織り込みブリーフ経由で届く）。両規範が注入されると読める旧記述を §2 ①と FAQ で書き分け。ops-rules 本文の `../dev-rules/SKILL.md` 相対参照も、preload 注入文脈ではパス基準を持たないため名前参照へ変更

## [1.1.2] - 2026-07-04

### Added

- **dev-rules に Compliance Marker 節** — 規範がコンテキストに載っているとき、報告末尾に `[dev-rules applied]` を一行記す行動カナリア。自己申告（「読んでいるか？」への作話リスク）に依存せず、規範配線の生死を応答から機械観測できる恒久の観測点（レビュー処方）

## [1.1.1] - 2026-07-04

### Fixed

- README の旧 `rules/` 表記の残存 2 箇所（§6 の規範参照・FAQ の衝突説明）を skills 表記へ追従

## [1.1.0] - 2026-07-04

### Changed

- **rules/ を skills/ へ一本化（構造変更）** — `rules/DEV.md`・`rules/OPS.md` を `skills/dev-rules/SKILL.md`・`skills/ops-rules/SKILL.md` へ移設。orchestrator / worker は frontmatter の `skills: dev-rules` により起動時に規範**全文**の注入を受ける（公式の正規配線。本文の Read 指示は不要になったため除去）
- **dev-rules を自己完結版に改稿** — 「System Prompt が既にカバーする汎用原則は繰り返さない」という旧 DEV.md の開幕宣言は、フルシステムプロンプトを受け取らないサブエージェント文脈で偽になるため（レビュー指摘）、General Principles 節（YAGNI・外科的変更・既存流儀への同調・テストが完了を定義）を備えた単体完結の規範へ書き直し
- plan-sdd の規範参照パスを skills/ へ追従。README の構造図・Why・FAQ（常時ロード案内は `.claude/rules/` → `skills/` への junction/symlink 方式へ）を更新

## [1.0.3] - 2026-07-04

### Fixed

- **dig / plan-sdd から `context: fork` を除去（最重大）** — AskUserQuestion はメイン会話の UI に依存し、サブエージェント（fork 含む）では tools に列挙しても**沈黙して**使えない（公式仕様）。fork のままでは質問フローが静かに推測へ退化する——対話が本体の dig は main 実行が本来の姿、plan-sdd も重い探索を Explore へ委譲済みで main 実行のコストは許容範囲（レビュー指摘）
- **orchestrator の同期起動規律を環境変化へ追従** — サブエージェントの既定が background 起動に変わったため（v2.1.198）、「run_in_background: false を毎回明示する（省略は不達側に倒れる）」と明文化

### Added

- README §8: `CLAUDE_CODE_SUBAGENT_MODEL` 環境変数が frontmatter の `model:` を黙って上書きする注意
- README FAQ: プラグイン配布 agent では `hooks` / `mcpServers` / `permissionMode` が無効・`Agent(worker)` 括弧構文はメインスレッド専用という強制力の上限（配布形態が強制力の上限を決める）

## [1.0.2] - 2026-07-04

### Fixed

- **プラグイン内参照を `${CLAUDE_PLUGIN_ROOT}` に統一** — plan-sdd / outsource の `../` 相対リンクは実行時 cwd（利用者プロジェクト）基準で解決されるため、インストール後に壊れていた（レビュー指摘）。dig の `agent:` 値も通例の小文字 `general-purpose` へ修正
- **rules を配電網に結線** — orchestrator / worker 本文に「作業前に `${CLAUDE_PLUGIN_ROOT}/rules/DEV.md` を Read」を明記、plan-sdd の前提に OPS.md を追加。「三者が同一規範を参照」が思想から実装になった
- **構造保証の対称化** — worker に `disallowedTools: Agent`（再委任禁止をプロンプトの文化から許可リストの法律へ）、orchestrator の tools から SendMessage を除去（往復禁止の運用律と所持道具を一致）

### Added

- README FAQ 2 件 — rules をセッション常時ロードしたい場合の案内（`.claude/rules/` へのコピー、junction/symlink 透過）と、agents に memory を持たせない設計判断（`memory:` は Read/Write/Edit を自動有効化するため、orchestrator の無筆記構造保証と構造的に排他）

## [1.0.1] - 2026-07-04

### Added

- **README「モデル配分チューニング指針」に communicator 項を追加** — Opus 以上（可能なら Fable / Mythos 級）× effort `xhigh` 以上を推奨。orchestrator が `inherit` 既定のため、main セッションの器がそのまま采配の器を兼ねる（communicator のモデル選択が二重に効く）ことを明記。「使い始める」章のアウトソース型の項からも同指針へ誘導

## [1.0.0] - 2026-07-04 — 初回リリース

### Added

- **`agents/orchestrator.md` / `agents/worker.md`** — 采配・委任・物証レビュー・進捗管理を担う司令官定義と、スコープ済みタスクの調査・実装・検証を完遂する実働定義（UseCase 層、2 エージェント）
- **`commands/plan-sdd.md` / `commands/outsource.md`** — Clean Architecture × TDD の実装計画書（`IMPLEMENTATION_PLAN.md`）を生成する SDD コマンドと、communicator - orchestrator - worker の三層委任フローを規定する新設コマンド（Interface 層）。いずれも引数無し呼び出しで使い方を表示
- **`commands/dig.md`** — 意図が固まる前の深掘りインタビューコマンド（隠れた前提・未検討リスク・暗黙の決定を選択肢付き質問で掘り起こす、v3.0.0 同梱）
- **README「使い始める」章** — インプットは意図（宣言的な成功像）であることの説明と書き方の例、`/dig` → `/plan-sdd` → ペアプログラミング型／アウトソース型の 2 パターン分岐を含む導入フロー
- **`rules/DEV.md` / `rules/OPS.md`** — Clean Architecture・TDD Flow・3-Strike Rule・Decision Priority、およびデプロイ・セキュリティ・コスト・LLM 統合防御のチェックリスト（Domain 層、2 規範）
- **`templates/outsource-report.template.html`** — 検収レポート & 理解度クイズ生成用の自己完結 HTML 雛形（外部リソース読み込みなし、`<details>` による JS 非依存のクイズ構造）
- **構造テスト（`tests/`）** — マニフェスト整合・frontmatter・namespace 相互参照・一般化漏れの禁止トークン検査・テンプレート自己完結性・marketplace エントリ整合を stdlib のみで検証する Stage 1-4 のテスト一式
