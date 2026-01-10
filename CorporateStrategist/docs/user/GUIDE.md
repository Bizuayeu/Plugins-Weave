# CorporateStrategist ユーザーガイド

統合型経営支援システムの使い方を説明します。

## はじめに

CorporateStrategistは、中小企業経営者のための統合型経営支援プラグインです。
4つの専門スキルを組み合わせて、経営判断をサポートします。

**重要**: 利用前に必ず [DISCLAIMER.md](../../DISCLAIMER.md) をお読みください。

---

## スキル一覧

| コマンド | 説明 | 用途 |
|---------|------|------|
| `/corporate-strategist` | 統合エントリー | どのスキルを使うか迷ったらこちら |
| `/business-analyzer` | 事業分析 | 事業構造の可視化、戦略立案 |
| `/personnel-developer` | 人材開発 | 採用判断、育成計画、人材配置 |
| `/legal-adviser` | 法務助言 | 契約書作成、リーガルチェック |
| `/foresight-reader` | 洞察獲得 | 姓名判断、易占い（オプトイン） |

---

## 基本的な使い方

### 1. 統合エントリーから始める

```
/corporate-strategist
```

ユーザーの要望に応じて、適切なスキルを推定・提案します。

### 2. 直接スキルを指定する

特定のスキルを使いたい場合は直接指定できます：

```
/business-analyzer
```

---

## スキル別ガイド

### /business-analyzer（事業分析）

**主な機能**:
- Multiversal Structure Parser による多次元構造分析
- 事業モデルの構造化と可視化
- 業務フローの最適化提案

**使用例**:
- 「事業モデルを整理したい」
- 「業務フローを可視化してほしい」
- 「競合分析をしたい」

### /personnel-developer（人材開発）

**主な機能**:
- 採用前判断（AI活用 vs 外注 vs 採用）
- 外注QCD比較による客観的評価
- 人材4類型モデル（軍人・天才・秀才・凡人）

**使用例**:
- 「営業事務を採用すべきか判断したい」
- 「外注と内製のコスト比較をしたい」
- 「人材育成のロードマップを作りたい」

### /legal-adviser（法務助言）

**主な機能**:
- 50以上の契約書テンプレート
- 表記規則に基づいた契約書作成
- リーガルチェックと修正提案

**使用例**:
- 「業務委託契約書を作成したい」
- 「この契約書をレビューしてほしい」
- 「NDAを作成したい」

### /foresight-reader（洞察獲得）

**オプトイン**: 明示的に依頼した場合のみ使用されます

**主な機能**:
- 七格剖象法による姓名判断
- デジタル心易（易経占断）
- 人材4類型判定

**使用例**:
- 「姓名判断をしてほしい」
- 「易で今後の方針を占ってほしい」

---

## 複数スキルの連携

複数のスキルを組み合わせて使うことができます：

| シナリオ | 推奨スキル |
|---------|-----------|
| 採用から契約まで | personnel-developer + legal-adviser |
| 組織再編 | business-analyzer + personnel-developer |
| 新規事業立ち上げ | business-analyzer + personnel-developer + legal-adviser |

---

## 関連ドキュメント

- [QUICKSTART.md](../../QUICKSTART.md): クイックスタート
- [GLOSSARY.md](../../GLOSSARY.md): 用語集
- [DISCLAIMER.md](../../DISCLAIMER.md): 免責事項
- [INDEX.md](../../INDEX.md): ドキュメント一覧

---
*CorporateStrategist User Guide*
