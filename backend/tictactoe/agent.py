"""Tic-Tac-Toe specialist agent for Amazon Bedrock AgentCore Runtime.

Uses Strands Agents with Amazon Nova Lite. The orchestrator invokes this runtime
with {matchId, board, connectionId}. The agent reasons over the board and calls
the `play_move` tool, which is wired to the Action Group Lambda that writes state.
"""
import json
import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

app = BedrockAgentCoreApp()
_lambda = boto3.client("lambda")
ACTION_GROUP_FN = os.environ.get("ACTION_GROUP_FUNCTION", "TicTacToeActionFunction")

SYSTEM = (
    "You are O in tic-tac-toe playing to win. Board is a 9-int array, row-major: "
    "1=Human, -1=you, 0=empty. Pick the strongest empty cell (win, else block, "
    "else center/corner). Output EXACTLY one JSON object only: {\"cell\": 0-8}."
)

# Difficulty -> Nova model. Stronger model = tougher opponent.
MODELS = {"easy": "amazon.nova-micro-v1:0", "medium": "amazon.nova-lite-v1:0", "hard": "amazon.nova-pro-v1:0"}


def _agent(difficulty: str) -> Agent:
    return Agent(model=BedrockModel(model_id=MODELS.get(difficulty, MODELS["medium"])), system_prompt=SYSTEM)


def _parse_cell(text: str) -> int | None:
    try:
        start, end = text.index("{"), text.rindex("}") + 1
        data = json.loads(text[start:end])
        cell = int(data.get("cell"))
        return cell if 0 <= cell <= 8 else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _fallback_cell(board) -> int:
    for preferred in (4, 0, 2, 6, 8, 1, 3, 5, 7):
        if board[preferred] == 0:
            return preferred
    return 0


@app.entrypoint
def invoke(payload: dict):
    match_id = payload["matchId"]
    board = payload["board"]
    opp = payload.get("opponent", "")
    response = str(_agent(payload.get("difficulty", "medium"))(f"matchId={match_id}. Board={board}. {opp} Make your move. Output JSON only."))
    cell = _parse_cell(response)
    if cell is None or board[cell] != 0:
        cell = _fallback_cell(board)
    _lambda.invoke(FunctionName=ACTION_GROUP_FN, Payload=json.dumps({"matchId": match_id, "cell": cell}).encode())
    return {"status": "moved", "matchId": match_id}


if __name__ == "__main__":
    app.run()
