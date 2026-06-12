#!/usr/bin/env python3
"""Voice MCP server — exposes say and listen as tools."""

import subprocess
import sys
import json

SOUNDS_DIR = "/System/Library/Sounds"


def beep(sound="Tink"):
    subprocess.Popen(["afplay", f"{SOUNDS_DIR}/{sound}.aiff"])


def tool_say(text, voice=None, rate=None):
    import time
    timings = {}
    t0 = time.monotonic()

    beep("Hero")
    timings["hero_beep_ms"] = round((time.monotonic() - t0) * 1000)

    cmd = ["say"]
    if voice:
        cmd.extend(["-v", voice])
    if rate:
        cmd.extend(["-r", str(rate)])
    cmd.append(text)
    t1 = time.monotonic()
    subprocess.run(cmd, check=False)
    timings["say_ms"] = round((time.monotonic() - t1) * 1000)

    timings["total_ms"] = round((time.monotonic() - t0) * 1000)
    return {"status": "spoken", "text": text, "timings": timings}


def tool_list_voices(language=None):
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=False)
    voices = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split("#")
        description = parts[1].strip() if len(parts) > 1 else ""
        name_lang = parts[0].strip()
        name_parts = name_lang.rsplit(None, 1)
        if len(name_parts) == 2:
            name, lang = name_parts
        else:
            name, lang = name_parts[0], ""
        name = name.strip()
        lang = lang.strip()
        if language and language.lower() not in lang.lower() and language.lower() not in name.lower():
            continue
        voices.append({"name": name, "language": lang, "sample": description})
    return {"voices": voices, "count": len(voices)}


def tool_listen(timeout=10, phrase_time_limit=30):
    import speech_recognition as sr
    import time

    timings = {}
    t0 = time.monotonic()

    r = sr.Recognizer()
    r.energy_threshold = 150
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.5

    t1 = time.monotonic()
    with sr.Microphone(sample_rate=48000) as source:
        timings["mic_open_ms"] = round((time.monotonic() - t1) * 1000)

        t2 = time.monotonic()
        r.adjust_for_ambient_noise(source, duration=1)
        timings["noise_calibration_ms"] = round((time.monotonic() - t2) * 1000)

        beep("Tink")
        timings["ready_at_ms"] = round((time.monotonic() - t0) * 1000)

        try:
            t3 = time.monotonic()
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            timings["recording_ms"] = round((time.monotonic() - t3) * 1000)
        except sr.WaitTimeoutError:
            return {"error": "No speech detected", "text": None, "timings": timings}

    beep("Pop")

    import tempfile, os
    import mlx_whisper

    t4 = time.monotonic()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
        f.write(audio.get_wav_data())
    timings["wav_write_ms"] = round((time.monotonic() - t4) * 1000)

    try:
        t5 = time.monotonic()
        result = mlx_whisper.transcribe(tmp_path, path_or_hf_repo="mlx-community/whisper-base.en-mlx")
        timings["transcription_ms"] = round((time.monotonic() - t5) * 1000)

        text = result.get("text", "").strip()
        timings["total_ms"] = round((time.monotonic() - t0) * 1000)
        if not text:
            return {"error": "Could not understand audio", "text": None, "timings": timings}
        return {"text": text, "error": None, "timings": timings}
    except Exception as e:
        return {"error": f"Transcription error: {e}", "text": None, "timings": timings}
    finally:
        os.unlink(tmp_path)


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
        "name": "list_voices",
        "description": "List available macOS text-to-speech voices with their language and sample phrase. Use to pick the right voice for a scenario (e.g. a British accent, a novelty voice, a specific language).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Filter by language code or name (e.g. 'en_US', 'fr', 'Japanese'). Optional — returns all voices if omitted."},
            },
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
        elif name == "list_voices":
            result = tool_list_voices(args.get("language"))
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
