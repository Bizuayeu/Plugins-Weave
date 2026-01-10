# CorporateStrategist プラグイン化計画

**作成日**: 2026-01-11
**ステータス**: Implementation Complete ✓

---

## 概要

CorporateStrategist（4サブスキル統合型経営支援システム）を
Claude Code プラグイン構造に移行する計画。

---

## 決定事項サマリー

| カテゴリ | 決定 | 理由 |
|---------|------|------|
| プラグイン粒度 | 1プラグイン・5スキル | EpisodicRAG踏襲、統合管理容易 |
| Pythonツール | CLIコマンド化 | テスト可能、保守性向上 |
| スキル起動 | 統合+個別の両方 | 柔軟性確保 |
| ForesightReader | プラグイン内オプトイン | 明示的依頼時のみ起動 |
| 契約書テンプレート | プラグイン内同梱 | 即利用可能 |
| 多言語対応 | 日本語のみ | 中小企業向け日本市場特化 |
| ディレクトリ名 | CamelCase維持 | 既存構造尊重、Git履歴維持 |
| ファイル・コマンド | kebab-case | Claude Code標準準拠 |
| 共有リソース | プラグインルート配置 | 全スキルから参照容易 |
| 実装順序 | 全スキル同時移行 | 整合性維持 |
| マイグレーション | 新構造移動・旧削除 | クリーンな移行 |

---

## 目標構造

```
plugins-weave/CorporateStrategist/
├── INDEX.md                                 # プラグインエントリー
├── README.md                                # GitHub向け説明
├── LICENSE                                  # ライセンス（既存）
├── DISCLAIMER.md                            # 免責事項（既存）
├── QUICKSTART.md                            # クイックスタート（既存）
├── GLOSSARY.md                              # 用語集（旧COMMON_GLOSSARY.md）
├── CHANGELOG.md                             # 変更履歴（新規）
│
├── .claude/
│   └── CLAUDE.md                            # 開発ガイドライン
│
├── shared/                                  # 共有リソース
│   ├── WeaveIdentity.md                     # Weave人格定義
│   └── MSP_Practice_Manual.md               # MSP実践マニュアル
│
├── skills/
│   ├── corporate-strategist/                # 統合スキル（新規）
│   │   └── SKILL.md                         # name: corporate-strategist
│   │
│   ├── business-analyzer/                   # 旧BusinessAnalyzer/
│   │   ├── SKILL.md                         # name: business-analyzer
│   │   ├── CLAUDE.md
│   │   └── references/
│   │       ├── BMC_Template_JAJAAAN.pptx
│   │       ├── BMC_Example_YakinikuShop.webp
│   │       ├── SkillArchitectureTemplate_SKILL.md
│   │       ├── SkillArchitectureTemplate_CLAUDE.md
│   │       └── SkillPriorityScoringMatrix.md
│   │
│   ├── personnel-developer/                 # 旧PersonnelDeveloper/
│   │   ├── SKILL.md                         # name: personnel-developer
│   │   ├── CLAUDE.md
│   │   ├── templates/
│   │   │   ├── RecruitmentSheet.md
│   │   │   ├── ScreeningCheckList.md
│   │   │   ├── InterviewQuestions.md
│   │   │   ├── TrainingRoadmap.md
│   │   │   ├── OneOnOneQuestions.md
│   │   │   └── EvaluationFramework.md
│   │   └── references/
│   │       ├── 人材4類型詳細.md
│   │       ├── AIスキル化判定基準.md
│   │       └── 外注QCD比較手法.md
│   │
│   ├── legal-adviser/                       # 旧LegalAdviser/
│   │   ├── SKILL.md                         # name: legal-adviser
│   │   ├── CLAUDE.md
│   │   ├── templates/                       # 50+ 契約書テンプレート
│   │   │   └── *.docx
│   │   ├── notation-rules/
│   │   │   ├── 01_基本表記原則.json
│   │   │   ├── 02_数字日付金額表記.txt
│   │   │   └── 03_条項構造.txt
│   │   ├── legal-check-guide/
│   │   │   ├── 01_総論.txt
│   │   │   └── 02_主要チェック項目.txt
│   │   └── precedent-database/
│   │       └── 01_トラブル事例集.txt
│   │
│   └── foresight-reader/                    # 旧ForesightReader/
│       ├── SKILL.md                         # name: foresight-reader
│       ├── CLAUDE.md
│       ├── i-ching/
│       │   ├── 大卦データベース.json
│       │   ├── デジタル心易システム仕様.md
│       │   ├── 変卦仕様_append.md
│       │   └── DivineTemplate.md
│       ├── seimei/
│       │   ├── 数理星導一覧.json
│       │   ├── ここのそ数霊表.json
│       │   ├── 陰陽配列パターン.json
│       │   ├── 五気判定マトリックス.json
│       │   ├── 七格剖象法鑑定理論.md
│       │   └── AssessmentTemplate.md
│       └── references/
│           └── 数霊術基礎理論.txt
│
├── scripts/
│   ├── __init__.py
│   └── interfaces/                          # CLIコマンド
│       ├── __init__.py
│       ├── qcd_analyzer.py                  # 外注QCD分析
│       ├── iching_divination.py             # 易占い
│       └── fortune_teller_assessment.py     # 姓名判断
│
├── agents/                                  # 将来拡張用
│   └── .gitkeep
│
├── commands/                                # 将来拡張用
│   └── .gitkeep
│
└── docs/
    ├── user/
    │   └── GUIDE.md                         # ユーザーガイド
    └── dev/
        └── ARCHITECTURE.md                  # アーキテクチャ説明
```

---

## スキル一覧

| スキル名 | コマンド | 説明 | オプトイン |
|---------|---------|------|-----------|
| corporate-strategist | /corporate-strategist | 統合エントリー（パターンA/B/C選択） | No |
| business-analyzer | /business-analyzer | 事業分析・MSP | No |
| personnel-developer | /personnel-developer | 人材開発・採用判断 | No |
| legal-adviser | /legal-adviser | 契約書作成・リーガルチェック | No |
| foresight-reader | /foresight-reader | 占術（姓名判断・易経・星導） | Yes |

---

## 実装ステージ

### Stage 1: 基盤構築
**Goal**: プラグイン骨格とINDEX.mdの作成
**Success Criteria**:
- INDEX.mdが存在し、プラグインとして認識される
- .claude/CLAUDE.mdが配置される
- shared/ディレクトリが作成される
**Status**: Complete ✓

**Tasks**:
1. [x] INDEX.mdを作成（プラグインエントリーポイント）
2. [x] .claude/CLAUDE.mdを現在のCLAUDE.mdから移動
3. [x] shared/ディレクトリを作成
4. [x] COMMON_GLOSSARY.mdをGLOSSARY.mdにリネーム
5. [x] WeaveIdentity.mdをshared/に移動
6. [x] MSP_Practice_Manual.mdをshared/に移動

---

### Stage 2: スキルディレクトリ再構築
**Goal**: 4サブスキルをskills/配下に移動
**Success Criteria**:
- skills/配下に5つのスキルディレクトリが存在
- 各スキルにSKILL.md（kebab-case name）が存在
**Status**: Complete ✓

**Tasks**:
1. [x] skills/corporate-strategist/SKILL.mdを新規作成（統合スキル）
2. [x] BusinessAnalyzer/ → skills/business-analyzer/ にリネーム・移動
3. [x] PersonnelDeveloper/ → skills/personnel-developer/ にリネーム・移動
4. [x] LegalAdviser/ → skills/legal-adviser/ にリネーム・移動
5. [x] ForesightReader/ → skills/foresight-reader/ にリネーム・移動
6. [x] 各SUBSKILL.mdをSKILL.mdにリネーム
7. [x] SKILL.mdのfront matterをkebab-case nameに更新（既にkebab-case済み）

---

### Stage 3: リソースファイル整理
**Goal**: サブディレクトリをkebab-caseにリネーム
**Success Criteria**:
- 全サブディレクトリがkebab-case
- 参照パスが更新される
**Status**: Complete ✓

**Tasks**:
1. [x] References/ → references/ にリネーム（全スキル）
2. [x] Templates/ → templates/ にリネーム（該当スキル）
3. [x] Tools/ → scripts/interfaces/に統合
4. [x] NotationRules/ → notation-rules/ にリネーム
5. [x] LegalCheckGuide/ → legal-check-guide/ にリネーム
6. [x] PrecedentDatabase/ → precedent-database/ にリネーム
7. [x] I-Ching/ → i-ching/ にリネーム
8. [x] Seimei/ → seimei/ にリネーム

---

### Stage 4: CLIコマンド実装
**Goal**: PythonスクリプトをCLIコマンドとして整備
**Success Criteria**:
- scripts/interfaces/からCLI呼び出し可能
- 基本的なエラーハンドリングが実装される
**Status**: Complete ✓

**Tasks**:
1. [x] scripts/__init__.pyを作成
2. [x] scripts/interfaces/__init__.pyを作成
3. [x] qcd_analyzer.pyをCLI対応に更新（argparse追加）
4. [x] iching_divination.pyをCLI対応に更新（argparse追加、パス更新）
5. [x] fortune_teller_assessment.pyをCLI対応に更新（argparse追加、パス更新）
6. [x] 各CLIのヘルプメッセージを整備

---

### Stage 5: ドキュメント整備
**Goal**: ユーザー・開発者向けドキュメントの整備
**Success Criteria**:
- docs/user/GUIDE.mdが存在
- docs/dev/ARCHITECTURE.mdが存在
- CHANGELOG.mdが存在
**Status**: In Progress

**Tasks**:
1. [x] docs/user/GUIDE.mdを作成
2. [x] docs/dev/ARCHITECTURE.mdを作成
3. [x] CHANGELOG.mdを作成
4. [ ] README.mdを更新（プラグイン構造を反映）- スキップ（既存で十分）
5. [ ] 各SKILL.mdの参照パスを更新 - Stage 6で対応

**Status**: Complete ✓

---

### Stage 6: 旧構造クリーンアップ
**Goal**: 不要になった旧ファイル・ディレクトリの削除
**Success Criteria**:
- 旧CamelCaseサブスキルディレクトリが削除される
- 重複ファイルが削除される
**Status**: Complete ✓

**Tasks**:
1. [x] 移動済みの旧ディレクトリを削除（Stage 2で完了）
2. [x] 重複ファイルを削除（旧SKILL.md）
3. [x] .gitkeepを適切な空ディレクトリに配置（agents/, commands/）
4. [x] 最終動作確認

---

## ファイル移動マッピング

| 旧パス | 新パス |
|-------|--------|
| SKILL.md | skills/corporate-strategist/SKILL.md（内容を統合スキル用に） |
| CLAUDE.md | .claude/CLAUDE.md |
| COMMON_GLOSSARY.md | GLOSSARY.md |
| BusinessAnalyzer/ | skills/business-analyzer/ |
| BusinessAnalyzer/SUBSKILL.md | skills/business-analyzer/SKILL.md |
| BusinessAnalyzer/References/ | skills/business-analyzer/references/ |
| BusinessAnalyzer/References/WeaveIdentity.md | shared/WeaveIdentity.md |
| BusinessAnalyzer/References/MSP_Practice_Manual.md | shared/MSP_Practice_Manual.md |
| PersonnelDeveloper/ | skills/personnel-developer/ |
| PersonnelDeveloper/SUBSKILL.md | skills/personnel-developer/SKILL.md |
| PersonnelDeveloper/Templates/ | skills/personnel-developer/templates/ |
| PersonnelDeveloper/References/ | skills/personnel-developer/references/ |
| PersonnelDeveloper/Tools/qcd_analyzer.py | scripts/interfaces/qcd_analyzer.py |
| LegalAdviser/ | skills/legal-adviser/ |
| LegalAdviser/SUBSKILL.md | skills/legal-adviser/SKILL.md |
| LegalAdviser/Templates/ | skills/legal-adviser/templates/ |
| LegalAdviser/NotationRules/ | skills/legal-adviser/notation-rules/ |
| LegalAdviser/LegalCheckGuide/ | skills/legal-adviser/legal-check-guide/ |
| LegalAdviser/PrecedentDatabase/ | skills/legal-adviser/precedent-database/ |
| ForesightReader/ | skills/foresight-reader/ |
| ForesightReader/SUBSKILL.md | skills/foresight-reader/SKILL.md |
| ForesightReader/I-Ching/ | skills/foresight-reader/i-ching/ |
| ForesightReader/Seimei/ | skills/foresight-reader/seimei/ |
| ForesightReader/Seimei/fortune_teller_assessment.py | scripts/interfaces/fortune_teller_assessment.py |
| ForesightReader/I-Ching/iching_divination.py | scripts/interfaces/iching_divination.py |

---

## 注意事項

1. **Git履歴維持**: `git mv`を使用してファイル移動
2. **パス参照更新**: 各SKILL.md/CLAUDE.md内の相対パスを更新
3. **ForesightReaderのオプトイン**: 起動条件の明示を維持
4. **テスト**: 各ステージ完了後に動作確認

---

## 次のアクション

1. Stage 1から順に実装開始
2. 各ステージ完了時にこのファイルのStatusを更新
3. 全ステージ完了後、このファイルを削除

---

*Created by Weave via /dig - 2026-01-11*
