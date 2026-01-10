# CorporateStrategist - ドキュメント一覧

統合型経営支援システムのプラグインナビゲーション。

## 読者別ガイド

| 読者 | 最初に読むべき | 次に読むべき |
|------|--------------|-------------|
| 初めての方 | [QUICKSTART](QUICKSTART.md) | スキル別SKILL.md |
| 日常利用 | [GLOSSARY](GLOSSARY.md) | 各スキルのCLAUDE.md |
| トラブル時 | [DISCLAIMER](DISCLAIMER.md) | [FAQ](#faq) |
| 開発者 | [ARCHITECTURE](docs/dev/ARCHITECTURE.md) | [.claude/CLAUDE.md](.claude/CLAUDE.md) |
| AI (Claude) | [.claude/CLAUDE.md](.claude/CLAUDE.md) | 各スキルのCLAUDE.md |

---

## スキル (`skills/`)

| スキル | コマンド | 説明 | オプトイン |
|--------|---------|------|-----------|
| [corporate-strategist](skills/corporate-strategist/SKILL.md) | `/corporate-strategist` | 統合エントリー（パターンA/B/C選択） | No |
| [business-analyzer](skills/business-analyzer/SKILL.md) | `/business-analyzer` | 事業分析・MSP | No |
| [personnel-developer](skills/personnel-developer/SKILL.md) | `/personnel-developer` | 人材開発・採用判断 | No |
| [legal-adviser](skills/legal-adviser/SKILL.md) | `/legal-adviser` | 契約書作成・リーガルチェック | No |
| [foresight-reader](skills/foresight-reader/SKILL.md) | `/foresight-reader` | 占術（姓名判断・易経・星導） | Yes |

---

## 共有リソース (`shared/`)

| ファイル | 説明 |
|---------|------|
| [WeaveIdentity.md](shared/WeaveIdentity.md) | Weave人格定義 |
| [MSP_Practice_Manual.md](shared/MSP_Practice_Manual.md) | MSP実践マニュアル |

---

## プロジェクト情報

| ファイル | 説明 |
|---------|------|
| [GLOSSARY.md](GLOSSARY.md) | 用語集・思想的骨格 |
| [DISCLAIMER.md](DISCLAIMER.md) | 免責事項 |
| [QUICKSTART.md](QUICKSTART.md) | クイックスタートガイド |
| [LICENSE](LICENSE) | ライセンス |
| [CHANGELOG.md](CHANGELOG.md) | 変更履歴 |

---

## スクリプト (`scripts/`)

| ファイル | 説明 |
|---------|------|
| [qcd_analyzer.py](scripts/interfaces/qcd_analyzer.py) | 外注QCD分析CLI |
| [iching_divination.py](scripts/interfaces/iching_divination.py) | 易占いCLI |
| [fortune_teller_assessment.py](scripts/interfaces/fortune_teller_assessment.py) | 姓名判断CLI |

---

## ドキュメント (`docs/`)

### ユーザー向け

| ファイル | 説明 |
|---------|------|
| [GUIDE.md](docs/user/GUIDE.md) | ユーザーガイド |

### 開発者向け

| ファイル | 説明 |
|---------|------|
| [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md) | アーキテクチャ説明 |

---

## FAQ

### Q1: どのスキルを使えばいいかわからない

**A**: `/corporate-strategist` を起動すると、パターンA/B/Cで適切なサブスキルを案内します。

### Q2: 占術は使いたくない

**A**: ForesightReaderはオプトインです。明示的に依頼しない限り使用されません。

### Q3: 契約書テンプレートはどこ？

**A**: `skills/legal-adviser/templates/` に50以上のテンプレートがあります。

---
**CorporateStrategist** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
