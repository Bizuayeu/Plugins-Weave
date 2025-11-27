# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.3.0] - 2025-11-28

### Breaking Changes

- **config/__init__.py: 後方互換性用の再エクスポートを完全削除**
  - `extract_file_number`, `extract_number_only`, `format_digest_number` → `domain.file_naming`から直接インポート
  - `ConfigData`, `LevelConfigData` → `domain.types`から直接インポート

  ```python
  # 旧（動作しない）
  from config import extract_file_number, ConfigData

  # 新（推奨）
  from domain.file_naming import extract_file_number
  from domain.types import ConfigData
  ```

---

## [2.2.0] - 2025-11-28

### Changed

- **型安全性向上**: `Dict[str, Any]` → `ConfigData` (TypedDict) への移行
  - `config/path_resolver.py`: パラメータ型を `ConfigData` に変更
  - `config/threshold_provider.py`: パラメータ型を `ConfigData` に変更
- **config/__init__.py リファクタリング**:
  - domain定数の再エクスポートを削除（直接 `from domain.constants import ...` を使用）
  - 初期化パターンを即時初期化に統一（遅延初期化を廃止）
  - ローカルインポートをモジュールレベルに移動
- **infrastructure/json_repository.py**: エラーハンドリングを `_safe_read_json()` ヘルパー関数に共通化
- **反復プロパティの動的化**:
  - `ThresholdProvider`: `__getattr__` を使用した動的プロパティアクセス
  - `DigestConfig`: threshold委譲を動的化

### Added

- **GrandDigestManager のユニットテスト追加** (11件):
  - `get_template()` の構造・バージョン・レベル検証
  - `load_or_create()` の新規作成・既存読み込み・破損ファイル処理
  - `update_digest()` の正常更新・レベル保持・タイムスタンプ更新
- **`__all__` エクスポートの追加**:
  - `config/path_resolver.py`
  - `config/threshold_provider.py`
  - `infrastructure/json_repository.py`
  - `infrastructure/logging_config.py`
  - `application/shadow/cascade_processor.py`
- `agents/README.md` にフッターを追加

### Fixed

- `config/__init__.py`: ローカルインポート (`show_paths` メソッド内) をモジュールトップレベルに移動
- インポートパスの統一: `from config import LEVEL_CONFIG` → `from domain.constants import LEVEL_CONFIG`

---

## [2.1.0] - 2025-11-27

### Changed

- **DEPRECATED メソッド完全削除**:
  - `load_or_create`, `save`, `find_new_files` を削除

### Added

- **型安全性向上**:
  - `ProvisionalDigestFile` 型追加
  - `provisional_loader.py`, `save_provisional_digest.py` の型置換
  - `Dict[str, Any]` 使用箇所を汎用関数のみに限定

---

## [2.0.1] - 2025-11-27

### Changed

- **ログ統一**: `print` → `logger` に全面置換
- **Facade簡潔化**: public APIを整理（DEPRECATED 3メソッド）

### Added

- **テストカバレッジ拡大**
- **型定義統一**: `DigestMetadataComplete` 追加

### Fixed

- `cascade_processor.py`: 型チェック漏れ修正

---

## [2.0.0] - 2025-11-27

### Breaking Changes

**Clean Architecture リファクタリング完了** - 内部構造を4層アーキテクチャに全面移行

- **後方互換性レイヤー削除**: 旧インポートパス（`from validators import ...`, `from finalize_from_shadow import ...`等）は動作しなくなりました
- **推奨インポートパス変更**:
  ```python
  # 旧（動作しない）
  from validators import validate_dict
  from finalize_from_shadow import DigestFinalizerFromShadow

  # 新（推奨）
  from application.validators import validate_dict
  from interfaces import DigestFinalizerFromShadow
  ```

### Added

- **Clean Architecture 4層構造**:
  - `domain/` - コアビジネスロジック（定数、型、例外、ファイル命名）
  - `infrastructure/` - 外部関心事（JSON操作、ファイルスキャン、ロギング）
  - `application/` - ユースケース（Shadow管理、GrandDigest管理、Finalize処理）
  - `interfaces/` - エントリーポイント（DigestFinalizerFromShadow, ProvisionalDigestSaver）

- **テスト大幅拡充**:
  - 新規テストファイル追加
  - 全テストが新アーキテクチャに対応

- **ドキュメント更新**:
  - ARCHITECTURE.md - 4層構造の詳細説明追加
  - API_REFERENCE.md - 層別に再構成
  - scripts/README.md - 4層構造に全面更新
  - CONTRIBUTING.md - 新機能追加ガイド追加

### Changed

- **依存関係の明確化**: 循環参照を解消し、層的依存関係を確立
  - `domain/` ← 何にも依存しない
  - `infrastructure/` ← domain/ のみ
  - `application/` ← domain/ + infrastructure/
  - `interfaces/` ← application/

### Removed

- **後方互換性レイヤー削除**:
  - `scripts/finalize/`
  - `scripts/shadow/`
  - ルートレベルファイル: `validators.py`, `digest_times.py`, `grand_digest.py`, `shadow_grand_digest.py`, `finalize_from_shadow.py`, `save_provisional_digest.py`, `__version__.py`, `digest_types.py`, `exceptions.py`, `utils.py`

### Migration Guide

開発者向け移行ガイド:

1. **インポートパスの更新**:
   ```python
   # Domain層
   from domain import LEVEL_CONFIG, __version__, ValidationError
   from domain.file_naming import extract_file_number

   # Application層
   from application.shadow import ShadowUpdater
   from application.grand import ShadowGrandDigestManager

   # Interfaces層
   from interfaces import DigestFinalizerFromShadow
   from interfaces.interface_helpers import sanitize_filename
   ```

2. **詳細**: ARCHITECTURE.md および scripts/README.md を参照

---

## [1.1.8] - 2025-11-27

### Added
- **CLAUDE.md**: プロジェクト固有のAIエージェント向けガイドライン
  - SSoTの場所と参照パターン
  - 開発ワークフローとコーディング規約
  - 用語統一ルール（Loop, Digest, GrandDigest）
- **バックアップ＆リカバリ**: ADVANCED.md にセクション追加
  - 長期記憶の4層構造（Loop/Provisional/階層Digest/Essence）
  - 再構築可能性に基づくバックアップ優先度（Loopのみ必須）
  - Git連携/手動/クラウド同期の3つの方法
  - リカバリ手順（各層別）と推奨頻度

### Changed
- **SSoT参照の徹底**:
  - `digest-auto/SKILL.md`: 「まだらボケ」説明を `_common-concepts.md` 参照に置換
  - `FAQ.md`: 「まだらボケ」回答をSSoT参照に簡略化
- **バージョン情報統一**:
  - `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `API_REFERENCE.md` にバージョンヘッダー追加

### Documentation
- ドキュメント健全性診断に基づく改善
- 重複コンテンツ削減
- ADVANCED.md 目次更新

---

## [1.1.7] - 2025-11-27

### Changed
- **ドキュメントリファクタリング**: 大規模なドキュメント整理
  - README.md: トラフィックディレクター化（大幅簡略化）
  - docs/README.md: AI Specification Hub に特化
  - バージョンフッター削除 - SSoTに集約
  - ブレッドクラム追加（docs/配下）
  - scripts/README.md: shadow/, finalize/, __version__.py を追記

### Fixed
- **パス参照修正**: `homunculus/Toybox` → プレースホルダーに変更
  - `skills/digest-config/SKILL.md` (line 26, 97)
  - `skills/digest-setup/SKILL.md` (line 27)

### Documentation
- ARCHITECTURE.md: カスケードフローのSSoT参照を追加
- 全docsファイルにブレッドクラムナビゲーション追加
- ペルソナベースのナビゲーションテーブル導入

---

## [1.1.6] - 2025-11-27

### Added
- **shadow/ パッケージ**: `shadow_grand_digest.py` を4つのモジュールに分割
  - `shadow/template.py`: テンプレート生成（ShadowTemplate クラス）
  - `shadow/file_detector.py`: ファイル検出（FileDetector クラス）
  - `shadow/shadow_io.py`: Shadow I/O（ShadowIO クラス）
  - `shadow/shadow_updater.py`: Shadow更新（ShadowUpdater クラス）

### Changed
- **リファクタリング**: shadow_grand_digest.py のFacade分割
  - 元ファイルはFacadeとして後方互換性を維持

---

## [1.1.5] - 2025-11-27

### Added
- **finalize/ パッケージ**: `finalize_from_shadow.py` を4つのモジュールに分割
  - `finalize/shadow_validator.py`: Shadow検証（ShadowValidator クラス）
  - `finalize/provisional_loader.py`: Provisional読込（ProvisionalLoader クラス）
  - `finalize/digest_builder.py`: Digest構築（RegularDigestBuilder クラス）
  - `finalize/persistence.py`: 永続化処理（DigestPersistence クラス）

### Changed
- **リファクタリング**: finalize_from_shadow.py のFacade分割
  - 元ファイルはFacadeとして後方互換性を維持

---

## [1.1.4] - 2025-11-27

### Changed
- **リファクタリング**: 例外処理の完全移行
  - `exceptions.py` の例外クラス（`ValidationError`, `DigestError`, `FileIOError`）を実際に使用開始
  - `log_error()` → 適切な例外に置換
  - 各メソッドの戻り値を `bool`/`Optional` から例外ベースに変更
  - 関連テストを `assertFalse()` → `assertRaises()` に更新

---

## [1.1.3] - 2025-11-27

### Added
- **__version__.py**: バージョン定数のSingle Source of Truth（`DIGEST_FORMAT_VERSION`）を新規作成

### Changed
- **リファクタリング**: バージョン文字列の集約
  - ハードコードされていた `"1.0"` を `DIGEST_FORMAT_VERSION` 定数に置換
- **リファクタリング**: validators.py の段階的採用
  - `isinstance()` → `is_valid_dict()`/`is_valid_list()` に置換

---

## [1.1.2] - 2025-11-27

### Fixed
- **plugin.json**: バージョン番号を 1.1.2 に更新（CHANGELOGとの整合性確保）
- **digest-auto/SKILL.md**: パス参照を修正（Toybox → Weave）
- **save_provisional_digest.py**: Provisional Digestのフィールド名を `source_file` に統一（digest_types.pyとの整合性確保）
- **ARCHITECTURE.md**: Provisional Digestのフィールド名を `source_file` に統一

### Changed
- **SKILL.md**: 実装ガイドラインを共通ファイル（_implementation-notes.md）への参照に変更（重複削減）

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

*For more details, see [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md)*

<!-- Version comparison links -->
[2.3.0]: https://github.com/Bizuayeu/Plugins-Weave/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/Bizuayeu/Plugins-Weave/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/Bizuayeu/Plugins-Weave/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/Bizuayeu/Plugins-Weave/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.8...v2.0.0
[1.1.8]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Bizuayeu/Plugins-Weave/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Bizuayeu/Plugins-Weave/releases/tag/v1.0.0
