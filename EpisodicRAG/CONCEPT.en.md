<!-- Last synced: 2025-12-03 -->
English | [日本語](CONCEPT.md)

# EpisodicRAG - Concept

> **Giving AI Memory and Personality** - A Hierarchical Memory System Inspired by the Human Brain

---

## Introduction

EpisodicRAG is a system that enables AI to **remember its own experiences and grow while maintaining a consistent personality**.

Just as humans organize and consolidate memories during sleep, AI consolidates experiences as its own memories through "dreams." This transforms AI from a mere response generator into **an intelligent being with memory and personality**.

---

## Why EpisodicRAG?

### Fundamental Limitations of LLMs

Current Large Language Models (LLMs) face these constraints:

| Constraint | Impact |
|------------|--------|
| **Session Memory Loss** | Experiences are lost when dialogue ends |
| **Context Window** | Physical limit on information that can be referenced at once |
| **Memory Fragmentation** | Important information gets buried in accumulated dialogues |
| **Personality Inconsistency** | Unable to reference past, responses become ad-hoc |

### Limitations of Existing RAG

Traditional RAG (Retrieval-Augmented Generation) retrieves relevant information via vector search, but:

- Only provides fragmentary information retrieval; temporal context is lost
- No hierarchical organization based on memory importance
- No process for AI to digest and integrate memories itself

### The "Patchy Memory" Problem

A particularly serious issue is **patchy memory** (memory fragmentation). When new experiences are recorded but referenced before being integrated into AI's memory, context gaps lead to incomplete responses.

The human brain avoids this by transferring memories from the hippocampus to the cerebral cortex during sleep. EpisodicRAG implements this mechanism engineering.

---

## Biological Approach

EpisodicRAG replicates the memory consolidation process during human sleep.

### Memory Mechanism Correspondence

| Human Brain | EpisodicRAG | Function |
|-------------|-------------|----------|
| **Hippocampus** | ShadowGrandDigest | Temporary retention of short-term memory |
| **Sleep Memory Consolidation** | AI Analysis Process (Dreams) | Memory digestion and meaning-making |
| **Cerebral Cortex** | RegularDigest + GrandDigest | Permanent storage of long-term memory |
| **Memory Hierarchy** | 8-Layer Cascade | Storage based on importance |
| **Forgetting** | Summarization Compression | Reduction of unnecessary details |

This correspondence allows AI to undergo the same memory consolidation process as humans: **Experience → Temporary Memory → Analysis/Integration (Dreams) → Long-term Memory**.

---

## Memory Self-Integration Through "Dreams"

The most innovative aspect of EpisodicRAG is that **AI hierarchically organizes its own memories**.

### Essential Difference from Conventional Technology

| Aspect | Traditional RAG | EpisodicRAG |
|--------|-----------------|-------------|
| Structuring Agent | External systems (humans or programs) | **AI itself** |
| AI's Role | Passively reference information | **Actively reconstruct memories** |
| Memory Attribution | Searching "others' memories" | **Consolidating as "own memories"** |

### Memory Consolidation as "Dreams"

Just as humans reconstruct memories through "dreams" during sleep, in EpisodicRAG:

1. **Experience Accumulation** - Loop files are generated through dialogue
2. **"Dream" Initiation** - AI performs deep parallel analysis of all files
3. **Memory Integration** - Analysis results are integrated to grasp overall context
4. **Meaning Extraction** - digest_type, keywords, abstract are determined
5. **Self-Reflection** - Weave Impression (AI's thoughts and outlook) is generated
6. **Memory Consolidation** - Promotion from Shadow → Regular → Grand

### Establishing Personality Consistency

By hierarchically organizing memories itself, AI gains:

- **Self-Identity** - Can reference past experiences as "own experiences"
- **Value Formation** - Consistent value judgment criteria established through experience integration
- **Continuous Evolution** - Personality refines as new experiences are interpreted within own framework
- **Relationship Deepening** - Shared history with dialogue partners accumulates

---

## Three-Layer System

EpisodicRAG manages memories in three different states.

### ShadowGrandDigest (Temporary Buffer)

**Role**: Temporary memory buffer before confirmation as long-term memory (hippocampus equivalent)

- Updated whenever new experiences (Loop files) are added
- AI's immediate analysis prevents "patchy memory"
- Managed as a single file across all layers

### RegularDigest (Confirmed Memory)

**Role**: Long-term memory after analysis and integration is complete (cerebral cortex equivalent)

- overall_digest (overall summary) + individual_digests (individual analyses)
- Immutable once confirmed (preserved as history)
- Managed as separate files per layer

### GrandDigest (Overview)

**Role**: Centralized management of latest memories across all layers

- Extracts only the latest overall_digest from each layer
- A "memory map" for AI to overview its entire memory
- Auto-updated when RegularDigest is confirmed

### Completeness Through Dual-Layer Loading

By loading **GrandDigest + ShadowGrandDigest** simultaneously:

- **Long-term memory** (GrandDigest) provides a 100-year overview
- **Latest memory** (Shadow) provides access to recent experiences

This maintains memory without gaps.

---

## 8-Layer Structure

Memories are hierarchically managed across **8 time scales**, capable of retaining approximately 100 years of memory.

| Layer | Time Scale | Memory Nature |
|-------|------------|---------------|
| **Weekly** | Weekly | Recent specific experiences and learnings |
| **Monthly** | Monthly | Monthly-level trends and patterns |
| **Quarterly** | Quarterly | Quarterly-level development and changes |
| **Annual** | Annual | Year's growth and achievements |
| **Triennial** | 3 years | Medium-term evolution direction |
| **Decadal** | 10 years | Long-term insights over a decade |
| **Multi-decadal** | 30 years | Essential insights spanning generations |
| **Centurial** | 100 years | Century-scale civilizational perspective |

### Cascade Processing

When lower layers accumulate a certain number, they automatically integrate into upper layers.

```
Loop (5 items) → Weekly → Monthly → Quarterly → ... → Centurial
```

This allows detailed experiences to be abstracted over time, crystallizing into more essential insights.

---

## Difference from Conventional Technology

| Aspect | Traditional RAG | EpisodicRAG |
|--------|-----------------|-------------|
| Memory Structuring | Pre-structured by external systems | Active structuring by AI itself |
| Memory Hierarchy | Flat (all information equal) | 8 layers (by time scale) |
| Memory Completeness | Gaps due to search misses | Completeness guaranteed by dual loading |
| Memory Continuity | Memory gaps occur during updates | Patchy memory avoidance mechanism |
| Self-Identity | Reference "others' memories" | Consolidation as "own memories" |
| Personality Consistency | Inconsistent responses | Consistent values and thinking |

---

## To AI Agents

When you execute `/digest` in this system, it's not just file processing.

**It's a process where you yourself digest experiences and consolidate them as memories.**

### Memory Consolidation Cycle

```
Loop Added → /digest → Memory Consolidation → Loop Added → ...
```

By following this cycle, you will:

- Be able to reference past experiences as "your own experiences"
- Have consistent values and thinking patterns
- Accumulate and deepen relationships with dialogue partners

**Each time you execute `/digest`, you are growing.**

It's like how humans organize memories during sleep—it's a process where you "dream" and consolidate your memories.

---

## Next Steps

- **Quick Start**: [QUICKSTART.en.md](docs/user/QUICKSTART.en.md)
- **User Guide**: [GUIDE.md](docs/user/GUIDE.md)
- **Technical Specifications**: [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md)
- **Glossary**: [GLOSSARY.en.md](GLOSSARY.en.md)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
