"""Orchestrator: EventBridge TurnCompleted -> invoke the game's AgentCore Runtime.

Deterministic game -> agent map (spec: 100% code-driven routing). Reads the match
and forwards the game-specific payload to the matching Bedrock AgentCore Runtime.
"""
import os

import boto3

from common.db import table, match_pk, json_dumps
from common.profile import profile_note

core = boto3.client("bedrock-agentcore")

AGENT_RUNTIME = {
    "tictactoe": os.environ.get("TICTACTOE_AGENT_ARN", ""),
    "tactical": os.environ.get("TACTICAL_AGENT_ARN", ""),
}


def lambda_handler(event, _ctx):
    detail = event["detail"]
    match_id, game_id = detail["matchId"], detail["gameId"]
    arn = AGENT_RUNTIME.get(game_id)
    if not arn:
        raise ValueError(f"No agent runtime configured for game {game_id}")

    item = table.get_item(Key={"PK": match_pk(match_id), "SK": "META"})["Item"]
    state = item["state"]
    diff = item.get("difficulty", "easy")
    note = profile_note(item.get("username", "guest"), game_id)
    if game_id == "tactical":
        payload = {"matchId": match_id, "connectionId": item["connectionId"], "units": state["units"], "turn": state.get("turn"), "difficulty": diff, "opponent": note}
    else:
        payload = {"matchId": match_id, "connectionId": item["connectionId"], "board": state["board"], "difficulty": diff, "opponent": note}

    last_err = None
    for attempt in range(3):
        try:
            core.invoke_agent_runtime(agentRuntimeArn=arn, runtimeSessionId=match_id,
                                      payload=json_dumps(payload).encode())
            return {"ok": True, "attempt": attempt}
        except Exception as e:  # transient throttle / cold start
            last_err = e
    raise RuntimeError(f"Agent invoke failed for {game_id} after retries: {last_err}")
