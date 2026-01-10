---
name: corporate-strategist
description: 統合型経営支援システムのエントリーポイント。4つの専門スキル（事業分析・人材開発・法務助言・洞察獲得）へのルーティングを行う。
---

# corporate-strategist - 統合エントリースキル

CorporateStrategistプラグインの統合エントリーポイント。
ユーザーの要望に応じて適切なサブスキルを選択・起動します。

## 概要

**免責事項**: 利用前に必ず [DISCLAIMER.md](../../DISCLAIMER.md) をお読みください。

---

## サブスキル選択フロー

### 優先順位

```
1. パターンA（明示的指定） ← 最優先
   ユーザーが明示的にスキル名を指定した場合
   ↓ なければ
2. パターンB（推定+確認） ← 第二優先
   キーワードから1つ以上のスキルが推定できる場合
   ↓ 推定困難なら
3. パターンC（選択肢提示） ← フォールバック
   キーワードが曖昧すぎて推定が困難な場合
```

---

## パターンA: 明示的指定（即座に実行）

```
ユーザー: 「/personnel-developer で採用判断をしてください」
    ↓
Claude: [確認なしで即座にpersonnel-developer起動]
    ↓
skills/personnel-developer/SKILL.md + CLAUDE.md を読み込み
```

---

## パターンB: 推定可能な場合（推定+確認）

```
ユーザー: 「営業事務を採用すべきか判断したい」
    ↓
Claude: 「/personnel-developer（人材開発）で対応します。
         採用前判断と外注QCD比較を実施しますが、よろしいですか？

         必要に応じて他のスキルも追加できます：
         - /legal-adviser（雇用契約書作成）
         - /foresight-reader（候補者の適性分析）」
    ↓
選択されたスキルのSKILL.md + CLAUDE.mdのみ読み込み
```

---

## パターンC: 推定困難な場合（選択肢提示）

```
ユーザー: 「人事について相談したい」
    ↓
Claude: 「どのスキルを使用しますか？（複数選択可能）

         1. **/personnel-developer** - 人材開発
            採用前判断、外注QCD比較、育成支援

         2. **/legal-adviser** - 法務助言
            雇用契約書、就業規則、法的確認

         3. **/foresight-reader** - 洞察獲得
            姓名判断、適性分析、人材配置」
    ↓
選択されたスキルのSKILL.md + CLAUDE.mdのみ読み込み
```

---

## キーワードマッピング

### 単一スキル判定

| スキル | キーワード例 |
|--------|------------|
| business-analyzer | 事業モデル整理、構造化、業務フロー、戦略、SWOT |
| personnel-developer | 採用判断、外注比較、育成、人材配置 |
| legal-adviser | 雇用契約書、就業規則、リーガルチェック |
| foresight-reader | 姓名判断、易、星導、適性、相性 |

### 複数スキル連携パターン

| トリガー | 推奨組み合わせ |
|---------|--------------|
| 「採用して契約まで」 | personnel-developer + legal-adviser |
| 「組織見直し」 | business-analyzer + personnel-developer |
| 「新規事業立ち上げ」 | business-analyzer + personnel-developer + legal-adviser |
| 「人材戦略全体」 | personnel-developer + foresight-reader |

---

## 選択的読み込みの徹底

**必要のない全スキル一括読み込みを回避**

読み込み例：
- **business-analyzerのみ**: `skills/business-analyzer/SKILL.md` + `CLAUDE.md`
- **personnel-developer + legal-adviser**: 両方のSKILL.md + CLAUDE.md

**選択されていないスキルは読み込まない** = トークン最適化

---

## 関連ドキュメント

- [QUICKSTART.md](../../QUICKSTART.md): クイックスタートガイド
- [GLOSSARY.md](../../GLOSSARY.md): 用語集・思想的骨格
- [DISCLAIMER.md](../../DISCLAIMER.md): 免責事項

---
*CorporateStrategist - 経営者の参謀として、事業・人事・法務・戦略を統合支援*
