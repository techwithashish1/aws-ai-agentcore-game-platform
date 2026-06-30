# How To Play: Tactical Arena

This guide describes the game as it works in the current implementation.

## Goal
Defeat all enemy units before all of your units are defeated.

## Commander Selection

Before creating a match, choose how the enemy AI will make decisions:

### Play Without AI / LLM
- Enemy uses deterministic fallback policy (rule-based, no LLM)
- Best for: understanding core game mechanics without AI variance
- Tactics: always focus lowest HP, move closer if out of range

### LLM Models (Bedrock-Powered)
Each model has a complexity tier that affects reasoning depth and tactics:

#### Low Complexity
- Amazon Nova Lite
- Claude 3 Haiku
- Behavior: Simple, direct tactics; limited long-range planning
- Use for: casual or learning matches

#### Medium Complexity
- Amazon Nova Micro
- Claude 3.5 Sonnet
- Claude 3.7 Sonnet
- Behavior: Balanced tactics; considers positioning and HP pressure

#### High Complexity
- Amazon Nova Pro
- Claude Haiku 4.5
- Claude Sonnet 4.5
- Behavior: Strategic depth; adapts to player positioning and damage trades

#### Top Complexity
- Claude Opus 4.7
- Claude Opus 4.8
- Behavior: Maximum reasoning; complex multi-unit tactics and long-term plans
- Note: Takes longer per turn due to extended token budgets

## AI Source Verification

After the enemy takes a turn, check the **AI Source** in the status panel:
- `Bedrock Llm` = Real LLM driving tactics (model_id shown below)
- `Local Fallback` = LLM call failed, using deterministic policy
  - Fallback Reason: error type (ResourceNotFoundException, ValidationException, etc.)
- `Local Only` = Local mode selected (no LLM attempt)

If you see fallback, it usually means:
- Model not available in your AWS Bedrock account
- Model ID format incorrect for your region
- Bedrock API error or timeout

Check [README.md](../README.md#known-issues) for troubleshooting.

## Broadcast Audio Mode (Bedrock Matches Only)

When you create a match with an LLM model (not "Play Without AI"), you get access to an advanced broadcast audio experience:

### What You'll Hear
- **Dual-Voice Commentary**: Two commentators alternate play-by-play calls
  - Matthew: Male commentator for action calls (e.g., "Player Tank launches on Enemy Striker!")
  - Joanna: Female analyst for strategic observations (e.g., "That damage trade puts pressure on the frontline")
- **Procedural Crowd Audio**: Stadium ambience that reacts to match intensity
  - Louder cheers and build-up during aggressive moments
  - Dramatic stingers on kills and victory
- **Dynamic Pitch and Pacing**: Commentary speed and tone adjust based on match momentum

### Unit Names in Commentary
Commentary uses natural, easy-to-follow unit names:
- **Your units**: "Player Tank", "Player Striker", "Player Support"
- **Enemy units**: "Enemy Tank", "Enemy Striker", "Enemy Support"

This makes it much easier to follow the action than technical IDs.

### Broadcasting Controls
Look for the **Broadcast Audio Mode** toggle in the UI:
- **Enable/Disable**: Toggle the entire broadcast system on/off
- **Volume Mixer**: Adjust three independent sliders
  - **Commentary**: Voice synthesis volume (0-100%)
  - **Crowd**: Procedural crowd ambience volume (0-100%)
  - **SFX**: Event stingers and reactions (0-100%)

### How the Audio Works
1. As you and the enemy take actions, live commentary is generated
2. Commentary text is synthesized to speech via AWS Polly
3. Crowd audio reacts to match intensity and key events
4. All audio layers mix together for an immersive broadcast experience

### Post-Match Strategy Coach
After each Bedrock-powered match ends, you'll receive **AI Coach** tactical feedback:
- Formation recommendations based on your play style
- Timing analysis of key moments
- Counter-strategies against the opponent's tactics
- Specific improvement suggestions

This analysis is only available in Bedrock matches; local matches show no coaching.

## Current Match Structure
- The board is an 8x8 grid.
- You start with 3 units (Tank, Striker, Support).
- The enemy starts with 3 units.
- Each living player unit gets one action per round.
- After all of your living units have acted, the enemy takes its full turn.
- A match ends when one side has no living units left.
- Turn counter increments after enemy finishes their turn.

## Starting Positions
Your units start on the left side:
- Tank at `(1, 1)`
- Striker at `(1, 2)`
- Support at `(1, 3)`

Enemy units start on the right side:
- Tank at `(6, 6)`
- Striker at `(6, 5)`
- Support at `(6, 4)`

## Unit Classes
### Tank
- HP: `140`
- Attack: `18`
- Defense: `8`
- Move Range: `2`
- Attack Range: `1`
- Role: Absorb damage, block space

### Striker
- HP: `90`
- Attack: `30`
- Defense: `3`
- Move Range: `3`
- Attack Range: `1`
- Role: High burst damage, high risk

### Support
- HP: `80`
- Attack: `20`
- Defense: `2`
- Move Range: `2`
- Attack Range: `3`
- Role: Ranged pressure, keep safe

## Your Turn
During your round, each living player unit may do one of these actions once:
- `Move` - Relocate to a valid tile
- `Attack` - Deal damage to an enemy unit in range
- `Skip` - Do nothing this round

There is no defend, heal, item, or special ability yet.

## Move Rules
A move is valid when all of these are true:
- The target tile is inside the 8x8 board.
- The target tile is not occupied by any living unit.
- The target tile is within the unit's move range.

### Important movement detail
Movement is checked by Manhattan distance:
- Distance formula: `abs(x1 - x2) + abs(y1 - y2)`

That means:
- A Tank can move up to distance `2`
- A Striker can move up to distance `3`
- A Support can move up to distance `2`

The current implementation does not check path blocking between the start and end tile.
If the destination is within range and empty, the move is allowed.

## Attack Rules
An attack is valid when all of these are true:
- The acting unit is alive.
- The target enemy unit is alive.
- The target is within the attack range.

Attack range is also checked by Manhattan distance.

### Attack ranges
- Tank: range `1`
- Striker: range `1`
- Support: range `3`

## Damage Rules
Damage is calculated as:

`max(1, attacker.attack - defender.defense)`

Examples:
- Striker attacking Tank: `max(1, 30 - 8) = 22`
- Tank attacking Tank: `max(1, 18 - 8) = 10`
- Support attacking Striker: `max(1, 20 - 3) = 17`

If a unit's HP reaches `0`, that unit dies and is removed from play.

## Enemy Turn
After your valid action, the enemy takes its turn automatically.

### LLM-Driven Behavior (When Bedrock Source = `Bedrock Llm`)
The LLM receives:
- Current board state (positions, HP, alive/dead status)
- Unit stats (attack, defense, range)
- Your recent behavior profile (aggression tendency)
- Current turn and match context

The LLM returns a tactical policy:
- `focus_fire`: probability of attacking the same target again (0.0–1.0)
- `flank`: probability of moving to attack from a different angle (0.0–1.0)
- `hold_line`: probability of moving backward or holding position (0.0–1.0)

These probabilities guide which enemy units attack, defend, or retreat.

### Fallback Behavior (When Source = `Local Fallback` or `Local Only`)
- All living enemy units act during the enemy turn.
- The enemy usually focuses the living player unit with the lowest HP.
- If an enemy unit is already in range, it attacks.
- If not in range, it moves closer using Manhattan distance.

Enemy movement currently steps both x and y toward the target when possible, so it can look like a diagonal move.

## Turn Counter
- The match starts at turn `1`.
- The turn number increases after the enemy finishes its turn.

## Win and Loss Conditions
You win when:
- All enemy units are dead.

You lose when:
- All your units are dead.

## How To Play In The React UI

### Step 1: Start the backend
From the project root:

```powershell
uvicorn app.main:app --reload
```

You will see a startup log line:
```
INFO: ai_trace_logging_enabled region=us-east-1 default_runtime_mode=...
```

### Step 2: Start the frontend
From the `frontend` folder:

```powershell
npm run dev
```

Then open:

```text
http://localhost:5173
```

### Step 3: Select a commander
- Commander dropdown shows all available models grouped by complexity.
- Choose `Play Without AI / LLM` for pure local play.
- Choose a model under Low/Medium/High/Top Complexity for LLM-driven enemy.

### Step 4: Create a match
- Enter a player name.
- Click `Create Match`.

### Step 5: Select a unit
- Click one of your unit cards on the left, or
- Click your unit directly on the board.

### Step 6: Choose an action mode
- Click `Move` if you want to move to an empty tile.
- Click `Attack` if you want to attack an enemy unit.
- Click `Skip` if you want that unit to do nothing this round.

### Step 7: Perform the action
#### For move
- Click an empty tile on the board.
- If the move is valid, your unit is marked as having acted this round.

#### For attack
- Click an enemy unit on the board.
- If the target is in range, damage is applied and your unit is marked as having acted this round.

#### For skip
- Click `Skip` for the selected unit.
- That unit is marked as having acted without moving or attacking.

#### End of your round
- After all living player units have acted, the enemy team takes its turn automatically.
- The AI Source, Model Used, and Fallback Reason appear in the status panel.

### Step 8: Read the result
Use the UI panels to watch:
- Current turn number
- Selected unit stats
- AI Source (Bedrock Llm, Local Fallback, or Local Only)
- AI Model Used (model ID)
- Fallback Reason (if applicable)
- Error messages for invalid actions

## Common Invalid Actions
You will get an error if you try to:
- Move outside the board
- Move onto an occupied tile
- Move farther than the unit's move range
- Attack a dead target
- Attack a target outside your unit's attack range
- Act with the same unit twice in the same round

## Practical Tips
- Use the Support unit early because it can attack from range `3`.
- Avoid exposing low-HP units because the LLM tends to focus weak targets.
- Tanks are best used to absorb damage and block space.
- Strikers hit hard and can finish weakened enemies quickly.
- Do not waste movement if the enemy can immediately counterattack.
- Higher complexity models play deeper strategies; expect longer games.

## Current Prototype Limitations
This is the current local prototype, so a few things are intentionally simple:
- No terrain bonuses
- No obstacles
- No healing
- No special skills
- No multiplayer
- No animations yet
- No true pathfinding
- Single map (8x8 arena)

## Troubleshooting AI Source

### I only see `Local Fallback` even though I selected a model.
1. Check the Fallback Reason in the status panel (e.g., ResourceNotFoundException).
2. Verify the model is available in your AWS Bedrock account:
   ```powershell
   aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[*].modelId' --output table
   ```
3. Check backend logs for `ai_decision` lines with the error type.
4. Ensure AWS credentials are configured (check `echo $env:AWS_PROFILE` or `aws sts get-caller-identity`).

### I don't see `Bedrock Llm` in logs.
- Make sure you selected a model (not "Play Without AI / LLM").
- Complete a full round so the enemy takes a turn (check "Actions Left").
- Look for `ai_decision` lines in the backend terminal after the player round finishes.

## Suggested First Match Strategy
A simple opening that usually works well:
1. Select a Low or Medium Complexity model for your first game.
2. Advance the Tank carefully toward the center.
3. Keep the Support one or two tiles behind the Tank.
4. Use the Striker to finish targets that the Support weakens.
5. Focus one enemy unit at a time.
6. Try to remove the enemy Striker early because it has the highest raw damage.

Once you win a match, try a higher complexity model and see how the tactics change!
