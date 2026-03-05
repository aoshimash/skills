---
name: multi-agent-review
description: >
  Run multiple AI CLIs (Claude, Codex, Gemini) in parallel for code review,
  then aggregate, deduplicate, and reconcile results into a unified review.
  Supports both standalone invocation and internal use from other skills.
  Use when the user says "multi-agent review", "multi review", "マルチレビュー",
  "複数AIでレビュー", "レビューして", or wants a thorough code review using
  multiple AI agents.
---

# Multi-Agent Review

Run multiple AI CLIs in parallel for code review and produce a unified review output.

## Core Principles

1. **All agents, same perspectives** — By default, every agent reviews with the same set of perspectives. Per-agent customization is available via project settings.
2. **Fault tolerant** — Skip uninstalled or failing CLIs and proceed with available agents.
3. **Unified output** — Deduplicate, resolve contradictions, and sort by severity into a single review.
4. **Review only** — This skill produces review output in the conversation. Where to post it (PR comment, file, etc.) is the caller's responsibility.

## Step Tracking

Maintain an internal checklist of completed steps throughout the workflow.

Steps: `setup` -> `prepare` -> `execute` -> `aggregate` -> `present` -> `log-and-improve`

Mark each step as completed when it finishes. If a step is skipped (with reason) or abandoned, record that too. The final `log-and-improve` step is **mandatory**.

## Workflow

### Phase 0: Setup — Agent Configuration

1. Check for existing configuration in `.claude/aoshimash-skills.local.md` (YAML frontmatter).
2. If configuration exists, load it and proceed to Phase 1.
3. If no configuration exists (first run):
   a. Check which CLIs are installed using `command -v claude`, `command -v codex`, `command -v gemini`.
   b. Present the list of detected CLIs to the user and ask which ones to use.
   c. Save the selection to `.claude/aoshimash-skills.local.md`.

#### Configuration format

```yaml
# .claude/aoshimash-skills.local.md frontmatter
multi-agent-review:
  agents:
    - name: claude
      enabled: true
      # Optional: override perspectives for this agent
      # perspectives:
      #   - correctness
      #   - security
    - name: codex
      enabled: true
    - name: gemini
      enabled: true
  # Optional: override default perspectives for all agents
  # perspectives:
  #   - name: custom-perspective
  #     description: "..."
  #     prompt: "..."
```

### Phase 1: Prepare — Diff Acquisition

Determine the review target and obtain the diff.

1. **If PR number/URL is provided** -> `gh pr diff <number>` to get the diff.
2. **If no PR specified** -> Use local diff:
   - Detect the default branch (`git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`).
   - Get diff: `git diff origin/<default-branch>...HEAD` combined with `git diff` (unstaged) and `git diff --cached` (staged).
3. Save diff to a temporary file (`mktemp /tmp/multi-review-XXXXXX`).
4. If diff is empty, report "No changes found" and exit (clean up temp file).

Record the temp file path for use in subsequent phases and cleanup.

See [references/agent-cli.md](references/agent-cli.md) for diff preparation details.

### Phase 2: Execute — Parallel CLI Invocation

Run all enabled agents in parallel using Background Bash.

1. Load review perspectives: project custom perspectives (from settings) merged with defaults from [references/default-perspectives.md](references/default-perspectives.md).
2. Build the review prompt incorporating all perspectives.
3. For each enabled agent, invoke its CLI in the background. See [references/agent-cli.md](references/agent-cli.md) for exact commands.
4. Before invoking each agent, verify the CLI is installed (`command -v <cli>`). Skip if not found.
5. Wait for all background tasks to complete (timeout: 5 minutes).
   - All completed -> Phase 3.
   - Some timed out -> Proceed with completed results, note timed-out agents.
   - All failed -> Report to user and exit (clean up temp file).

### Phase 3: Aggregate — Unified Review

Combine results from all agents into a single review.

See [references/aggregation.md](references/aggregation.md) for the detailed procedure.

**Summary:**
1. **Parse** each agent's output into structured findings (severity, file, line, issue, fix).
2. **Deduplicate** — Merge findings about the same file/line/issue from different agents.
3. **Resolve contradictions** — When agents disagree:
   - Majority agrees -> Adopt majority view, note dissent.
   - No majority -> Present all views to the user for decision.
4. **Sort by severity** — Critical -> Warning -> Suggestion.

### Phase 4: Present — Output Results

Display the unified review in the conversation using this format:

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
...

### Suggestions
...

### Summary
| Severity | Count |
|----------|-------|
| Critical | N     |
| Warning  | N     |
| Suggestion | N  |
```

If no issues are found, state that clearly.

### Phase 5: Cleanup

Delete the temporary diff file. This must happen on every exit path (success, error, early termination).

### Phase 6: Log & Improve (mandatory)

**Always execute this phase**, even if the workflow was abandoned or partially completed.

#### Signals to track during execution

- **Agent failure**: A CLI fails to execute or times out
- **Parse failure**: Agent output cannot be parsed into structured findings
- **Contradiction**: Agents disagree on a finding
- **User friction**: User asks for clarification or expresses confusion
- **Skip**: A step is skipped (e.g., no agents available)

#### Spawn skill-analyzer agent

Pass a session summary containing:
- `skill`: "multi-agent-review"
- `project`: repository name
- `target`: PR number or "local diff"
- `agents_configured`: list of configured agents
- `agents_executed`: list of agents that successfully ran
- `agents_skipped`: list with reasons (not installed, timed out, failed)
- `steps_completed`: list from step tracking checklist
- `steps_skipped`: list with reasons
- `findings_count`: {critical, warning, suggestion}
- `contradictions`: list of contradictions found
- `user_friction`: list of friction observations
- `outcome`: "success", "partial", or "abandoned"
- `notes`: any additional observations

See [references/log-analysis.md](references/log-analysis.md) for how to handle the agent's results.

## References

- [references/agent-cli.md](references/agent-cli.md) — CLI invocation commands and diff handling
- [references/default-perspectives.md](references/default-perspectives.md) — Default review perspectives
- [references/aggregation.md](references/aggregation.md) — Aggregation logic details
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
- [references/log-analysis.md](references/log-analysis.md) — Skill-analyzer agent integration
