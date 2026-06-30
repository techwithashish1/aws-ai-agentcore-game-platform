/** Live-commentary caption banner; color reflects the AI commentator's emotion. */
const EMOTION_COLOR: Record<string, string> = {
  excited: "#e8590c",
  joyful: "#2f9e44",
  tense: "#1971c2",
  disappointed: "#868e96",
  dramatic: "#9c36b5",
  neutral: "#343a40",
};

export function Commentary({ commentary }: { commentary: { line: string; emotion: string } | null }) {
  if (!commentary) return <p className="commentary-empty">Live commentary will appear here once the match begins.</p>;
  return (
    <div
      className="commentary-banner"
      style={{ background: EMOTION_COLOR[commentary.emotion] ?? "#343a40" }}
    >
      🎙️ {commentary.line}
    </div>
  );
}
