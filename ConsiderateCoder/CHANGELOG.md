# Changelog

すべての主要な変更をこのファイルに記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

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
