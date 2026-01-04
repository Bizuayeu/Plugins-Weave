<!-- Last synced: 2025-12-16 -->
English | [日本語](CHEATSHEET.md)

# EpisodicRAG Quick Reference

A one-page cheat sheet for quick reference of key features.

## Table of Contents

- [Command Quick Reference](#command-quick-reference)
- [Skill Quick Reference](#skill-quick-reference)
- [File Naming Conventions](#file-naming-conventions)
- [Default Thresholds](#default-thresholds)
- [Key Paths](#key-paths)
- [Daily Workflow](#daily-workflow)
- [Troubleshooting](#troubleshooting)
- [Related Documentation](#related-documentation)

---

## Command Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/digest` | Detect & analyze new Loops | After adding each Loop |
| `/digest weekly` | Finalize Weekly Digest | When 5 Loops are ready |
| `/digest monthly` | Finalize Monthly Digest | When 5 Weeklies are ready |

## Skill Quick Reference

| Skill | Purpose |
|-------|---------|
| `@digest-auto` | System status diagnosis & recommended actions |
| `@digest-setup` | Initial setup |
| `@digest-config` | Configuration changes |

---

## File Naming Conventions

| Type | Prefix | Digits | Format | Example |
|------|--------|--------|--------|---------|
| Loop | L | 5 | `L[5digits]_Title.txt` | `L00001_FirstSession.txt` |
| Weekly | W | 4 | `W[4digits]_Title.txt` | `W0001_WeeklySummary.txt` |
| Monthly | M | 4 | `M[4digits]_Title.txt` | `M0001_MonthlySummary.txt` |
| Quarterly | Q | 3 | `Q[3digits]_Title.txt` | `Q001_Quarterly.txt` |

---

## Default Thresholds

| Layer | Required Count | Cumulative Loops |
|-------|----------------|------------------|
| Weekly | 5 Loops | 5 |
| Monthly | 5 Weekly | 25 |
| Quarterly | 3 Monthly | 75 |
| Annual | 4 Quarterly | 300 |

---

## Key Paths

| Item | Path |
|------|------|
| Config file | `~/.claude/plugins/.episodicrag/config.json` |
| Loop files | `{loops_dir}/` |
| Digest files | `{digests_dir}/` |
| GrandDigest | `{essences_dir}/GrandDigest.txt` |
| ShadowGrandDigest | `{essences_dir}/ShadowGrandDigest.txt` |

---

## Daily Workflow

```text
Daily:   Add Loop → /digest
Weekend: @digest-auto → /digest weekly
Month-end: @digest-auto → /digest monthly
```

---

## Troubleshooting

1. Run `@digest-auto` to check status
2. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for specific solutions
3. See [FAQ.md](FAQ.md) for conceptual questions

---

## Related Documentation

| Purpose | Document |
|---------|----------|
| Getting Started | [QUICKSTART.en.md](QUICKSTART.en.md) |
| Daily Operations | [GUIDE.md](GUIDE.md) |
| Advanced Settings | [ADVANCED.md](ADVANCED.md) |
| Glossary | [GLOSSARY.en.md](../../GLOSSARY.en.md) |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
