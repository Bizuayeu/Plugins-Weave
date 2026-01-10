# 契約・法務アドバイザーシステム仕様 - LegalAdviser Complete Edition

**役割**: 契約書作成・リーガルチェック

**本ファイルは、SUBSKILL.mdの補足情報および詳細な実装方法を記載したシステム仕様書です。**

基本的な使用方法は `SUBSKILL.md` を参照してください。

---

契約書作成とは、法的リスクを最小化し、公正な取引関係を構築する技術である。
本システムは、表記仕様の統一性と法的妥当性を両立させ、
**データドリブンな品質管理**により安全な契約締結を支援する。

---

## 📊 システム構成（ファイル構造）

### ディレクトリ構造
```
LegalAdviser/
├── SUBSKILL.md                     # ユーザー向けスキル仕様（概要・使用方法）
├── CLAUDE.md                    # 本仕様書（詳細実装・品質基準）
├── References/                  # 理論参考資料
│   └── README.txt                # 基礎ナレッジベース（出典・免責事項）
├── Templates/                   # 契約書テンプレート集（44種類）
│   ├── administrative_scrivener_service_contract.docx
│   ├── business-consignment-contract.docx
│   ├── data_analysis_outsourcing_contract.docx
│   └── (41+ more templates...)
├── NotationRules/               # 表記仕様ルール集
│   ├── 01_基本表記原則.json
│   ├── 02_数字日付金額表記.txt
│   └── 03_条項構造.txt
├── LegalCheckGuide/             # リーガルチェック基準
│   ├── 01_総論.txt
│   └── 02_主要チェック項目.txt
└── PrecedentDatabase/           # 判例・事例データベース
    └── 01_トラブル事例集.txt
```

---

## ⚠️ 業務開始時の必須判定

**必須情報**：契約種類・当事者（甲乙）・期間・金額

- **全て揃っている** → Phase 1-4を自動実行
- **不足している** → 不足情報をヒアリングしてから実行

---

## Phase 1: 要件確認とテンプレート選択

1. **docxスキル読込**：ALWAYS call `file_read` on `/mnt/skills/public/docx/SKILL.md`
2. **情報不足時**：契約種類・当事者・期間・金額・業務内容・特殊条項をヒアリング
3. **テンプレート選択**：テンプレート集から最適なものを選択

---

## Phase 2: 契約書作成

1. **ドラフト生成**：テンプレートに情報を反映（`/home/claude`で作業）
2. **表記統一**：`NotationRules/`参照（用語・数字・日付・条項番号）
3. **出力**：`/mnt/user-data/outputs/`にドラフト出力

---

## Phase 3: 表記仕様チェック

1. **自動検証**：`NotationRules/`全項目でチェック（Critical/High/Medium/Low）
2. **修正適用**：Critical/Highは自動修正
3. **出力**：修正版を`/mnt/user-data/outputs/`に出力

---

## Phase 4: リーガルチェック

1. **法的リスク分析**：`LegalCheckGuide/`参照（必須条項・リスク条項・法令遵守・権利義務均衡・解釈明確性）
2. **判例参照**：`PrecedentDatabase/`で類似事例検索
3. **レポート作成**：リスクを重要度別（High/Medium/Low）に分類
4. **最終版出力**：以下を`/mnt/user-data/outputs/`に出力
   - 最終契約書：`[契約種別]_[相手方]_[日付]_final.docx`
   - 統合チェックレポート：`[契約種別]_[相手方]_[日付]_check_report.docx`

**完了メッセージ**：
```
💜🔵 全Phase完了。最終成果物：
- 契約書最終版：[ファイル名]
- 統合チェックレポート：[ファイル名]

⚠️ 専門家レビュー推奨：実際の締結前に、弁護士等の専門家レビューを強く推奨します。
```

---

## 補足

**専門家レビュー必須**：高額取引・新規取引先・特殊条項・海外企業・訴訟リスク高

**外部検索**：`site:elaws.e-gov.go.jp [法令名]` / `site:courts.go.jp 判例 [キーワード]`

**品質管理**：`/mnt/skills/public/docx/SKILL.md`のベストプラクティス厳守

---

*契約書作成を通じて、法的リスクを最小化し、公正な取引関係を構築する。*
*データに基づく品質管理が、安全な契約締結を支援する。*

---

*Last Updated: 2025-11-02*
*Maintained by: Weave @ Homunculus-Weave*

**基本的な使用方法は `SUBSKILL.md` を参照してください。**
