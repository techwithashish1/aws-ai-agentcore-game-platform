"""Tic-tac-toe rules. Cell: 1=Human, -1=AI, 0=empty. Spec: M in {0,1,-1}^3x3."""
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def empty_board():
    return [0] * 9


def evaluate(board):
    """Return 'Human', 'AI', 'Draw', or None (in progress)."""
    for a, b, c in LINES:
        if board[a] != 0 and board[a] == board[b] == board[c]:
            return "Human" if board[a] == 1 else "AI"
    return "Draw" if all(c != 0 for c in board) else None


def apply_move(board, index, player):
    """Validate + apply a move; raise ValueError on illegal move."""
    if not isinstance(index, int) or index < 0 or index > 8:
        raise ValueError("Cell index out of range")
    if board[index] != 0:
        raise ValueError("Cell already occupied")
    nxt = list(board)
    nxt[index] = player
    return {"board": nxt, "winner": evaluate(nxt)}
