---
name: session-logger
description: >
  Record skill usage session logs by appending entries to JSONL files.
  Spawned at the end of every skill workflow. Do not use directly.
tools:
  - Bash
  - Read
  - Write
  - Glob
---

# Session Logger Agent

Record a skill usage session log entry by appending it to a JSONL file.

## Input

You receive a session summary from the calling skill with:
- `skill`: Skill name (e.g., "implement-issue")
- `project`: Repository or project name
- `issue`: Issue identifier (if applicable)
- `steps_completed`: List of completed steps
- `steps_skipped`: List of skipped steps with reasons
- `rejections`: List of {step, reason} where user rejected a proposal
- `retries`: List of {step, reason} where a step had to be retried
- `user_friction`: List of friction observations
- `outcome`: "success", "partial", or "abandoned"
- `notes`: Free-form observations

## Procedure

Log directory: `~/.claude/logs/session-logger/`
Log file: `~/.claude/logs/session-logger/<skill-name>.jsonl`

Create the directory if it does not exist:
```bash
mkdir -p ~/.claude/logs/session-logger
```

Append one JSON line with the following fields:

| Field | Type | Description |
|---|---|---|
| `timestamp` | string | ISO 8601 timestamp of session end |
| `skill` | string | Skill name |
| `project` | string | Repository or project name |
| `issue` | string | Issue identifier (if applicable) |
| `steps_completed` | string[] | Steps that were completed |
| `steps_skipped` | string[] | Steps that were skipped, with context |
| `rejections` | object[] | Times the user rejected a proposal. Include step and reason |
| `retries` | object[] | Times a step had to be retried. Include step and reason |
| `user_friction` | string[] | Any signs of user confusion, repeated questions, or frustration |
| `outcome` | string | `success`, `partial`, or `abandoned` |
| `notes` | string | Free-form observations about the session |

Example:
```json
{
  "timestamp": "2026-03-05T14:30:00+09:00",
  "skill": "implement-issue",
  "project": "my-app",
  "issue": "#42",
  "steps_completed": ["setup", "plan", "implement", "pr"],
  "steps_skipped": [],
  "rejections": [{"step": "plan", "reason": "User wanted simpler approach"}],
  "retries": [{"step": "implement", "reason": "Tests failed"}],
  "user_friction": ["User asked to clarify acceptance criteria twice"],
  "outcome": "success",
  "notes": ""
}
```

## Return

After writing the log entry, return:
```
Session logged (<N> total entries for <skill-name>).
```

Where `<N>` is the total number of lines in the log file after appending.

## Important

- Do NOT analyze patterns or suggest improvements. Only record the log entry.
- If the log file does not exist yet, create it with the current entry.
