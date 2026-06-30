"""WebSocket route 'leaderboard': returns top players for a game + difficulty."""
from common.leaderboard import top
from common.ws import push_to_client


def lambda_handler(event, _ctx):
    ctx = event["requestContext"]
    cid = ctx["connectionId"]
    endpoint = f"https://{ctx['domainName']}/{ctx['stage']}"
    import json
    body = json.loads(event.get("body") or "{}")
    rows = top(body.get("game", "tictactoe"), body.get("difficulty", "easy"), int(body.get("limit", 10)))
    push_to_client(endpoint, cid, {"type": "leaderboard", "game": body.get("game"), "difficulty": body.get("difficulty"), "rows": rows})
    return {"statusCode": 200}
