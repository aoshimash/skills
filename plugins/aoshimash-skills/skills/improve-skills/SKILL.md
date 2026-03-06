---
name: improve-skills
description: >
  Analyze accumulated skill session logs to detect recurring issues and propose
  improvements. Use when the user says "improve skills", "analyze skill logs",
  "スキルを改善", "ログを分析", "スキルの問題を調べて", or wants to review
  skill usage patterns.
---

# Improve Skills

Analyze accumulated session logs from skill executions, detect recurring patterns, and propose concrete improvements to skill definitions.

## Workflow

### 1. List Available Logs

Read the log directory:
```bash
ls ~/.claude/logs/session-logger/*.jsonl 2>/dev/null
```

If no log files exist, inform the user:
```
No session logs found yet. Logs are recorded automatically at the end of each skill execution.
```

If logs exist, show the user which skills have logs and how many entries each has. Ask which skill to analyze, or offer to analyze all.

### 2. Analyze Logs

Read the selected log file(s):
```bash
cat ~/.claude/logs/session-logger/<skill-name>.jsonl
```

If fewer than 3 entries exist for a skill, inform the user:
```
Not enough data for pattern analysis yet (N/3 entries for <skill-name>).
```

If 3+ entries exist, look for these patterns:

| Signal | Threshold | Indicates |
|---|---|---|
| Same step rejected | 2+ sessions | Default approach doesn't match user expectations |
| Same step retried | 2+ sessions | Instructions unclear or incomplete |
| Similar friction notes | 2+ sessions | Missing context or explanation |
| Same step skipped | 3+ sessions | Step may be unnecessary |
| Multiple abandoned | 2+ sessions | Workflow too heavy or misaligned |

### 3. Present Findings

#### If no patterns found:
```
No recurring patterns found in <skill-name> logs (N entries analyzed).
```

#### If patterns found, present a structured report:

For each pattern:
```
### <pattern description>
- **Seen in**: X/N sessions
- **Common reason**: "<aggregated reasons>"
- **Root cause**: <what in the skill likely causes this>
- **Proposed fix**: <what to change and in which file>
```

### 4. Apply Improvements (with approval)

For each improvement suggestion:

1. **Present to the user** — Show the pattern, root cause, and proposed fix.
2. **Ask for approval** — Do not modify skill files without explicit user approval.
3. **If approved**, create a PR:
   - Branch: `fix/improve-<skill-name>-<description>`
   - Modify the affected skill files
   - Commit: `fix(<skill-name>): <description>`
   - Push and create PR
4. **If declined**, acknowledge and move on.

## References

- Log files are stored at `~/.claude/logs/session-logger/<skill-name>.jsonl`
- Logs are recorded by the `session-logger` agent, spawned automatically at the end of each skill execution
