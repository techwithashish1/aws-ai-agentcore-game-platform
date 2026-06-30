"""Tactical Arena specialist agent for Amazon Bedrock AgentCore Runtime.

8x8 squad combat (Tank/Striker/Support). The orchestrator invokes this runtime
with the full unit list and a modelProfile. The selected profile chooses between
Nova and Claude per difficulty tier, and the agent reasons over positioning,
HP pressure, and focus-fire before calling the action-group Lambda.
"""
import json
import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

app = BedrockAgentCoreApp()
_lambda = boto3.client("lambda")
ACTION_GROUP_FN = os.environ.get("ACTION_GROUP_FUNCTION", "TacticalActionFunction")

MODEL_MAP = {
    "easy_amazon": os.environ.get("TACTICAL_EASY_AMAZON_MODEL_ID", "amazon.nova-lite-v1:0"),
    "easy_claude": os.environ.get("TACTICAL_EASY_CLAUDE_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
    "medium_amazon": os.environ.get("TACTICAL_MEDIUM_AMAZON_MODEL_ID", "amazon.nova-micro-v1:0"),
    "medium_claude": os.environ.get("TACTICAL_MEDIUM_CLAUDE_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
    "hard_amazon": os.environ.get("TACTICAL_HARD_AMAZON_MODEL_ID", "amazon.nova-pro-v1:0"),
    "hard_claude": os.environ.get("TACTICAL_HARD_CLAUDE_MODEL_ID", "global.anthropic.claude-opus-4-6-v1"),
}

SYSTEM = (
    "You command the AI squad in an 8x8 tactical arena. Tank(hp140,atk18,rng1), "
    "Striker(hp90,atk30,rng1), Support(hp80,atk20,rng3). Manhattan distance. "
    "Damage=max(1,atk-def). Focus the lowest-HP enemy in range; otherwise move "
    "closer. Keep Support at range, Tank in front. Output EXACTLY one JSON object "
    "only with this schema: {\"unitId\": str, \"action\": \"move\"|\"attack\", "
    "\"x\": int, \"y\": int, \"targetId\": str}. Choose exactly ONE action for "
    "ONE AI unit per turn."
)

STRATEGIST = (
    "You are the squad Strategist. Read the unit list and give a 2-line battle plan: "
    "which enemy to focus, who advances, who holds. No tool calls, just the plan."
)

EXECUTOR = (
    "You are the squad Executor. Given the tactical board, strategist plan, and unit "
    "stats, output EXACTLY one JSON object with the chosen action for one AI unit. "
    "Use this schema: {\"unitId\": str, \"action\": \"move\"|\"attack\", "
    "\"x\": int, \"y\": int, \"targetId\": str}. If moving, set targetId to \"\". "
    "If attacking, set x and y to -1. No extra text."
)


def unit_action(match_id: str, unit_id: str, action: str, x: int = -1, y: int = -1, target_id: str = "") -> str:
    """Order one unit. action='move' uses x,y; action='attack' uses target_id."""
    resp = _lambda.invoke(
        FunctionName=ACTION_GROUP_FN,
        Payload=json.dumps({"matchId": match_id, "game": "tactical", "unitId": unit_id,
                            "action": action, "x": x, "y": y, "targetId": target_id}).encode(),
    )
    return resp["Payload"].read().decode()


def _agent(model_profile: str, system_prompt: str = EXECUTOR) -> Agent:
    return Agent(model=BedrockModel(model_id=MODEL_MAP.get(model_profile, MODEL_MAP["medium_amazon"])), system_prompt=system_prompt)


def _plan(model_profile: str, units) -> str:
    """A2A: a Strategist agent sets intent; easy profiles skip planning."""
    if model_profile.startswith("easy_"):
        return ""
    strategist = _agent(model_profile, STRATEGIST)
    return str(strategist(f"Units={json.dumps(units)}. Plan the squad's turn."))


def _parse_action(text: str) -> dict:
    try:
        start, end = text.index("{"), text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {}


def _fallback_action(units) -> dict:
    ai_units = [u for u in units if u.get("owner") == "AI" and u.get("hp", 0) > 0]
    human_units = [u for u in units if u.get("owner") == "Human" and u.get("hp", 0) > 0]
    if not ai_units:
        return {}
    actor = ai_units[0]
    if human_units:
        target = human_units[0]
        return {"unitId": actor["id"], "action": "attack", "targetId": target["id"], "x": -1, "y": -1}
    return {"unitId": actor["id"], "action": "move", "x": actor.get("x", 0), "y": max(0, actor.get("y", 0) - 1), "targetId": ""}


def _normalize_action(action: dict, units) -> dict:
    ai_ids = {u["id"] for u in units if u.get("owner") == "AI" and u.get("hp", 0) > 0}
    human_ids = {u["id"] for u in units if u.get("owner") == "Human" and u.get("hp", 0) > 0}
    unit_id = action.get("unitId")
    if unit_id not in ai_ids:
        return _fallback_action(units)
    move = action.get("action") == "move"
    attack = action.get("action") == "attack"
    if not (move or attack):
        return _fallback_action(units)
    if attack:
        target_id = action.get("targetId")
        if target_id not in human_ids:
            return _fallback_action(units)
        return {"unitId": unit_id, "action": "attack", "targetId": target_id, "x": -1, "y": -1}
    return {"unitId": unit_id, "action": "move", "x": int(action.get("x", -1)), "y": int(action.get("y", -1)), "targetId": ""}


@app.entrypoint
def invoke(payload: dict):
    match_id = payload["matchId"]
    model_profile = payload.get("modelProfile", "easy_amazon")
    difficulty = payload.get("difficulty", "easy")
    units = payload["units"]
    plan = _plan(model_profile, units)
    agent = _agent(model_profile)
    response = str(agent(f"matchId={match_id}. Units={json.dumps(units)}. Turn={payload.get('turn')}. "
                         f"{payload.get('opponent', '')} Strategist plan: {plan or 'none'}. "
                         "Choose exactly one action for exactly one AI unit and output JSON only."))
    action = _normalize_action(_parse_action(response), units)
    unit_action(
        match_id=match_id,
        unit_id=action["unitId"],
        action=action["action"],
        x=int(action.get("x", -1)),
        y=int(action.get("y", -1)),
        target_id=str(action.get("targetId", "")),
    )
    return {"status": "moved", "matchId": match_id}


if __name__ == "__main__":
    app.run()
