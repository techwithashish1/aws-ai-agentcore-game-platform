import { Match } from "../common/types";

const MARK = { "1": "X", "-1": "O", "0": "" } as const;

/** Tic-tac-toe board. Sends {action:"move", matchId, cell} over the shared socket. */
export function TicTacToe({ match, status, send }: { match: Match | null; status: string; send: (p: unknown) => void }) {
  const board = match?.gameId === "tictactoe" ? match.state.board : Array(9).fill(0);
  const winner = match?.gameId === "tictactoe" ? match.state.winner : null;
  const turn = match?.currentTurn;

  const play = (cell: number) => {
    if (!match || match.gameId !== "tictactoe" || turn !== "Human" || winner || board[cell] !== 0) return;
    send({ action: "move", matchId: match.matchId, cell });
  };

  const banner = winner
    ? winner === "Draw"
      ? "It's a draw"
      : `${winner} wins!`
    : turn === "AI"
      ? "🤖 AI thinking…"
      : status || "Your move — you are X";

  return (
    <>
      <div className="board-banner">{banner}</div>
      <div className="board-wrap">
        <div className="ttt-board">
          {board.map((c, i) => {
            const mark = MARK[String(c) as keyof typeof MARK];
            const cls = c === 1 ? "ttt-cell x" : c === -1 ? "ttt-cell o" : "ttt-cell";
            return (
              <button
                key={i}
                className={cls}
                onClick={() => play(i)}
                disabled={!match || turn !== "Human" || !!winner || c !== 0}
              >
                {mark}
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}
