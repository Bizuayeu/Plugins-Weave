# Changelog

CorporateStrategistの変更履歴。

## [1.1.0] - 2026-01-11

### Changed
- プラグイン構造に移行
  - スキルを `skills/` 配下に再配置
  - サブディレクトリをkebab-caseにリネーム
  - CLIスクリプトを `scripts/interfaces/` に統合
  - 共有リソースを `shared/` に集約

### Added
- INDEX.md（プラグインエントリーポイント）
- .claude/CLAUDE.md（開発ガイドライン配置）
- skills/corporate-strategist/SKILL.md（統合スキル）
- docs/user/GUIDE.md（ユーザーガイド）
- docs/dev/ARCHITECTURE.md（アーキテクチャ説明）
- CHANGELOG.md（本ファイル）
- scripts/__init__.py, scripts/interfaces/__init__.py

### Improved
- CLIスクリプトにargparse追加
- エラーハンドリングの強化
- データベースパスの相対パス対応

---

## [1.0.0] - 2025-11-09

### Added
- 初期リリース
- BusinessAnalyzer（事業分析）
- PersonnelDeveloper（人材開発）
- LegalAdviser（法務助言）
- ForesightReader（洞察獲得）

---
*CorporateStrategist Changelog*
