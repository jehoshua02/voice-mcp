#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Setting up voice-mcp..."

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Requires macOS (uses say command and system sounds)."
    exit 1
fi

if ! brew ls --versions portaudio &>/dev/null; then
    echo "Installing portaudio..."
    brew install portaudio
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q SpeechRecognition pyaudio mlx-whisper

echo "Pre-downloading mlx-whisper base.en model..."
"$VENV_DIR/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/whisper-base.en-mlx')"

echo "Setup complete."
echo "Add to Claude Code settings.json:"
echo ""
echo "  \"mcpServers\": {"
echo "    \"voice\": {"
echo "      \"command\": \"$VENV_DIR/bin/python\","
echo "      \"args\": [\"$SCRIPT_DIR/server.py\"]"
echo "    }"
echo "  }"
