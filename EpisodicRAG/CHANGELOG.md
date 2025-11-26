# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
