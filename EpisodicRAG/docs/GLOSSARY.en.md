[Home](../README.md) > [Docs](README.md) > GLOSSARY

[English](GLOSSARY.en.md) | [日本語](GLOSSARY.md)

# Glossary

A collection of terminology definitions used in the EpisodicRAG plugin.

## Table of Contents

- [Basic Concepts](#basic-concepts)
- [Memory Structure](#memory-structure)
- [8-Layer Hierarchy](#8-layer-hierarchy)
- [Processes & Operations](#processes--operations)
- [File Naming Conventions](#file-naming-conventions)
- [Commands & Skills](#commands--skills)
- [Configuration Files](#configuration-files)
- [Related Documents](#related-documents)

---

## Basic Concepts

### plugin_root
**Definition**: The plugin installation directory

- The directory where `.claude-plugin/config.json` exists
- Skills and scripts operate relative to this directory
- Example: `C:\Users\anyth\.claude\plugins\marketplaces\Plugins-Weave\EpisodicRAG`

### base_dir
**Definition**: The base directory for data placement

- **Location**: `base_dir` field in `config.json`
- **Format**: Relative path from plugin_root
- **Example**: `.` (within plugin), `../../../../../DEV/data` (external)

Path resolution: `plugin_root + base_dir` → actual data base directory

### paths
**Definition**: Placement locations for each data directory

- **Location**: `paths` section in `config.json`
- **Format**: Relative paths from base_dir
- **Includes**: `loops_dir`, `digests_dir`, `essences_dir`, `identity_file_path`

Path resolution: `base_dir + paths.loops_dir` → actual Loop directory

### Loop
**Definition**: A text file recording an entire conversation session with AI

- **Format**: `Loop[sequence_number]_[title].txt`
- **Example**: `Loop0001_CognitiveArchitecture.txt`
- **Regex**: `^Loop[0-9]+_[\p{L}\p{N}ー・\w]+\.txt$`
- **Location**: `{loops_dir}/`

Loops are the smallest unit of the EpisodicRAG system and serve as the foundation for all Digest generation.

### Digest
**Definition**: A hierarchical record that summarizes and integrates multiple Loops or lower-level Digests

Types of Digests:

| Type | Description |
|------|-------------|
| **Individual Digest** | Summary of a single Loop/Digest |
| **Overall Digest** | Integrated summary of multiple Loops/Digests |
| **Provisional Digest** | Temporary digest (pre-finalization storage) |
| **Regular Digest** | Official digest (finalized) |

### Essences
**Definition**: Meta-information directory storing GrandDigest and ShadowGrandDigest

- **Location**: `{essences_dir}/`
- **Contains**:
  - `GrandDigest.txt` - Finalized memory
  - `ShadowGrandDigest.txt` - Unfinalized memory

---

## Memory Structure

### GrandDigest
**Definition**: JSON file storing finalized long-term memory

- **File**: `{essences_dir}/GrandDigest.txt`
- **Contents**: Latest finalized Digest for each hierarchy (Weekly to Centurial)
- **Update timing**: When a hierarchy is finalized with `/digest <type>`

> See [ARCHITECTURE.md](dev/ARCHITECTURE.md#granddigesttxt) for detailed format

```json
{
  "metadata": { "last_updated": "...", "version": "1.0" },
  "major_digests": {
    "weekly": { "overall_digest": {...} },
    "monthly": { "overall_digest": {...} }
  }
}
```

### ShadowGrandDigest
**Definition**: JSON file storing unfinalized incremental digests

- **File**: `{essences_dir}/ShadowGrandDigest.txt`
- **Purpose**: Temporarily stores analysis results of new Loops, promoted to Regular after threshold is met
- **Update timing**: When new Loops are detected and analyzed with `/digest`

> See [ARCHITECTURE.md](dev/ARCHITECTURE.md#shadowgranddigesttxt) for detailed format

```json
{
  "latest_digests": {
    "weekly": {
      "overall_digest": {
        "source_files": ["Loop0001.txt", "Loop0002.txt"],
        "keywords": ["<!-- PLACEHOLDER -->", ...],
        "abstract": "<!-- PLACEHOLDER: ... -->"
      }
    }
  }
}
```

### Provisional Digest
**Definition**: Individual digest for next hierarchy (temporary file)

- **Location**: `{digests_dir}/{level_dir}/Provisional/`
- **Format**: `{prefix}{number}_Individual.txt`
- **Example**: `W0001_Individual.txt`
- **Lifespan**: Until RegularDigest finalization when `/digest <type>` is executed

### Regular Digest
**Definition**: Finalized official digest file

- **Location**: `{digests_dir}/{level_dir}/`
- **Format**: `{date}_{prefix}{number}_title.txt`
- **Example**: `2025-07-01_W0001_CognitiveArchitecture.txt`

---

## 8-Layer Hierarchy

EpisodicRAG manages memory across 8 hierarchical layers (approximately 108 years):

| Layer | Prefix | Time Scale | Default Threshold | Cumulative Loops |
|-------|--------|-----------|------------------|-----------------|
| **Weekly** | W | ~1 week | 5 Loops | 5 |
| **Monthly** | M | ~1 month | 5 Weekly | 25 |
| **Quarterly** | Q | ~3 months | 3 Monthly | 75 |
| **Annual** | A | ~1 year | 4 Quarterly | 300 |
| **Triennial** | T | ~3 years | 3 Annual | 900 |
| **Decadal** | D | ~9 years | 3 Triennial | 2,700 |
| **Multi-decadal** | MD | ~27 years | 3 Decadal | 8,100 |
| **Centurial** | C | ~108 years | 4 Multi-decadal | 32,400 |

---

## Processes & Operations

### Mottled Memory (まだらボケ)
**Definition**: A state where AI cannot remember the contents of Loops (fragmented memory)

> See [_common-concepts.md](../skills/shared/_common-concepts.md#まだらボケとは) for patterns and countermeasures

### Threshold
**Definition**: Minimum number of files required to generate each hierarchy's Digest

- **Location**: `{plugin_root}/.claude-plugin/config.json`
- **Change method**: Interactively change with `@digest-config` skill

### Cascade
**Definition**: Process that automatically propagates to upper hierarchies when finalizing a Digest

```
Weekly finalized → Added to Monthly Shadow
Monthly finalized → Added to Quarterly Shadow
...
```

### Placeholder
**Definition**: An unanalyzed state where `digest: null` in ShadowGrandDigest

- **Cause**: Error during `/digest` processing, or analysis incomplete
- **Resolution**: Re-run `/digest` to complete analysis

---

## File Naming Conventions

### Loop Files
```
Format: Loop[sequence_number]_[title].txt
Number: 4+ digit number (larger = newer)
Examples: Loop0001_InitialSession.txt
          Loop0186_CognitiveArchitecture.txt
```

### Provisional Files
```
Format: {prefix}{number}_Individual.txt
Examples: W0001_Individual.txt
          M001_Individual.txt
```

### Regular Files
```
Format: {date}_{prefix}{number}_title.txt
Examples: 2025-07-01_W0001_CognitiveArchitecture.txt
          2025-08-15_M001_MonthlySummary.txt
```

---

## Commands & Skills

| Command/Skill | Description |
|---------------|-------------|
| `/digest` | Detect new Loops and analyze (mottled memory prevention) |
| `/digest <type>` | Finalize specific hierarchy (e.g., `/digest weekly`) |
| `@digest-auto` | System status diagnosis and recommended action presentation |
| `@digest-setup` | Initial setup (interactive) |
| `@digest-config` | Configuration changes (interactive) |

---

## Configuration Files

### config.json
**Location**: `{plugin_root}/.claude-plugin/config.json`

```json
{
  "base_dir": ".",
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": {
    "weekly_threshold": 5,
    "monthly_threshold": 5,
    "quarterly_threshold": 3,
    "annual_threshold": 4,
    "triennial_threshold": 3,
    "decadal_threshold": 3,
    "multi_decadal_threshold": 3,
    "centurial_threshold": 4
  }
}
```

---

## Related Documents

- [README.md](../README.md) - Project Overview
- [QUICKSTART.md](user/QUICKSTART.md) - 5-minute Tutorial
- [GUIDE.md](user/GUIDE.md) - User Guide
- [ARCHITECTURE.md](dev/ARCHITECTURE.md) - Technical Specifications

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
