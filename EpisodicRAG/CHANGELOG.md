# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.5] - 2025-11-27

### Added
- **finalize/ パッケージ**: `finalize_from_shadow.py` を4つのモジュールに分割
  - `finalize/shadow_validator.py`: Shadow検証（ShadowValidator クラス）
  - `finalize/provisional_loader.py`: Provisional読込（ProvisionalLoader クラス）
  - `finalize/digest_builder.py`: Digest構築（RegularDigestBuilder クラス）
  - `finalize/persistence.py`: 永続化処理（DigestPersistence クラス）
  - `finalize/__init__.py`: 公開API

### Changed
- **リファクタリング Phase 4**: finalize_from_shadow.py のFacade分割
  - 497行 → 203行に削減（約59%削減）
  - 元ファイルはFacadeとして後方互換性を維持
  - 既存APIに変更なし（全129テストがパス）

---

## [1.1.4] - 2025-11-27

### Changed
- **リファクタリング Phase 3**: 例外処理の完全移行
  - `exceptions.py` の例外クラス（`ValidationError`, `DigestError`, `FileIOError`）を実際に使用開始
  - `grand_digest.py`: 3箇所の `log_error()` → `raise DigestError()` に置換
  - `finalize_from_shadow.py`: 12箇所の `log_error()` → 適切な例外に置換、`main()` に例外ハンドラ追加
  - `save_provisional_digest.py`: 2箇所の `log_error()` → `raise FileIOError()` に置換、`EpisodicRAGError` ハンドラ追加
  - 各メソッドの戻り値を `bool`/`Optional` から例外ベースに変更
  - 関連テストを `assertFalse()` → `assertRaises()` に更新

---

## [1.1.3] - 2025-11-27

### Added
- **__version__.py**: バージョン定数のSingle Source of Truth（`DIGEST_FORMAT_VERSION`）を新規作成

### Changed
- **リファクタリング Phase 1**: バージョン文字列の集約
  - `grand_digest.py`, `shadow_grand_digest.py`, `finalize_from_shadow.py`, `save_provisional_digest.py` でハードコードされていた `"1.0"` を `DIGEST_FORMAT_VERSION` 定数に置換
- **リファクタリング Phase 2**: validators.py の段階的採用
  - `grand_digest.py`: `isinstance()` → `is_valid_dict()` に置換
  - `digest_times.py`: `isinstance()` → `is_valid_list()` に置換
  - `shadow_grand_digest.py`: 3箇所の `isinstance()` → `is_valid_dict()` に置換
  - `save_provisional_digest.py`: 6箇所の `isinstance()` → `is_valid_dict()`/`is_valid_list()` に置換
  - `finalize_from_shadow.py`: 4箇所の `isinstance()` → `is_valid_dict()`/`is_valid_list()` に置換

### Notes
- Phase 3, Phase 4 は v1.1.4 で実施

---

## [1.1.2] - 2025-11-27

### Fixed
- **plugin.json**: バージョン番号を 1.1.2 に更新（CHANGELOGとの整合性確保）
- **digest-auto/SKILL.md**: パス参照を修正（Toybox → Weave）
- **save_provisional_digest.py**: Provisional Digestのフィールド名を `source_file` に統一（digest_types.pyとの整合性確保）
- **ARCHITECTURE.md**: Provisional Digestのフィールド名を `source_file` に統一

### Changed
- **SKILL.md (3ファイル)**: 実装ガイドラインを共通ファイル（_implementation-notes.md）への参照に変更（重複削減）

---

## [1.1.1] - 2025-11-27

### Changed
- **ARCHITECTURE.md**: GrandDigest/ShadowGrandDigest/Provisionalのファイル形式をソースコードに合わせて修正
- **API_REFERENCE.md**: format_digest_number(), PLACEHOLDER_*定数, utils.py関数群を追記
- **TROUBLESHOOTING.md**: Provisionalパス修正、last_digest_times.jsonパス修正
- **GUIDE.md**: SSoT参照化によりまだらボケ説明を簡略化、トラブルシューティングをTROUBLESHOOTING.md参照に変更
- **GLOSSARY.md**: SSoT参照化
- **FAQ.md**: SSoT参照化
- **docs/README.md**: SSoTクロスリファレンス表を追加
- **skills/digest-setup/SKILL.md**: Provisionalディレクトリパス修正

### Fixed
- 全ドキュメントの日付を2025-11-27に統一
- ドキュメント間の重複記載を削減（Single Source of Truth確立）

---

## [1.1.0] - 2025-11-26

### Added
- **GLOSSARY.md**: 用語集を新規作成
- **QUICKSTART.md**: 5分クイックスタートガイドを新規作成
- **docs/README.md**: ドキュメントハブを新規作成
- **skills/shared/**: 共通コンポーネントディレクトリを新規作成
  - `_common-concepts.md`: まだらボケ、記憶定着サイクルの共通定義
  - `_implementation-notes.md`: 実装ガイドラインの共通定義
- **CHANGELOG.md**: 変更履歴ファイルを新規作成

### Changed
- **ARCHITECTURE.md**: バージョン表記を1.3.0から1.1.0に修正（整合性確保）
- **README.md**: プラグインパスを`@Plugins-Weave`に統一
- **TROUBLESHOOTING.md**: ファイル命名規則の説明を修正
- **digest-setup/SKILL.md**: サンプルパスを変数形式に変更
- **digest-config/SKILL.md**: サンプルパスを変数形式に変更
- **digest-auto/SKILL.md**: サンプルパスを変数形式に変更

### Fixed
- ドキュメント間のバージョン不整合を解消
- プラグイン名（@Toybox → @Plugins-Weave）の統一
- ファイル命名規則の説明を正確な形式に修正

---

## [1.0.0] - 2025-11-24

### Added
- 初回リリース
- 8階層の記憶構造（Weekly〜Centurial）
- `/digest` コマンド
- `@digest-setup` スキル
- `@digest-config` スキル
- `@digest-auto` スキル
- DigestAnalyzerエージェント
- GrandDigest/ShadowGrandDigest管理
- Provisional/Regular Digest生成
- まだらボケ検出機能

---

## バージョニング規則

- **MAJOR**: 互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

---

*For more details, see [ARCHITECTURE.md](docs/ARCHITECTURE.md)*
