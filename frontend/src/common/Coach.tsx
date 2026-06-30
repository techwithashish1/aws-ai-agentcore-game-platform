/** Coaching tip banner; a teaching voice that reacts to the player's own moves. */
const TOPIC_ICON: Record<string, string> = {
  opening: "🚀",
  tempo: "⏱️",
  defense: "🛡️",
  threats: "⚠️",
  positioning: "📍",
  endgame: "🏁",
  general: "💡",
};

export function Coach({ coach }: { coach: { tip: string; topic: string } | null }) {
  if (!coach) return <p className="commentary-empty">Your coach will offer tips after your moves.</p>;
  return (
    <div className="coach-box">
      <span className="coach-label">{TOPIC_ICON[coach.topic] ?? "💡"} Coach · {coach.topic}</span>
      <span className="coach-tip">{coach.tip}</span>
    </div>
  );
}
