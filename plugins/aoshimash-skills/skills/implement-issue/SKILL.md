---
name: implement-issue
description: >
  Read platform issues (GitHub/GitLab/Backlog), analyze the codebase, plan,
  implement, and open pull/merge requests with two-stage review (spec
  compliance, then code quality). Implements a single issue interactively by
  default; when given a parent issue, a milestone, a label, or a list of
  issues, offers batch implementation with a dependency graph, git worktrees,
  and parallel subagents. Use when the user says "implement issue",
  "issue を実装", "issue #N を対応", "この issue をやって", "implement #N",
  "fix issue #N", "work on issue", "run sprint", "スプリント実行",
  "これらの issue を実装", "implement these issues", "start the sprint",
  "issue を順に実装して", "sprint を回して", or references issue numbers/URLs
  with the intent to implement them.
---

# Implement Issue

Read an issue (or a set of issues), plan the implementation, get approval, implement, and create PR(s)/MR(s) with two-stage review. **Single mode** (one issue, interactive) is the default. **Batch mode** (many issues, dependency-ordered, parallel) is used for parent issues, milestones, labels, or explicit lists.

## Core Principles

1. **Issues are the source of truth** — Scope to what each issue describes. Do not add unrelated changes. Do not deviate from acceptance criteria.
2. **Plan before code** — In Single mode, always present an implementation plan and get user approval before writing code.
3. **Small, reviewable changes** — Prefer focused PRs. If an issue is large, suggest splitting (see the create-issue skill's Split Proposal). If the user insists on a single PR, implement incrementally with clear scope per commit.
4. **Follow project conventions** — Read CLAUDE.md and existing code patterns before implementing.
5. **Two-stage review on every PR** — Spec compliance, then code quality, in both modes (see [references/review-gates.md](references/review-gates.md)). They catch different classes of problems; combining them into one review loses signal.
6. **Dependency-driven parallelism** (Batch mode) — Issues with no unresolved dependencies run in parallel. The dependency graph is the scheduler.
7. **Worktree isolation** (Batch mode) — Each issue gets its own git worktree. No cross-contamination between parallel implementations.
8. **Fail fast, report clearly** (Batch mode) — If an issue fails after retries, mark it blocked and continue with independent issues. Never block the entire batch on one failure.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |
| **Separate agent instance** — run a task in a fresh context that has not seen this conversation | Subagent dispatch (e.g. Claude Code's Task tool) | Run sequentially in the current context; for verification, mark the result `SELF-REVIEWED` in the artifact it lands in (e.g. the PR body or reply comment the step produces) |
| **Background execution** — run long commands without blocking | Background shell (e.g. Claude Code's background Bash) | Run commands sequentially |

## Phase 0: Setup and Mode Selection

1. Detect the **issue tracker** platform (check CLAUDE.md `## Issue Tracker` → git remote → ask user). Note: the issue tracker and code hosting platform may differ (e.g., Backlog for issues + GitHub for PRs). Read the platform-specific guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog: [references/platform-backlog.md](references/platform-backlog.md)
2. Obtain the issue identifier(s). If none are provided, list open issues from the platform (when supported) and ask the user to select.
3. **Mode routing:**
   - **Multiple issues referenced** — a list of numbers, "these issues", a milestone, a label, or "run sprint" / "スプリント実行" phrasing → **Batch mode**. If the source is ambiguous, ask the user to choose (see Environment Adaptation): Parent issue / Milestone / Label / Manual list.
   - **Single issue referenced** — fetch it, then **check whether it is a parent issue** with open sub-issues (GitHub: sub-issues API; GitLab: issue links/task list; Backlog: `--parent` search — see the platform guide's "Detect Sub-Issues / Child Items" section).
     - If it has open sub-issues, ask the user to choose (see Environment Adaptation): "Issue #N has M open sub-issue(s). How do you want to proceed?" with options:
       - **Implement all sub-issues (batch)** — mark "(Recommended)" when 2+ children are open. Proceeds to Batch mode with those sub-issues as the source set.
       - **Implement only this issue** — treat #N itself as a normal single issue, ignore its children.
       - **Pick one sub-issue** — list the children, let the user select one, continue in Single mode with that child.
     - If it has no open sub-issues → **Single mode** on #N.
4. **Single mode only** — check issue state: if the issue is already closed or merged:
   - Inform the user: "Issue #N is already \<state\>."
   - Ask the user to choose (see Environment Adaptation): "Reopen and implement" / "Pick another issue" / "Abort"
   - If "Reopen and implement": reopen the issue, then continue. If "Pick another issue": return to step 2. If "Abort": stop.

   **Batch mode**: closed/merged issues in the source set are filtered out silently. If all issues are closed, inform the user and stop.
5. **Single mode only** — ask the user where to implement (see Environment Adaptation) with numbered options:
   - **Worktree** (default) — Create a git worktree for isolated work. Keeps current branch untouched.
   - **New branch** — Create a new branch in the current working tree.
   - **Current branch** — Work directly on the current branch (useful if already on a feature branch).

   **Batch mode**: always uses a worktree per issue (see Batch Mode below) — do not ask.

## Single Mode

The default mode: one issue, main agent executes directly, user present throughout.

### Phase 1: Plan

See [references/workflow.md](references/workflow.md) (Interactive columns) for the detailed procedure.

**Summary:**
1. Parse the issue — extract motivation, background, proposal, acceptance criteria.
2. Analyze the codebase — identify files, patterns, dependencies relevant to the issue.
3. Resolve design decisions — if multiple valid approaches exist, ask the user to choose (see Environment Adaptation) from numbered options with pros/cons and a recommendation. Wait for the user's choice.
4. Draft implementation plan — list files to create/modify, approach for each, edge cases.
5. Self-evaluate — verify plan addresses all acceptance criteria and stays in scope.
6. Present the plan as text output, then ask the user to choose (see Environment Adaptation) for approval with options: Approve / Request changes / Abort. If the user requests changes, revise and re-present. Do not proceed without approval.

**On Claude Code specifically:** do not use plan mode (`EnterPlanMode`/`ExitPlanMode`) for this approval — present the plan directly as text and collect approval via a user choice. Plan mode's approval UI can cause accidental rejections with no way to provide feedback.

### Phase 2: Implement

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**
1. Prepare working environment (worktree / new branch / current branch, per Phase 0 Step 5).
2. Implement changes following the approved plan. Regenerate derived files if source files that drive code generation were modified.
3. Run auto-fix commands (formatters, linters with `--fix`) once, then run project checks (tests, lint, type-check, build) — loop until all pass (max 3 attempts).
4. AI self-review of the full diff — loop until clean (max 3 rounds). Escalate to the user (via a user choice, see Environment Adaptation) when human judgment is needed. After completion, output a visible self-review summary (e.g., "Self-review: N round(s), N issue(s) found, N fixed").
5. Commit with a message referencing the issue (`Refs #N`).

**Continuous flow**: After user approves the plan, proceed through Phase 2 and Phase 3 without stopping — do not pause between steps unless user input is needed (e.g., escalation).

### Phase 3: Pull/Merge Request and Review Gates

See [references/workflow.md](references/workflow.md) for the PR/MR body format and [references/review-gates.md](references/review-gates.md) for the review procedure.

1. Detect the **code hosting** platform from the git remote URL (this may differ from the issue tracker).
2. Push the branch and create a PR/MR (title under 70 chars; body with Closes #N / Relates to #N and a test plan).
3. **Review gates**: run Stage 1 (spec compliance) then Stage 2 (code quality) against the PR diff. Fix findings and push; max 2 fix rounds per stage. If a stage still fails after 2 rounds, escalate to the user via a user choice (see Environment Adaptation) with options Proceed as-is / Keep fixing / Abandon rather than silently marking anything — Stage 2.5 (pattern propagation) is always skipped in Single mode, since there are no other in-flight PRs to propagate a fix to.
4. Monitor CI — run `gh pr checks --watch` (GitHub) or `glab mr checks` (GitLab) and verify all checks pass. If CI fails and is fixable, push a fix commit and re-monitor.
5. If the issue tracker supports comments (e.g., Backlog), post a comment on the issue with the PR/MR link.
6. Return the PR/MR URL to the user, along with a summary of the review gate results.

## Batch Mode

Used for a parent issue's sub-issues, a milestone, a label, or a manual list of issues. See [references/batch.md](references/batch.md) for the full procedure.

**Summary:**

1. **Dependency graph** — parse `Blocked by` / `Depends on` / `After` declarations and platform-specific links from each issue body; build a DAG; detect cycles and ask the user how to resolve them; compute parallel execution groups (topological levels); visualize the plan; get approval via a user choice (see Environment Adaptation) with options Approve / Reorder / Abort.
2. **Execution loop** — for each group, dispatch one implementer subagent per issue in parallel, each working in its own git worktree and executing [references/workflow.md](references/workflow.md) in **Autonomous mode** (see that file's Execution Modes table). After each PR is created, the orchestrator runs the two-stage review gates ([references/review-gates.md](references/review-gates.md)), including **Stage 2.5 pattern propagation** across other in-flight PRs when a rule-violation is found. Update the DAG as issues complete; on failure, mark the issue `BLOCKED` and cascade `SKIPPED` to its transitive dependents, then continue with independent issues.
3. **Summary** — present a status table (issue, title, status, PR) covering DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED / SKIPPED, explain any blockers, and optionally post a summary comment on the parent issue.

## References

- [references/workflow.md](references/workflow.md) — Canonical plan/implement/PR procedure, used by both Single mode (Interactive) and Batch mode's implementer subagents (Autonomous)
- [references/batch.md](references/batch.md) — Batch mode dependency graph, parallel dispatch, and failure handling
- [references/review-gates.md](references/review-gates.md) — Two-stage review procedure (Stage 1 spec compliance, Stage 2 code quality, Stage 2.5 pattern propagation)
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog CLI commands (bee)
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
