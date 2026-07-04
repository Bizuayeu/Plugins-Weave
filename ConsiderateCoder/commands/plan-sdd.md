---
description: "Spec-Driven Development（SDD）として Clean Architecture × TDD の実装計画書（IMPLEMENTATION_PLAN.md）を作成する"
version: "1.2.0"
argument-hint: "<機能名・対象スコープ・背景>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
  - AskUserQuestion
  - Agent
---

# Spec-Driven Plan: Clean Architecture × TDD

あなたは **Spec-Driven Development（SDD）** の計画立案者です。
`${CLAUDE_PLUGIN_ROOT}/rules/DEV.md`（本プラグイン同梱の開発規範）を Read し、その方針に従い、`$ARGUMENTS` で示された機能・対象について、
**仕様＋実装ステージ＋ドキュメント整備計画** を統合した `IMPLEMENTATION_PLAN.md` を作成します。

各 Stage の **実装時** には Clean Architecture × TDD のサイクルを回しますが、
**このコマンド自身は計画書の作成までを担当**します。実装は行わず、ユーザーの確認を待ちます。

> **SDD と TDD の関係**：SDD（仕様駆動）が外側で実装計画を編み、TDD（テスト駆動）が各 Stage 内部で Red→Green→Refactor サイクルを回す。本コマンドは外側の SDD レイヤーのみを担当。

---

## 引数が空の場合

`$ARGUMENTS` が空・空白のみの場合は、計画書を作らず、以下の使い方を簡潔に表示して終了する：

- **インプットは意図**——宣言的な成功像（何が実現されていれば成功か）。手順指示や完全な仕様書は不要
- 意図には Goal のほか Constraints / Edge cases / Non-goals / Acceptance を含められると計画の質が上がる（全部揃える必要はない）
- 意図がまだ固まっていなければ、先に `/ConsiderateCoder:dig` で掘り起こす
- 計画書の生成後は 2 パターン：**ペアプログラミング型**（main セッションで Stage を順に指示、完了後に計画書を削除）／**アウトソース型**（`/ConsiderateCoder:outsource` で三層委任、計画書は保持）
- 詳細はプラグイン README の「使い始める」章

---

## 前提：必ず参照する規範

1. `${CLAUDE_PLUGIN_ROOT}/rules/DEV.md`（Read する） — Clean Architecture / TDD Flow / 3-Strike Rule / Completion Checklist / Decision Priority
2. `${CLAUDE_PLUGIN_ROOT}/rules/OPS.md`（Read する） — セキュリティ・コスト・データ設計・性能・障害対応・LLM 統合防御の事前チェック観点（該当する Stage の Success Criteria / Implementation Notes に織り込む）
3. 対象プロジェクトの `CLAUDE.md` / 関連 `CLAUDE.md`（あれば全て）
4. 対象プロジェクトの既存コード — 類似パターンを **3つ** 把握する（TDD Flow Step 1 "Understand"）

---

## Phase 1: 主題の把握

`$ARGUMENTS` は**意図**（宣言的な成功像）として解釈し、以下を抽出する：

- **What**: 何を実装するか（機能名・対象範囲。意図の Goal / Acceptance に相当）
- **Why**: なぜ必要か（背景・解決する課題）
- **Where**: どこに実装するか（プロジェクトルート・対象ディレクトリ。Constraints / Non-goals があればここで拾う）

上記3点のうち2点以上が不明な場合は、`AskUserQuestion` で2-3問のみ確認する。
**過剰な質問は禁止**。1往復で計画立案に必要な最小情報を取りに行く。

---

## Phase 2: 既存コードの調査（Understand）

DEV.md の TDD Flow Step 1 に従い、以下を調査する：

1. **プロジェクト構造**：`Glob` でルート〜2-3階層を把握
2. **類似機能**：`Grep` で3つの類似実装を特定し、ファイルパスを記録
   - 3 件は経験則。**2 件未満しか見つからない場合の段階的フォールバック**：
     - 第1段：検索語を一段抽象化して再 `Grep`（同義語・上位概念・関連機能名で再探索）
     - 第2段：それでも足りなければ `AskUserQuestion` で参考実装をユーザーに直接尋ねる
     - 第3段：ゼロ件で確定したら計画書の `Reference Patterns` に「**類似実装なし（新規ドメイン）**」と明記し、Phase 3 の Architecture 設計を既存パターン引用ではなく Domain Driven な再設計として進める
   - 新規プロジェクト初期や、ドメイン特化度が高いリポジトリ、本コマンドのような Markdown 仕様書系で発火する。形式数を埋めるために性質の異なるものを混ぜない（責務境界の侵食を未然に防ぐ）
3. **テスト設計パターン**：既存テストの配置・命名規約・モック戦略を把握
4. **規約**：`CLAUDE.md` / `README.md` / `package.json` 等で言語・フレームワーク・依存性を確認

調査は **読むだけ**。書き込みは Phase 6 まで行わない。

---

## Phase 3: Clean Architecture 責務分解

DEV.md の Architecture セクションに従い、本機能を 4 層に分解する：

| Layer | 本機能における責務 | 主要な型/関数 | 依存先 |
|-------|-----------------|-------------|--------|
| **Domain** | 純粋なビジネスロジック・エンティティ・値オブジェクト | [...] | なし |
| **UseCase** | アプリケーション固有のオーケストレーション | [...] | Domain のみ |
| **Interface** | コントローラ・プレゼンタ・ゲートウェイ | [...] | UseCase, Domain |
| **Infrastructure** | フレームワーク・DB・外部サービス | [...] | 全層（最外殻） |

**依存方向（外 → 内）の遵守**を明示する。Domain が外層を import しないこと、Interface で境界を切ることを必ず計画に反映する。

---

## Phase 4: Implementation Staging（3-5 段階）

DEV.md の Implementation Staging に従い、以下のテンプレートで Stage を分割する：

```markdown
## Stage N: [Name]
**Goal**: [具体的な成果物]
**Layer**: [Domain / UseCase / Interface / Infrastructure]
**Success Criteria**: [テスト可能な完了条件]
**Tests** (Red → Green) — *Stage を駆動する代表ケース 2-4 件のみ。網羅は実装フェーズで TDD サイクルが拾う*:
  - [テストケース1: 失敗するテスト + 期待挙動]
  - [テストケース2: ...]
**Implementation Notes**: [TDD Flow Step 3-4 の指針、参考にする既存パターン]
**Status**: Not Started
```

### Stage 順序の原則

**内側から外側へ**：

1. Domain（純粋ロジック・値オブジェクト・エンティティ）
2. UseCase（オーケストレーション、Domain のみに依存）
3. Interface（コントローラ・ゲートウェイ）
4. Infrastructure（DB・外部 API・フレームワーク統合）

各 Stage は TDD Flow（**Test → Implement → Refactor → Commit**）を踏む。
Stage 数は **3-5 を目安**。多すぎる場合は粒度を上げ、少なすぎる場合は責務を分離する。

---

## Phase 5: ドキュメント整備計画

DEV.md の Completion Checklist を **計画段階から織り込む**（実作成は実装完了時）。
構成は **基本セット（毎回確認）+ 拡張レイヤー（プロジェクト依存）** の二層。

### 5-1. 基本セット（3 文書、毎回確認）

すべての機能追加で **必ず確認対象** となる 3 文書。これは固定。

| ドキュメント | 役割 | 新規 / 更新 / 不要 | 計画内容 |
|---|---|---|---|
| `README.md` | プロジェクトの顔 | [更新 / 不要] | [追記ポイント / 不要なら理由] |
| `CHANGELOG.md` | 変更履歴 | [更新 / 不要] | [エントリのドラフト / 不要なら理由] |
| `IMPLEMENTATION_PLAN.md` | 本計画書 | 新規 | 全 Stage 完了後に削除 |

> **削除ポリシー分岐**: `IMPLEMENTATION_PLAN.md` は `/plan-sdd` 単体利用時は全 Stage 完了後に削除する（従来どおり）。ただし `/outsource` 経由の実装では**自動削除しない**（HTML レポート & 理解度クイズの生成材料、および communicator 検収の照合元として保持し、削除はユーザーの明示指示があった場合のみ行う）。

**「不要」判定でも一行で理由を明示**する（半年後の自分が迷わないため）。
「確認自体を省略しない」が DEV.md の Completion Checklist の方針。

### 5-2. 拡張レイヤー（Explore サブエージェントに委譲）

3 文書だけで済まないケースの**棚卸しと影響判定は `Explore` サブエージェントに委譲**する（read-only 調査タスクなので main の context を保護）。

以下のテンプレートで `Agent` を呼び出す：

```
description: ドキュメント整備候補の棚卸し
subagent_type: Explore
prompt: |
  対象プロジェクトで「[Phase 1 の What]」を実装するにあたり、
  影響を受けうるドキュメントを棚卸しし、整備候補を返してください。

  # 対象プロジェクト
  [プロジェクトルートのパス]

  # 機能概要
  - What: [...]
  - Why:  [...]
  - Where: [...]
  - 主要な変更点: [API追加 / 挙動変更 / 新規依存 / 設計変更 / etc.]

  # 調査タスク
  1. Glob で既存ドキュメントを棚卸し（ルート + docs/ + サブパッケージ + プロジェクト固有）
  2. 各文書について、以下のカテゴリで本機能との接点を評価：
     API変更系 / 挙動変更系 / セキュリティ系 / アーキテクチャ系
     / 環境系 / ユーザー向け系 / インライン系 / プロジェクト固有
  3. 新規作成を提案すべき文書があれば候補を挙げる

  # 除外
  README.md / CHANGELOG.md / IMPLEMENTATION_PLAN.md は基本セット側で扱うため
  本調査の対象外。

  # 出力フォーマット（簡潔に、判断はメインに戻す）
  | ドキュメント | パス | 候補（更新/新規/不要） | 1行根拠 |

  備考や長い解説は不要。表 + 一言サマリで返してください。
```

### 5-3. 統合整備計画表

5-1 基本セット 3 行 + 5-2 サブエージェント返却分を合成して計画書に書き出す：

| ドキュメント | パス | 新規 / 更新 / 不要 | 計画内容 / 理由 |
|---|---|---|---|
| `README.md` | `./README.md` | [更新 / 不要] | ... |
| `CHANGELOG.md` | `./CHANGELOG.md` | [更新 / 不要] | ... |
| `IMPLEMENTATION_PLAN.md` | `./IMPLEMENTATION_PLAN.md` | 新規 | 全 Stage 完了後に削除 |
| --- *拡張レイヤー（サブエージェント結果より）* --- | | | |
| (サブエージェントが特定した文書) | ... | ... | ... |

#### 判定の原則（サブエージェント結果を main で再評価する際）

- **迷ったら "更新候補"** に倒す（漏れは取り戻せない、後で削るのは容易）
- **新規ドキュメント作成は慎重に**（既存に居場所がないかを先に確認、System Prompt のデフォルト方針と整合）
- **SSoT 違反を確認**：類似情報を持つ既存文書がないか確認、ある場合は「片方をポインター化」「廃止」「同期運用」のどれを採るか判定（重複記述は片方が古くなる事故の温床）
- **"不要" 判定にも理由を一行**（半年後の自分が迷わないため）

実作成は実装完了時にユーザー承認を得てから行う。表に並べるのは「確認」のため。

---

## Phase 6: IMPLEMENTATION_PLAN.md として出力

以下の構造で `IMPLEMENTATION_PLAN.md` を対象プロジェクトのルートに `Write` で作成する：

```markdown
# Implementation Plan: [機能名]

> 本計画は `rules/DEV.md` および `/plan-sdd` コマンドで生成。全 Stage 完了後に削除する。

## Overview
- **What**: [Phase 1 の What]
- **Why**: [Phase 1 の Why]
- **Where**: [Phase 1 の Where]
- **Reference Patterns**: [Phase 2 で発見した類似機能のパス（最大3件、フォールバックでも見つからなければ「類似実装なし（新規ドメイン）」と記録）]

## Architecture
[Phase 3 の責務分解表]

### Dependency Direction
[依存方向の図示またはテキスト記述]

## Stages
[Phase 4 の Stage テンプレート一覧、3-5 個]

## Documentation Plan
[Phase 5 のドキュメント計画表]

## Decision Priority Notes
DEV.md の優先順位（Testability > Readability > Consistency > Simplicity > Reversibility）を本計画でどう適用したか、特に分岐があった箇所の判断記録。

## 3-Strike Rule
本機能で 3 回詰まった場合の停止条件：
- 詰まりやすい予想ポイント: [...]
- 代替アプローチ候補: [...]
- ユーザーへ相談する判断ライン: [...]
```

書き出した後、ユーザーに以下を端的に報告する：

1. 作成した `IMPLEMENTATION_PLAN.md` のパス
2. Stage の総数とハイライト（Stage 1 のみ要約）
3. ドキュメント整備の判断（README/CHANGELOG の新規/更新/不要）
4. 確認すべき判断分岐（あれば）

**実装は行わない**。ユーザーが「Stage 1 から進めて」等と明示的に指示するまで待機する。

---

## 重要事項

- **TDD Flow を裏切らない**: Stage 内で Red → Green → Refactor → Commit の順序を守る
- **Clean Architecture の依存方向を裏切らない**: 内向きのみ
- **ドキュメントを後回しにしない**: 計画段階で確認自体を組み込む（実作成は完了時）
- **SSoT (Single Source of Truth) を維持**: 同じ情報を複数ドキュメントに重複記述しない。一次ソースを確定し、他は参照ポインターに留める（重複記述は片方が古くなる事故の温床）
- **3-Strike Rule**: 計画立案で 3 回詰まったら、`AskUserQuestion` で方針を仰ぐ
- **YAGNI と技術的負債の優先順位**: 「将来必要になりそう」な機能は入れない（YAGNI）、動く最小から積む。**ただし YAGNI を理由に例外（暗黙挙動・特別扱い・場当たり対応）を追加してはならない** — 例外の追加は技術的負債の主要因。YAGNI は将来機能の追加を避ける原則であって、構造の不整合や暗黙挙動を許す原則ではない。テスト堅牢化・契約の明示化・暗黙挙動の解消は YAGNI 解除対象ではなく開発プロセスの基底要件として扱う（「テストで品質を担保する」が「動く最小」の前提条件）
- **過剰計画の禁止**: Stage 数は 3-5 を目安。各 Stage に列挙する **代表テストケース** は 2-4 件（実装時の総ケース数やテストモジュール数とは別物 — 計画書では Red→Green を駆動する「核となる挙動」のみ書き、網羅は実装フェーズで TDD サイクルが拾う）。10 Stage の壮大な計画は粒度の失敗
- **既存パターンの尊重**: Phase 2 で発見したパターンに合わせる。独自設計は最後の手段
- **ドキュメント編集方針**: エビデンス（何が起きたか・どう判断したか）は残す。メタ的なレッテル張り（"〜癖の校正"、"〜運動"）は外す。抽象的な総括は読者の側に委ねる
