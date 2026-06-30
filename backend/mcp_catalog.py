"""Shared MCP catalog: one server exposing every reusable platform capability.

This is the platform's capability catalog. Any agent — these games, the coach, a
future critic, or a game I haven't built yet — can connect over MCP and *discover*
commentary, memory, leaderboard, analysis, and coaching tools instead of importing
code. The same underlying functions back the EventBridge handlers, so behavior is
identical whether a capability is fired by the platform or pulled by an agent.

Promoting these to MCP means the catalog grows without the coupling: add a tool here
once and every agent can use it with zero new wiring.

Run locally:  python -m mcp_catalog   (stdio transport)
"""
from mcp.server.fastmcp import FastMCP

from coach.coach import coach_tip
from commentary.commentary import commentate
from commentary.voice import synthesize
from common.analysis import analyze_position as _analyze_position
from common.leaderboard import top
from common.profile import get_profile, profile_note

mcp = FastMCP("game-platform")


# --- Commentary -----------------------------------------------------------
@mcp.tool()
def generate_commentary(event: dict) -> dict:
    """Return {'line', 'emotion'} for a match event (move, score, result)."""
    return commentate(event)


@mcp.tool()
def speak(line: str, emotion: str = "neutral") -> str:
    """Synthesize an emotional MP3 (base64) for a commentary line."""
    return synthesize(line, emotion)


@mcp.tool()
def commentate_and_speak(event: dict) -> dict:
    """One-shot: commentary text, emotion, and base64 MP3 for a match event."""
    c = commentate(event)
    return {**c, "audio": synthesize(c["line"], c["emotion"])}


# --- Memory ---------------------------------------------------------------
@mcp.tool()
def recall_player(username: str, game: str) -> dict:
    """Recall a player's profile: a one-line note plus the raw memory item."""
    return {"note": profile_note(username, game), "profile": get_profile(username, game)}


# --- Leaderboard ----------------------------------------------------------
@mcp.tool()
def top_players(game: str, difficulty: str, limit: int = 10) -> list:
    """Top-N players for a game and difficulty, ranked by score."""
    return top(game, difficulty, limit)


# --- Analysis -------------------------------------------------------------
@mcp.tool()
def analyze_position(game: str, state: dict) -> dict:
    """Immediate threats, opportunities, and a one-line read for a position."""
    return _analyze_position(game, state)


# --- Coaching -------------------------------------------------------------
@mcp.tool()
def explain_move(summary: dict) -> dict:
    """Return {'tip', 'topic'}: a constructive coaching tip for a match event."""
    return coach_tip(summary)


if __name__ == "__main__":
    mcp.run()
