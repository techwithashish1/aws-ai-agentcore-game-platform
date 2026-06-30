"""Coach agent: a teaching A2A role that turns match events into improvement tips.

A pure consumer of existing contracts — it never plays a move. It watches each
MatchEvent, reads the latest move/board (and the Strategist's plan when present),
and returns one short, constructive tip the player can use on their next turn.

The same `coach_tip` function backs both the EventBridge handler and the MCP
`explain_move` tool, so coaching behaves identically whether the platform fires it
or another agent pulls it.
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

MODEL_ID = os.environ.get("COACH_MODEL_ID", "amazon.nova-lite-v1:0")

TOPICS = ["opening", "tempo", "defense", "threats", "positioning", "endgame", "general"]

SYSTEM = (
    "You are a friendly, sharp game coach for a Human-vs-AI board-game arena. "
    "Given the latest move and board/units, give the HUMAN player ONE short, "
    "constructive tip (max 22 words) to play better next turn. Be specific and "
    "encouraging — point out a missed threat, a better square, or a tempo gain. "
    "Never make a move yourself. Reply ONLY as JSON: {\"tip\": str, \"topic\": one "
    f"of {TOPICS}}}. No extra text."
)

_agent = Agent(model=BedrockModel(model_id=MODEL_ID), system_prompt=SYSTEM)
app = BedrockAgentCoreApp()


def coach_tip(summary: dict) -> dict:
    """Return {'tip': str, 'topic': str} of constructive feedback for a match event."""
    res = str(_agent(json.dumps(summary)))
    try:
        start, end = res.index("{"), res.rindex("}") + 1
        data = json.loads(res[start:end])
        tip = str(data.get("tip", "")).strip()
        topic = data.get("topic", "general")
    except (ValueError, json.JSONDecodeError):
        tip, topic = res.strip()[:140], "general"
    if topic not in TOPICS:
        topic = "general"
    return {"tip": tip, "topic": topic}


@app.entrypoint
def invoke(payload: dict):
    """AgentCore entrypoint: accepts {'summary': {...}} and returns tip+topic."""
    summary = payload.get("summary", payload)
    return coach_tip(summary)


if __name__ == "__main__":
    app.run()
