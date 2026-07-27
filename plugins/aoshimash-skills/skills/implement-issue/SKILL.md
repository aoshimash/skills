---
name: implement-issue
description: >
  Read platform issues (GitHub/GitLab/Backlog), analyze the codebase,
  implement autonomously, and open review-first pull/merge requests: draft
  PR with decisions logged in the body, two-stage review (spec compliance,
  then code quality), a pre-push security review, and a flip to
  ready-for-review once gates and CI pass. Implements a single issue end to
  end with zero routine questions by default; when given a parent issue, a
  milestone, a label, or a list of issues, offers batch implementation with
  a dependency graph, git worktrees, and parallel agent instances where the
  environment supports them (sequential otherwise). Use when the user says
  "implement issue", "issue を実装", "issue #N を対応", "この issue をやって",
  "implement #N", "fix issue #N", "work on issue", "run sprint",
  "スプリント実行", "これらの issue を実装", "implement these issues",
  "start the sprint", "issue を順に実装して", "sprint を回して", or references
  issue numbers/URLs with the intent to implement them.
---

# Implement Issue

Read an issue (or a set of issues), implement autonomously, and deliver
review-first PR(s)/MR(s). **Single mode** (one issue) is the default and runs
end to end without routine user interaction: decisions are resolved from the
issue, its parent, repository agent instructions, or user-level configuration
— and logged in the PR instead of asked. **Batch mode** (many issues,
dependency-ordered, parallel where the environment supports it) is used for
parent issues, milestones, labels, or explicit lists.

## Core Principles

1. **Issues are the source of truth** — Scope to what each issue describes. Do
   not add unrelated changes. Do not deviate from acceptance criteria.
2. **Autonomous by default, decisions logged not asked** — There is no plan
   approval gate and no location question. Settled decisions are followed;
   local, reversible decisions are made by repository convention and logged in
   the PR body (`Decisions & Deviations`). The only routine-flow stop is a
   genuinely undecidable decision, asked as **one batched question** whose
   answers are written back to the issue before implementation proceeds —
   never ask twice.
3. **Review-first PRs; machines finish before humans start** — The PR is
   created as a **draft** and flipped to ready-for-review only after CI and
   both review-gate stages pass. The body is ordered for the reviewer:
   decisions and risk areas first, acceptance criteria mapped to verification
   evidence, mechanical change lists last. Repository PR templates, when
   present, take precedence as the skeleton.
4. **Nothing unsafe leaves the machine** — A security review of the pending
   changes runs after checks and self-review pass and **before the branch is
   pushed**; unresolved Critical/High findings block the push.
5. **Two-stage review on every PR** — Spec compliance, then code quality, in
   both modes (see [references/review-gates.md](references/review-gates.md)).
   They catch different classes of problems; combining them loses signal.
6. **Small, reviewable changes** — Prefer focused PRs. If an issue is too
   large for one, suggest splitting (see the create-issue skill); if it must
   be one PR, implement incrementally with clear scope per commit.
7. **Batch mode: the DAG is the scheduler** — Dependency-driven parallelism,
   one worktree per issue, fail fast without blocking independent issues (see
   [references/batch.md](references/batch.md)).

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`, which can carry several questions in one round) | Numbered options as plain text; wait for the user's reply |
| **Separate agent instance** — run a task in a fresh context that has not seen this conversation | Subagent dispatch (e.g. Claude Code's Task tool) | Run sequentially in the current context; for verification, mark the result `SELF-REVIEWED` in the artifact it lands in (e.g. the PR body) |
| **Model selection** — run a separate agent instance on a chosen model | Per-instance model override (e.g. Claude Code's Task tool `model` parameter, or an agent definition's `model` frontmatter) | Run every instance on the session's default model — only the reviewer-stronger-than-implementer recommendation (see [references/review-gates.md](references/review-gates.md)) is unavailable |
| **Security review** — security-focused review of the pending diff | Dedicated command (e.g. Claude Code's `/security-review`) | Review the diff yourself against the checklist in [references/workflow.md](references/workflow.md) step 2-6 |

## Phase 0: Setup and Mode Selection

1. Detect the **issue tracker** platform (check the project's agent
   instructions for an `## Issue Tracker` section → git remote → ask the user
   only if neither identifies it). The issue tracker and code hosting platform
   may differ (e.g. Backlog issues + GitHub PRs). Read the platform guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog: [references/platform-backlog.md](references/platform-backlog.md)
2. Obtain the issue identifier(s). If none are provided, list open issues from
   the platform (see the platform guide's issue-listing section) and ask the
   user to select.
3. **Mode routing:**
   - **Multiple issues referenced** — a list of numbers, "these issues", a
     milestone, a label, or "run sprint" / "スプリント実行" phrasing →
     **Batch mode**. If the source is ambiguous, ask the user to choose (see
     Environment Adaptation): Parent issue / Milestone / Label / Manual list.
   - **Single issue referenced** — fetch it, then **check whether it is a
     parent issue** with open sub-issues (see the platform guide's sub-issue
     detection section).
     - If it has open sub-issues, ask the user to choose (see Environment
       Adaptation): "Issue #N has M open sub-issue(s). How do you want to
       proceed?" — **Implement all sub-issues (batch)** (mark "(Recommended)"
       when 2+ children are open) / **Implement only this issue** / **Pick one
       sub-issue** (list the children, continue in Single mode with the
       selection). This is a scope decision, not a routine gate — it changes
       what gets implemented.
     - No open sub-issues → **Single mode** on #N.
4. **Issue state check.** Single mode: if the issue is already closed or
   merged, inform the user and ask (see Environment Adaptation): "Reopen and
   implement" / "Pick another issue" / "Abort". Batch mode: closed issues in
   the source set are filtered out silently; if all are closed, inform the
   user and stop.

There is no implementation-location question: Single mode works in a git
worktree by default, reusing one the host environment already prepared for
this run when present (see [references/workflow.md](references/workflow.md)
step 2-1). Batch mode always uses one worktree per issue.

## Single Mode

One issue, executed by the main agent in the **Direct** context of
[references/workflow.md](references/workflow.md) — read that file and follow
its phases end to end without pausing between them:

1. **Understand and decide** — parse the issue, its parent, and any attached
   research comment (re-verify only the delta against current code); analyze
   the codebase; resolve decisions from the stores or by convention. Genuinely
   undecidable decisions become one batched question; the answers are appended
   to the issue's Design Decisions before any code is written.
2. **Implement and verify** — worktree, implement, project checks (max 3
   attempts), self-review (max 3 rounds, with a visible summary line),
   security review **before any push** (Critical/High findings block the
   push), commit.
3. **PR and gates** — push, create a **draft** PR with the review-first body,
   run Stage 1 and Stage 2 review gates, monitor CI, and flip the PR to ready
   only when gates and CI all pass; otherwise it stays a draft with the
   unresolved state recorded.
4. **Recap** — report the PR URL and state, every decision made, every issue
   write-back performed, the review-focus areas, and one line per gate.

Former mid-run stops (plan approval, location choice, per-decision questions,
failing-check and self-review escalations) no longer exist: they either
resolved into the batched question or complete with the concern recorded in
the PR. **On Claude Code specifically:** plan mode is opt-in only — enter it
solely when the user explicitly asks for a plan gate; never by default.

## Batch Mode

Used for a parent issue's sub-issues, a milestone, a label, or a manual list.
See [references/batch.md](references/batch.md) for the full procedure.

**Summary:**

1. **Dependency graph** — collect dependencies from the platform's own
   relationship records (e.g. GitHub's `blockedBy` field) and, as a fallback,
   from `Blocked by` / `Depends on` / `After` declarations in each issue body;
   build a DAG from the union; detect cycles and ask the user how to resolve
   them; compute parallel execution groups (topological levels); visualize the
   plan; get approval via a user choice (see Environment Adaptation) with
   options Approve / Reorder / Abort (Reorder collects dependency-graph edits
   and re-presents the plan — see batch.md B1-3).
2. **Execution loop** — for each group, implement its issues, each in its own
   git worktree, executing [references/workflow.md](references/workflow.md) in
   the **Orchestrated** context (see that file's Invocation Contexts). Where
   the environment supports separate agent instances, dispatch one implementer
   per issue in parallel; otherwise implement sequentially in dependency order
   — the DAG, review gates, and failure cascade are identical either way.
   After each draft PR is created, the orchestrator runs the two-stage review
   gates ([references/review-gates.md](references/review-gates.md)), including
   **Stage 2.5 pattern propagation** across other in-flight PRs when a
   rule-violation is found, and flips the PR to ready when gates and CI pass.
   Update the DAG as issues complete; on failure, mark the issue `BLOCKED`,
   cascade `SKIPPED` to its transitive dependents, and continue with
   independent issues.
3. **Summary** — present a status table (issue, title, status, PR) covering
   DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED / SKIPPED, explain any
   blockers, and optionally post a summary comment on the parent issue.

## References

- [references/workflow.md](references/workflow.md) — Canonical autonomous pipeline (Direct context for Single mode, Orchestrated context for Batch implementers)
- [references/batch.md](references/batch.md) — Batch mode dependency graph, dispatch, and failure handling
- [references/review-gates.md](references/review-gates.md) — Two-stage review procedure (Stage 1 spec compliance, Stage 2 code quality, Stage 2.5 pattern propagation)
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog CLI commands (bee)
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
