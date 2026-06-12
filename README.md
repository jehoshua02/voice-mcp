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

Add to your `~/.claude/settings.json` or project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "voice": {
      "command": "/path/to/voice-mcp/.venv/bin/python",
      "args": ["/path/to/voice-mcp/server.py"]
    }
  }
}
```

## Tools

### `say`

Speak text aloud.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to speak |
| `voice` | string | No | Voice name (e.g. Samantha, Daniel) |
| `rate` | integer | No | Words per minute (default ~175) |

### `listen`

Listen to microphone and transcribe speech.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `timeout` | integer | No | Seconds to wait for speech (default 10) |
| `phrase_time_limit` | integer | No | Max seconds of speech (default 30) |

Returns `{"text": "transcribed speech", "error": null}` on success.

## Audio Cues

- **Tink** — mic is ready, speak now
- **Pop** — recording captured, transcribing

## How it works

- **TTS**: macOS built-in `say` command
- **STT**: OpenAI Whisper `base.en` model running locally (no API calls)
- **MCP**: JSON-RPC over stdio (MCP protocol 2024-11-05)
