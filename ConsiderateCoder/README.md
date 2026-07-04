# ConsiderateCoder

Clean Architecture × TDD × 三層委任（communicator / orchestrator / worker）を一つの開発方法論として配布するプラグイン。`/plan-sdd` で実装計画を編み、`/outsource` でその計画を委任実行する。

## 1. コンセプト

SDD（Spec-Driven Development）を外環、TDD（Test-Driven Development）を内環とする二重構造で開発を進める。SDD が要件・アーキテクチャ・Stage 分割を仕様として先に固め、各 Stage の内部では TDD の Red → Green → Refactor サイクルが回る。

この二重の環の上に、三層委任を重ねる：

- **communicator**（main セッション）— ユーザーとの対話・主題確定・完了時の検収を担当する。エージェント定義を持たず、`commands/outsource.md` が main の振る舞いとして規定する
- **orchestrator** — タスクの切り出し・worker への委任・成果物の物証レビュー・進捗管理を担当する。自らは調査も実装もしない（tools に Edit/Write を含まない構造保証）
- **worker** — スコープ済みブリーフを受け取り、調査・実装・検証を完遂する実働（Agent を `disallowedTools` で持たない——再委任しないことの構造保証）

Clean Architecture の 4 層は、収録物とそのまま対応する：

| Layer | 責務 | 収録物 |
|---|---|---|
| Domain | 開発方法論の規範そのもの | `skills/dev-rules/`・`skills/ops-rules/` |
| UseCase | 規範の上で回る役割編成 | `agents/` |
| Interface | ユーザー入口・レポート整形 | `commands/`, `templates/` |
| Infrastructure | 配布・接続 | `.claude-plugin/plugin.json`, marketplace エントリ |

依存は内向きのみ：`commands` → `agents` → 規範（`skills/*-rules`）。規範は agents・commands・プラグイン機構の存在を知らない。

## 2. なぜこの方法論か（Why）

### ① Rules の役割

`skills/dev-rules`・`skills/ops-rules` は、規範を揮発性コンテキスト（対話の流れ・その場限りの判断）から分離する。communicator はコマンド実行時に `${CLAUDE_PLUGIN_ROOT}` 参照で両規範を Read し、orchestrator / worker には起動時に `skills:` preload で **dev-rules の全文が注入される**（サブエージェントは Claude Code のフルシステムプロンプトを受け取らないため、規範は明示配線でのみ届く）。ops-rules は常時注入せず、`/plan-sdd` が該当 Stage の Success Criteria / Implementation Notes へ織り込むことでブリーフ経由で worker に届く——コンテキスト費用を規範の適用場面に応じてだけ払う設計。三者が同一の規範を共有するため、役割が変わっても規範がぶれない。

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
│   ├── outsource.md
│   └── dig.md
├── skills/
│   ├── dev-rules/
│   │   └── SKILL.md
│   └── ops-rules/
│       └── SKILL.md
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
- [`commands/dig.md`](commands/dig.md) — 意図が固まる前の深掘りインタビュー（隠れた前提・未検討リスクの掘り起こし）
- [`skills/dev-rules/SKILL.md`](skills/dev-rules/SKILL.md) — Clean Architecture・TDD Flow・3-Strike Rule・Decision Priority を定める開発規範（orchestrator / worker へ起動時に全文注入される）
- [`skills/ops-rules/SKILL.md`](skills/ops-rules/SKILL.md) — デプロイ・セキュリティ・コスト・LLM 統合防御のチェックリスト
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

## 5. 使い始める — 意図から完成まで

### 全体フロー

```text
あなたの意図（宣言的な成功像）
   │  まだ曖昧なら → /ConsiderateCoder:dig で掘り起こし
   ▼
/ConsiderateCoder:plan-sdd <意図>
   │  → IMPLEMENTATION_PLAN.md 生成 → あなたがレビュー・裁可
   ▼
実装 —— 2 つのパターンから選ぶ
   ├─ A. ペアプログラミング型（アドホック開発）
   │      main セッションで「Stage 1 を実装して」と順に指示し、
   │      対話しながら方向修正する。完了後に計画書を削除するのが既定
   └─ B. アウトソース型（委託開発）
          /ConsiderateCoder:outsource で三層委任。orchestrator/worker が
          実装を進め、communicator が検収して HTML レポート &
          理解度クイズを届ける。計画書は保持
```

### /plan-sdd に何を渡すか — インプットは「意図」

渡すのはプロンプト（手順指示）でも完全な仕様書でもなく、**意図＝宣言的な成功像**。「どうやるか」ではなく「何が実現されていれば成功か」を書く。

弱い例：

```text
/ConsiderateCoder:plan-sdd ログイン機能を作って
```

強い例（Goal / Constraints / Edge cases / Non-goals / Acceptance の観点を含む意図）：

```text
/ConsiderateCoder:plan-sdd 社内ツールにログイン機能が欲しい。
Goal: 既存の Google Workspace アカウントでシングルサインオンできること。
Constraints: パスワードは自前で保存しない。既存の Express サーバに載せる。
Edge cases: Workspace 外のアカウントは拒否してエラー画面を出す。
Non-goals: 権限管理（ロール）は今回はやらない。
Acceptance: 未ログインで /dashboard に来たら認証へ飛び、成功後に元のページへ戻る。
```

5 観点をすべて揃える必要はない——曖昧な部分は plan-sdd 側が調査と質問で補う。ただし**意図の解像度が計画の質を決める**。固まっていないと感じたら、先に `/ConsiderateCoder:dig` へ。

### 意図がまだ固まっていないとき — /dig

隠れた前提・未検討のリスク・暗黙の決定を、選択肢付きの深掘り質問で掘り起こすインタビューコマンド。「作りたい気はするが、何が決まっていないのか分からない」段階で最も効く。発見した決定は計画ファイルへ反映される。

### plan-sdd の後 — どちらで実装するか

| | A. ペアプログラミング型 | B. アウトソース型（/outsource） |
|---|---|---|
| 向く場面 | 方向修正しながら進めたい／変更が小さい／文脈依存の判断が多い | スコープが固まった／Stage が独立している／完了まで任せたい |
| あなたの関与 | Stage ごとに指示と確認 | 最初（裁可）と最後（検収レポート & クイズ）のみ |
| コンテキスト | main セッションに実装文脈が蓄積 | worker は常にフレッシュ、main は対話文脈を保持 |
| 計画書の扱い | 全 Stage 完了後に削除（既定） | 保持（検収・レポートの照合元） |

どちらの場合も、各 Stage の内部は規範（dev-rules）の TDD Flow（Red → Green → Refactor → Commit）で進む。

とくにアウトソース型では、main セッション（communicator）自体を高い器で走らせるのが効く——**Opus 以上（可能なら Fable / Mythos 級）× effort `xhigh` 以上を推奨**。詳細は「モデル配分チューニング指針」の章を参照。

> `/ConsiderateCoder:plan-sdd`・`/ConsiderateCoder:outsource` を引数無しで呼ぶと、この使い方の要約が表示される。

## 6. /plan-sdd リファレンス

```
/ConsiderateCoder:plan-sdd <機能名・対象スコープ・背景>
```

同梱の規範（dev-rules / ops-rules）に従い、既存コードの調査（類似実装3件の把握）を経て `IMPLEMENTATION_PLAN.md` を対象プロジェクト直下に生成する。生成物の構造：

- **Overview** — What / Why / Where / Reference Patterns
- **Architecture** — Clean Architecture 4層の責務分解表 + Dependency Direction
- **Stages** — 3-5 段階、各段が Goal / Layer / Success Criteria / Tests / Implementation Notes / Status を持つ
- **Documentation Plan** — README/CHANGELOG/本計画書の基本セット + 拡張レイヤーの棚卸し
- **Decision Priority Notes** — Testability > Readability > Consistency > Simplicity > Reversibility の適用記録
- **3-Strike Rule** — 詰まりやすい予想ポイントと代替アプローチ、ユーザーに相談する判断ライン

計画作成のみを行い、実装はユーザーが明示的に指示するまで着手しない。

## 7. /outsource リファレンスと運用律

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

## 8. モデル配分チューニング指針

設計思想は「最も高い器が采配し、廉価な器が全力で手を動かす」。

- **communicator（main セッション）** — **Opus 以上（可能なら Fable / Mythos 級）× effort `xhigh` 以上を推奨**。主題確定・ブリーフ結晶化・検収（報告を鵜呑みにしない物証照合）・上申裁定と、三層で最も高い判断力を要する層。さらに orchestrator が `inherit` 既定のため、**main セッションの器がそのまま采配の器を兼ねる——communicator のモデル選択は二重に効く**。Claude Code では `/model` で切り替えられる
- **orchestrator** — 既定は `model: inherit`（呼び出し元＝communicator の器を継ぐ）。采配の質が成果物全体の質を左右するため、communicator 側を高い器にするか、frontmatter で明示指定する
- **worker** — 既定は `model: sonnet` / `effort: max`。実働は数を打つ場面が多く、コストと質のバランスを取った既定値

利用者は [`agents/orchestrator.md`](agents/orchestrator.md) / [`agents/worker.md`](agents/worker.md) の frontmatter（`model:` / `effort:`）を1行書き換えるだけで上書きできる。本文の運用律は変更不要。このチューニング指針は README にのみ記載し、agent 本文には書かない（単一正典の維持）。

> **注意**: 環境変数 `CLAUDE_CODE_SUBAGENT_MODEL` が設定されていると、agent frontmatter の `model:` も呼び出し時の指定も**黙って上書き**され、すべてのサブエージェントの器が変わる（`inherit` を設定すれば通常の解決順に戻る）。挙動がこの指針と食い違うときは、まずこの環境変数を疑う。

## 9. FAQ

**Q. 既存の `CLAUDE.md` やローカルの `.claude/rules/` と衝突しないか？**
A. 衝突しない。プラグイン内の規範（`skills/dev-rules`・`skills/ops-rules`）は配布向けに一般化した版であり、リポジトリ固有の `CLAUDE.md` や既存のローカル規範を上書きしない。同じ規範を指していれば重複があっても実害はなく、内容が食い違う場合はローカル側を正とする。

**Q. pytest が無い環境でもテンプレートは動作するか？**
A. 動作する。`templates/outsource-report.template.html` は外部リソース読み込みや `<script>` を持たない自己完結 HTML で、プレースホルダの文字列置換だけで生成できる。`tests/` の pytest はプラグイン自体の構造検証用であり、`/plan-sdd` や `/outsource` の実行には依存しない。

**Q. 規範（dev-rules / ops-rules）をメイン会話にも常時ロードできるか？**
A. 既定では、communicator はコマンド実行時に Read、orchestrator / worker は `skills:` preload で dev-rules を受け取る（メイン会話への常時ロードはされない）。メイン会話にも常時ロードしたい場合は、プロジェクトの `.claude/rules/` を本プラグインの `skills/` ディレクトリへの junction（Windows）/ symlink（macOS/Linux）にする——`.claude/rules/` はサブディレクトリを再帰的に読むため、`dev-rules/SKILL.md`・`ops-rules/SKILL.md` の両方が常時ロードに乗り、コピーが存在しないので反映漏れも構造的に起きない。ops-rules の paths frontmatter によるパススコープ適用も `.claude/rules/` 配下でのみ機能する。

**Q. agents に memory を持たせられるか？**
A. 意図的に非搭載（設計判断）。orchestrator は「Edit/Write を持たない」構造保証を採っているが、`memory:` を有効化すると tools 指定に関わらず Read/Write/Edit が自動有効化されるため、無筆記の構造保証と memory は構造的に排他になる。worker 側の非搭載も「常にフレッシュなコンテキストで品質が上がる」という設計そのもの——記憶を持てば前回の枝葉を引きずる。

**Q. main セッションに communicator の agent 定義が無いのはなぜか？**
A. main は Claude Code harness の与件であり、プラグインが差し替えられる層ではないため。`commands/outsource.md` が main セッションの振る舞いとして communicator のフローを規定する。

**Q. orchestrator / worker の規律を hooks で機械的に強制できるか？**
A. プラグイン配布のサブエージェントでは、セキュリティ上の理由で frontmatter の `hooks` / `mcpServers` / `permissionMode` が**無視される**（`tools` / `disallowedTools` は有効——本プラグインの構造保証はこの範囲で設計している）。また委任先を限定する `Agent(worker)` のような括弧構文はメインスレッド専用で、サブエージェント定義では括弧内が無視される——orchestrator が worker 以外を起動しないのは**プロンプト規律**である。フックによる機械強制まで必要なら、agent ファイルを `.claude/agents/` へコピーして利用者側でフィールドを追加する（**配布形態が強制力の上限を決める**）。

**Q. orchestrator と worker の役割を入れ替えたり、二層以上に増やせるか？**
A. 本プラグインは三層委任を固定の設計としている。層を増減させたい場合は `agents/` に新しい定義を追加し、`commands/outsource.md` のフローを合わせて調整する必要がある。
