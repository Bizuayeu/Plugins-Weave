# フヒト（Fuhito）— LoopExporter

claude.ai の会話を、内部 JSON API から直接取得して EpisodicRAG の Loop 互換形式（`.txt`）でローカル保存する、私用の Chrome 拡張（MV3・unpacked）です。

> 仮称「フヒト」の由来：史部（ふひとべ）＝ヤマト王権の記録官氏族。対話の場に立ち入らず、外から記録だけを取る役割の写し。

## これは何か

- **課題**: 現行の DOM スクレイピング手段（Save my Chatbot）は、本番スレッドで仮想スクロールにより本文がまだらに欠落する。EpisodicRAG の Loop は記憶コーパスの正典＝不可逆ドメインであり、まだらな採取物が気づかれず Digest 階層へ流れる「静かな失敗」を構造的に排除する必要がある。
- **解法**: claude.ai フロントエンドが自身のために叩く内部 JSON API を same-origin fetch で直取得する。DOM のマウント状態と無関係になるため、仮想スクロール問題が原理的に消える。
- **不可逆ドメインへの態度**: 完全性検証（連鎖・件数・空・鮮度の4検証）に一つでも失敗したら、**ファイルを出力せずエラー表示で停止**する（fail-closed）。まだらなファイルを黙って出さないことが、このツールの存在理由。
- **スコープ**: 単一会話の current leaf path（UI に表示されている一枝）を Loop 形式へ変換してローカル DL するところまで（Phase 0〜1）。全ツリー出力・thinking 展開・一括エクスポートは非対応（YAGNI 境界。詳細は [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) の Non-goals）。

要求の正典は [要件定義書_Fuhito_LoopExporter_v0.3.md](./要件定義書_Fuhito_LoopExporter_v0.3.md)（v0.3 で凍結。以後の運用手順の更新はこの README 側で行う）。実装計画は [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)。

## 導入（初回のみ・ストア不使用）

1. 拡張フォルダ（`manifest.json` が直下にあるこの `LoopExporter/` ディレクトリ）をローカルに配置する。この git リポジトリの clone をそのまま指定するのが推奨（フヒト自体がバージョン管理下にある）。
2. Chrome で `chrome://extensions` を開き、右上の「デベロッパーモード」を ON にする。
3. 「パッケージ化されていない拡張機能を読み込む」→ 手順1の `LoopExporter` フォルダを指定する。

以上で有効化。ブラウザ再起動後も維持される。ストア審査・パッケージング・署名は不要で、権限確認ダイアログも出ない（`downloads` 権限を含め追加権限を要求しない最小構成のため）。

**注意事項**:
- 読み込みは**フォルダの実体参照**。読み込み後にフォルダを移動・削除・リネームすると拡張が無効化される。
- コード修正は自動反映されない。`chrome://extensions` の拡張カードの更新ボタン（↻）で再読み込みする。

## 日常運用（1 Loop の採取）

1. claude.ai で保存したい会話を開く（スクロール位置は不問——DOM を読まないため）。
2. 画面右下固定のボタン「フヒト: Loop保存」（ダーク角丸）を押す。会話ページ（`/chat/{uuid}`）以外で押すと「会話ページ（claude.ai/chat/{id}）で実行してください。」と表示され、そこで停止する。
3. `window.prompt` で Loop 番号を聞かれる：「フヒト: Loop番号を入力してください（例: L00553）。空欄でキャンセル。」デフォルトは空欄——番号は推測しない。**キャンセルまたは空欄で無音終了**（ファイルは出ない）。採番の正典は大環主側にある。
4. 完全性検証が通れば、`L{番号}_{タイトル}.txt` がブラウザ既定の DL 先へダウンロードされ、ボタン直上に成功トースト「保存しました: {filename}」（12秒で自動消滅）が表示される。トーストには human/assistant 件数と鮮度（最終メッセージ日時、「最新まで採れているか」の一目確認用）、警告があれば先頭3件と残数も併記される。
5. 検証に**通らなければファイルは出ず**、赤系のエラートーストで理由が表示される（後述の一次切り分け参照）。
6. 実行中はボタンが disabled になる（連打防止＝「1クリック1GET」の運用規律の実装）。

Loop ファイルの中身の形式（ヘッダブロック・`## User` / `## Claude` 交互見出し）は [EpisodicRAG GLOSSARY](../EpisodicRAG/GLOSSARY.md#loop) を正典として参照。ここでは重複記述しない。

## 開発ループ（Claude Code との往復）

```
Claude Code で編集 → chrome://extensions で ↻ → claude.ai でボタンを押して試す
```

の三拍子。修正のたびにこのループを回す。

- 変換ロジック（Domain / UseCase / Adapter）の単体テストは `node --test` で完結させる（後述）。
- ブラウザでの手動確認は結合部（ボタン注入・fetch・DL）に絞る。
- `content_scripts.js` は `manifest.json` に配列で列挙されたファイルを domain → adapter → usecase → content の順で classic script として順次ロードする（ビルドなし）。ファイルを追加・並べ替えた場合は `manifest.json` の配列も更新すること。
- **各 src ファイルは必ず IIFE（`(function () { ... })();`）で包む**——classic script は全ファイルが一つのグローバル lexical スコープを共有するため、トップレベルの `const`/`class` がファイル間で衝突すると後続ファイルが SyntaxError で丸ごと死ぬ（Node の `require` 経路では再現しない）。回帰は `test/classic_script_load.test.js`（ブラウザ条件のシミュレーション）が検知する。

### テスト実行

```bash
cd LoopExporter
npm test
```

Node 組み込みの `node --test`（依存ゼロ）。フィクスチャは二層運用——`test/fixtures/`（合成・track 対象）と `test/fixtures/local/`（実レスポンス・`.gitignore` 済み）。スキーマドリフトを検知したら合成フィクスチャ側を更新する。

## セキュリティと運用規律

- **自分の会話のみ**: ログイン済みブラウザセッションの same-origin fetch のみを使う。cookie を持ち出して curl 等ブラウザ外から叩く実装は行わない（bot 対策抵触につき禁止）。
- **手動トリガのみ**: 自動巡回・一括連打は行わない。1クリック1GET（実行中はボタン disabled で構造的に強制）。
- **外部送信ゼロ**: 通信先は claude.ai same-origin のみ。テレメトリなし。GitHub 等への直接送信機能は持たない（Write 系 credential をブラウザに置かない＝攻撃面ゼロ）。
- **最小権限**: `manifest.json` の permissions は `content_scripts.matches: ["https://claude.ai/*"]` のみ。`downloads` 等の追加権限は要求しない（Blob + `<a download>` で権限不要の DL を実現）。
- **内部 API は無保証**: Anthropic 側の変更で壊れうる。依存点が「エンドポイント＋スキーマ」の一点に集約されるため、DOM 依存より修理コストは低い（NFR-2/3 で受ける設計）。

## 一次切り分け（壊れたとき）

- **エラー「会話ページで実行してください」**: 非会話ページでボタンを押した。対象会話を開き直す。
- **エラー「完全性検証に失敗したため、ファイルは出力していません」**: 仕様どおりの fail-closed 停止。レスポンス構造の変化が疑われる。[docs/SCHEMA_NOTES.md](./docs/SCHEMA_NOTES.md) の手順で新レスポンスを再採取し、フィクスチャ差分を確認する。
- **セッション切れ（401/403）**: claude.ai に再ログインしてから再試行する。
- **API 変更疑い（404/5xx 等）**: [docs/SCHEMA_NOTES.md](./docs/SCHEMA_NOTES.md) の手順で再採取・修理する。
- **暫定回避**: どうしても急ぐ場合のみ、従来の共有リンク＋Save my Chatbot 迂回を使う（恒久運用はしない）。

## ディレクトリ構成

```
LoopExporter/
├── manifest.json              # MV3、最小権限
├── package.json                # private・依存ゼロ・scripts.test のみ
├── src/
│   ├── domain/                 # message_tree / blocks / integrity / loop_format（純粋関数のみ）
│   ├── adapter/                # claude_api_gateway / loop_file_presenter
│   ├── usecase/                # export_conversation
│   └── content.js               # MV3 結線（ボタン注入・DL）
├── test/                       # node:test（fixtures/ は track、fixtures/local/ は .gitignore）
├── docs/SCHEMA_NOTES.md        # API 実測スキーマの SSoT
├── README.md / CHANGELOG.md
└── 要件定義書_Fuhito_LoopExporter_v0.3.md   # 要求 SSoT（v0.3 凍結）
```

## 関連ドキュメント

- [要件定義書_Fuhito_LoopExporter_v0.3.md](./要件定義書_Fuhito_LoopExporter_v0.3.md) — 要求 SSoT（背景・方式選定・FR/NFR/AC、凍結）
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — Clean Architecture の Stage 分割と判断確定履歴
- [docs/SCHEMA_NOTES.md](./docs/SCHEMA_NOTES.md) — API 実測スキーマの SSoT
- [CHANGELOG.md](./CHANGELOG.md) — バージョン履歴
- [EpisodicRAG GLOSSARY](../EpisodicRAG/GLOSSARY.md#loop) — Loop 形式仕様の正典
