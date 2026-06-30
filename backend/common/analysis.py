"""Board analysis: lightweight, model-free position insight shared as an MCP tool.

Deterministic heuristics (no LLM call) so any agent — a coach, a critic, or a future
game — can cheaply ask "what's going on in this position?" and get immediate threats,
opportunities, and a one-line read. Exposed via the MCP catalog as `analyze_position`.
"""
from tictactoe.rules import LINES


def _ttt_lines(board):
    """Find lines where one side has two-in-a-row and the third cell is empty."""
    threats, chances = [], []  # AI about to win / Human about to win
    for a, b, c in LINES:
        cells = [board[a], board[b], board[c]]
        empties = [i for i, v in zip((a, b, c), cells) if v == 0]
        if len(empties) != 1:
            continue
        if cells.count(-1) == 2:
            threats.append(empties[0])
        elif cells.count(1) == 2:
            chances.append(empties[0])
    return sorted(set(threats)), sorted(set(chances))


def _analyze_tictactoe(board):
    threats, chances = _ttt_lines(board)
    if chances:
        read = f"You can win now at cell {chances[0]}."
    elif threats:
        read = f"Block the AI at cell {threats[0]} or you lose next turn."
    elif board[4] == 0:
        read = "Center is open — take cell 4 for the strongest position."
    else:
        read = "Even position; fight for a corner and build a double threat."
    return {
        "game": "tictactoe",
        "humanWins": chances,   # cells where Human wins immediately
        "aiThreats": threats,   # cells the Human must block
        "read": read,
    }


def _analyze_tactical(units):
    units = units or []
    mine = [u for u in units if u.get("owner") == "Human"]
    foes = [u for u in units if u.get("owner") == "AI"]
    read = (
        f"You have {len(mine)} unit(s) vs {len(foes)}. "
        + ("Press the advantage and trade aggressively." if len(mine) >= len(foes)
           else "You're outnumbered — group up and fight defensively.")
    )
    return {"game": "tactical", "myUnits": len(mine), "enemyUnits": len(foes), "read": read}


def analyze_position(game: str, state: dict) -> dict:
    """Return immediate threats/opportunities and a one-line read for a position."""
    if game == "tictactoe":
        return _analyze_tictactoe(state.get("board") or [0] * 9)
    if game == "tactical":
        return _analyze_tactical(state.get("units"))
    return {"game": game, "read": "No analyzer registered for this game."}
