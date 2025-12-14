# Learning Path - EpisodicRAGで学ぶエンタープライズPython開発

このドキュメントでは、EpisodicRAGプラグインのコードベースを通じて学べるエンタープライズPython開発のベストプラクティスを紹介します。

## 目次

**開発方法論**
- [コンセプト駆動AI指向OODAループ開発](#コンセプト駆動ai指向oodaループ開発)

**学習コンテンツ**
- [このプロジェクトで学べること](#このプロジェクトで学べること)
  - [1. Clean Architecture](#1-clean-architecture4層構造)
  - [2. Single Source of Truth](#2-single-source-of-truth-ssot)
  - [3. デザインパターン実践](#3-デザインパターン実践)
  - [4. テスト設計](#4-テスト設計)
  - [5. ドキュメント設計](#5-ドキュメント設計)
- [推奨学習順序](#推奨学習順序)
- [関連ドキュメント](#関連ドキュメント)

---

## コンセプト駆動AI指向OODAループ開発

> 別名「思い付きの行き当たりばったり」開発 — EpisodicRAGはこの方法論で生まれました。

### 概要

AI（Claude Code）を活用した高速プロトタイピングとTDDリファクタリングを組み合わせた開発手法です。

### 3つのフェーズ

```
1. Concept（コンセプト）
   アプリケーションの核となるアイデアを言語化する
        ↓
2. Prototype（プロトタイプ）
   コンセプトをClaude Codeに共有し、プロトタイプ作成を依頼
        ↓
3. OODA Loop（無限リファクタリング）
   完成したプロトタイプをTDD（Plan mode）で継続的に改善
```

### なぜOODAループか

TDDリファクタリングのサイクルがOODAループ（Observe→Orient→Decide→Act）に対応:

| OODA | TDDリファクタリング |
|------|-------------------|
| Observe | テスト実行・結果確認 |
| Orient | 問題箇所・改善点の分析 |
| Decide | リファクタリング方針決定 |
| Act | コード修正・テスト追加 |

このサイクルを「無限に」回すことで、プロトタイプがプロダクション品質に進化します。

### EpisodicRAGでの実践

このプラグインは実際にこの方法論で開発されました:
- **v1.0**: コンセプト（階層的記憶管理）→ Claude Codeでプロトタイプ
- **v2.0〜v4.x**: TDDで無限リファクタリング → Clean Architecture達成

---

## このプロジェクトで学べること

### 1. Clean Architecture（4層構造）

EpisodicRAGは依存関係ルールに基づく4層構造を採用しています。

| レイヤー | ディレクトリ | 責務 |
|----------|-------------|------|
| Domain | `scripts/domain/` | ビジネスロジックの純粋な定義（外部依存なし） |
| Infrastructure | `scripts/infrastructure/` | 外部I/Oの抽象化（JSON、ファイル、ログ） |
| Application | `scripts/application/` | ユースケースの実装 |
| Interfaces | `scripts/interfaces/` | エントリーポイント |

> **Note (v4.0.0+)**: 設定管理機能（Config）は各層のサブディレクトリに分散:
> - `domain/config/` - 定数・バリデーション
> - `infrastructure/config/` - ファイルI/O・パス解決
> - `application/config/` - DigestConfig（Facade）

**学習ポイント**:
- `scripts/domain/` を読む → 外部依存のない純粋な定義を理解
- `scripts/application/` を読む → 依存関係ルールの実践を確認
- 参照: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

> ⚠️ **Config機能の層分散**（重要な学習ポイント v4.0.0+）
>
> v4.0.0でConfig機能は各層のサブディレクトリに分散配置されました。
> これはClean Architectureの依存関係ルールを純粋に適用するための設計判断です:
> - `domain/config/`: 定数・型検証（外部依存なし）
> - `infrastructure/config/`: ファイルI/O・パス解決
> - `application/config/`: DigestConfig（Facade）
>
> 「なぜ分散させたか」を学ぶことで、アーキテクチャリファクタリングの実践例を理解できます。
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
| Facade | `application/config/` (DigestConfig), `application/shadow/` (ShadowUpdater) | 複雑なサブシステムの隠蔽 |
| Repository | `application/shadow/` (ShadowIO), `application/grand/` (GrandDigestManager) | データアクセスの抽象化 |
| Singleton | `domain/level_registry.py` (LevelRegistry) | 設定の一元管理 |
| Strategy | `domain/level_registry.py` (LevelBehavior) | 振る舞いの交換可能性 |
| Template Method | `domain/error_formatter/base.py` | 共通処理の基底クラス定義 |
| Builder | `application/finalize/` (RegularDigestBuilder), `application/config/` (DigestConfigBuilder) *(v4.1.0+)* | 複雑なオブジェクト構築 |
| Factory | `domain/level_registry.py` (get_level_registry) | オブジェクト生成の抽象化 |
| Composite | `domain/error_formatter/` (CompositeErrorFormatter) | 統合インターフェース提供 |
| Registry *(v4.1.0+)* | `domain/error_formatter/registry.py` (FormatterRegistry) | 動的登録と取得 |
| Orchestrator *(v4.1.0+)* | `application/shadow/cascade_orchestrator.py` | ワークフロー制御 |
| Chain of Responsibility *(v4.1.0+)* | `infrastructure/json_repository/chained_loader.py`, `infrastructure/config/path_validators.py` | 処理の順次試行 |

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
| SSoT準拠 | 相互リンクで詳細を1箇所に集約 |

**学習ポイント**:
- `docs/` のディレクトリ構造を確認

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

> **コンセプト駆動AI指向OODAループ開発の哲学**:
> とはいえ、事前に理解することより試してみることの方が重要です。
> 完璧に理解してから始めるのではなく、まず動かしてみて、壁にぶつかったら戻って学ぶ。
> それがOODAループの本質です。

---

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) - 設計判断
- [API_REFERENCE.md](API_REFERENCE.md) - API仕様
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発ガイド

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
