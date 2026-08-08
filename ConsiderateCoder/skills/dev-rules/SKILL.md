---
name: dev-rules
description: Development methodology rules (Clean Architecture, TDD flow, 3-Strike rule, decision priority) that govern planning, implementation, and review. Load before designing, staging, implementing, or reviewing code changes.
---

# Development Guidelines

本規範は単体で完結する（メイン会話・サブエージェントのどちらで読まれても前提を欠かない）。

## General Principles

- **求められたものを作る** — 頼まれていない機能・抽象化・設定項目を先回りで足さない（YAGNI）
- **Deletion Test で検品する** — 成果物の各要素に「これを削っても完了条件の証明は成立するか？」と問い、成立するなら削る（YAGNI の出口側の操作形）。ただし入力検証・エラー処理・セキュリティ対策は削る対象にしない——動くだけの近道は簡潔ではなく未完成である
- **根拠なき数値を発明しない** — タイムアウト・リトライ回数・閾値・上限は、出所（依頼元の指定・仕様・実測・プラットフォーム制約）を言える値だけを書く。仮置きが避けられない場合は、仮置きである旨と選定理由を明示する
- **先送りは grep 可能に刻む** — 意図的な仮置き・簡易実装には、天井（何で妥協したか）と昇格トリガー（何が起きたら本実装へ進むか）の二成分を `cc-defer:` コメントでコード内に残す（例: `# cc-defer: グローバルロック、スループット問題時にアカウント別へ`）。トリガーの無い先送りは、回収の機会を失って腐る
- **短く、正確に書く** — コードも文章も、同じ内容ならより短い表現を採る。削れる語を削り、意味が落ちる手前で止める（KISS）
- **変更は外科的に** — タスクの達成に必要な最小限のファイルだけに触れる
- **既存の流儀に合わせる** — 命名・コメント密度・イディオムは周囲のコードに揃える
- **完了はテストが定義する** — テストと静的チェックが通る状態だけを「完了」と呼ぶ

---

## Architecture: Clean Architecture

本プロジェクトは **Clean Architecture** を採用する。

```
Infrastructure → Interface(Adapter) → UseCase → Domain
              依存方向: 外から内へのみ
```

| Layer | 責務 | 依存先 |
|-------|------|--------|
| **Domain** | ビジネスロジック、エンティティ、値オブジェクト | なし（純粋） |
| **UseCase** | アプリケーション固有のオーケストレーション | Domain のみ |
| **Interface (Adapter)** | コントローラ、プレゼンタ、ゲートウェイ | UseCase, Domain |
| **Infrastructure** | フレームワーク、DB、外部サービス | 全層（最外殻） |

### 原則
- **依存は内向きのみ** — Domain は外層を import しない
- **Composition over Inheritance** — DI で組み立てる
- **Interface で境界を切る** — テスト容易性と差し替え可能性の確保
- **データフローは明示的** — グローバル状態・隠れた依存を禁止

---

## Process

### TDD Flow

1. **Understand** — 既存コードから類似機能を3つ探し、パターンを把握する。書き始める前に ①そもそも書かずに済むか → ②既存コードの再利用 → ③標準ライブラリ・プラットフォーム固有機能（DB 制約をアプリコードより、CSS を JS より） → ④導入済みの依存 → ⑤最小の新規実装 の順で解を探す（梯子を一段下りるごとに、その段で済まない理由を一つ添えること）
2. **Test** — 失敗するテストを書く（red）
3. **Implement** — テストを通す最小限のコード（green）
4. **Refactor** — テストが通る状態を維持しつつ整理
5. **Commit** — "why" を説明するメッセージで記録。push 前に CI と同じ静的チェックをローカルで通す（例: `mypy` / `ruff check` / `ruff format --check` — pytest green だけでは CI は通らない）

### Implementation Staging

複雑なタスクは 3-5 段階に分割し `IMPLEMENTATION_PLAN.md` で管理する：

```markdown
## Stage N: [Name]
**Goal**: [具体的な成果物]
**Success Criteria**: [テスト可能な完了条件]
**Tests**: [具体的なテストケース]
**Status**: Not Started | In Progress | Complete
```

- 進行に応じて Status を更新する
- 全 Stage 完了後にファイルを削除する（/outsource 経由の実装では削除しない——コマンド側の削除ポリシーに従う）

### 3-Strike Rule

1つの問題に対し **最大3回** まで試行する。3回失敗したら STOP：

1. **記録** — 何を試し、何が起き、なぜ失敗したか
2. **調査** — 2-3 の代替アプローチを探す
3. **再考** — 抽象度は正しいか？ より小さい問題に分割できないか？ もっと単純な方法はないか？
4. **確認** — 候補を提示し、ユーザー（または委任元）に選択を仰ぐ

### Completion Checklist

開発完了時に以下を **確認** する：

- **README.md** — 作成または更新が必要か
- **CHANGELOG.md** — 作成または更新が必要か

ドキュメントを勝手に乱造しないことと、この確認自体を省略しないことは両立する。

---

## Decision Priority

複数の妥当なアプローチが存在するとき、以下の優先順で選択する：

1. **Testability** — 容易にテストできるか
2. **Readability** — 6ヶ月後に理解できるか
3. **Consistency** — プロジェクトの既存パターンと一致するか
4. **Simplicity** — 動く最も単純な解か
5. **Reversibility** — 後から変更する難易度はどうか

---

## Compliance Marker

本規範がコンテキストに載っているとき、作業報告・最終応答の末尾に `[dev-rules applied]` と一行記す。規範の配線（常時ロード・preload・明示 Read のいずれの経路でも）が生きていることの観測点として機能する。
