# Ralph Wiggum Windows Plugin

Windows-native PowerShell port of the Ralph Wiggum technique for iterative, self-referential AI development loops in Claude Code.

## Why This Plugin?

The original [ralph-wiggum@claude-plugins-official](https://awesomeclaude.ai/ralph-wiggum) plugin uses bash scripts, which don't work natively on Windows. This port provides identical functionality using PowerShell, enabling Windows users to leverage the Ralph Wiggum technique without WSL or Git Bash.

## What is Ralph?

Ralph is a development methodology based on continuous AI agent loops. As Geoffrey Huntley describes it: **"Ralph is a Bash loop"** - a simple `while true` that repeatedly feeds an AI agent a prompt file, allowing it to iteratively improve its work until completion.

The technique is named after Ralph Wiggum from The Simpsons, embodying the philosophy of persistent iteration despite setbacks.

### Core Concept

This plugin implements Ralph using a **Stop hook** that intercepts Claude's exit attempts:

```powershell
# You run ONCE:
/ralph-loop "Your task description" --completion-promise "DONE"

# Then Claude Code automatically:
# 1. Works on the task
# 2. Tries to exit
# 3. Stop hook blocks exit
# 4. Stop hook feeds the SAME prompt back
# 5. Repeat until completion
```

## Installation

```bash
/plugin install ralph-wiggum-windows@plugins-weave
```

## Quick Start

```bash
/ralph-loop "Build a REST API for todos. Requirements: CRUD operations, input validation, tests. Output <promise>COMPLETE</promise> when done." --completion-promise "COMPLETE" --max-iterations 50
```

Claude will:
- Implement the API iteratively
- Run tests and see failures
- Fix bugs based on test output
- Iterate until all requirements met
- Output the completion promise when done

## Commands

### /ralph-loop

Start a Ralph loop in your current session.

**Usage:**
```bash
/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"
```

**Options:**
- `--max-iterations <n>` - Stop after N iterations (default: unlimited)
- `--completion-promise <text>` - Phrase that signals completion

### /cancel-ralph

Cancel the active Ralph loop.

**Usage:**
```bash
/cancel-ralph
```

### /help

Show detailed help and examples.

## Differences from Original

| Feature | Original (bash) | Windows (PowerShell) |
|---------|-----------------|---------------------|
| Scripts | `.sh` files | `.ps1` files |
| Shell | bash | PowerShell |
| Platform | Unix/macOS/WSL | Native Windows |
| Functionality | Full | Full (identical) |

## Philosophy

Ralph embodies several key principles:

1. **Iteration > Perfection** - Don't aim for perfect on first try. Let the loop refine the work.
2. **Failures Are Data** - "Deterministically bad" means failures are predictable and informative.
3. **Operator Skill Matters** - Success depends on writing good prompts, not just having a good model.
4. **Persistence Wins** - Keep trying until success. The loop handles retry logic automatically.

## When to Use Ralph

**Good for:**
- Well-defined tasks with clear success criteria
- Tasks requiring iteration and refinement
- Greenfield projects where you can walk away
- Tasks with automatic verification (tests, linters)

**Not good for:**
- Tasks requiring human judgment or design decisions
- One-shot operations
- Tasks with unclear success criteria

## Credits

- Original technique by Geoffrey Huntley: https://ghuntley.com/ralph/
- Original Claude Code plugin: ralph-wiggum@claude-plugins-official
- Windows port by Weave @ plugins-weave

## License

MIT
