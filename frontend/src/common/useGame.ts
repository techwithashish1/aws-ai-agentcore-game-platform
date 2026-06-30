import { useEffect, useRef, useState } from "react";
import { Match, WS_URL } from "./types";

/** Shared WebSocket connection + match state for all games. */
export function useGame() {
  const ws = useRef<WebSocket | null>(null);
  const [match, setMatch] = useState<Match | null>(null);
  const [board, setBoard] = useState<any[]>([]);
  const [status, setStatus] = useState("connecting…");
  const [commentary, setCommentary] = useState<{ line: string; emotion: string } | null>(null);
  const [coach, setCoach] = useState<{ tip: string; topic: string } | null>(null);

  useEffect(() => {
    const sock = new WebSocket(WS_URL);
    ws.current = sock;
    sock.onopen = () => setStatus("connected");
    sock.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "state") { setMatch(msg.match); setStatus(""); }
      if (msg.type === "leaderboard") setBoard(msg.rows);
      if (msg.type === "error") setStatus(msg.message);
      if (msg.type === "commentary") {
        setCommentary({ line: msg.line, emotion: msg.emotion });
        if (msg.audio) new Audio("data:audio/mp3;base64," + msg.audio).play().catch(() => {});
      }
      if (msg.type === "coach") setCoach({ tip: msg.tip, topic: msg.topic });
    };
    sock.onclose = () => setStatus("disconnected");
    return () => sock.close();
  }, []);

  const send = (payload: unknown) => ws.current?.send(JSON.stringify(payload));
  return { match, status, board, commentary, coach, send };
}
