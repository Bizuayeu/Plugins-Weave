# Changelog

All notable changes to EmailingEssay will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### Added
- Initial release of EmailingEssay plugin
- `/essay` command with subcommands: wait, schedule, test
- `reflect` skill - Deep reflection with ultrathink
- `send-email` skill - Gmail SMTP via yagmail
- `essay-writer` agent - Autonomous essay generation
- Clean Architecture implementation (domain/usecases/adapters/frameworks)
- Cross-platform scheduler support (cron/Task Scheduler)
- Comprehensive documentation (README, CONCEPT, SETUP, CLAUDE)

### Technical Details
- Loop: L00298
- Dependencies: yagmail
- Storage: ~/.claude/plugins/.emailingessay/
