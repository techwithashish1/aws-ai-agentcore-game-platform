"""Tactical Arena Engine: validates the human squad's move or attack, then emits TurnCompleted.

Accepts WebSocket messages:
  - No matchId → creates a new tactical match and pushes initial state.
  - action='tactical_move' {matchId, unitId, x, y} → moves a Human unit.
  - action='tactical_attack' {matchId, unitId, targetId} → attacks an enemy unit.
  - action='tactical_end_turn' {matchId} → human ends their turn, AI wakes.

All three order types validate ownership, alive status, range, and legality before
applying. After all Human units have acted (or end_turn is called), emits
TurnCompleted to wake the AI.
"""
import json
import os
import uuid
from datetime import datetime, timezone

from common.db import table, events, match_pk, EVENT_BUS, json_dumps
from common.ws import push_to_client
from common.leaderboard import record_result
from common.profile import note_move
from tactical.rules import STATS, new_state, winner, distance


def lambda_handler(event, _ctx):
    ctx = event["requestContext"]
    cid = ctx["connectionId"]
    endpoint = f"https://{ctx['domainName']}/{ctx['stage']}"
    body = json.loads(event.get("body") or "{}")
    action = body.get("action", "")

    # --- Create new match --------------------------------------------------
    if not body.get("matchId"):
        mid = str(uuid.uuid4())
        match = {
            "PK": match_pk(mid), "SK": "META",
            "matchId": mid, "gameId": "tactical",
            "connectionId": cid,
            "currentTurn": "Human",
            "username": body.get("username", "guest"),
            "difficulty": body.get("difficulty", "easy"),
            "state": {**new_state(), "actedIds": []},
        }
        _persist(match, endpoint)
        return {"statusCode": 200}

    # --- Load existing match -----------------------------------------------
    res = table.get_item(Key={"PK": match_pk(body["matchId"]), "SK": "META"})
    if "Item" not in res:
        return _reject(endpoint, cid, "Match not found")
    match = res["Item"]

    if match["currentTurn"] != "Human" or match["state"].get("winner"):
        return _reject(endpoint, cid, "Not your turn")

    units = {u["id"]: u for u in match["state"]["units"]}
    acted = set(match["state"].get("actedIds", []))

    # --- End turn ----------------------------------------------------------
    if action == "tactical_end_turn":
        return _end_turn(match, units, cid, endpoint)

    unit_id = body.get("unitId")
    unit = units.get(unit_id)
    if not unit or unit["owner"] != "Human" or unit["hp"] <= 0:
        return _reject(endpoint, cid, "Invalid unit")
    if unit_id in acted:
        return _reject(endpoint, cid, "Unit already acted this turn")

    # --- Move --------------------------------------------------------------
    if action == "tactical_move":
        x, y = int(body["x"]), int(body["y"])
        if not (0 <= x < 8 and 0 <= y < 8):
            return _reject(endpoint, cid, "Out of bounds")
        occupied = any(u["x"] == x and u["y"] == y and u["hp"] > 0 for u in units.values())
        if occupied:
            return _reject(endpoint, cid, "Tile occupied")
        move_range = STATS[unit["cls"]]["move"]
        if distance(unit, {"x": x, "y": y}) > move_range:
            return _reject(endpoint, cid, "Out of move range")
        unit["x"], unit["y"] = x, y
        note_move(match.get("username", "guest"), "tactical", f"move-{unit_id}->{x},{y}")

    # --- Attack ------------------------------------------------------------
    elif action == "tactical_attack":
        target_id = body.get("targetId")
        target = units.get(target_id)
        if not target or target["owner"] != "AI" or target["hp"] <= 0:
            return _reject(endpoint, cid, "Invalid target")
        atk_range = STATS[unit["cls"]]["range"]
        if distance(unit, target) > atk_range:
            return _reject(endpoint, cid, "Out of attack range")
        dmg = max(1, STATS[unit["cls"]]["atk"] - STATS[target["cls"]]["def"])
        target["hp"] = max(0, target["hp"] - dmg)
        note_move(match.get("username", "guest"), "tactical", f"attack-{unit_id}->{target_id}")

    else:
        return _reject(endpoint, cid, f"Unknown tactical action: {action}")

    # Mark unit as acted
    acted.add(unit_id)
    match["state"]["units"] = list(units.values())
    match["state"]["actedIds"] = list(acted)
    match["state"]["winner"] = winner(match["state"]["units"])
    match["connectionId"] = cid

    w = match["state"]["winner"]
    if w:
        match["currentTurn"] = "Human"  # game over
        _persist(match, endpoint)
        record_result(match.get("username", "guest"), "tactical", match.get("difficulty", "easy"),
                      "win" if w == "Human" else "loss")
        _commentate(match, endpoint, {"game": "tactical", "actor": "Human", "unitId": unit_id,
                                     "action": action, "winner": w})
        return {"statusCode": 200}

    # Check if all human units have acted → auto-end turn
    human_alive = [u for u in units.values() if u["owner"] == "Human" and u["hp"] > 0]
    if all(u["id"] in acted for u in human_alive):
        return _end_turn(match, units, cid, endpoint)

    _persist(match, endpoint)
    _commentate(match, endpoint, {"game": "tactical", "actor": "Human", "unitId": unit_id,
                                 "action": action, "winner": None})
    return {"statusCode": 200}


def _end_turn(match, units, cid, endpoint):
    match["state"]["actedIds"] = []
    match["currentTurn"] = "AI"
    match["connectionId"] = cid
    _persist(match, endpoint)
    events.put_events(Entries=[{
        "EventBusName": EVENT_BUS,
        "Source": "game.engine",
        "DetailType": "TurnCompleted",
        "Detail": json_dumps({
            "matchId": match["matchId"],
            "gameId": "tactical",
            "connectionId": cid,
        }),
    }])
    return {"statusCode": 200}


def _commentate(match, endpoint, summary):
    events.put_events(Entries=[{
        "EventBusName": EVENT_BUS,
        "Source": "game.engine",
        "DetailType": "MatchEvent",
        "Detail": json_dumps({
            "matchId": match["matchId"],
            "connectionId": match["connectionId"],
            "wsEndpoint": endpoint,
            "summary": summary,
        }),
    }])


def _persist(match, endpoint):
    match["updatedAt"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=match)
    push_to_client(endpoint, match["connectionId"], {"type": "state", "match": _clean(match)})


def _reject(endpoint, cid, message):
    push_to_client(endpoint, cid, {"type": "error", "message": message})
    return {"statusCode": 400}


def _clean(obj):
    if isinstance(obj, list):
        return [_clean(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj
