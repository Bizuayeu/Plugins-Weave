# Ralph Loop Setup Script (Windows PowerShell)
# Creates state file for in-session Ralph loop

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Force UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Parse arguments
$PromptParts = @()
$MaxIterations = 0
$CompletionPromise = "null"

$i = 0
while ($i -lt $Arguments.Count) {
    $arg = $Arguments[$i]

    switch -Regex ($arg) {
        "^(-h|--help)$" {
            @"
Ralph Loop - Interactive self-referential development loop (Windows)

USAGE:
  /ralph-loop [PROMPT...] [OPTIONS]

ARGUMENTS:
  PROMPT...    Initial prompt to start the loop (can be multiple words without quotes)

OPTIONS:
  --max-iterations <n>           Maximum iterations before auto-stop (default: unlimited)
  --completion-promise '<text>'  Promise phrase (USE QUOTES for multi-word)
  -h, --help                     Show this help message

DESCRIPTION:
  Starts a Ralph Wiggum loop in your CURRENT session. The stop hook prevents
  exit and feeds your output back as input until completion or iteration limit.

  To signal completion, you must output: <promise>YOUR_PHRASE</promise>

EXAMPLES:
  /ralph-loop Build a todo API --completion-promise 'DONE' --max-iterations 20
  /ralph-loop --max-iterations 10 Fix the auth bug
  /ralph-loop Refactor cache layer  (runs forever)

STOPPING:
  Only by reaching --max-iterations or detecting --completion-promise
  No manual stop - Ralph runs infinitely by default!
"@
            exit 0
        }
        "^--max-iterations$" {
            $i++
            if ($i -ge $Arguments.Count -or $Arguments[$i] -notmatch '^\d+$') {
                Write-Error "Error: --max-iterations requires a positive integer"
                exit 1
            }
            $MaxIterations = [int]$Arguments[$i]
        }
        "^--completion-promise$" {
            $i++
            if ($i -ge $Arguments.Count -or [string]::IsNullOrEmpty($Arguments[$i])) {
                Write-Error "Error: --completion-promise requires a text argument"
                exit 1
            }
            $CompletionPromise = $Arguments[$i]
        }
        default {
            $PromptParts += $arg
        }
    }
    $i++
}

# Join prompt parts
$Prompt = $PromptParts -join " "

# Validate prompt
if ([string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Error @"
Error: No prompt provided

Ralph needs a task description to work on.

Examples:
  /ralph-loop Build a REST API for todos
  /ralph-loop Fix the auth bug --max-iterations 20
  /ralph-loop --completion-promise 'DONE' Refactor code

For all options: /ralph-loop --help
"@
    exit 1
}

# Create state file
$ClaudeDir = ".claude"
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
}

$StateFile = "$ClaudeDir/ralph-loop.local.md"
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Format completion promise for YAML
$CompletionPromiseYaml = if ($CompletionPromise -ne "null") { "`"$CompletionPromise`"" } else { "null" }

$StateContent = @"
---
active: true
iteration: 1
max_iterations: $MaxIterations
completion_promise: $CompletionPromiseYaml
started_at: "$Timestamp"
---

$Prompt
"@

# Write UTF8 without BOM (PowerShell 5.x compatibility)
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($StateFile, $StateContent, $Utf8NoBom)

# Output setup message
$MaxIterMsg = if ($MaxIterations -gt 0) { $MaxIterations } else { "unlimited" }
$PromiseMsg = if ($CompletionPromise -ne "null") { "$CompletionPromise (ONLY output when TRUE - do not lie!)" } else { "none (runs forever)" }

Write-Output @"
Ralph loop activated in this session!

Iteration: 1
Max iterations: $MaxIterMsg
Completion promise: $PromiseMsg

The stop hook is now active. When you try to exit, the SAME PROMPT will be
fed back to you. You'll see your previous work in files, creating a
self-referential loop where you iteratively improve on the same task.

To monitor: Get-Content .claude/ralph-loop.local.md -Head 10

WARNING: This loop cannot be stopped manually! It will run infinitely
    unless you set --max-iterations or --completion-promise.


"@

# Output the initial prompt
if (-not [string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Output ""
    Write-Output $Prompt
}

# Display completion promise requirements if set
if ($CompletionPromise -ne "null") {
    Write-Output @"

===============================================================
CRITICAL - Ralph Loop Completion Promise
===============================================================

To complete this loop, output this EXACT text:
  <promise>$CompletionPromise</promise>

STRICT REQUIREMENTS (DO NOT VIOLATE):
  - Use <promise> XML tags EXACTLY as shown above
  - The statement MUST be completely and unequivocally TRUE
  - Do NOT output false statements to exit the loop
  - Do NOT lie even if you think you should exit

IMPORTANT - Do not circumvent the loop:
  Even if you believe you're stuck, the task is impossible,
  or you've been running too long - you MUST NOT output a
  false promise statement. The loop is designed to continue
  until the promise is GENUINELY TRUE. Trust the process.
===============================================================
"@
}

exit 0
