---
name: improve-skills
description: >
  Analyze Claude Code session history to detect recurring skill usage issues and
  propose improvements. Use when the user says "improve skills", "analyze skill logs",
  "スキルを改善", "ログを分析", "スキルの問題を調べて", or wants to review
  skill usage patterns.
---

# Improve Skills

Analyze Claude Code's built-in conversation history to detect recurring patterns in skill executions and propose concrete improvements to skill definitions.

## Data Source

Claude Code persists session conversation history as JSONL files at:
```
~/.claude/projects/<project-path>/<session-id>.jsonl
```

Each line is a JSON object with a `type` field (`"human"`, `"assistant"`, `"tool_use"`, `"tool_result"`, etc.) containing full message content including tool calls and results.

## Workflow

### 1. Discover Skill Sessions

Scan session history files to find sessions where skills were invoked.

Search for skill invocation markers in session files:
```bash
grep -rl "aoshimash-skills:" ~/.claude/projects/ 2>/dev/null
```

A skill invocation is identified by the presence of `<command-name>aoshimash-skills:<skill-name></command-name>` in the conversation.

If no sessions are found, inform the user:
```
No skill execution sessions found in Claude Code history.
```

If sessions are found, list which skills were used and how many sessions each has. Ask the user which skill to analyze, or offer to analyze all.

### 2. Analyze Sessions

For each session file containing the target skill invocation, read the full conversation and detect these patterns:

#### Rejection
User explicitly rejects a proposal or asks to change something. Look for:
- User messages containing negation ("no", "that's wrong", "change this", "違う", "修正して")
- User requesting revisions to plans, drafts, or implementations

#### Retry
A step fails and must be re-done. Look for:
- Tool results showing test/lint/build failures followed by fix attempts
- Repeated tool calls to the same file or command

#### Friction
User experiences confusion or frustration. Look for:
- User asking the same question multiple times
- User requesting clarification on skill behavior
- User expressing frustration or confusion

#### Abandonment
Workflow was not completed. Look for:
- Sessions that start a skill workflow but never reach the final step (e.g., no PR created for implement-issue)

If fewer than 3 sessions exist for a skill, inform the user:
```
Not enough data for pattern analysis yet (N/3 sessions for <skill-name>).
```

If 3+ sessions exist, aggregate findings using these thresholds:

| Signal | Threshold | Indicates |
|---|---|---|
| Same-step rejection | 2+ sessions | Default approach doesn't match user expectations |
| Same-step retry | 2+ sessions | Instructions unclear or incomplete |
| Similar friction | 2+ sessions | Missing context or explanation |
| Abandonment | 2+ sessions | Workflow too heavy or misaligned |

### 3. Present Findings

#### If no patterns found:
```
No recurring patterns found in <skill-name> sessions (N sessions analyzed).
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
