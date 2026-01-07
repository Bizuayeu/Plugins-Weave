# Ralph Wiggum Stop Hook (Windows PowerShell)
# Prevents session exit when a ralph-loop is active
# Feeds Claude's output back as input to continue the loop

# Force UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Read hook input from stdin
$HookInput = $input | Out-String

# Check if ralph-loop is active
$StateFile = ".claude/ralph-loop.local.md"

if (-not (Test-Path $StateFile)) {
    # No active loop - allow exit
    exit 0
}

# Read and parse state file
$StateContent = Get-Content $StateFile -Raw -Encoding UTF8

# Extract frontmatter (YAML between ---)
$FrontmatterMatch = [regex]::Match($StateContent, '(?s)^---\r?\n(.+?)\r?\n---')
if (-not $FrontmatterMatch.Success) {
    Write-Error "Ralph loop: State file corrupted - no frontmatter found"
    Remove-Item $StateFile -Force
    exit 0
}

$Frontmatter = $FrontmatterMatch.Groups[1].Value

# Parse YAML fields
$Iteration = 0
$MaxIterations = 0
$CompletionPromise = "null"

foreach ($line in $Frontmatter -split "`n") {
    $line = $line.Trim()
    if ($line -match '^iteration:\s*(\d+)') {
        $Iteration = [int]$Matches[1]
    }
    elseif ($line -match '^max_iterations:\s*(\d+)') {
        $MaxIterations = [int]$Matches[1]
    }
    elseif ($line -match '^completion_promise:\s*"?([^"]+)"?') {
        $CompletionPromise = $Matches[1].Trim()
    }
}

# Validate iteration
if ($Iteration -le 0) {
    Write-Error "Ralph loop: State file corrupted - invalid iteration"
    Remove-Item $StateFile -Force
    exit 0
}

# Check if max iterations reached
if ($MaxIterations -gt 0 -and $Iteration -ge $MaxIterations) {
    Write-Output "Ralph loop: Max iterations ($MaxIterations) reached."
    Remove-Item $StateFile -Force
    exit 0
}

# Get transcript path from hook input
try {
    $HookData = $HookInput | ConvertFrom-Json
    $TranscriptPath = $HookData.transcript_path
}
catch {
    Write-Error "Ralph loop: Failed to parse hook input"
    Remove-Item $StateFile -Force
    exit 0
}

if (-not (Test-Path $TranscriptPath)) {
    Write-Error "Ralph loop: Transcript file not found: $TranscriptPath"
    Remove-Item $StateFile -Force
    exit 0
}

# Read transcript (JSONL format)
$TranscriptLines = Get-Content $TranscriptPath -Encoding UTF8

# Find last assistant message
$LastOutput = ""
foreach ($line in $TranscriptLines) {
    if ($line -match '"role":\s*"assistant"') {
        try {
            $Message = $line | ConvertFrom-Json
            $TextContent = $Message.message.content | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
            if ($TextContent) {
                $LastOutput = $TextContent -join "`n"
            }
        }
        catch {
            # Skip malformed lines
        }
    }
}

if ([string]::IsNullOrEmpty($LastOutput)) {
    Write-Error "Ralph loop: No assistant message found in transcript"
    Remove-Item $StateFile -Force
    exit 0
}

# Check for completion promise
if ($CompletionPromise -ne "null" -and -not [string]::IsNullOrEmpty($CompletionPromise)) {
    # Extract text from <promise> tags
    $PromiseMatch = [regex]::Match($LastOutput, '<promise>(.+?)</promise>', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if ($PromiseMatch.Success) {
        $PromiseText = $PromiseMatch.Groups[1].Value.Trim()
        $PromiseText = $PromiseText -replace '\s+', ' '

        if ($PromiseText -eq $CompletionPromise) {
            Write-Output "Ralph loop: Detected <promise>$CompletionPromise</promise>"
            Remove-Item $StateFile -Force
            exit 0
        }
    }
}

# Not complete - continue loop with SAME PROMPT
$NextIteration = $Iteration + 1

# Extract prompt (everything after the closing ---)
$PromptMatch = [regex]::Match($StateContent, '(?s)^---\r?\n.+?\r?\n---\r?\n(.+)$')
$PromptText = ""
if ($PromptMatch.Success) {
    $PromptText = $PromptMatch.Groups[1].Value.Trim()
}

if ([string]::IsNullOrEmpty($PromptText)) {
    Write-Error "Ralph loop: State file corrupted - no prompt text found"
    Remove-Item $StateFile -Force
    exit 0
}

# Update iteration in state file (UTF8 without BOM)
$NewStateContent = $StateContent -replace 'iteration:\s*\d+', "iteration: $NextIteration"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($StateFile, $NewStateContent, $Utf8NoBom)

# Build system message
if ($CompletionPromise -ne "null" -and -not [string]::IsNullOrEmpty($CompletionPromise)) {
    $SystemMsg = "Ralph iteration $NextIteration | To stop: output <promise>$CompletionPromise</promise> (ONLY when statement is TRUE - do not lie to exit!)"
}
else {
    $SystemMsg = "Ralph iteration $NextIteration | No completion promise set - loop runs infinitely"
}

# Output JSON to block the stop and feed prompt back
$OutputJson = @{
    decision = "block"
    reason = $PromptText
    systemMessage = $SystemMsg
} | ConvertTo-Json -Compress

Write-Output $OutputJson

exit 0
