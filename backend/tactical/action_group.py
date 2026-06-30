"""Action Group Lambda: applies the AI squad's orders in Tactical Arena.

Invoked by the Tactical Arena AgentCore agent. Validates and applies one move or
attack, recomputes winner, sets current_turn back to Human, and pushes state over
WebSocket.
"""
import os

import boto3

from common.leaderboard import record_result
from common.db import events, EVENT_BUS, json_dumps

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
WS_ENDPOINT = os.environ["WS_ENDPOINT"]

STATS = {"Tank": (18, 8), "Striker": (30, 3), "Support": (20, 2)}  # (attack, defense)


def lambda_handler(event, _ctx):
    match_id = event["matchId"]
    item = TABLE.get_item(Key={"PK": f"MATCH#{match_id}", "SK": "META"})["Item"]
    units = {u["id"]: u for u in item["state"]["units"]}
    unit = units.get(event["unitId"])
    if not unit or unit["owner"] != "AI" or unit["hp"] <= 0:
        return {"ok": False, "error": "invalid unit"}

    if event["action"] == "move":
        x, y = int(event["x"]), int(event["y"])
        if not (0 <= x < 8 and 0 <= y < 8) or any(u["x"] == x and u["y"] == y and u["hp"] > 0 for u in units.values()):
            return {"ok": False, "error": "illegal tile"}
        unit["x"], unit["y"] = x, y
    elif event["action"] == "attack":
        tgt = units.get(event["targetId"])
        if not tgt or tgt["hp"] <= 0:
            return {"ok": False, "error": "bad target"}
        tgt["hp"] = max(0, tgt["hp"] - max(1, STATS[unit["cls"]][0] - STATS[tgt["cls"]][1]))

    alive = lambda o: any(u["owner"] == o and u["hp"] > 0 for u in units.values())
    item["state"]["winner"] = "Human" if not alive("AI") else "AI" if not alive("Human") else None
    item["currentTurn"] = "Human"
    item["state"]["units"] = list(units.values())
    TABLE.put_item(Item=item)

    w = item["state"]["winner"]
    if w:
        record_result(item.get("username", "guest"), "tactical", item.get("difficulty", "easy"),
                       "win" if w == "Human" else "loss")

    api = boto3.client("apigatewaymanagementapi", endpoint_url=WS_ENDPOINT)
    api.post_to_connection(ConnectionId=item["connectionId"], Data=json_dumps({"type": "state", "match": item}).encode())
    events.put_events(Entries=[{"EventBusName": EVENT_BUS, "Source": "game.engine", "DetailType": "MatchEvent",
                                "Detail": json_dumps({"matchId": match_id, "connectionId": item["connectionId"],
                                                      "wsEndpoint": WS_ENDPOINT,
                                                      "summary": {"game": "tactical", "actor": "AI", "unit": event.get("unitId"),
                                                                  "action": event.get("action"), "winner": w}})}])
    return {"ok": True, "winner": item["state"]["winner"]}
