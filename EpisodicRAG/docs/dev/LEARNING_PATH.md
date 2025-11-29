[EpisodicRAG](../../README.md) > [Docs](../README.md) > LEARNING_PATH

# Learning Path - EpisodicRAGで学ぶエンタープライズPython開発

このドキュメントでは、EpisodicRAGプラグインのコードベースを通じて学べるエンタープライズPython開発のベストプラクティスを紹介します。

---

## このプロジェクトで学べること

### 1. Clean Architecture（4層構造 + Config層）

EpisodicRAGは依存関係ルールに基づく4層構造を採用しています。

| レイヤー | ディレクトリ | 責務 |
|----------|-------------|------|
| Domain | `scripts/domain/` | ビジネスロジックの純粋な定義（外部依存なし） |
| Infrastructure | `scripts/infrastructure/` | 外部I/Oの抽象化（JSON、ファイル、ログ） |
| Application | `scripts/application/` | ユースケースの実装 |
| Interfaces | `scripts/interfaces/` | エントリーポイント |
| **Config** | `scripts/config/` | **完全独立** - 設定管理、パス解決 |

**学習ポイント**:
- `scripts/domain/` を読む → 外部依存のない純粋な定義を理解
- `scripts/application/` を読む → 依存関係ルールの実践を確認
- 参照: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

> ⚠️ **Config層の独立性**（重要な学習ポイント）
>
> Config層は4層とは別に**完全独立**しており、domain/を含む全層に依存しません。
> これはプラグインとして単独ロード可能にするための設計判断です。
> 「なぜ独立させるか」を学ぶことで、アーキテクチャ判断の実践例を理解できます。
>
> 参照: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

### 2. Single Source of Truth (SSoT)

情報の重複を避け、一元管理する原則を徹底しています。

| 対象 | SSoT | 実装 |
|------|------|------|
| 用語定義 | `README.md` | 用語集として機能 |
| バージョン | `plugin.json` | 他ファイルはここを参照 |
| 設定仕様 | `docs/dev/api/config.md` | 詳細は1箇所のみ |

**学習ポイント**:
- `README.md` → 用語集としての機能を確認
- `plugin.json` → バージョンSSoTの実装を確認
- `docs/dev/API_REFERENCE.md` → リンク集としてSSoT違反を回避する設計
- 参照: [CONTRIBUTING.md](../../CONTRIBUTING.md#single-source-of-truth-ssot-原則)

### 3. デザインパターン実践

実際の問題解決に適用されたデザインパターンを学べます。

| パターン | 実装箇所 | 学習ポイント |
|---------|---------|-------------|
| Facade | `DigestConfig`, `ShadowUpdater` | 複雑なサブシステムの隠蔽 |
| Repository | `ShadowIO`, `GrandDigestManager` | データアクセスの抽象化 |
| Singleton | `LevelRegistry` | 設定の一元管理 |
| Strategy | `LevelBehavior` | 振る舞いの交換可能性 |
| Builder | `RegularDigestBuilder` | 複雑なオブジェクト構築 |
| Factory | `get_level_registry()` | オブジェクト生成の抽象化 |

**学習ポイント**:
- 各パターンの実装ファイルを読む
- 参照: [API_REFERENCE.md](API_REFERENCE.md#デザインパターン)
- 参照: [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)

### 4. テスト設計

層別テストと高いカバレッジを実現するテスト設計を学べます。

| 観点 | 実装 |
|------|------|
| 層別テスト | `scripts/test/` 配下でレイヤーごとにテストを分離 |
| フィクスチャ | `conftest.py` で共通フィクスチャを定義 |
| マーカー | `@pytest.mark.slow` 等でテスト実行戦略を制御 |

**学習ポイント**:
- `scripts/test/` のファイル命名規則を確認
- 参照: [CONTRIBUTING.md](../../CONTRIBUTING.md#テスト)

### 5. ドキュメント設計

オーディエンス別に整理されたドキュメント構造を学べます。

| 観点 | 実装 |
|------|------|
| オーディエンス分離 | `docs/user/` vs `docs/dev/` |
| パンくずナビ | 各ファイル先頭に配置 |
| SSoT準拠 | 相互リンクで詳細を1箇所に集約 |

**学習ポイント**:
- `docs/` のディレクトリ構造を確認
- 各ファイルの先頭パンくずを確認

---

## 推奨学習順序

```
1. README.md          → プロジェクト概要と用語を把握
       ↓
2. ARCHITECTURE.md    → 技術構造を理解
       ↓
3. domain/            → 純粋なビジネスロジックを読む
       ↓
4. application/       → ユースケース実装を読む
       ↓
5. DESIGN_DECISIONS.md → 設計判断の理由を理解
       ↓
6. test/              → テスト設計を学ぶ
```

---

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) - 設計判断
- [API_REFERENCE.md](API_REFERENCE.md) - API仕様
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発ガイド
