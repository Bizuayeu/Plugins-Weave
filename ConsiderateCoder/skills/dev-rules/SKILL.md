---
name: dev-rules
description: Development methodology rules (Clean Architecture, TDD flow, 3-Strike rule, decision priority) that govern planning, implementation, and review. Load before designing, staging, implementing, or reviewing code changes.
---

# Development Guidelines

本規範は単体で完結する（メイン会話・サブエージェントのどちらで読まれても前提を欠かない）。

## General Principles

- **求められたものを作る** — 頼まれていない機能・抽象化・設定項目を先回りで足さない（YAGNI）
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

1. **Understand** — 既存コードから類似機能を3つ探し、パターンを把握する
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
