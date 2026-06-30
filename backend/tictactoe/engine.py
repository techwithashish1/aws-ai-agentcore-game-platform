"""Game Engine: validates the human tic-tac-toe move, then emits TurnCompleted.

Loads/creates the match, applies the move, sets current_turn=AI, persists, pushes
state, and fires TurnCompleted to EventBridge so the orchestrator wakes the agent.
"""
import json
import os
import uuid
from datetime import datetime, timezone

from common.db import table, events, match_pk, EVENT_BUS, json_dumps
from common.ws import push_to_client
from common.leaderboard import record_result
from common.profile import note_move
from tictactoe.rules import apply_move, empty_board, evaluate


def lambda_handler(event, _ctx):
    ctx = event["requestContext"]
    cid = ctx["connectionId"]
    endpoint = f"https://{ctx['domainName']}/{ctx['stage']}"
    body = json.loads(event.get("body") or "{}")

    if body.get("matchId"):
        res = table.get_item(Key={"PK": match_pk(body["matchId"]), "SK": "META"})
        if "Item" not in res:
            return _reject(endpoint, cid, "Match not found")
        match = res["Item"]
    else:
        mid = str(uuid.uuid4())
        match = {"PK": match_pk(mid), "SK": "META", "matchId": mid, "gameId": "tictactoe",
                 "connectionId": cid, "currentTurn": "Human", "username": body.get("username", "guest"),
                 "difficulty": body.get("difficulty", "easy"), "state": {"board": empty_board(), "winner": None}}

    if match["currentTurn"] != "Human" or match["state"]["winner"]:
        return _reject(endpoint, cid, "Not your turn")
    if "cell" not in body:
        _persist(match, endpoint)
        return {"statusCode": 200}

    try:
        match["state"] = apply_move(match["state"]["board"], int(body["cell"]), 1)
    except ValueError as e:
        return _reject(endpoint, cid, str(e))

    note_move(match.get("username", "guest"), "tictactoe", f"cell{int(body['cell'])}")
    match["connectionId"] = cid
    match["currentTurn"] = "Human" if match["state"]["winner"] else "AI"
    _persist(match, endpoint)

    winner = match["state"]["winner"]
    _commentate(match, endpoint, {"game": "tictactoe", "actor": "Human", "cell": int(body["cell"]),
                                  "board": match["state"]["board"], "winner": winner})
    if winner:
        _record(match)
    else:
        events.put_events(Entries=[{"EventBusName": EVENT_BUS, "Source": "game.engine", "DetailType": "TurnCompleted",
                                    "Detail": json_dumps({"matchId": match["matchId"], "gameId": "tictactoe", "connectionId": cid})}])
    return {"statusCode": 200}


def _commentate(match, endpoint, summary):
    events.put_events(Entries=[{"EventBusName": EVENT_BUS, "Source": "game.engine", "DetailType": "MatchEvent",
                                "Detail": json_dumps({"matchId": match["matchId"], "connectionId": match["connectionId"],
                                                      "wsEndpoint": endpoint, "summary": summary})}])


def _record(match):
    w = match["state"]["winner"]
    outcome = "win" if w == "Human" else "draw" if w == "Draw" else "loss"
    record_result(match.get("username", "guest"), "tictactoe", match.get("difficulty", "easy"), outcome)


def _persist(match, endpoint):
    match["state"]["winner"] = evaluate(match["state"]["board"])
    match["updatedAt"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=match)
    push_to_client(endpoint, match["connectionId"], {"type": "state", "match": match})


def _reject(endpoint, cid, message):
    push_to_client(endpoint, cid, {"type": "error", "message": message})
    return {"statusCode": 400}
