---
name: analyze-sessions
description: >
  Analyze Claude Code session history to detect recurring patterns and
  propose improvements to skills and settings.json. Use when the user says
  "analyze sessions", "improve skills", "analyze skill logs",
  "セッションを分析", "スキルを改善", "ログを分析", "設定を提案",
  or wants to review skill usage patterns and environment configuration.
---

# Analyze Sessions

Analyze Claude Code's built-in conversation history to detect recurring patterns in skill executions and propose concrete improvements to skill definitions and `settings.json` configuration.

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
  | xargs -d '\n' grep -l "aoshimash-skills:" 2>/dev/null
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

#### Skill-Level Patterns

These patterns indicate issues with the skill definition itself:

##### Rejection
User explicitly rejects a proposal or asks to change something. Look for:
- User messages containing negation ("no", "that's wrong", "change this", "違う", "修正して")
- User requesting revisions to plans, drafts, or implementations

##### Retry
A step fails and must be re-done. Look for:
- Tool results showing test/lint/build failures followed by fix attempts
- Repeated tool calls to the same file or command

##### Friction
User experiences confusion or frustration. Look for:
- User asking the same question multiple times
- User requesting clarification on skill behavior
- User expressing frustration or confusion

##### Abandonment
Workflow was not completed. Look for:
- Sessions that start a skill workflow but never reach the final step (e.g., no PR created for implement-issue)

#### Environment-Level Patterns

These patterns indicate issues solvable by `settings.json` or `settings.local.json` changes rather than skill modifications:

##### Permission Friction
Repeated tool permission prompts slow down the workflow. Look for:
- The same tool type being invoked multiple times across sessions with short user approval responses ("yes", "y", "allow", "approve", "許可") immediately following
- User expressing annoyance at repeated permission prompts
- Patterns where a tool is consistently approved (never denied) across sessions

When detected, propose adding the tool to `permissions.allow` in the appropriate settings file:
- `~/.claude/settings.json` for global tools (used across all projects)
- `.claude/settings.local.json` for project-specific tools

##### Hook Opportunity
Repeated manual actions suggest automation via hooks. Look for:
- The same Bash command or sequence executed at the start of multiple sessions (→ `SessionStart` hook)
- Repeated manual validation before specific tool calls (→ `PreToolUse` hook)
- Consistent post-action cleanup steps (→ `PostToolUse` or `Stop` hook)

When detected, propose a specific hook configuration with the event type and command.

#### Aggregation Thresholds

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
| Permission friction | 2+ sessions | Tool should be added to permissions.allow |
| Hook opportunity | 2+ sessions | Manual step should be automated via hook |

### 3. Present Findings

#### If no patterns found:
```
No recurring patterns found in <skill-name> sessions (N sessions analyzed).
```

#### If patterns found, present a structured report:

Group findings by target:

**Skill Improvements** (changes to SKILL.md):
```
### <pattern description>
- **Type**: Rejection / Retry / Friction / Abandonment
- **Seen in**: X/N sessions
- **Common reason**: "<aggregated reasons>"
- **Root cause**: <what in the skill likely causes this>
- **Proposed fix**: <what to change in SKILL.md>
```

**Settings Proposals** (changes to settings.json / settings.local.json):
```
### <pattern description>
- **Type**: Permission Friction / Hook Opportunity
- **Seen in**: X/N sessions
- **Common reason**: "<aggregated reasons>"
- **Root cause**: <missing configuration>
- **Proposed fix**: Add to <target file>
- **Configuration**:
  ```json
  <proposed JSON snippet>
  ```
```

### 4. Choose Output Method

After presenting findings, ask the user how to proceed:

1. **Issue** — Submit feedback as a GitHub Issue (no code changes)
2. **PR** — Submit with SKILL.md modifications included
3. **Conversation only** — No external submission; review findings in this session only

### 5. Apply Improvements (with approval)

For each improvement suggestion:

1. **Present to the user** — Show the pattern, root cause, and proposed fix.
2. **Ask for approval** — Do not modify files without explicit user approval.
3. **If declined**, acknowledge and move to the next suggestion.

#### If "Conversation only" was selected:

Present the full analysis report. No external submission occurs. End the workflow.

#### If "Issue" was selected:

Create an issue for the analyzed skill:

1. Draft the issue body containing:
   - Skill name and number of sessions analyzed
   - Each pattern found (description, frequency, root cause, proposed fix)
   - Settings.json proposals (if any) with proposed configuration snippets
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

Note: Settings.json proposals are **not** auto-applied via PR — they are included in the PR description as recommendations for the user to apply manually. This avoids modifying the user's environment configuration without explicit action.
