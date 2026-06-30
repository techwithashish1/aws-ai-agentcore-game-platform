"""Coach Lambda adapter: EventBridge -> AgentCore runtime -> WS push."""
import os

from common.agentcore import invoke_runtime_json
from common.ws import push_to_client

COACH_RUNTIME_ARN = os.environ.get("COACH_RUNTIME_ARN", "")


def lambda_handler(event, _ctx):
    detail = event["detail"]
    endpoint = detail.get("wsEndpoint")
    connection_id = detail.get("connectionId")
    summary = detail.get("summary", {})

    # Coach the human's own moves; skip pure AI-move events.
    if summary.get("actor") != "Human":
        return {"ok": True, "skipped": True}

    if not COACH_RUNTIME_ARN:
        return {"ok": False, "error": "COACH_RUNTIME_ARN is not configured"}

    result = invoke_runtime_json(
        COACH_RUNTIME_ARN,
        detail.get("matchId", "coach"),
        {"summary": summary},
    )
    tip = str(result.get("tip", "")).strip()
    topic = str(result.get("topic", "general") or "general")

    if endpoint and connection_id and tip:
        push_to_client(endpoint, connection_id, {
            "type": "coach",
            "tip": tip,
            "topic": topic,
        })
    return {"ok": True}
