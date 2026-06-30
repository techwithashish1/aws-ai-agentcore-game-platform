export type Cell = -1 | 0 | 1;
export interface TicTacToeMatch {
  matchId: string;
  gameId: "tictactoe";
  currentTurn: "Human" | "AI";
  state: { board: Cell[]; winner: "Human" | "AI" | "Draw" | null };
}
export interface Unit { id: string; owner: "Human" | "AI"; cls: "Tank" | "Striker" | "Support"; hp: number; x: number; y: number }
export const UNIT_STATS: Record<string, { hp: number; move: number; range: number; atk: number; def: number }> = {
  Tank:    { hp: 140, move: 2, range: 1, atk: 18, def: 8 },
  Striker: { hp:  90, move: 3, range: 1, atk: 30, def: 3 },
  Support: { hp:  80, move: 2, range: 3, atk: 20, def: 2 },
};
export interface TacticalMatch {
  matchId: string;
  gameId: "tactical";
  currentTurn: "Human" | "AI";
  state: { units: Unit[]; turn: number; winner: "Human" | "AI" | null; actedIds: string[] };
}
export type Match = TicTacToeMatch | TacticalMatch;

export const WS_URL = import.meta.env.VITE_WS_URL ?? "wss://localhost";
