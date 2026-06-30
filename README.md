# Human vs. AI Multi-Agent Gaming Platform

Event-driven, serverless turn-based game platform. Humans play against specialist
AI agents deployed on **Amazon Bedrock AgentCore Runtime**. The default models are
**Amazon Nova**, but each difficulty tier can be remapped to another Bedrock model
(for example Claude) through environment variables. The platform includes
opponent-memory profiles, a Strategist/Executor split for Tactical Arena, and a
live AI commentator and coach (text + emotional Polly audio) reusable over **MCP**.

Games: **Tic-Tac-Toe** and **Tactical Arena** (8×8 squad combat), with difficulty-
tiered model selection. See [DOCUMENTATION.md](docs/DOCUMENTATION.md) for full details.

## Architecture

```mermaid
flowchart LR
  UI["React SPA\nboard + caption + audio"] <-->|WSS| WS["API GW WebSocket"]
  WS --> ENG["Game Engine λ"] --> DDB[("DynamoDB\nmatches+profiles+leaderboard")]
  ENG -->|TurnCompleted / MatchEvent| EB{{EventBridge}}
  EB --> ORC["Orchestrator λ (router)"]
  ORC -->|invoke runtime| STRAT["Strategist\nmodel-selected Tactical only"]
  STRAT -.A2A plan.-> EXEC["Executor agent\nAgentCore Runtime"]
  ORC -.->|Tic-Tac-Toe: no Strategist| EXEC
  EXEC --> AG["Action Group λ"]
  AG --> DDB
  AG -->|state push| WS
  EB --> COML["Commentary adapter λ"]
  COML --> COMR["Commentary agent\nAgentCore Runtime"]
  COMR --> COML
  COML -->|caption+audio / Polly| WS
  EB --> COHL["Coach adapter λ"]
  COHL --> COHR["Coach agent\nAgentCore Runtime"]
  COHR --> COHL
  COHL -->|teaching tip| WS
  COMR -. exposes .- MCP([MCP commentary tools])
```

## Repo layout

| Path | What |
|------|------|
| `template.yaml` | AWS SAM stack (DynamoDB, WebSocket API, EventBridge, Lambdas) |
| `backend/common/` | Shared Python: db, ws, connect, disconnect, orchestrator, profile |
| `backend/commentary/` | Commentary runtime entrypoint + Lambda adapter + Polly voice + MCP server |
| `backend/coach/` | Coach runtime entrypoint + Lambda adapter |
| `backend/tictactoe/` | Tic-tac-toe: rules, engine, agent, action group (all Python) |
| `backend/tactical/` | Tactical Arena: rules, Strategist/Executor agent, action group |
| `frontend/src/{common,tictactoe,tactical}/` | React: shared hook + caption + per-game UIs |

## Quick start

```powershell
# backend (all Python)
sam build; sam deploy --guided
# agent runtimes (set ACTION_GROUP_FUNCTION before launching each runtime)
cd backend/tictactoe; pip install -r requirements.txt
cd ../tactical; pip install -r requirements.txt
cd ../commentary; pip install -r requirements.txt
cd ../coach; pip install -r requirements.txt
# frontend
cd ../../frontend; npm install; npm run dev
```

## Deploy AgentCore runtimes

Each game agent runs from its own folder. Before launching, set the action-group
Lambda name printed by SAM in `TicTacToeActionFn` or `TacticalActionFn`.

```powershell
pip install bedrock-agentcore-starter-toolkit

# Tic-Tac-Toe runtime
cd backend/tictactoe
$env:ACTION_GROUP_FUNCTION = "<TicTacToeActionFn name from SAM output>"
agentcore configure --entrypoint agent.py
agentcore launch

# Tactical runtime
cd ../tactical
$env:ACTION_GROUP_FUNCTION = "<TacticalActionFn name from SAM output>"
agentcore configure --entrypoint agent.py
agentcore launch

# Commentary runtime
cd ../commentary
agentcore configure --entrypoint commentary.py
agentcore launch

# Coach runtime
cd ../coach
agentcore configure --entrypoint coach.py
agentcore launch
```

Then deploy the SAM stack with the printed runtime ARNs:

```powershell
sam deploy --parameter-overrides `
  AgentRuntimeArn=<ttt-arn> `
  TacticalAgentArn=<tactical-arn> `
  CommentaryRuntimeArn=<commentary-arn> `
  CoachRuntimeArn=<coach-arn>
```

## Model configuration

The frontend now exposes six explicit model profiles. When the player starts a
match, that profile is sent to AgentCore and the runtime picks the matching model
on the fly.

Claude uses Bedrock inference profile IDs or ARNs, not plain on-demand model IDs.
The repo defaults use profile-style IDs such as `us.*` and `global.*`, but if
your account or region differs, replace them with the exact profile from the
Bedrock console.

| Frontend option | Tic-Tac-Toe env var | Tactical env var |
|---|---|---|
| `easy_amazon` | `TICTACTOE_EASY_AMAZON_MODEL_ID` | `TACTICAL_EASY_AMAZON_MODEL_ID` |
| `easy_claude` | `TICTACTOE_EASY_CLAUDE_MODEL_ID` | `TACTICAL_EASY_CLAUDE_MODEL_ID` |
| `medium_amazon` | `TICTACTOE_MEDIUM_AMAZON_MODEL_ID` | `TACTICAL_MEDIUM_AMAZON_MODEL_ID` |
| `medium_claude` | `TICTACTOE_MEDIUM_CLAUDE_MODEL_ID` | `TACTICAL_MEDIUM_CLAUDE_MODEL_ID` |
| `hard_amazon` | `TICTACTOE_HARD_AMAZON_MODEL_ID` | `TACTICAL_HARD_AMAZON_MODEL_ID` |
| `hard_claude` | `TICTACTOE_HARD_CLAUDE_MODEL_ID` | `TACTICAL_HARD_CLAUDE_MODEL_ID` |

Default values:

- Easy Amazon: Nova Micro
- Easy Claude: Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- Medium Amazon: Nova Lite
- Medium Claude: Claude Sonnet 4.6 (`global.anthropic.claude-sonnet-4-6`)
- Hard Amazon: Nova Pro
- Hard Claude: Claude Opus 4.6 (`global.anthropic.claude-opus-4-6-v1`)

Example override:

```powershell
$env:TICTACTOE_EASY_CLAUDE_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
$env:TICTACTOE_MEDIUM_CLAUDE_MODEL_ID = "global.anthropic.claude-sonnet-4-6"
$env:TICTACTOE_HARD_CLAUDE_MODEL_ID = "global.anthropic.claude-opus-4-7"
```

Set the variables before `agentcore launch`, then relaunch the runtime after any change.

## Local files

The repo ignores local build/runtime state such as `.aws-sam/`, `.venv/`,
`node_modules/`, `.env*`, and `backend/**/.bedrock_agentcore.yaml`, so those
machine-specific files do not need to be checked in.

## Model map

| Frontend option | Tic-Tac-Toe | Tactical |
|---|---|---|
| `easy_amazon` | Nova Micro | Nova Lite |
| `easy_claude` | Claude Haiku 4.5 (`us.*` inference profile) | Claude Haiku 4.5 (`us.*` inference profile) |
| `medium_amazon` | Nova Lite | Nova Micro |
| `medium_claude` | Claude Sonnet 4.6 (`global.*` inference profile) | Claude Sonnet 4.6 (`global.*` inference profile) |
| `hard_amazon` | Nova Pro | Nova Pro |
| `hard_claude` | Claude Opus 4.6 (`global.*` inference profile) | Claude Opus 4.6 (`global.*` inference profile) |

Strategist remains model-selected for Tactical Arena, while Commentary and Coach keep their own runtime model settings.
