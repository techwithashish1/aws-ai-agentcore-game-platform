"""Tactical Arena rules: 8x8 squad combat. Tank/Striker/Support."""
STATS = {
    "Tank": {"hp": 140, "atk": 18, "def": 8, "move": 2, "range": 1},
    "Striker": {"hp": 90, "atk": 30, "def": 3, "move": 3, "range": 1},
    "Support": {"hp": 80, "atk": 20, "def": 2, "move": 2, "range": 3},
}


def distance(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def new_state():
    def mk(owner, cls, x, y):
        return {"id": f"{owner}-{cls}", "owner": owner, "cls": cls, "hp": STATS[cls]["hp"], "x": x, "y": y}
    return {
        "turn": 1, "winner": None,
        "units": [mk("Human", "Tank", 1, 1), mk("Human", "Striker", 1, 2), mk("Human", "Support", 1, 3),
                  mk("AI", "Tank", 6, 6), mk("AI", "Striker", 6, 5), mk("AI", "Support", 6, 4)],
    }


def winner(units):
    human = any(u["owner"] == "Human" and u["hp"] > 0 for u in units)
    ai = any(u["owner"] == "AI" and u["hp"] > 0 for u in units)
    return "Human" if not ai else "AI" if not human else None
