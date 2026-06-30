"""Leaderboard: record results and read top players, keyed by game + difficulty.

Single-table layout:
  PK = LEADER#<game>#<difficulty>   SK = USER#<username>
  GSI1 (Leaderboard): GSI1PK = LEADER#<game>#<difficulty>   GSI1SK = score
Scoring: +3 per win, +1 per draw, +0 per loss.
"""
from boto3.dynamodb.conditions import Key

from common.db import table

DIFFICULTIES = ("easy", "medium", "hard")
POINTS = {"win": 3, "draw": 1, "loss": 0}


def _pk(game: str, difficulty: str) -> str:
    return f"LEADER#{game}#{difficulty}"


def record_result(username: str, game: str, difficulty: str, outcome: str) -> None:
    """Atomically bump a player's tallies. outcome in {win, draw, loss}."""
    pk = _pk(game, difficulty)
    table.update_item(
        Key={"PK": pk, "SK": f"USER#{username}"},
        UpdateExpression=(
            "SET username=:u, gameId=:g, difficulty=:d, GSI1PK=:pk "
            "ADD wins :w, losses :l, draws :dr, games :one, score :pts, GSI1SK :pts"
        ),
        ExpressionAttributeValues={
            ":u": username, ":g": game, ":d": difficulty, ":pk": pk, ":one": 1,
            ":w": 1 if outcome == "win" else 0,
            ":l": 1 if outcome == "loss" else 0,
            ":dr": 1 if outcome == "draw" else 0,
            ":pts": POINTS.get(outcome, 0),
        },
    )


def top(game: str, difficulty: str, limit: int = 10):
    res = table.query(
        IndexName="Leaderboard",
        KeyConditionExpression=Key("GSI1PK").eq(_pk(game, difficulty)),
        ScanIndexForward=False, Limit=limit,
    )
    if res["Items"]:
        return [
            {"username": i["username"], "score": int(i.get("score", 0)), "wins": int(i.get("wins", 0)),
             "losses": int(i.get("losses", 0)), "draws": int(i.get("draws", 0)), "games": int(i.get("games", 0))}
            for i in res["Items"]
        ]

    if difficulty not in DIFFICULTIES:
        return []

    merged = {}
    for tier in DIFFICULTIES:
        tier_rows = table.query(
            IndexName="Leaderboard",
            KeyConditionExpression=Key("GSI1PK").eq(_pk(game, tier)),
            ScanIndexForward=False,
        )["Items"]
        for item in tier_rows:
            username = item["username"]
            acc = merged.setdefault(username, {"username": username, "score": 0, "wins": 0, "losses": 0, "draws": 0, "games": 0})
            acc["score"] += int(item.get("score", 0))
            acc["wins"] += int(item.get("wins", 0))
            acc["losses"] += int(item.get("losses", 0))
            acc["draws"] += int(item.get("draws", 0))
            acc["games"] += int(item.get("games", 0))

    rows = sorted(merged.values(), key=lambda row: (-row["score"], row["username"]))[:limit]
    return [
        {"username": i["username"], "score": int(i.get("score", 0)), "wins": int(i.get("wins", 0)),
         "losses": int(i.get("losses", 0)), "draws": int(i.get("draws", 0)), "games": int(i.get("games", 0))}
        for i in rows
    ]
