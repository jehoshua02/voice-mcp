# voice-mcp

MCP server that gives Claude a voice — text-to-speech output and speech-to-text input on macOS.

## Requirements

- macOS (uses `say` command and system sounds)
- Python 3.9+
- Homebrew (for portaudio)

## Setup

```bash
git clone https://github.com/jehoshua02/voice-mcp.git
cd voice-mcp
bash setup.sh
```

## Configure Claude Code

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "voice": {
      "type": "stdio",
      "command": "/path/to/voice-mcp/.venv/bin/python",
      "args": ["/path/to/voice-mcp/server.py"]
    }
  }
}
```

### Auto-allow permissions

Add to `~/.claude/settings.json` under `permissions.allow`:

```json
"mcp__voice__say",
"mcp__voice__listen",
"mcp__voice__list_voices"
```

## Tools

### `say`

Speak text aloud using macOS text-to-speech.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to speak |
| `voice` | string | No | Voice name (e.g. Samantha, Daniel, Zarvox) |
| `rate` | integer | No | Words per minute (default ~175) |

### `listen`

Listen to microphone and transcribe speech to text using local Whisper.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `timeout` | integer | No | Seconds to wait for speech (default 10) |
| `phrase_time_limit` | integer | No | Max seconds of speech (default 30) |

Returns `{"text": "transcribed speech", "error": null}` on success.

### `list_voices`

List available macOS TTS voices with language and sample phrase.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `language` | string | No | Filter by language code or name (e.g. `en_US`, `fr`, `Japanese`) |

Returns `{"voices": [...], "count": N}`. Each voice has `name`, `language`, and `sample` fields.

## Audio Cues

| Sound | Meaning |
|-------|---------|
| Hero | Claude is about to speak |
| Tink | Mic is ready, speak now |
| Pop | Recording captured, transcribing |

## How it works

- **TTS**: macOS built-in `say` command
- **STT**: OpenAI Whisper `base.en` model running locally — no API calls, fully offline
- **MCP**: JSON-RPC over stdio (MCP protocol 2024-11-05)
