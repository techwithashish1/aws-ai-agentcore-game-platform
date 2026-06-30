import { useState } from "react";
import { Match, Unit, UNIT_STATS } from "../common/types";

const GLYPH: Record<string, string> = { Tank: "⬡", Striker: "◆", Support: "✚" };

function manhattan(a: Unit, b: { x: number; y: number }) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

interface Props {
  match: Match | null;
  status: string;
  send: (payload: unknown) => void;
}

/**
 * Interactive Tactical Arena.
 * - Click one of your units to select it.
 * - In Move mode, highlighted green cells show valid destinations; click to move.
 * - In Attack mode, highlighted red enemy cells are in range; click to attack.
 * - Skip skips the selected unit's turn.
 * - End Turn passes to the AI immediately.
 */
export function TacticalArena({ match, status, send }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<"move" | "attack">("move");

  if (!match || match.gameId !== "tactical") {
    return <div className="board-empty-hint">Start a tactical match to deploy your squad.</div>;
  }

  const { units, winner, actedIds = [] } = match.state;
  const acted = new Set(actedIds);
  const myTurn = match.currentTurn === "Human" && !winner;

  const selected = units.find((u) => u.id === selectedId && u.hp > 0 && u.owner === "Human") ?? null;
  const canUse = !!selected && myTurn && !acted.has(selected.id);

  const at = (x: number, y: number) => units.find((u) => u.x === x && u.y === y && u.hp > 0) ?? null;

  function selectUnit(u: Unit) {
    setSelectedId(u.id);
    // auto-switch to attack if unit can't move (already acted one action)
  }

  function handleEmptyClick(x: number, y: number) {
    if (!selected || !canUse || mode !== "move") return;
    const stats = UNIT_STATS[selected.cls];
    if (manhattan(selected, { x, y }) > stats.move) return;
    send({ action: "tactical_move", matchId: match.matchId, unitId: selected.id, x, y });
    setSelectedId(null);
  }

  function handleEnemyClick(target: Unit) {
    if (!selected || !canUse || mode !== "attack") return;
    const stats = UNIT_STATS[selected.cls];
    if (manhattan(selected, target) > stats.range) return;
    send({ action: "tactical_attack", matchId: match.matchId, unitId: selected.id, targetId: target.id });
    setSelectedId(null);
  }

  function handleSkip() {
    if (!selected || !canUse) return;
    // Pass the whole turn (our backend doesn't have per-unit skip)
    send({ action: "tactical_end_turn", matchId: match.matchId });
    setSelectedId(null);
  }

  function handleEndTurn() {
    if (!myTurn) return;
    send({ action: "tactical_end_turn", matchId: match.matchId });
    setSelectedId(null);
  }

  const banner = winner
    ? `${winner === "Human" ? "🏆 You win!" : "💀 AI wins!"}`
    : match.currentTurn === "AI"
      ? "🤖 Enemy thinking…"
      : status || "Your turn";

  const humanUnits = units.filter((u) => u.owner === "Human");
  const aliveHuman = humanUnits.filter((u) => u.hp > 0);
  const aliveAI = units.filter((u) => u.owner === "AI" && u.hp > 0);
  const unactedCount = aliveHuman.filter((u) => !acted.has(u.id)).length;

  return (
    <>
      {/* Turn banner */}
      <div className={`board-banner ${winner ? "banner-result" : ""}`}>{banner}</div>

      {/* Unit roster + mode controls */}
      <div className="tactical-hud">
        <div className="squad-roster">
          {humanUnits.map((u) => {
            const stats = UNIT_STATS[u.cls];
            const hp_pct = Math.round((u.hp / stats.hp) * 100);
            const dead = u.hp <= 0;
            const isActed = acted.has(u.id);
            return (
              <button
                key={u.id}
                className={`unit-card${selectedId === u.id ? " selected" : ""}${dead ? " dead" : ""}${isActed ? " acted" : ""}`}
                disabled={dead || !myTurn}
                onClick={() => selectUnit(u)}
              >
                <div className="unit-card-top">
                  <span>{GLYPH[u.cls]} {u.cls}</span>
                  <span className="unit-pos">{u.x},{u.y}</span>
                </div>
                <div className="unit-hp-bar">
                  <div className="unit-hp-fill" style={{ width: `${hp_pct}%` }} />
                </div>
                <div className="unit-card-bottom">
                  <span>{u.hp}/{stats.hp}</span>
                  <span>{isActed ? "Done" : dead ? "KIA" : "Ready"}</span>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mode-controls">
          <button
            className={`btn-mode${mode === "move" ? " active" : ""}`}
            onClick={() => setMode("move")}
            disabled={!myTurn}
          >Move</button>
          <button
            className={`btn-mode${mode === "attack" ? " active" : ""}`}
            onClick={() => setMode("attack")}
            disabled={!myTurn}
          >Attack</button>
          <button
            className="btn-mode"
            onClick={handleEndTurn}
            disabled={!myTurn}
          >End Turn</button>
        </div>

        {selected && (
          <div className="selection-info">
            <strong>{selected.cls}</strong> @ ({selected.x},{selected.y})
            &nbsp;·&nbsp; Move {UNIT_STATS[selected.cls].move} &nbsp;·&nbsp; Range {UNIT_STATS[selected.cls].range}
            &nbsp;·&nbsp; {acted.has(selected.id) ? "✓ Done" : canUse ? "Ready" : "Wait"}
          </div>
        )}

        <div className="battle-stats">
          <span>⚔️ {aliveHuman.length} vs {aliveAI.length}</span>
          <span>Actions left: {unactedCount}</span>
          <span>Turn: {match.state.turn}</span>
        </div>
      </div>

      {/* 8×8 grid */}
      <div className="board">
        {Array.from({ length: 8 }, (_, row) =>
          Array.from({ length: 8 }, (_, col) => {
            const u = at(col, row);
            const dist = selected ? manhattan(selected, { x: col, y: row }) : Infinity;
            const canMove = canUse && mode === "move" && !u && dist <= UNIT_STATS[selected!.cls].move;
            const canAttack = canUse && mode === "attack" && !!u && u.owner === "AI" && dist <= UNIT_STATS[selected!.cls].range;
            const isSelected = !!u && u.id === selectedId;

            let cellClass = "grid-cell";
            if (u) cellClass += u.owner === "Human" ? " player-cell" : " enemy-cell";
            if (isSelected) cellClass += " selected-cell";
            if (canMove) cellClass += " move-target-cell";
            if (canAttack) cellClass += " attack-target-cell";

            function handleClick() {
              if (!u) { handleEmptyClick(col, row); return; }
              if (u.owner === "Human") { selectUnit(u); return; }
              if (u.owner === "AI") handleEnemyClick(u);
            }

            return (
              <button
                key={`${col}-${row}`}
                className={cellClass}
                onClick={handleClick}
                title={u ? `${u.owner} ${u.cls} HP:${u.hp}` : `(${col},${row})`}
              >
                {u && <span className="cell-glyph">{GLYPH[u.cls]}</span>}
                {u && <span className="cell-hp">{u.hp}</span>}
              </button>
            );
          })
        )}
      </div>

      <div className="legend-items">
        <span><i className="legend-dot player" /> You</span>
        <span><i className="legend-dot enemy" /> AI</span>
        <span className="legend-dot move-hint" /> Move range
        <span><i className="legend-dot attack-hint" /> Attack range
        &nbsp;·&nbsp; ⬡ Tank · ◆ Striker · ✚ Support</span>
      </div>
    </>
  );
}
