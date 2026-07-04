# Changelog

すべての主要な変更をこのファイルに記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [1.0.0] - 2026-07-04 — 初回リリース

### Added

- **`agents/orchestrator.md` / `agents/worker.md`** — 采配・委任・物証レビュー・進捗管理を担う司令官定義と、スコープ済みタスクの調査・実装・検証を完遂する実働定義（UseCase 層、2 エージェント）
- **`commands/plan-sdd.md` / `commands/outsource.md`** — Clean Architecture × TDD の実装計画書（`IMPLEMENTATION_PLAN.md`）を生成する SDD コマンドと、communicator - orchestrator - worker の三層委任フローを規定する新設コマンド（Interface 層）。いずれも引数無し呼び出しで使い方を表示
- **`commands/dig.md`** — 意図が固まる前の深掘りインタビューコマンド（隠れた前提・未検討リスク・暗黙の決定を選択肢付き質問で掘り起こす、v3.0.0 同梱）
- **README「使い始める」章** — インプットは意図（宣言的な成功像）であることの説明と書き方の例、`/dig` → `/plan-sdd` → ペアプログラミング型／アウトソース型の 2 パターン分岐を含む導入フロー
- **`rules/DEV.md` / `rules/OPS.md`** — Clean Architecture・TDD Flow・3-Strike Rule・Decision Priority、およびデプロイ・セキュリティ・コスト・LLM 統合防御のチェックリスト（Domain 層、2 規範）
- **`templates/outsource-report.template.html`** — 検収レポート & 理解度クイズ生成用の自己完結 HTML 雛形（外部リソース読み込みなし、`<details>` による JS 非依存のクイズ構造）
- **構造テスト（`tests/`）** — マニフェスト整合・frontmatter・namespace 相互参照・一般化漏れの禁止トークン検査・テンプレート自己完結性・marketplace エントリ整合を stdlib のみで検証する Stage 1-4 のテスト一式
