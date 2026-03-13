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

Scan **recent** session history files in the **current project** to find sessions where skills were invoked.

#### 1a. Determine the session directory

Derive the current project's session directory from `pwd`:
```bash
PROJECT_DIR=$(pwd | sed 's|/|-|g; s|^-||')
SESSION_DIR="$HOME/.claude/projects/$PROJECT_DIR"
```

#### 1b. Find recent sessions with skill invocations

Search only the most recent session files (up to 20, within the last 30 days) for skill invocation markers:
```bash
find "$SESSION_DIR" -name "*.jsonl" -mtime -30 -type f -print0 \
  | xargs -0 ls -t 2>/dev/null \
  | head -20 \
  | xargs grep -l "aoshimash-skills:" 2>/dev/null
```

A skill invocation is identified by the presence of `<command-name>aoshimash-skills:<skill-name></command-name>` in the conversation.

If no sessions are found, inform the user:
```
No skill execution sessions found in recent history (last 30 days, current project).
```

#### 1c. Select a skill to analyze

If sessions are found, list which skills were used and how many sessions each has. Ask the user which **single skill** to analyze. Do not offer an "analyze all" option — analyze one skill per invocation to keep execution fast.

### 2. Analyze Sessions

For each session file containing the target skill invocation, read the conversation. Focus on `human` and `assistant` message types to understand the interaction flow — skip large `tool_result` entries unless needed for context (e.g., to confirm a test failure). Detect these patterns:

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

### 4. Choose Output Method

After presenting findings, ask the user how to proceed:

1. **Issue** — Submit feedback as a GitHub Issue (no code changes)
2. **PR** — Submit with SKILL.md modifications included
3. **Conversation only** — No external submission; review findings in this session only

### 5. Apply Improvements (with approval)

For each improvement suggestion:

1. **Present to the user** — Show the pattern, root cause, and proposed fix.
2. **Ask for approval** — Do not modify skill files without explicit user approval.
3. **If declined**, acknowledge and move to the next suggestion.

#### If "Conversation only" was selected:

Present the full analysis report. No external submission occurs. End the workflow.

#### If "Issue" was selected:

Create an issue for the analyzed skill:

1. Draft the issue body containing:
   - Skill name and number of sessions analyzed
   - Each pattern found (description, frequency, root cause, proposed fix)
   - Do NOT include raw session data or project-specific details (privacy)
2. Show the draft to the user for review and confirmation.
3. On approval, create the issue:
   ```bash
   gh issue create --title "improve(<skill-name>): <summary>" --body "<drafted body>" --label "enhancement"
   ```
4. Return the issue URL.

#### If "PR" was selected:

Create a PR with the approved fixes for the analyzed skill:

1. Create a branch: `fix/improve-<skill-name>-<description>`
2. Modify the affected skill files.
3. Commit: `fix(<skill-name>): <description>`
4. Show the diff to the user for review and confirmation.
5. Push and create PR:
   ```bash
   gh pr create --title "fix(<skill-name>): <description>" --body "<summary of changes>"
   ```
6. Return the PR URL.
