# ConsiderateCoder

Clean Architecture × TDD × 三層委任（communicator / orchestrator / worker）を一つの開発方法論として配布するプラグイン。`/plan-sdd` で実装計画を編み、`/outsource` でその計画を委任実行する。

## 1. コンセプト

SDD（Spec-Driven Development）を外環、TDD（Test-Driven Development）を内環とする二重構造で開発を進める。SDD が要件・アーキテクチャ・Stage 分割を仕様として先に固め、各 Stage の内部では TDD の Red → Green → Refactor サイクルが回る。

この二重の環の上に、三層委任を重ねる：

- **communicator**（main セッション）— ユーザーとの対話・主題確定・完了時の検収を担当する。エージェント定義を持たず、`commands/outsource.md` が main の振る舞いとして規定する
- **orchestrator** — タスクの切り出し・worker への委任・成果物の物証レビュー・進捗管理を担当する。自らは調査も実装もしない（tools に Edit/Write を含まない構造保証）
- **worker** — スコープ済みブリーフを受け取り、調査・実装・検証を完遂する実働

Clean Architecture の 4 層は、収録物とそのまま対応する：

| Layer | 責務 | 収録物 |
|---|---|---|
| Domain | 開発方法論の規範そのもの | `rules/` |
| UseCase | 規範の上で回る役割編成 | `agents/` |
| Interface | ユーザー入口・レポート整形 | `commands/`, `templates/` |
| Infrastructure | 配布・接続 | `.claude-plugin/plugin.json`, marketplace エントリ |

依存は内向きのみ：`commands` → `agents` → `rules`。rules は agents・commands・プラグイン機構の存在を知らない。

## 2. なぜこの方法論か（Why）

### ① Rules の役割

`rules/DEV.md`・`rules/OPS.md` は、規範を揮発性コンテキスト（対話の流れ・その場限りの判断）から分離する。communicator・orchestrator・worker のいずれも同一の rules を参照するため、役割が変わっても規範がぶれない。

### ② なぜ SDD か

要件と完了条件を着手前に明確化しておくことが、最終的な品質を決める。手戻りのコストが高い作業ほど、着手前の認識合わせが結果の大半を決めるという原理に基づく——`/plan-sdd` が生成する `IMPLEMENTATION_PLAN.md` は、この認識合わせを文書として固定する装置である。

### ③ アウトソース開発の利点

- **開発の全非同期化** — communicator は待機するだけで、調査・実装は orchestrator/worker 側で完結する
- **適材適所のモデル配分によるトークンコスト最適化** — 采配には高性能なモデル、実働には廉価なモデルを割り当てる
- **ブリーフ規格が要件・完了条件を強制的に明確化** — 「関心事は一つ」「文脈」「完了定義」「報告形式」の4条件を満たさないブリーフは委任として成立しない
- **worker は常にフレッシュなコンテキストで品質が向上** — 前段の対話の枝葉に引きずられず、渡されたブリーフだけに集中できる
- **communicator は文脈を保持しているためレビュー・全体感の把握・ユーザーへの説明に優れる** — 対話の経緯を知っているのは communicator だけであり、検収と説明はここに集約する

### ④ クイジングの効果

`/outsource` が生成する HTML レポートには理解度クイズを添える。目的は正解を問うことではなく、**受注能力を持った発注者であり続けること**——委任によって手放されがちな「変更の理解」の所有権を、発注者側に保持し続けるための構造装置である。クイズは変更意図・影響範囲・リスクを問う設問で構成する。

## 3. 収録物

```
ConsiderateCoder/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── orchestrator.md
│   └── worker.md
├── commands/
│   ├── plan-sdd.md
│   └── outsource.md
├── rules/
│   ├── DEV.md
│   └── OPS.md
├── templates/
│   └── outsource-report.template.html
├── tests/
├── README.md
└── CHANGELOG.md
```

- [`agents/orchestrator.md`](agents/orchestrator.md) — 采配・委任・物証レビュー・進捗管理を担う司令官定義
- [`agents/worker.md`](agents/worker.md) — スコープ済みタスクの調査・実装・検証を完遂する実働定義
- [`commands/plan-sdd.md`](commands/plan-sdd.md) — `IMPLEMENTATION_PLAN.md` を生成する SDD 計画コマンド
- [`commands/outsource.md`](commands/outsource.md) — communicator - orchestrator - worker の三層委任フローの入口コマンド
- [`rules/DEV.md`](rules/DEV.md) — Clean Architecture・TDD Flow・3-Strike Rule・Decision Priority を定める開発規範
- [`rules/OPS.md`](rules/OPS.md) — デプロイ・セキュリティ・コスト・LLM 統合防御のチェックリスト
- [`templates/outsource-report.template.html`](templates/outsource-report.template.html) — 検収レポート & 理解度クイズの自己完結 HTML 雛形
- [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) — プラグインマニフェスト
- [`CHANGELOG.md`](CHANGELOG.md) — 変更履歴
- `tests/` — 構造テスト（stdlib のみ、pytest）

## 4. インストール

```
/plugin marketplace add https://github.com/Bizuayeu/Plugins-Weave
/plugin install ConsiderateCoder@plugins-weave
```

インストール後、コマンドと agent は `ConsiderateCoder:` namespace 配下に配置される（例: `/ConsiderateCoder:plan-sdd`、`subagent_type: ConsiderateCoder:orchestrator`）。

## 5. /plan-sdd の使い方

```
/ConsiderateCoder:plan-sdd <機能名・対象スコープ・背景>
```

対象プロジェクトの `rules/DEV.md` に従い、既存コードの調査（類似実装3件の把握）を経て `IMPLEMENTATION_PLAN.md` を対象プロジェクト直下に生成する。生成物の構造：

- **Overview** — What / Why / Where / Reference Patterns
- **Architecture** — Clean Architecture 4層の責務分解表 + Dependency Direction
- **Stages** — 3-5 段階、各段が Goal / Layer / Success Criteria / Tests / Implementation Notes / Status を持つ
- **Documentation Plan** — README/CHANGELOG/本計画書の基本セット + 拡張レイヤーの棚卸し
- **Decision Priority Notes** — Testability > Readability > Consistency > Simplicity > Reversibility の適用記録
- **3-Strike Rule** — 詰まりやすい予想ポイントと代替アプローチ、ユーザーに相談する判断ライン

計画作成のみを行い、実装はユーザーが明示的に指示するまで着手しない。

## 6. /outsource の使い方と運用律

```
/ConsiderateCoder:outsource <委任する開発タスクの説明>
```

5段のフローで進む：

1. **主題確定** — What / Why / Where を抽出し、不明瞭な点のみ1往復で確認する
2. **ブリーフ結晶化** — orchestrator へ渡す最初のブリーフを、worker への委任と同じ4条件で組む
3. **orchestrator 同期起動** — `run_in_background: false` で起動し、以降の采配・レビュー・進捗管理を委ねる
4. **検収** — orchestrator の報告を鵜呑みにせず、communicator 自身が変更ファイル・テスト結果を物証照合する。上申事項はユーザーの明示承認へ回す
5. **HTML レポート & 理解度クイズ生成** — `templates/outsource-report.template.html` を器に、検収結果を埋めたレポートを生成する

`IMPLEMENTATION_PLAN.md` の削除ポリシーはここで分岐する。`/plan-sdd` 単体利用時は全 Stage 完了後に削除するのが既定だが、**`/outsource` 経由では自動削除しない**（レポート & クイズの生成材料、検収の照合元として保持する）。

運用律（ブリーフの4条件・レビューの規律・通信と再投入の規律）の詳細は [`agents/orchestrator.md`](agents/orchestrator.md) を単一の正典とする。ここでは重複記述しない。

## 7. モデル配分チューニング指針

設計思想は「最も高い器が采配し、廉価な器が全力で手を動かす」。

- **orchestrator** — 既定は `model: inherit`（呼び出し元の器をそのまま継ぐ）。采配の質が成果物全体の質を左右するため、高性能なモデルの明示指定を推奨する
- **worker** — 既定は `model: sonnet` / `effort: max`。実働は数を打つ場面が多く、コストと質のバランスを取った既定値

利用者は [`agents/orchestrator.md`](agents/orchestrator.md) / [`agents/worker.md`](agents/worker.md) の frontmatter（`model:` / `effort:`）を1行書き換えるだけで上書きできる。本文の運用律は変更不要。このチューニング指針は README にのみ記載し、agent 本文には書かない（単一正典の維持）。

## 8. FAQ

**Q. 既存の `CLAUDE.md` やローカルの `rules/` と衝突しないか？**
A. 衝突しない。プラグイン内の `rules/DEV.md`・`rules/OPS.md` は配布向けに一般化した版であり、リポジトリ固有の `CLAUDE.md` や既存のローカル規範を上書きしない。同じ規範を指していれば重複があっても実害はなく、内容が食い違う場合はローカル側を正とする。

**Q. pytest が無い環境でもテンプレートは動作するか？**
A. 動作する。`templates/outsource-report.template.html` は外部リソース読み込みや `<script>` を持たない自己完結 HTML で、プレースホルダの文字列置換だけで生成できる。`tests/` の pytest はプラグイン自体の構造検証用であり、`/plan-sdd` や `/outsource` の実行には依存しない。

**Q. main セッションに communicator の agent 定義が無いのはなぜか？**
A. main は Claude Code harness の与件であり、プラグインが差し替えられる層ではないため。`commands/outsource.md` が main セッションの振る舞いとして communicator のフローを規定する。

**Q. orchestrator と worker の役割を入れ替えたり、二層以上に増やせるか？**
A. 本プラグインは三層委任を固定の設計としている。層を増減させたい場合は `agents/` に新しい定義を追加し、`commands/outsource.md` のフローを合わせて調整する必要がある。
