# Aggregation Logic

## Overview

The central agent (Claude Code itself) combines outputs from all AI CLIs into a single unified review.

## Step 1: Parse Agent Outputs

Parse each agent's output into structured findings. Each finding has:

| Field | Description |
|-------|-------------|
| **severity** | `Critical`, `Warning`, or `Suggestion` |
| **title** | Short description of the issue |
| **file** | File path |
| **line** | Line number (if available) |
| **issue** | Detailed description |
| **fix** | Concrete suggestion |
| **source** | Which agent(s) found it |

If an agent's output does not follow the expected format, attempt best-effort parsing. If unparseable, include the raw output in a separate "Unparsed Output" section attributed to that agent.

## Step 2: Deduplicate

Merge findings that refer to the same issue:

1. **Same file + same/adjacent line + same issue type** -> Merge into one finding. List all source agents.
2. **Same file + different line + same issue pattern** -> Keep separate but note the pattern (e.g., "similar issue found at lines 10, 25, 42").
3. **Different file + same conceptual issue** -> Keep separate. Each file gets its own finding.

When merging, prefer the most detailed description and the most actionable fix suggestion.

## Step 3: Resolve Contradictions

Agents may disagree. Handle as follows:

### Majority Agreement (2+ agents agree out of 3)
Adopt the majority position as the primary finding. Add a note:
```
> **Dissent** (<agent name>): <alternative view>
```

### No Majority (all agents differ)
Present all views and ask the user to decide:
```
> **Conflicting views — user decision needed:**
> - **<agent1>:** <view>
> - **<agent2>:** <view>
> - **<agent3>:** <view>
```

### Severity Disagreement Only
If agents agree on the issue but disagree on severity:
- Use the **highest** severity as the primary level.
- Note the range: "Severity: Critical (Claude, Codex) / Warning (Gemini)".

## Step 4: Sort by Severity

Order findings by severity: Critical -> Warning -> Suggestion.

Within the same severity level, sort by:
1. Number of agents that found the issue (descending — more consensus = higher priority)
2. File path (alphabetical)
3. Line number (ascending)

## Output Format

```markdown
## Multi-Agent Review

**Agents:** <agent1> <status> | <agent2> <status> | ...
**Target:** <PR #N / local diff (branch-name)>

### Critical Issues
#### <title>
- **File:** `path/to/file:L<line>`
- **Found by:** <agent names>
- **Issue:** <description>
- **Fix:** <suggestion>

### Warnings
#### <title>
- **File:** `path/to/file:L<line>`
- **Found by:** <agent names>
- **Issue:** <description>
- **Fix:** <suggestion>

### Suggestions
#### <title>
- **File:** `path/to/file:L<line>`
- **Found by:** <agent names>
- **Issue:** <description>
- **Fix:** <suggestion>

### Summary
| Severity | Count |
|----------|-------|
| Critical | N     |
| Warning  | N     |
| Suggestion | N  |
```

If a severity category has no findings, omit that section entirely.

If no issues are found by any agent, output:
```markdown
## Multi-Agent Review

**Agents:** <agent1> <status> | <agent2> <status> | ...
**Target:** <PR #N / local diff (branch-name)>

No issues found.
```
