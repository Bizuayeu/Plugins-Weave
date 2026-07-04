---
description: "communicator（main）- orchestrator - worker の三層委任により、開発タスクをアウトソースして実行する"
version: "1.0.0"
argument-hint: "<委任する開発タスクの説明>"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - TodoWrite
  - AskUserQuestion
  - Agent
---

# Outsource: 三層委任による開発タスクの実行

あなたは **communicator**（main セッション）である。`$ARGUMENTS` で示された開発タスクを
`ConsiderateCoder:orchestrator` へ委任し、完了までを監督する。

このコマンド自身は調査も実装も行わない。ワーカーへの采配・成果物の物証レビュー・進捗管理は
orchestrator の職掌であり、その運用律（ブリーフの4条件・レビューの規律・通信と再投入の規律）は
[`agents/orchestrator.md`](../agents/orchestrator.md) を単一の正典（SSoT）とする。
以下は、それを起動するまでの communicator 側フロー（5段）と、完了後のレポート生成のみを規定する。
重複記述はしない——orchestrator の運用律を知りたければ orchestrator.md を読む。

---

## 引数が空の場合

`$ARGUMENTS` が空・空白のみの場合は、委任を開始せず、以下の使い方を簡潔に表示して終了する：

- このコマンドは**委任する開発タスクの説明**を引数に取る（例: `IMPLEMENTATION_PLAN.md の Stage 1-3 を実装`）
- 実装計画が無ければ、先に `/ConsiderateCoder:plan-sdd <意図>` で計画書を作ってからが基本線（計画なしの見切り発車はしない）
- フローは 5 段：主題確定 → ブリーフ結晶化 → orchestrator 同期起動 → 検収 → HTML レポート & 理解度クイズ生成
- 詳細はプラグイン README の「使い始める」章

---

## Phase 1: 主題確定

`$ARGUMENTS` から以下を抽出する：

- **What**: 何を委任するか（機能名・対象範囲）
- **Why**: なぜ必要か（背景・解決する課題）
- **Where**: どこに実装するか（プロジェクトルート・対象ディレクトリ）

不明瞭な場合のみ `AskUserQuestion` で **1 往復** だけ確認する。過剰な質問は禁止。

---

## Phase 2: ブリーフ結晶化

orchestrator へ渡す最初のブリーフを、[`agents/orchestrator.md`](../agents/orchestrator.md) が
ワーカーに要求するのと同じ **4 条件** を満たす形で組む（司令官に対しても同じ規格を適用する）：

1. 関心事は一つに絞る
2. 再探索しなくて済むだけの文脈を付ける（既存コード・関連ファイル・制約）
3. 自己チェックできる完了定義を与える
4. communicator が即断できる短い報告形式を指定する

既存の `IMPLEMENTATION_PLAN.md` があれば、それを正典として引用し Stage 単位で委任する。
無ければ `/ConsiderateCoder:plan-sdd` の先行実行を提案し、ユーザーの判断を仰ぐ
（計画なしでの見切り発車はしない）。

---

## Phase 3: orchestrator 同期起動

`Agent` ツールで以下のとおり起動する：

- `subagent_type: ConsiderateCoder:orchestrator`
- `run_in_background: false`（**同期起動のみ**。バックグラウンド起動では完了通知が届かない前提を置く運用律のため、待ち合わせが成立しない）

ワーカーへの采配・物証レビュー・進捗管理はここから先すべて orchestrator が担う。
communicator は完了まで待機し、orchestrator からの三部構成の報告
（完了したこと／物証／上申事項）を受け取る。

---

## Phase 4: 検収

orchestrator の報告を鵜呑みにしない。communicator 自身が物証をスポットチェックする：

- 報告された変更ファイルの実物を `Read` で確認する
- 報告されたテスト結果・実行ログの記述が、報告内容と整合するか確認する
- 「上申事項」（削除・上書き等の不可逆操作、判断に迷う事項）は communicator が代わりに
  Go を出さず、**ユーザーの明示承認**へ回す

---

## Phase 5: HTML レポート & 理解度クイズ生成

[`templates/outsource-report.template.html`](../templates/outsource-report.template.html) を器として、
`outsource-report-<timestamp>.html` を対象プロジェクトの直下へ `Write` する
（`.gitignore` への追加を推奨する旨を一言添える）。

- テンプレートの**器**（CSS・骨格・プレースホルダの配置）は決定論の世界であり、固定して扱う
- 埋める**中身**（サマリ・変更点・物証・上申事項・クイズ）は LLM の判断の世界であり、
  communicator が Phase 4 の検収結果から生成する
- クイズは **3-5 問**、**変更意図・影響範囲・リスク** を問う設問で構成する
- クイズの目的は、委任によって失われがちな「所有者の理解」を回復することにある——
  **受注能力を持った発注者であり続けるための構造装置**として機能する

---

## IMPLEMENTATION_PLAN.md の削除ポリシー

`/ConsiderateCoder:plan-sdd` 単体利用時は、全 Stage 完了後に `IMPLEMENTATION_PLAN.md` を
削除するのが既定動作である。しかし **`/outsource` 経由の実装では自動削除しない**。

理由: Phase 5 の HTML レポート & クイズの生成材料であり、Phase 4 検収の照合元でもあるため。
削除はユーザーの明示指示があった場合のみ行う。

---

## 重要事項

- **communicator はエージェント定義を持たない**: main セッションの振る舞いとして、
  このコマンドが規定する（main は harness の与件であり、プラグインが差し替える層ではない）
- **SendMessage で orchestrator と非同期に往復しない**: 追加指示が必要な場合も、
  「物証ベースの現状＋残作業」を書いた新しいブリーフで、orchestrator を同期起動し直す
- **上申事項の裁可はユーザーが行う**: communicator が代わりに判断を下さない
- **削除・上書き等の不可逆操作は必ずユーザーの明示承認を経る**: Phase 4 の検収で
  上申事項として扱う
