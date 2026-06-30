"""Commentary Lambda adapter: EventBridge -> AgentCore runtime -> WS push.

This Lambda no longer hosts the LLM logic directly. It invokes the dedicated
Commentary AgentCore runtime, then synthesizes voice and pushes line+audio.
"""
import os

from common.agentcore import invoke_runtime_json
from commentary.voice import synthesize
from common.ws import push_to_client

COMMENTARY_RUNTIME_ARN = os.environ.get("COMMENTARY_RUNTIME_ARN", "")


def lambda_handler(event, _ctx):
    detail = event["detail"]
    endpoint = detail.get("wsEndpoint")
    connection_id = detail.get("connectionId")
    summary = detail.get("summary", {})

    if not COMMENTARY_RUNTIME_ARN:
        return {"ok": False, "error": "COMMENTARY_RUNTIME_ARN is not configured"}

    result = invoke_runtime_json(
        COMMENTARY_RUNTIME_ARN,
        detail.get("matchId", "commentary"),
        {"summary": summary},
    )
    line = str(result.get("line", "")).strip() or "What a match!"
    emotion = str(result.get("emotion", "neutral") or "neutral")
    audio = synthesize(line, emotion)

    if endpoint and connection_id:
        push_to_client(endpoint, connection_id, {
            "type": "commentary",
            "line": line,
            "emotion": emotion,
            "audio": audio,  # base64 mp3, '' if synthesis unavailable
        })
    return {"ok": True}
