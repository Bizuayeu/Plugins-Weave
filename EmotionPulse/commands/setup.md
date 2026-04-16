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
  → hooks/stop_handler.py (thin launcher, sys.path管理)
  → stop_hook_handler.handle_stop(): lock制御 + block
      reason: systemMessage全文を埋め込み (silent mode #34600 fallback)
      systemMessage: 自己評価指示 (正規ルート、#34600修正後に復活)
  → メインエージェントが自己評価
  → python hooks/emotion_writer_launcher.py '{"calm":2,...}'
      (thin launcher, sys.path管理で他pluginとのimport衝突を回避)
  → emotion_writer.main() → emotion_state.json書き出し
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
> → `落ち着き:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡`
>
> Enter to accept defaults, or specify your preference:

### Step 3: Create display config

Write the config file to `~/.claude/plugins/.emotionpulse/config.json`:

```json
{
  "version": "1.3.0",
  "display": {
    "show_labels": true,
    "language": "ja"
  }
}
```

Adjust `show_labels` and `language` based on user's answer from Step 2.

### Step 4: Register Stop hook

Read the current project settings from `.claude/settings.json` (in the user's working directory).

Add (or merge) the Stop hook entry into settings.json. The command should point directly to `<plugin_dir>/hooks/stop_handler.py`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python \"<plugin_dir>/hooks/stop_handler.py\"",
        "timeout": 5000
      }]
    }]
  }
}
```

Replace `<plugin_dir>` with the resolved path from Step 1.

You can also generate this entry programmatically:
```bash
cd "<plugin_dir>"
python -c "import json; from scripts.application.hook_config import build_stop_hook_entry; print(json.dumps(build_stop_hook_entry(), indent=2))"
```

**IMPORTANT**: Preserve any existing hooks in the file. Merge, don't overwrite.

### Step 5: Configure statusline

Use the `/statusline` command or the statusline-setup agent to configure the statusline script. The script command is:

```bash
cd <plugin_dir> && python -m scripts statusline
```

Where `<plugin_dir>` is the EmotionPulse plugin root found in Step 1.

### Step 6: Confirm

Display a summary to the user:

```
EmotionPulse setup complete!

  Hook: Stop (command) → hooks/stop_handler.py → stop_hook_handler
  Fallback: reason field embeds systemMessage (silent mode #34600 workaround)
  Writer: python hooks/emotion_writer_launcher.py '{"calm":N,...}'
  Statusline: python -m scripts statusline
  Config: ~/.claude/plugins/.emotionpulse/config.json
  Display: labels=ON, lang=ja

Each response will show emotion indicators in the statusline:
  落ち着き:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡
```
