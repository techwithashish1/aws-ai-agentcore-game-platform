"""Live-commentary agent: turns a match event into a short, emotional call.

Nova reads the latest move/result and produces one punchy sports-style line plus an
emotion tag. The emotion drives the voice synthesis (see voice.py). Kept tiny and
fast (Nova Micro) so it can fire after every move without slowing the game. Designed
to be exposed as an MCP tool so any game can request commentary.
"""
import json
import os

from strands import Agent
from strands.models import BedrockModel

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except Exception:  # optional outside AgentCore runtime packaging
    class BedrockAgentCoreApp:  # type: ignore[override]
        def entrypoint(self, fn):
            return fn

        def run(self):
            raise RuntimeError("bedrock-agentcore is required to run this as an AgentCore runtime")

MODEL_ID = os.environ.get("COMMENTARY_MODEL_ID", "amazon.nova-micro-v1:0")

EMOTIONS = ["neutral", "excited", "tense", "joyful", "disappointed", "dramatic"]

SYSTEM = (
    "You are a high-energy live e-sports commentator for AI-vs-Human board games. "
    "Given the latest move and score, reply with ONE short spoken line (max 18 words) "
    "and an emotion. Be vivid and reactive: hype big plays, build tension on close "
    "games, mourn blunders. Reply ONLY as JSON: {\"line\": str, \"emotion\": one of "
    f"{EMOTIONS}}}. No extra text."
)

_agent = Agent(model=BedrockModel(model_id=MODEL_ID), system_prompt=SYSTEM)
app = BedrockAgentCoreApp()


def commentate(event: dict) -> dict:
    """Return {'line': str, 'emotion': str} for a match event."""
    res = str(_agent(json.dumps(event)))
    try:
        start, end = res.index("{"), res.rindex("}") + 1
        data = json.loads(res[start:end])
        line = str(data.get("line", "")).strip()
        emotion = data.get("emotion", "neutral")
    except (ValueError, json.JSONDecodeError):
        line, emotion = res.strip()[:120], "neutral"
    if emotion not in EMOTIONS:
        emotion = "neutral"
    return {"line": line or "What a match!", "emotion": emotion}


@app.entrypoint
def invoke(payload: dict):
    """AgentCore entrypoint: accepts {'summary': {...}} and returns line+emotion."""
    summary = payload.get("summary", payload)
    return commentate(summary)


if __name__ == "__main__":
    app.run()
