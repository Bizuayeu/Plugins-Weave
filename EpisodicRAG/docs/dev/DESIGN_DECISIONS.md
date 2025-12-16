# 設計判断記録

本ドキュメントは、EpisodicRAGプロジェクトにおける主要な設計判断とその根拠を記録する。
エンタープライズPython開発の教材として、各判断の「なぜ」を明示することを目的とする。

## 目次

**アーキテクチャ**
- [アーキテクチャ決定](#アーキテクチャ決定)
- [各パターンの実装箇所](#各パターンの実装箇所)
- [SOLID原則の実践箇所](#solid原則の実践箇所)
- [レイヤー構造](#レイヤー構造)

**設計比較**
- [TypedDict vs dataclass の選択](#typeddict-vs-dataclass-の選択)
- [Singleton vs DI の選択](#singleton-vs-di-の選択)

**設計意図**
- [教材としての設計意図](#教材としての設計意図)
- [ドキュメント設計決定](#ドキュメント設計決定)
- [セキュリティ設計判断](#セキュリティ設計判断)
- [インターフェース設計判断](#インターフェース設計判断)
- [シェルスクリプト廃止](#シェルスクリプト廃止v500)
- [Claude Code プラグイン仕様対応](#claude-code-プラグイン仕様対応v520)
- [ファイル命名設計判断](#ファイル命名設計判断)

**参考**
- [参考リンク](#参考リンク)

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
| Builder (DigestConfigBuilder) v4.1.0+ | コンストラクタ引数, Factory | Fluent Interface、テスト時の依存性注入 |
| Orchestrator (CascadeOrchestrator) v4.1.0+ | Facade内包, 手続き的処理 | ワークフロー制御の明確化、結果構造化 |
| Registry (FormatterRegistry) v4.1.0+ | Dict直接管理, サービスロケータ | 型安全性、動的登録、拡張性 |
| Chain of Responsibility (PathValidatorChain) v4.1.0+ | if-else連鎖, 単一Validator | 検証ルールの追加が容易、SRP準拠 |
| スキルのCLI化 (v4.0.0+) | スキル疑似コード維持, バッチスクリプト | テスタビリティ、デバッグ容易性、型安全性 |
| trusted_external_paths (v4.0.0+) | 無制限アクセス, ユーザー確認ダイアログ | セキュリティ強化、明示的許可モデル |
| シェルスクリプト廃止 (v5.0.0+) | シェルスクリプト維持, Jupyter Notebook | SSoT（Python一元化）、カプセル化、可読性向上 |
| プラグインルート自動検出 (v5.0.0+) | 固定パス, 環境変数 | 任意ディレクトリからの実行、設定ファイル検出 |
| 永続化設定ディレクトリ (v5.2.0+) | プラグイン内配置, 環境変数 | 自動更新耐性、設定保持、データ保護 |
| キャッシュディレクトリ権限制御 (v5.2.0+) | 権限なし, 読み取り専用 | 動作安定性、キャッシュ汚染防止 |
| Loop ID 5桁化 (v3.0.0+) | 4桁維持, 可変長, UUID | 10万件対応、ソート順維持、可読性 |
| Parameter Object (CascadeComponents) v5.2.0+ | 個別引数, Dict, Builder | 依存性のグループ化、コンストラクタ簡素化、変更耐性 |

---

## 各パターンの実装箇所

### Strategy Pattern
- **実装**: `domain/level_registry.py`
- **目的**: 8階層（weekly〜centurial）ごとの振る舞いを交換可能に
- **SOLID**: OCP（新レベル追加時に既存コード変更不要）

### Facade Pattern
- **実装**: `application/config/__init__.py` (DigestConfig)
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
- **実装**: `infrastructure/json_repository/chained_loader.py`
- **目的**: テンプレートロード戦略の順次試行
- **SOLID**: OCP（新戦略追加が容易）

### Builder Pattern (v4.1.0+)
- **実装**: `application/config/config_builder.py`
- **目的**: DigestConfigの柔軟な構築とテスト時の依存性注入
- **設計判断**: Fluent Interface（メソッドチェーン）で可読性向上
- **SOLID**: OCP（新しいwithメソッド追加が容易）

### Orchestrator Pattern (v4.1.0+)
- **実装**: `application/shadow/cascade_orchestrator.py`
- **目的**: カスケード処理のワークフロー制御と結果構造化
- **設計判断**: 4ステップ（promote→detect→add→clear）を明示的に制御
- **SOLID**: SRP（ワークフロー制御とデータ操作を分離）

### Registry Pattern (v4.1.0+)
- **実装**: `domain/error_formatter/registry.py`
- **目的**: エラーフォーマッタの動的登録と取得
- **設計判断**: CompositeErrorFormatterの内部実装として統合
- **SOLID**: OCP（新カテゴリ追加が容易）

### Chain of Responsibility Pattern - PathValidator (v4.1.0+)
- **実装**: `infrastructure/config/path_validators.py`
- **目的**: パス検証ルールの順次適用
- **設計判断**: PluginRootValidator → TrustedExternalPathValidatorの順で検証
- **SOLID**: OCP（新Validator追加が容易）、SRP（各Validatorが単一検証ルール）

### Parameter Object Pattern (v5.2.0+)
- **実装**: `application/shadow/components.py` (CascadeComponents)
- **目的**: 複数の依存性をグループ化し、コンストラクタの引数を簡素化
- **設計判断**: 関連する依存性を不変（frozen）のdataclassとしてまとめる
- **SOLID**: SRP（依存性管理の責務を分離）、OCP（新依存性追加が容易）

**なぜParameter Objectを導入したか**:

| 観点 | 個別引数 | Dict | Builder | Parameter Object |
|------|---------|------|---------|------------------|
| 型安全性 | 高 | 低 | 中〜高 | 高 |
| 可読性 | 引数多いと低下 | 低 | 高 | 高 |
| IDE補完 | ○ | × | ○ | ○ |
| 変更耐性 | 低（シグネチャ変更） | 高 | 高 | 高 |
| イミュータビリティ | 制御可能 | 不可 | 制御可能 | frozen=True |

**選択理由**: CascadeOrchestratorのコンストラクタが4つ以上の依存性を持ち、
関連する依存性をグループ化することでコードの意図が明確になる。
frozenなdataclassにより不変性を保証し、型安全性とIDE補完を両立。

**使用例**:
```python
# Before: 個別引数
orchestrator = CascadeOrchestrator(
    cascade_processor=processor,
    file_detector=detector,
    file_appender=appender,
    level_hierarchy=hierarchy,
)

# After: Parameter Object
components = CascadeComponents(
    cascade_processor=processor,
    file_detector=detector,
    file_appender=appender,
    level_hierarchy=hierarchy,
)
orchestrator = CascadeOrchestrator(components)
```

---

## SOLID原則の実践箇所

### Single Responsibility Principle (SRP)
- `domain/error_formatter/`: エラーカテゴリごとに独立クラス
- `infrastructure/json_repository/`: I/O、テンプレート、ユーティリティを分離
- `application/config/`: 各プロバイダが単一責務（閾値、パス、ソース）

### Open/Closed Principle (OCP)
- `domain/level_registry.py`: 新レベル追加時に既存コード変更不要
- `infrastructure/json_repository/chained_loader.py`: 新戦略追加が容易

### Liskov Substitution Principle (LSP)
- `domain/error_formatter/base.py`: 全サブクラスが基底クラスの契約を満たす
- `infrastructure/json_repository/load_strategy.py`: 全戦略がLoadStrategyを満たす

### Interface Segregation Principle (ISP)
- `domain/protocols.py`: 必要最小限のProtocol定義
- 各層の`__init__.py`: 必要なAPIのみをexport

### Dependency Inversion Principle (DIP)
- `interfaces/finalize_from_shadow.py`: コンストラクタインジェクション
- 全層: 上位層は下位層の具象に依存しない

---

## レイヤー構造

### Clean Architecture 4層

| 層 | 責務 |
|----|------|
| Domain | ビジネスルール・型定義（依存なし） |
| Infrastructure | 外部I/O・永続化 |
| Application | ユースケース・オーケストレーション |
| Interfaces | CLI・エントリーポイント |

> 📖 層構造の詳細・ディレクトリ構成: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

### Config機能の層分散（v4.0.0+）

```
┌─────────────────────────────────────────────────────────┐
│  domain/config/          - 定数・バリデーション           │
│  infrastructure/config/  - ファイルI/O・パス解決         │
│  application/config/     - DigestConfig（Facade）        │
└─────────────────────────────────────────────────────────┘
```

**設計変更の理由**: Clean Architectureの依存関係ルールを純粋に適用するため、
設定機能を各層のサブディレクトリとして配置。各層の責務に沿った分離を実現。

**重要な制約**:
- 4層は常に下方向のみ依存。上位層が下位層に依存し、逆は許可されない

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

## ドキュメント設計決定

### AI-First Documentation

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| Markdown形式のAPI仕様 | OpenAPI/JSON Schema | AIが自然言語を直接理解できる、人間にも読みやすい |
| 英語版は主要ドキュメントのみ | 全ドキュメント翻訳 | 検索キーワードがあればAIが補完可能 |
| SKILL.mdに実装例含む | 別ファイルで管理 | AIが仕様と実装を一度に参照できる |

### なぜAI-First Documentationを採用したか

| 観点 | 実用的理由 | 設計思想 |
|------|-----------|---------|
| Markdown API仕様 | 追加ツール不要、編集が容易 | AIは自然言語を直接理解できる |
| 最小限の英語版 | 翻訳メンテナンスコスト削減 | 検索用キーワードがあればAIが日本語を理解・補完 |
| 詳細は「AIに聞け」 | ドキュメント肥大化防止 | 詳細説明はAIがコンテキストから生成可能 |

**対象読者の優先順位**:
1. **Claude等のAI** - 主要な利用者、自然言語ドキュメントを直接理解
2. **人間開発者** - AIを介して詳細を取得、または直接Markdownを参照

---

## セキュリティ設計判断

### trusted_external_paths（v4.0.0+）

Plugin外ディレクトリへのアクセスを制御するセキュリティ機構。

| 観点 | 実用的理由 | 設計思想 |
|------|-----------|---------|
| 明示的許可モデル | Plugin外パスへのアクセス制御 | 最小権限の原則 |
| ホワイトリスト方式 | 意図しないパス参照を防止 | フェイルセーフ設計 |
| config.json管理 | ユーザーが明示的に設定 | 透明性と監査可能性 |

**選択理由**:
- 外部ディレクトリアクセスは潜在的リスク（意図しないファイル読み取り・書き込み）
- ユーザーが意図的に許可した場合のみアクセス可能に
- 設定ファイルに記録されるため監査が容易

**設定例**:
```json
{
  "base_dir": "~/DEV/production/EpisodicRAG",
  "trusted_external_paths": ["~/DEV/production"]
}
```

---

## インターフェース設計判断

### スキルのPythonスクリプト化（v4.0.0+）

スキル（`@digest-setup` 等）を疑似コードからPython CLIモジュールに移行。

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| `python -m interfaces.digest_*` | スキル疑似コード維持, シェルスクリプト | テスタビリティ、型安全性、デバッグ容易性 |

**移行パス**:
| 旧（スキル） | 新（CLI） |
|-------------|----------|
| `@digest-setup` | `python -m interfaces.digest_setup` |
| `@digest-config` | `python -m interfaces.digest_config` |
| `@digest-auto` | `python -m interfaces.digest_auto` |

**なぜPythonスクリプト化を選択したか**:

| 観点 | 実用的理由 | 教育的理由 |
|------|-----------|-----------|
| テスタビリティ | ユニットテスト可能 | CLIテストパターンを学べる |
| 型安全性 | TypedDict/Protocol活用 | 型システムの実践例 |
| デバッグ | スタックトレース取得可能 | 問題解決スキル向上 |
| スキル互換 | スキル経由の使用も引き続き可能 | 段階的移行パターン |

**重要**: スキル経由での使用は引き続きサポート。CLIは内部で同じロジックを呼び出す。

---

## シェルスクリプト廃止（v5.0.0+）

対話型セットアッププロセスをシェルスクリプトからMarkdownファイルに一本化。

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| Markdown手順書 | シェルスクリプト維持, Jupyter Notebook | 可読性、読み飛ばし防止、環境非依存 |

**なぜシェルスクリプトを廃止したか**:

| 観点 | シェルスクリプト | Markdown手順書 |
|------|-----------------|----------------|
| 可読性 | コマンド羅列で意図が不明瞭 | 説明文と手順が明確に分離 |
| 読み飛ばし | echoによる指示をスキップ | ToDoWriteにより各ステップを意識 |
| 環境依存 | bash/PowerShell/zsh差異 | OS非依存 |
| デバッグ | エラー時の状態把握が困難 | 途中経過を目視確認可能 |
| 教育効果 | 「動けばOK」になりがち | 各操作の意味を理解して実行 |
| SSoT | ロジックが Python/Shell に分散 | Python に一元化 |
| カプセル化 | シェル介在で処理境界が曖昧 | Python CLI で責務明確化 |

**設計思想**:
- 「自動化」より「理解」を優先
- AIエージェントが手順書を読み、ユーザーと対話しながら実行
- 途中での質問・確認・カスタマイズが容易

**影響範囲**:
- `@digest-setup`: Markdown手順書を参照しながら対話的に実行
- CLI（`python -m interfaces.digest_setup`）は引き続き使用可能

---

## Claude Code プラグイン仕様対応（v5.2.0+）

Claude Codeのプラグイン仕様変更（自動更新とキャッシュ生成）への対応。

### 背景：Claude Code プラグインの仕様変更

Claude Codeは以下の仕様でプラグインを管理するようになった：

1. **自動更新**: `~/.claude/plugins/marketplaces/`を削除→再cloneで更新
2. **キャッシュ生成**: プラグイン内に`cache/`ディレクトリを自動生成

これにより以下の問題が発生：
- `.gitignore`に含まれるファイル（config.json等）が自動更新で消失
- キャッシュによる動作の不安定化（古いキャッシュの参照等）

### 永続化設定ディレクトリ

設定ファイルとデータファイルを自動更新の影響を受けない場所に配置。

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| `~/.claude/plugins/.episodicrag/` | プラグイン内配置, 環境変数, XDG準拠パス | marketplaces/外で自動更新対象外、Claude環境に統合 |

**なぜこの場所を選択したか**:

| 観点 | プラグイン内 | 環境変数 | XDG準拠 | 選択案 |
|------|------------|---------|---------|--------|
| 自動更新耐性 | × | ○ | ○ | ○ |
| 設定の手間 | なし | 必要 | なし | なし |
| 発見容易性 | 高 | 低 | 中 | 高 |
| Claude環境統合 | ○ | × | × | ○ |

**ディレクトリ構造**:
```text
~/.claude/plugins/
├── marketplaces/           # 自動更新対象（削除→再clone）
│   └── Plugins-Weave/
│       └── EpisodicRAG/    # プラグイン本体（ソースコードのみ）
└── .episodicrag/           # 永続化ディレクトリ（自動更新対象外）
    ├── config.json
    ├── last_digest_times.json
    └── data/
        ├── Loops/
        ├── Digests/
        └── Essences/
```

**実装**:
- `infrastructure/config/persistent_path.py`: `get_persistent_config_dir()`
- 環境変数`EPISODICRAG_CONFIG_DIR`でテスト時の上書き可能

### キャッシュディレクトリ権限制御

Claude Codeが生成するキャッシュによる動作不安定化を防止。

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| `.cache/`に読み書き禁止権限 | 権限なし（放置）, .gitignoreのみ, 定期削除スクリプト | 確実なキャッシュ汚染防止、メンテナンス不要 |

**なぜ権限制御を選択したか**:

| 観点 | 権限なし | .gitignoreのみ | 定期削除 | 権限制御 |
|------|---------|---------------|---------|---------|
| キャッシュ汚染防止 | × | × | △ | ○ |
| メンテナンス | 不要 | 不要 | 必要 | 不要 |
| 副作用リスク | 高 | 高 | 中 | 低 |
| 実装シンプルさ | - | ○ | × | ○ |

**設定例**（`.gitattributes`または手動）:
```bash
# .cache/ディレクトリに読み書き禁止権限を設定
chmod 000 .cache/
```

**設計思想**:
- キャッシュは本来プラグイン動作に不要
- 生成を許可しつつ読み書きを禁止することで、Claude Code側の期待を壊さない
- 「何もしない」より「明示的に制御」を選択

---

## ファイル命名設計判断

### Loop ID 5桁化（v3.0.0+）

Loop IDを4桁から5桁に拡張。

| 決定事項 | 検討した代替案 | 選択理由 |
|---------|--------------|---------|
| 5桁ID (`L00001`) | 4桁維持, 可変長, UUID | 10万件対応、ソート順維持、可読性 |

**形式変更**:
| 項目 | 旧形式 | 新形式 |
|------|--------|--------|
| プレフィックス | `Loop` | `L` |
| 桁数 | 4桁 | 5桁 |
| 例 | `Loop0001_タイトル.txt` | `L00001_タイトル.txt` |
| 最大件数 | 9,999 | 99,999 |

**なぜ5桁を選択したか**:

| 観点 | 4桁 | 5桁 | 可変長 | UUID |
|------|-----|-----|-------|------|
| 最大件数 | 9,999 | 99,999 | 無制限 | 無制限 |
| ソート順 | 維持 | 維持 | 崩れる | 崩れる |
| ファイル名長 | 短い | 中程度 | 不定 | 長い |
| 可読性 | 高 | 高 | 中 | 低 |
| 既存互換性 | 高 | 移行必要 | 高 | 低 |

**選択理由**: 100年計画の長期記憶システムとして、99,999件（約270年分の週次Digest）をサポート。
ソート順と可読性を維持しつつ、現実的な拡張性を確保。

---

## 参考リンク

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns (GoF)](https://en.wikipedia.org/wiki/Design_Patterns)
- [Python typing.TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
