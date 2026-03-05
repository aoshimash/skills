# Log Analysis & Skill Improvement

## Overview

Log analysis and pattern detection are handled by the `skill-analyzer` agent.
This file documents how the calling skill should act on the agent's results.

## Flow

1. Skill spawns `skill-analyzer` agent with session data
2. Agent writes log and analyzes patterns
3. Agent returns results to the calling skill
4. Calling skill presents findings to the user (if any)

## Handling Agent Results

### No patterns found

The agent returns a message like:
```
Session logged (N total entries). No recurring patterns found.
```

Relay this to the user briefly. No further action needed.

### Patterns found

The agent returns a structured report with improvement suggestions. For each suggestion:

1. **Present to the user** — Show the pattern, root cause, and proposed fix.
2. **Ask for approval** — Do not modify skill files without explicit user approval.
3. **If approved**, create a PR:
   - Branch: `fix/improve-<skill-name>-<description>`
   - Modify the affected skill files
   - Update `references/eval-cases.md` evaluation log
   - Commit: `fix(<skill-name>): <description>`
   - Push and create PR
4. **If declined**, acknowledge and move on.
