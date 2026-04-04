# EmotionPulse Setup Command

## Metadata
- Name: setup
- Description: EmotionPulseの対話式セットアップ（hook登録 + statusline設定 + display config）
- User invocable: true

## Instructions

You are setting up the EmotionPulse plugin. This plugin displays the model's emotion vector in Claude Code's statusline.

### Architecture

```
[Stop hook fires after each response]
  → stop_hook_handler: block + systemMessage注入
  → メインエージェントが自己評価
  → python emotion_writer.py '{"calm":2,...}'
  → emotion_state.json書き出し
  → statuslineが読んで絵文字表示
```

### Step 1: Verify plugin location

Check that the EmotionPulse plugin exists by reading:
- `~/DEV/plugins-weave/EmotionPulse/scripts/domain/constants.py`

If not found, also try:
- `~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse/scripts/domain/constants.py`

Store the found path as `<plugin_dir>`. If neither found, inform the user and stop.

### Step 2: Ask display preferences

Ask the user (use AskUserQuestion):

> EmotionPulse display設定:
> 1. ラベル表示: ON / OFF
> 2. 言語: ja (日本語) / en (English)
>
> デフォルト: labels=ON, lang=ja
> → `安定性:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡`
>
> Enter to accept defaults, or specify your preference:

### Step 3: Create display config

Write the config file to `~/.claude/plugins/.emotionpulse/config.json`:

```json
{
  "version": "1.2.0",
  "display": {
    "show_labels": true,
    "language": "ja"
  }
}
```

Adjust `show_labels` and `language` based on user's answer from Step 2.

### Step 4: Copy thin launcher

Copy the Stop hook launcher to the user hooks directory:

```bash
cp "<plugin_dir>/hooks/stop_handler.py" ~/.claude/hooks/emotion_pulse_stop.py
```

### Step 5: Register Stop hook

Read the current project settings from `.claude/settings.json` (in the user's working directory).

Add (or merge) the Stop hook entry into settings.json:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python \"~/.claude/hooks/emotion_pulse_stop.py\"",
        "timeout": 5000
      }]
    }]
  }
}
```

**IMPORTANT**: Preserve any existing hooks in the file. Merge, don't overwrite.

### Step 6: Configure statusline

Use the `/statusline` command or the statusline-setup agent to configure the statusline script. The script command is:

```bash
cd <plugin_dir> && python -m scripts statusline
```

Where `<plugin_dir>` is the EmotionPulse plugin root found in Step 1.

### Step 7: Confirm

Display a summary to the user:

```
EmotionPulse setup complete!

  Hook: Stop (command) → stop_handler.py → systemMessage → 自己評価
  Writer: python emotion_writer.py '{"calm":N,...}'
  Statusline: python -m scripts statusline
  Config: ~/.claude/plugins/.emotionpulse/config.json
  Display: labels=ON, lang=ja

Each response will show emotion indicators in the statusline:
  安定性:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡
```
