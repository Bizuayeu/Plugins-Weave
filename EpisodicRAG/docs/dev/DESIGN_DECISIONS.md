# 設計判断記録

本ドキュメントは、EpisodicRAGプロジェクトにおける主要な設計判断とその根拠を記録する。
エンタープライズPython開発の教材として、各判断の「なぜ」を明示することを目的とする。

---

## アーキテクチャ決定

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| Clean Architecture 4層 | MVC, 単純なLayered | テスタビリティ、依存方向の制御 |
| Strategy (LevelBehavior) | 継承階層, Switch文 | OCP準拠、新レベル追加時の変更最小化 |
| Thin Facade (DigestConfig) | 直接アクセス, Thick Facade | シンプル化、重複排除、カプセル化 |
| TypedDict | dataclass, NamedTuple | JSON互換性、段階的型付け、既存dictとの相互運用 |
| Singleton (Registry) | DIコンテナ, グローバル変数 | ドメイン層のシンプルさ、テスト時のリセット可能性 |
| Composite (ErrorFormatter) | 単一クラス, 関数群 | カテゴリ別責務分離、SRP準拠 |
| Chain of Responsibility (TemplateLoader) | if-else連鎖, Switch | 戦略の追加・削除が容易、OCP準拠 |

---

## 各パターンの実装箇所

### Strategy Pattern
- **実装**: `domain/level_registry.py`
- **目的**: 8階層（weekly〜centurial）ごとの振る舞いを交換可能に
- **SOLID**: OCP（新レベル追加時に既存コード変更不要）

### Facade Pattern
- **実装**: `config/facade.py`
- **目的**: 複雑な設定サブシステムへのシンプルなインターフェース
- **設計判断**: Thin Facade（プロバイダを直接公開、重複プロパティ排除）

### Repository Pattern
- **実装**: `infrastructure/json_repository/`
- **目的**: ファイルI/Oの抽象化、ビジネスロジックからの分離
- **SOLID**: DIP（上位層がI/O詳細に依存しない）

### Template Method Pattern
- **実装**: `domain/error_formatter/base.py`
- **目的**: パス正規化などの共通処理を基底クラスで定義
- **SOLID**: DRY（コード重複の排除）

### Composite Pattern
- **実装**: `domain/error_formatter/__init__.py`
- **目的**: カテゴリ別フォーマッタを統合インターフェースで提供
- **SOLID**: SRP（各フォーマッタが単一カテゴリに責任）

### Chain of Responsibility Pattern
- **実装**: `infrastructure/json_repository/template_loader.py`
- **目的**: テンプレートロード戦略の順次試行
- **SOLID**: OCP（新戦略追加が容易）

---

## SOLID原則の実践箇所

### Single Responsibility Principle (SRP)
- `domain/error_formatter/`: エラーカテゴリごとに独立クラス
- `infrastructure/json_repository/`: I/O、テンプレート、ユーティリティを分離
- `config/`: 各プロバイダが単一責務（閾値、パス、ソース）

### Open/Closed Principle (OCP)
- `domain/level_registry.py`: 新レベル追加時に既存コード変更不要
- `infrastructure/json_repository/template_loader.py`: 新戦略追加が容易

### Liskov Substitution Principle (LSP)
- `domain/error_formatter/base.py`: 全サブクラスが基底クラスの契約を満たす
- `infrastructure/json_repository/template_loader.py`: 全戦略がLoadStrategyを満たす

### Interface Segregation Principle (ISP)
- `domain/protocols.py`: 必要最小限のProtocol定義
- 各層の`__init__.py`: 必要なAPIのみをexport

### Dependency Inversion Principle (DIP)
- `interfaces/finalize_from_shadow.py`: コンストラクタインジェクション
- 全層: 上位層は下位層の具象に依存しない

---

## レイヤー構造

### Clean Architecture 4層

```
┌─────────────────────────────────────────────────────────┐
│                    Interfaces Layer                      │
│  (finalize_from_shadow.py, save_provisional_digest.py)  │
│  外部からのエントリーポイント                              │
└─────────────────────────────────────────────────────────┘
                          ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  (shadow/, grand/, finalize/, tracking/)                │
│  ユースケースの実装、ビジネスプロセスの調整                  │
└─────────────────────────────────────────────────────────┘
                          ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                    │
│  (json_repository/, file_scanner.py, logging_config.py) │
│  外部リソースへのアクセス（ファイル、ログ）                  │
└─────────────────────────────────────────────────────────┘
                          ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                      Domain Layer                        │
│  (types.py, constants.py, exceptions.py, protocols.py)  │
│  ビジネスルール、型定義、例外（外部依存なし）                │
└─────────────────────────────────────────────────────────┘
```

### Config層（完全独立）

```
┌─────────────────────────────────────────────────────────┐
│                      Config Layer                        │
│  (facade.py, threshold_provider.py, path_resolver.py)   │
│  設定管理、パス解決                                       │
│  ※ 4層とは独立 - domain/を含む全層に依存しない             │
└─────────────────────────────────────────────────────────┘
```

**重要な制約**:
- 4層は常に下方向のみ依存。上位層が下位層に依存し、逆は許可されない
- Config層は**完全独立**であり、domain/を含むすべての層に依存しない
- 詳細: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

---

## TypedDict vs dataclass の選択

| 観点 | TypedDict | dataclass |
|-----|-----------|-----------|
| JSON互換性 | ネイティブ対応 | 変換が必要 |
| 既存dictとの相互運用 | シームレス | 明示的変換 |
| 型チェック | 静的のみ | 静的＋実行時 |
| イミュータビリティ | 制御不可 | frozen=True |
| デフォルト値 | total=Falseで対応 | 直接サポート |

**選択理由**: EpisodicRAGはJSONファイルを多用するため、TypedDictの方が自然。

---

## Singleton vs DI の選択

| 観点 | Singleton | Dependency Injection |
|-----|-----------|---------------------|
| シンプルさ | 高 | 中〜低 |
| テスタビリティ | reset関数で対応 | 高 |
| グローバル状態 | あり | なし |
| 設定変更 | 難しい | 容易 |

**選択理由**: ドメイン層は外部依存を持たないため、シンプルなSingletonで十分。
テスト用に`reset_level_registry()`を提供してテスタビリティを確保。

---

## 教材としての設計意図

このプロジェクトは実用的なプラグインであると同時に、エンタープライズPython開発のベストプラクティスを学ぶ教材としても設計されています。

### なぜClean Architectureを採用したか

| 観点 | 実用的理由 | 教育的理由 |
|------|-----------|-----------|
| テスタビリティ | 層ごとに独立してテスト可能 | 依存関係ルールの実践例として最適 |
| 依存方向の制御 | 変更の影響範囲を限定 | 「どの層に何を置くか」の判断基準を学べる |
| 将来の拡張性 | 新機能追加が容易 | 大規模プロジェクトでの設計手法を小規模で体験 |

### なぜSSoTを徹底したか

| 観点 | 実用的理由 | 教育的理由 |
|------|-----------|-----------|
| メンテナンス性 | 変更箇所が1箇所で済む | 「情報の重複を避ける」原則の実践 |
| 一貫性 | 不整合の防止 | リファクタリング耐性の高い設計を学べる |

### なぜ複数のデザインパターンを使用したか

| 観点 | 実用的理由 | 教育的理由 |
|------|-----------|-----------|
| 問題解決 | 各パターンが解決する問題に対する最適解 | 実際のプロジェクトでパターンがどう使われるか学べる |
| コード品質 | 保守性・拡張性の向上 | 「パターンのための実装」ではなく「問題解決のための選択」を体験 |

### 学習リソース

このプロジェクトでの学習パスについては [LEARNING_PATH.md](LEARNING_PATH.md) を参照してください。

---

## 参考リンク

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns (GoF)](https://en.wikipedia.org/wiki/Design_Patterns)
- [Python typing.TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict)
