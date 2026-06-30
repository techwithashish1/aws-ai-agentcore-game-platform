"""Emotional text-to-speech via Amazon Polly.

Maps the commentary emotion to Polly prosody (rate/pitch/volume) and wraps the line
in SSML, then synthesizes a neural-voice MP3. Returns base64 so it can ride the
existing WebSocket channel with no extra storage. Falls back gracefully if Polly is
unavailable so the text caption still ships.
"""
import base64
import os

import boto3

polly = boto3.client("polly")

VOICE_ID = os.environ.get("COMMENTARY_VOICE", "Matthew")  # neural voice

# emotion -> (rate, pitch, volume) prosody
PROSODY = {
    "neutral": ("medium", "+0%", "medium"),
    "excited": ("fast", "+15%", "x-loud"),
    "joyful": ("fast", "+10%", "loud"),
    "tense": ("slow", "-5%", "medium"),
    "disappointed": ("x-slow", "-15%", "soft"),
    "dramatic": ("slow", "+5%", "loud"),
}


def synthesize(line: str, emotion: str = "neutral") -> str:
    """Return base64-encoded MP3 of the line spoken with emotion; '' on failure."""
    rate, pitch, volume = PROSODY.get(emotion, PROSODY["neutral"])
    ssml = (
        f'<speak><prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
        f"{_escape(line)}</prosody></speak>"
    )
    try:
        resp = polly.synthesize_speech(
            Text=ssml, TextType="ssml", OutputFormat="mp3",
            VoiceId=VOICE_ID, Engine="neural",
        )
        return base64.b64encode(resp["AudioStream"].read()).decode()
    except Exception:
        return ""


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
