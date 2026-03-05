---
name: implement-issue
description: >
  Read a platform issue (GitHub/GitLab), analyze the codebase, create an
  implementation plan, and after user approval, implement the changes and
  open a pull/merge request. Use when the user says "implement issue",
  "issue を実装", "issue #N を対応", "この issue をやって", "implement #N",
  "fix issue #N", "work on issue", or references an issue number/URL
  with the intent to implement it.
---

# Implement Issue

Read an issue, plan the implementation, get approval, implement, and create a PR/MR.

## Core Principles

1. **Issue is the source of truth** — Scope to what the issue describes. Do not add unrelated changes.
2. **Plan before code** — Always present an implementation plan and get user approval before writing code.
3. **Small, reviewable changes** — Prefer focused PRs. If the issue is large, suggest splitting. If the user insists on a single PR, implement incrementally with clear scope per commit.
4. **Follow project conventions** — Read CLAUDE.md and existing code patterns before implementing.

## Step Tracking

Throughout the workflow, maintain an internal checklist of completed steps. This ensures no step is skipped and provides data for the session log.

Steps: `setup` → `plan` → `implement` → `pr` → `log-and-improve`

Mark each step as completed when it finishes. If a step is skipped (with reason) or abandoned, record that too. The final `log-and-improve` step is **mandatory** — always execute it, even if the workflow is abandoned partway through.

## Workflow

### Phase 0: Setup

1. Detect platform (check CLAUDE.md → git remote → ask user). Read the platform-specific guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
2. Obtain the issue identifier (number or URL) from the user if not already provided.
3. Fetch the issue content using the platform CLI.
4. Ask the user where to implement. Options:
   - **Worktree** (default) — Create a git worktree for isolated work. Keeps current branch untouched.
   - **New branch** — Create a new branch in the current working tree.
   - **Current branch** — Work directly on the current branch (useful if already on a feature branch).

### Phase 1: Plan

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**
1. Parse the issue — extract motivation, background, proposal, acceptance criteria.
2. Analyze the codebase — identify files, patterns, dependencies relevant to the issue.
3. Resolve design decisions — if multiple valid approaches exist, present options with pros/cons and a recommendation. Wait for the user's choice.
4. Draft implementation plan — list files to create/modify, approach for each, edge cases.
5. Self-evaluate — verify plan addresses all acceptance criteria and stays in scope.
6. Present the plan to the user and wait for approval.

If the user requests changes, revise and re-present. Do not proceed without approval.

### Phase 2: Implement

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**
1. Prepare working environment (worktree / new branch / current branch).
2. Implement changes following the approved plan.
3. Run project checks (tests, lint, type-check, format) — loop until all pass.
4. AI self-review of the full diff — loop until clean. Escalate to user when human judgment is needed.
5. Commit with a message referencing the issue.

### Phase 3: Pull/Merge Request

See [references/workflow.md](references/workflow.md) for the PR/MR body format.

1. Push the branch to the remote.
2. Create a PR/MR with:
   - Title: concise summary (under 70 chars)
   - Body: summary of changes, link to the issue (Closes #N / Relates to #N), test plan
3. Return the PR/MR URL to the user.

### Phase 4: Log & Improve (mandatory)

**Always execute this phase**, even if the workflow was abandoned or partially completed.

#### What to track during execution

Throughout Phases 0–3, observe and record these signals:

- **Rejection**: User says "no", "that's wrong", "change this", or rejects a proposal
- **Retry**: A step fails (tests, lint, build) and must be re-done
- **Friction**: User asks the same question twice, asks for clarification, or expresses confusion
- **Scope change**: User changes requirements mid-implementation
- **Skip**: A step is skipped (e.g., no tests defined in project)

#### Spawn skill-analyzer agent

Pass a session summary containing:
- `skill`: "implement-issue"
- `project`: repository name
- `issue`: issue identifier
- `steps_completed`: list from step tracking checklist
- `steps_skipped`: list with reasons
- `rejections`: list of {step, reason} observed during this session
- `retries`: list of {step, reason} observed during this session
- `user_friction`: list of friction observations
- `outcome`: "success", "partial", or "abandoned"
- `notes`: any additional observations

The agent writes the log and analyzes accumulated entries for patterns.

See [references/log-analysis.md](references/log-analysis.md) for how to handle the agent's results. If the agent reports improvement suggestions, present them to the user and offer to create a PR.

## References

- [references/workflow.md](references/workflow.md) — Detailed plan / implement / PR procedure
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/log-analysis.md](references/log-analysis.md) — How to handle skill-analyzer agent results
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
