# Changelog

## [0.1.0] - 2026-07-16

Phase 0〜1 完成（要件定義書_Fuhito_LoopExporter_v0.3.md の Phase 分割）。claude.ai の内部 JSON API 直取得により、DOM 仮想スクロールに起因するまだら採取を構造的に解消する私用 Chrome 拡張の初版。

### Added

- **Domain**（`src/domain/`）: `message_tree.js`（`parent_message_uuid` 連鎖から current leaf path を解決）、`blocks.js`（FR-5 コンテンツブロック変換規則、未知 type は生 JSON を警告付き保全）、`integrity.js`（FR-6 完全性検証: 連鎖・件数・空・鮮度の4検証）、`loop_format.js`（FR-4 Loop 互換ドキュメント直列化、FR-7 ファイル名 sanitize）。fetch / chrome.* / DOM 非依存の純粋関数のみ
- **UseCase**（`src/usecase/export_conversation.js`）: 取得→ツリー化→検証→（合格時のみ）変換→保存のオーケストレーション。検証失敗時は `IntegrityError` を投げ、保存系を一切呼ばない（fail-closed の UseCase 層保証）
- **Adapter**（`src/adapter/`）: `claude_api_gateway.js`（orgId 解決・キャッシュ、conversation 取得、実スキーマ→中間表現マッピング、未知フィールド警告付き保全）、`loop_file_presenter.js`（LoopDocument→テキスト＋ファイル名）
- **Infrastructure**（`manifest.json` / `src/content.js`）: MV3 最小権限構成（`https://claude.ai/*` のみ、`downloads` 権限なし）。会話ページ判定・ボタン注入・Loop 番号入力プロンプト・完全性検証結果に応じた成功/エラートースト・Blob DL・連打防止（実行中ボタン disabled）
- **テスト**: `node --test` で 64 件 green。フィクスチャ二層運用（`test/fixtures/` 合成・track 対象、`test/fixtures/local/` 実レスポンス・`.gitignore`）
- **ドキュメント**: `README.md`（導入・日常運用・開発ループ・一次切り分け・セキュリティ）、`docs/SCHEMA_NOTES.md`（API 実測スキーマ SSoT、Phase 0 成果物）
