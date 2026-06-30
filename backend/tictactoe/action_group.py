"""Action Group Lambda: applies the AI's chosen tic-tac-toe move.

Invoked by the riddle/tictactoe AgentCore agent as a tool. Writes the move to
DynamoDB, sets current_turn back to Human, and pushes new state over WebSocket.
"""
import os

import boto3

from common.leaderboard import record_result
from common.db import events, EVENT_BUS, json_dumps

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
WS_ENDPOINT = os.environ["WS_ENDPOINT"]

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def _winner(board):
    for a, b, c in LINES:
        if board[a] != 0 and board[a] == board[b] == board[c]:
            return "Human" if board[a] == 1 else "AI"
    return "Draw" if all(c != 0 for c in board) else None


def lambda_handler(event, _ctx):
    match_id = event["matchId"]
    cell = int(event["cell"])
    item = TABLE.get_item(Key={"PK": f"MATCH#{match_id}", "SK": "META"})["Item"]
    board = item["state"]["board"]

    if board[cell] != 0:
        return {"ok": False, "error": "cell occupied"}

    board[cell] = -1  # AI is O / -1
    item["state"] = {"board": board, "winner": _winner(board)}
    item["currentTurn"] = "Human"
    TABLE.put_item(Item=item)

    w = item["state"]["winner"]
    if w:
        record_result(item.get("username", "guest"), "tictactoe", item.get("difficulty", "easy"),
                       "win" if w == "Human" else "draw" if w == "Draw" else "loss")

    api = boto3.client("apigatewaymanagementapi", endpoint_url=WS_ENDPOINT)
    api.post_to_connection(
        ConnectionId=item["connectionId"],
        Data=json_dumps({"type": "state", "match": item}).encode(),
    )
    events.put_events(Entries=[{"EventBusName": EVENT_BUS, "Source": "game.engine", "DetailType": "MatchEvent",
                                "Detail": json_dumps({"matchId": match_id, "connectionId": item["connectionId"],
                                                      "wsEndpoint": WS_ENDPOINT,
                                                      "summary": {"game": "tictactoe", "actor": "AI", "cell": cell,
                                                                  "board": board, "winner": w}})}])
    return {"ok": True, "winner": item["state"]["winner"]}


