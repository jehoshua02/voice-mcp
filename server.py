#!/usr/bin/env python3
"""Voice MCP server — exposes say and listen as tools."""

import subprocess
import sys
import json

SOUNDS_DIR = "/System/Library/Sounds"


def beep(sound="Tink"):
    subprocess.run(["afplay", f"{SOUNDS_DIR}/{sound}.aiff"], check=False)


def tool_say(text, voice=None, rate=None):
    cmd = ["say"]
    if voice:
        cmd.extend(["-v", voice])
    if rate:
        cmd.extend(["-r", str(rate)])
    cmd.append(text)
    subprocess.run(cmd, check=False)
    return {"status": "spoken", "text": text}


def tool_listen(timeout=10, phrase_time_limit=30):
    import speech_recognition as sr

    r = sr.Recognizer()
    r.energy_threshold = 150
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.5

    with sr.Microphone(sample_rate=48000) as source:
        r.adjust_for_ambient_noise(source, duration=1)
        beep("Tink")

        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return {"error": "No speech detected", "text": None}

    beep("Pop")

    try:
        text = r.recognize_whisper(audio, model="base.en")
        return {"text": text.strip(), "error": None}
    except sr.UnknownValueError:
        return {"error": "Could not understand audio", "text": None}
    except sr.RequestError as e:
        return {"error": f"Transcription error: {e}", "text": None}


TOOLS = [
    {
        "name": "say",
        "description": "Speak text aloud using macOS text-to-speech. Use for voice output, notifications, and voice conversations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak aloud"},
                "voice": {"type": "string", "description": "Voice name (e.g. Samantha, Daniel). Optional."},
                "rate": {"type": "integer", "description": "Words per minute. Default ~175. Optional."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "listen",
        "description": "Listen to microphone input and transcribe speech to text using local Whisper. Returns transcribed text. Use for voice input and voice conversations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "description": "Seconds to wait for speech before giving up. Default 10.", "default": 10},
                "phrase_time_limit": {"type": "integer", "description": "Max seconds of speech to capture. Default 30.", "default": 30},
            },
        },
    },
]


def handle_request(request):
    method = request.get("method")

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "voice", "version": "0.1.0"},
        }

    if method == "tools/list":
        return {"tools": TOOLS}

    if method == "tools/call":
        name = request["params"]["name"]
        args = request["params"].get("arguments", {})

        if name == "say":
            result = tool_say(args["text"], args.get("voice"), args.get("rate"))
        elif name == "listen":
            result = tool_listen(args.get("timeout", 10), args.get("phrase_time_limit", 30))
        else:
            return {"error": {"code": -32601, "message": f"Unknown tool: {name}"}}

        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "isError": result.get("error") is not None,
        }

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None

    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = request.get("id")
        result = handle_request(request)

        if result is None:
            continue

        response = {"jsonrpc": "2.0", "id": req_id}
        if "error" in result and isinstance(result["error"], dict) and "code" in result["error"]:
            response["error"] = result["error"]
        else:
            response["result"] = result

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
