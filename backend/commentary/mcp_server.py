"""MCP server exposing live-commentary tools.

Any agent (current games or future ones) can connect over MCP and call these tools to
generate emotional commentary and emotional speech. Wraps the same commentary agent +
Polly voice used by the EventBridge handler, so behavior is identical everywhere.

Run locally:  python -m commentary.mcp_server   (stdio transport)
"""
from mcp.server.fastmcp import FastMCP

from commentary.commentary import commentate
from commentary.voice import synthesize

mcp = FastMCP("game-commentary")


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


if __name__ == "__main__":
    mcp.run()
