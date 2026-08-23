# SCHEMA_NOTES — フヒト（LoopExporter）API 実測スキーマ

> Phase 0（Stage 1）の実測確定事項。要件定義書 §3.2 のスキーマ仮説を実測で上書きする一次資料。
> **本ファイルには実 orgId・実会話 uuid・本文断片は一切含まれない**（フィールド名と構造のみを記録する）。実物は `test/fixtures/local/`（.gitignore 済み・track 対象外）にのみ存在する。
> スキーマドリフト時は「壊れたときの一次切り分け」（要件 §9.4）に従い、下記の人手再採取手順で新レスポンスを採取し、本ファイルとの差分を確認すること。

## 1. 人手再採取手順（スキーマドリフト時に使用）

実装が壊れた・レスポンス形状が変わった疑いがあるときの再採取手順。**ブラウザ内 DevTools のみで完結させ、curl 等の外部呼び出しは行わない**（要件 §6 の禁止事項）。

1. claude.ai で対象の会話を開く（URL は `https://claude.ai/chat/{chatId}` の形）。
2. DevTools を開き Network タブへ切り替える。
3. フィルタ欄に `chat_conversations` と入力して絞り込む。
4. ページをリロードする（またはブラウザバック→再度会話を開く）と、GET リクエストが 1 件記録される。
5. そのリクエストを選択 → 右クリック → **Copy → Copy response**（または Response タブの内容を全選択してコピー）。
6. `test/fixtures/local/`（.gitignore 済みディレクトリ、初回は `mkdir -p` で作成）配下に任意のファイル名（先頭が `{` にならないよう注意——Chrome の自動命名がそのまま使われると URL 由来の `{` 始まりファイル名になることがある）で保存する。
7. 併せて `/api/organizations` へのリクエストも同じ手順（フィルタ欄に `organizations` と入力）で採取できると、gateway の orgId 解決ロジックの検証に使える（本 Stage では未採取・§5 参照）。
8. 保存したファイルは決して `git add` しない。合成フィクスチャ（`test/fixtures/` 直下）は実測差分をもとに手動で更新する。

## 2. 実測 URL

```
GET https://claude.ai/api/organizations/{orgId}/chat_conversations/{chatId}?tree=True&rendering_mode=messages&render_all_tools=true&consistency=strong
```

- 要件 §3.2 の仮説（`tree=True&rendering_mode=messages&render_all_tools=true`）との差分は **`consistency=strong` が追加される一点のみ**。それ以外はフロントエンドの実挙動と仮説が一致していた。
- `chatId` は URL パス `/chat/{uuid}` から取得する（要件どおり）。
- `orgId` はレスポンス本文には含まれない（`GET /api/organizations` から別途解決する必要がある。§5 参照）。

## 3. レスポンス構造（実測）

### 3.1 トップレベル

実測で確認したキー一覧（要件 §3.2 仮説は `name` / `chat_messages` のみを明示していたが、実際は以下 15 キー）:

```
uuid, name, summary, model, created_at, updated_at, settings,
is_starred, is_temporary, project_uuid, platform, is_wiggle_enabled,
effective_thinking_mode, current_leaf_message_uuid, chat_messages
```

- **`current_leaf_message_uuid` がトップレベルに存在する。** FR-3 の「UI 表示中の枝（current leaf path）」解決はこの値を起点に `parent_message_uuid` を遡行するだけでよく、`created_at` 比較などの推測ロジックは不要（実測で `current_leaf_message_uuid` は「一度も他メッセージの親になっていないノード（真の葉）」と一致することを確認済み）。
- `settings` はオブジェクトで、実測したサブキーは `enabled_web_search` / `enabled_sourdough` / `enabled_foccacia` / `enabled_mcp_tools` / `enabled_monkeys_in_a_barrel` / `enabled_saffron` / `tool_search_mode` / `preview_feature_uses_artifacts` / `enabled_artifacts_attachments` / `enabled_turmeric` / `thinking_mode` / `effort_level`（claude.ai 内部の機能フラグ群。Loop 変換には不要な情報のため FR-5 の変換規則では読み捨ててよい）。

### 3.2 `chat_messages[]` 要素

```
uuid, text, content, sender, index, created_at, updated_at,
truncated, attachments, files, sync_sources, parent_message_uuid
```

- `sender` は `human` | `assistant` の 2 値（実測: human 23 件 / assistant 23 件、計 46 件の標本で確認）。
- **`stop_reason` は assistant メッセージにのみ存在するフィールド**（human メッセージのキー一覧には現れない）。実測値は `end_turn` と `user_canceled` の 2 種（標本内訳: end_turn 22 件・user_canceled 1 件）。
- **root（会話の起点）メッセージの `parent_message_uuid` は定数 `00000000-0000-4000-8000-000000000000`。** FR-6 連鎖検証の終端判定に使う。標本では root に一致するメッセージが厳密に 1 件のみ存在することを確認済み。
- `attachments[]` と `files[]` はどちらもメッセージ直下の配列フィールドとして常に存在する（空配列でも欠落しない）。**標本では `attachments[]` は全メッセージで空、添付ファイル（doc 系）は `files[]` 側に実データが乗っていた**——要件 §3.2 は両者を区別せず書いていたが、実装時は `files[]` を主として扱う必要がある。`files[]` 要素の実測フィールド: `uuid, file_uuid, file_name, file_kind, path, size_bytes, success, created_at`。
- `sync_sources[]` は標本内では常に空配列（外部連携の同期ソースがあるメッセージが標本に含まれなかったため、非空時の形状は未確認）。
- `truncated` は真偽値フィールド。標本では常に `false`。
- **`input_mode` は 2026-07-16 の運用初日に出現した後付けフィールド（スキーマドリフト実測第一号）**。Phase 0 標本（同日 14 時台採取）には存在せず、同日中の再採取で一部の human メッセージにのみ付与されていた（実測 2 件）。入力方式（音声/キーボード等）のメタデータと推定されるが値・意味は未確認。Loop 変換には不要のため gateway の既知フィールド台帳に登録済み（警告は出ない）。NFR-3 の未知フィールド検知が設計どおり「うるさく」機能したことの記録として残す。
- **`compaction_summary` は 2026-07-18 に出現した後付けフィールド（スキーマドリフト実測第二号）**。L00556 エクスポート時に警告 `Unknown field "compaction_summary" on chat_messages[9]` として検知（1 メッセージのみ）。claude.ai のコンテキスト圧縮機能（長い会話でモデル側の文脈が要約される）由来のメタデータと推定されるが、値・形状は未採取（§5 残課題）。**圧縮が起きても `chat_messages[]` には全メッセージが残る**ことを FR-6 連鎖検証の通過（leaf→root 完走・ファイル出力成功・全 51 メッセージ直列化）で確認済みのため、Loop の完全性には影響しない。Loop 変換には不要のため gateway の既知フィールド台帳に登録済み（警告は出ない・回帰テストあり）。なお同じエクスポートで併発した警告 `Assistant message ... has no text block` は**別事象**——assistant ターンが 2 メッセージに分割された会話固有の状態（Loop 上は `## Claude` 見出しの連続、ヘッダ件数 human 25 / assistant 26 の非対称として正しく出力される）に対する integrity.js の設計どおりの注意喚起であり、スキーマドリフトではない。2026-08-23 の L00583 エクスポートでは `compaction_summary` を伴わず **no text block 単独 3 件**として再来した。台帳登録後は前者が黙るため、**以後の標準形はこちら**（ヘッダ件数 human 39 / assistant 42 の差 3 と警告数が一致、FR-6 通過）。2 件セット・単独のどちらで来ても切り分けはこの段落で足りる。分割位置は標本 2 件ともツール使用の途中だった（L00556 は 1 件、L00583 は 3 件＝`visualize:read_me`→`show_widget` の境目 1 箇所と bash_tool 長連鎖の途中 2 箇所）。**ツールを長く回すターンほど分割されるという読みは標本 2 件の観察であって確定ではない**が、これが正しければ警告件数はその回のツール使用量の粗い指標にすぎず、件数が跳ね上がっても異常ではない。判別は件数でなく非対称の一致で行う——**警告件数がヘッダの assistant − human の超過分と一致すればターン分割**、一致しなければ別事象として §1 の再採取手順へ進む。

### 3.3 `content[]` ブロック 4 種の実測形状

要件 §3.2 は type の列挙のみだったが、実測で各 type のフィールド一覧を確定した（`start_timestamp` / `stop_timestamp` は 4 種共通で付与される）。

| type | 実測フィールド一覧 |
|---|---|
| `text` | `type, text, citations, start_timestamp, stop_timestamp` |
| `thinking` | `type, thinking, summaries, cut_off, truncated, hidden, thinking_hidden, start_timestamp, stop_timestamp` |
| `tool_use` | `type, id, name, input, message, integration_name, icon_name, display_content, start_timestamp, stop_timestamp` |
| `tool_result` | `type, tool_use_id, name, content, is_error, meta, display_content, icon_name, integration_name, integration_icon_url, start_timestamp, stop_timestamp` |

補足:
- `text.citations` は標本内では常に空配列（フィールドは存在するが、非空時の要素形状は未確認）。
- `tool_use.name` / `tool_result.name` の実測値の例（claude.ai 標準ツールの汎用識別子。業務固有の値ではない）: `view` / `bash_tool` / `present_files` / `web_fetch` / `web_search`。`integration_name` の実測例: `File Creation` / `Web Fetch`。FR-5 の一行要約 `[tool: {name}]` はこの `name` フィールドを使う想定で問題ない。
- 未知の `content[].type`（上記 4 種以外）は標本内には出現しなかった。NFR-3 の「未知フィールドは警告付きで生 JSON 保全」は実装上のフォールバックとして維持する（実測で存在しないことは「今後も出ない」ことを意味しない）。

### 3.4 ページネーション（NFR-4）

- 標本（46 メッセージ・約 650KB）は **1 リクエストで全量が返った**。レスポンスにページネーション用のカーソル・`next` トークン等のフィールドは見当たらない。
- **1,000 メッセージ級の大規模会話でも同様に 1 リクエストで完結するかは未確認。NFR-4 の残課題として次 Stage 以降に持ち越す。**

## 4. 検証済み標本プロファイル

- 実体パス: `test/fixtures/local/L00553_conversation_full.json`（.gitignore 済み・このリポジトリには track されない）
- 有効な UTF-8 JSON（`JSON.parse` 成功）、664,067 bytes
- 46 メッセージ（human 23 / assistant 23）
- 分岐点 1（ある親メッセージに子が 2 通ぶら下がる）、葉ノード 2（分岐した死に枝の末端＋`current_leaf_message_uuid` が指す現行葉）
- 空 `content[]` のメッセージ 1 件（`sender: assistant` / `stop_reason: user_canceled` の死に枝）
- `content[]` の 4 type（text / thinking / tool_use / tool_result）を全て含有
- `files[]` に非空の添付（doc 系）を含むメッセージ 1 件、`attachments[]` は全件空、`sync_sources[]` は全件空
- `truncated: true` のメッセージは 0 件（標本内では未発生のケース）

この標本は分岐・死に枝・空 content・4 種 block を 1 会話に全て含む網羅的な個体のため、Stage 2 の合成フィクスチャ（`conversation_tree.json` / `conversation_pruned.json`）はこの構造をなぞって作成した（本文・UUID は全て架空の値に差し替え）。

## 5. 残課題（Stage 2 以降へ持ち越し）

- **NFR-4 大規模会話の未検証**: 1,000 メッセージ級でもページネーションなしに完走するかは未確認。実装後、大きめの実会話で回帰確認が必要。
- **仮想スクロール仮説（要件 §2.2）の検証は未実施**: DevTools Elements タブでのノード消滅目視は行っていない。「未検証（仮説のまま）」として記録する。API 直取得方式は DOM 状態に依存しないため、この仮説の真偽は実装の正しさに影響しない（検証は任意タスクのまま据え置いてよい）。
- **`GET /api/organizations` の実物は未採取**: gateway の orgId 解決ロジック用。本 Stage では要件 §3.2 の仮説形状（`[{ uuid: <orgId>, … }]`）に準拠した合成フィクスチャ（`test/fixtures/organizations.json`、架空 UUID）で代替した。Stage 3 の実装前後で実物採取が望ましいが、委任のブロッカーではない（HANDOFF.md にも同旨の記載あり）。
- `sync_sources[]` の非空時の要素形状、`text.citations` の非空時の要素形状は未確認（標本がどちらも空だったため）。将来これらを使うメッセージが実測できたら本ファイルを更新する。
- **`compaction_summary` の実物は未採取**: 値・形状は §1 の再採取手順（compaction が発生した長い会話を対象にする）で得られる。採取できたら §3.2 と gateway の台帳コメントを更新する。もし「古いメッセージの削除」や「要約メッセージのツリー挿入」を伴う挙動（＝Loop に異物が混じる/歴史が欠ける形）と判明した場合は、台帳登録では済まない設計判断になるため実装前にユーザーと協議すること（前者は FR-6 連鎖検証が hard fail で捕まえる設計）。
