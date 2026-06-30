interface Row { username: string; score: number; wins: number; losses: number; draws: number; games: number }

export function Leaderboard({ rows }: { rows: Row[] }) {
  if (rows.length === 0) return <p className="commentary-empty">No scores yet — play a match to climb the board.</p>;
  return (
    <table className="leaderboard-table">
      <thead>
        <tr><th>#</th><th>Player</th><th>Score</th><th>W</th><th>L</th><th>D</th></tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={r.username}>
            <td>{i + 1}</td><td>{r.username}</td><td>{r.score}</td><td>{r.wins}</td><td>{r.losses}</td><td>{r.draws}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
