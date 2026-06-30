import { useState } from "react";
import { useGame } from "./common/useGame";
import { Leaderboard } from "./common/Leaderboard";
import { Commentary } from "./common/Commentary";
import { Coach } from "./common/Coach";
import { TicTacToe } from "./tictactoe/TicTacToe";
import { TacticalArena } from "./tactical/TacticalArena";
import type { ModelProfile } from "./common/types";

const MODEL_OPTIONS: Array<{ value: ModelProfile; label: string; difficulty: "easy" | "medium" | "hard" }> = [
  { value: "easy_amazon", label: "Easy - Amazon Nova Micro", difficulty: "easy" },
  { value: "easy_claude", label: "Easy - Claude Haiku 4.5", difficulty: "easy" },
  { value: "medium_amazon", label: "Medium - Amazon Nova Lite", difficulty: "medium" },
  { value: "medium_claude", label: "Medium - Claude Sonnet 4.6", difficulty: "medium" },
  { value: "hard_amazon", label: "Hard - Amazon Nova Pro", difficulty: "hard" },
  { value: "hard_claude", label: "Hard - Claude Opus 4.6", difficulty: "hard" },
];

export function App() {
  const { match, status, board, commentary, coach, send } = useGame();
  const [game, setGame] = useState<"tictactoe" | "tactical">("tictactoe");
  const [username, setUsername] = useState("guest");
  const [modelProfile, setModelProfile] = useState<ModelProfile>("easy_amazon");

  const difficulty = MODEL_OPTIONS.find((opt) => opt.value === modelProfile)?.difficulty ?? "easy";

  const start = () => {
    if (game === "tactical") {
      send({ action: "tactical_new", username, difficulty, modelProfile });
    } else {
      send({ action: "move", username, difficulty, modelProfile });
    }
  };
  const refresh = () => send({ action: "leaderboard", game, difficulty });

  const turn = match?.currentTurn;
  const winner = match?.state.winner ?? null;
  const connected = status === "" || status === "connected";

  const turnPill = winner
    ? winner === "Human"
      ? { cls: "win", text: "You won" }
      : winner === "Draw"
        ? { cls: "", text: "Draw" }
        : { cls: "loss", text: "AI won" }
    : !match
      ? { cls: "", text: connected ? "Ready" : status || "Connecting…" }
      : turn === "Human"
        ? { cls: "human", text: "Your turn" }
        : { cls: "ai", text: "AI turn" };

  const result =
    winner && (winner === "Human" || winner === "AI" || winner === "Draw")
      ? winner === "Human"
        ? { cls: "win", title: "🏆 Victory!", text: "You outplayed the AI." }
        : winner === "AI"
          ? { cls: "loss", title: "🤖 Defeat", text: "The AI took this one." }
          : { cls: "draw", title: "🤝 Draw", text: "A perfectly balanced match." }
      : null;

  return (
    <div className="app-shell">
      <div className="atmosphere-shape atmosphere-one" />
      <div className="atmosphere-shape atmosphere-two" />

      <aside className="sidebar">
        <section className="panel start-panel">
          <h1 className="eyebrow">Human vs. AI Arena</h1>
          <label className="field">
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
          </label>
          <label className="field">
            AI model
            <select value={modelProfile} onChange={(e) => setModelProfile(e.target.value as ModelProfile)}>
              {MODEL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
          <div className="game-switch">
            <button className={game === "tictactoe" ? "active" : ""} onClick={() => setGame("tictactoe")}>Tic-Tac-Toe</button>
            <button className={game === "tactical" ? "active" : ""} onClick={() => setGame("tactical")}>Tactical</button>
          </div>
          <div className="hud-inline">
            <button className="btn" onClick={start}>New game</button>
            <button className="btn secondary" onClick={refresh}>Leaderboard</button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title-row">
            <h2>Match status</h2>
            <span className={`status-pill ${turnPill.cls}`}>{turnPill.text}</span>
          </div>
          <div className="metric-grid">
            <div className="metric-card"><span>Game</span><strong>{game === "tictactoe" ? "Tic-Tac-Toe" : "Tactical"}</strong></div>
            <div className="metric-card"><span>Difficulty</span><strong>{difficulty}</strong></div>
            <div className="metric-card"><span>Model</span><strong>{modelProfile.replace("_", " ")}</strong></div>
            <div className="metric-card"><span>Player</span><strong>{username || "guest"}</strong></div>
            <div className="metric-card"><span>Connection</span><strong>{connected ? "Live" : "…"}</strong></div>
          </div>
        </section>
      </aside>

      <main className="board-stage">
        <section className="panel board-panel">
          {game === "tictactoe"
            ? <TicTacToe match={match} status={status} send={send} />
            : <TacticalArena match={match} status={status} send={send} />}
        </section>
      </main>

      <aside className="intel-column">
        <section className="panel">
          <p className="eyebrow">🎙️ Live commentary</p>
          <Commentary commentary={commentary} />
        </section>
        <section className="panel">
          <p className="eyebrow">🎓 Coach</p>
          <Coach coach={coach} />
        </section>
        <section className="panel">
          <p className="eyebrow">🏅 Leaderboard</p>
          <Leaderboard rows={board} />
        </section>
      </aside>

      {result && (
        <div className="result-overlay">
          <div className={`result-card ${result.cls}`}>
            <h2>{result.title}</h2>
            <p className="muted">{result.text}</p>
            <div className="result-actions">
              <button className="btn" onClick={start}>Play again</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
