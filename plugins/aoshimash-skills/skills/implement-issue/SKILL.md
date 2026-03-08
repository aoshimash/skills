---
name: implement-issue
description: >
  Read a platform issue (GitHub/GitLab/Backlog), analyze the codebase, create an
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

## Workflow

### Phase 0: Setup

1. Detect the **issue tracker** platform (check CLAUDE.md `## Issue Tracker` → git remote → ask user). Note: the issue tracker and code hosting platform may differ (e.g., Backlog for issues + GitHub for PRs). Read the platform-specific guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog: [references/platform-backlog.md](references/platform-backlog.md)
2. Obtain the issue identifier (number, key, or URL) from the user. If not provided, list open issues from the platform (when supported) and ask the user to select one.
3. Fetch the issue content using the platform CLI or MCP tool.
4. Ask the user where to implement using `AskUserQuestion` with numbered options:
   - **Worktree** (default) — Create a git worktree for isolated work. Keeps current branch untouched.
   - **New branch** — Create a new branch in the current working tree.
   - **Current branch** — Work directly on the current branch (useful if already on a feature branch).

### Phase 1: Plan

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**
1. Parse the issue — extract motivation, background, proposal, acceptance criteria.
2. Analyze the codebase — identify files, patterns, dependencies relevant to the issue.
3. Resolve design decisions — if multiple valid approaches exist, use `AskUserQuestion` to present numbered options with pros/cons and a recommendation. Wait for the user's choice.
4. Draft implementation plan — list files to create/modify, approach for each, edge cases.
5. Self-evaluate — verify plan addresses all acceptance criteria and stays in scope.
6. Present the plan as text output, then use `AskUserQuestion` to ask for approval with options: Approve / Request changes / Abort. If the user requests changes, revise and re-present. Do not proceed without approval.

**Important:** Do NOT use `EnterPlanMode`/`ExitPlanMode` for plan approval. Present the plan directly as text and use `AskUserQuestion` for the approval step.

### Phase 2: Implement

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**
1. Prepare working environment (worktree / new branch / current branch).
2. Implement changes following the approved plan.
3. Run project checks (tests, lint, type-check, format) — loop until all pass.
4. AI self-review of the full diff — loop until clean. Escalate to user (via `AskUserQuestion`) when human judgment is needed. After completion, output a visible self-review summary (e.g., "Self-review: N round(s), N issue(s) found, N fixed").
5. Commit with a message referencing the issue.

**Continuous flow**: After user approves the plan, proceed through Phase 2 and Phase 3 without stopping — do not pause between steps unless user input is needed (e.g., escalation).

### Phase 3: Pull/Merge Request

See [references/workflow.md](references/workflow.md) for the PR/MR body format.

1. Detect the **code hosting** platform from the git remote URL (this may differ from the issue tracker).
2. Push the branch to the remote.
3. Create a PR/MR with:
   - Title: concise summary (under 70 chars)
   - Body: summary of changes, link to the issue (Closes #N / Relates to #N), test plan
4. If the issue tracker supports comments (e.g., Backlog), post a comment on the issue with the PR/MR link.
5. Return the PR/MR URL to the user.

## References

- [references/workflow.md](references/workflow.md) — Detailed plan / implement / PR procedure
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog MCP tools
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
