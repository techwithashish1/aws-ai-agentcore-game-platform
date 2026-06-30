"""Opponent profiles: lightweight per-player memory so the AI adapts across matches.

Stores a rolling summary per username+game (games played, win/loss, recent move
hints). The orchestrator reads it and passes a short note to the agent; engines call
note_move to keep it fresh. Keeps the AI feeling like it 'remembers' how you play.
"""
from common.db import table


def _key(username: str, game: str):
    return {"PK": f"PROFILE#{username}", "SK": f"GAME#{game}"}


def get_profile(username: str, game: str) -> dict:
    res = table.get_item(Key=_key(username, game))
    return res.get("Item", {}).get("profile", {})


def note_move(username: str, game: str, hint: str) -> None:
    """Append a recent-move hint (keep last 10)."""
    item = table.get_item(Key=_key(username, game)).get("Item") or {**_key(username, game), "profile": {}}
    prof = item.get("profile", {})
    moves = (prof.get("recent") or [])[-9:] + [hint]
    prof["recent"] = moves
    prof["games"] = prof.get("games", 0) + 1
    item["profile"] = prof
    table.put_item(Item=item)


def profile_note(username: str, game: str) -> str:
    """One-line summary for the agent prompt; '' if unknown player."""
    p = get_profile(username, game)
    if not p:
        return ""
    return f"Opponent {username}: {p.get('games', 0)} prior games; recent={p.get('recent', [])[-5:]}."
