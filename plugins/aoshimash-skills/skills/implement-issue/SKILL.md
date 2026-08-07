---
name: implement-issue
description: >
  Read platform issues (GitHub/GitLab/Backlog), analyze the codebase,
  implement autonomously, and open review-first pull/merge requests: draft
  PR with decisions logged in the body, two-stage review (spec compliance,
  then code quality), a pre-push security review, an automatic response to the
  repository's own bot/AI reviewers, and a flip to ready-for-review once gates,
  CI, and those reviewers are done. Implements a single issue end to
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
   the PR body (`Decisions & Deviations`). The only routine stop before the PR
   is delivered is a genuinely undecidable decision, asked as **one batched
   question** whose answers are written back to the issue before implementation
   proceeds — never ask twice. Once the PR is delivered, the decisions that were
   really rules are offered — in one batched confirmation, or none at all — for
   promotion into a durable store, so a later run does not re-decide them (see
   [references/harvesting.md](references/harvesting.md)).
3. **Review-first PRs; machines finish before humans start** — The PR is
   created as a **draft** and flipped to ready-for-review only after CI passes,
   both review-gate stages pass, and the repository's own automated reviewers
   have been responded to (detect → bounded wait → fix, push, reply → record
   what is left; see
   [references/automated-review.md](references/automated-review.md)). Human
   review comments are never auto-addressed — they go through the interactive
   respond-to-pr-review skill. The body is ordered for the reviewer: decisions
   and risk areas first, acceptance criteria mapped to verification evidence,
   mechanical change lists last. Repository PR templates, when present, take
   precedence as the skeleton.
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
   [references/batch.md](references/batch.md)). In integration mode the DAG
   advances on **merges** rather than on ready flips, so a dependent's worktree
   contains its dependency's code.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`, which can carry several questions in one round) | Numbered options as plain text; wait for the user's reply |
| **Separate agent instance** — run a task in a fresh context that has not seen this conversation | Subagent dispatch (e.g. Claude Code's Task tool) | Run sequentially in the current context; for verification, mark the result `SELF-REVIEWED` in the artifact it lands in (e.g. the PR body) |
| **Model selection** — run a separate agent instance on a chosen model | Per-instance model override (e.g. Claude Code's Task tool `model` parameter, or an agent definition's `model` frontmatter) | Run every instance on the session's default model — the implementer classification is skipped entirely rather than approximated, and the reviewer-stronger-than-implementer recommendation is unavailable |
| **Security review** — security-focused review of the pending diff | Dedicated command (e.g. Claude Code's `/security-review`) | Review the diff yourself against the checklist in [references/workflow.md](references/workflow.md) step 2-6 |
| **User-level configuration** — a durable instruction store belonging to the user, outside any repository | User-level instruction file (e.g. `~/.claude/CLAUDE.md` on Claude Code) | No such store: cross-repository preferences cannot be promoted — offer repository scope or skip (see [references/harvesting.md](references/harvesting.md) C) |
| **Skill invocation** — run another installed skill's procedure from this one | Skill dispatch by name (e.g. Claude Code's Skill tool) | Read that skill's `SKILL.md` and the reference files it points to from the installed skill directory, and follow them inline |
| **Background execution** — run long commands without blocking | Background shell (e.g. Claude Code's background Bash) | Run commands sequentially |
| **Scheduled invocation** — run this skill again later without a user present | Recurring or cron-scheduled agent runs (e.g. Claude Code's scheduled tasks) | Re-invoke manually once per session; a resumed batch re-derives its state from the tracker and git (see [references/batch-reentry.md](references/batch-reentry.md)) |

The last three are used only by Batch mode's **integration mode**. *Skill invocation* and
*background execution* serve its call into the merge-issue-prs skill
([references/batch.md](references/batch.md) B2-4). That skill performs
bounded waits — for a PR's checks to settle, and for post-merge verification on the
integration branch — and those waits happen inside whatever runs it, which is this run
wherever the invocation is inline rather than a separate process. Both waits are bounded by
a wall-clock deadline the agent owns, not by a blocking watch command; background execution
frees the agent during them, it does not supply the bound.

*Scheduled invocation* is the **repeated-invocation operating pattern**: one invocation
advances the batch as far as that session gets, and the next one re-derives where it
stopped and carries on from there — within the scope limit below (batch.md B0,
[references/batch-reentry.md](references/batch-reentry.md)). The pattern is the same
whether the repeat is scheduled or typed by hand — same batch source, one invocation per
session, until the milestone PR is ready — because nothing is persisted between sessions
either way: no state file, no session memory, only the tracker and git. Scheduling removes
the person from the loop; it is not what makes resumption work.

The two differ in **scope**, not mechanism. Which issues a batch implements is settled at
the execution-plan approval and recorded nowhere durable, so an invocation with no user
reachable advances the work an approved plan already produced — review gates on the drafts,
the merge gate, the reports — and **dispatches no new implementer**, naming instead whatever
is waiting on an approval. Since that bound is artifact evidence rather than plan
membership, an unattended run drains the group the last session dispatched and then stalls
on the next one, even though the user approved it; a batch is advanced without ever being
widened, and finishing one still takes a session with a user in it. That, and the rest of
what re-derivation cannot recover, is in batch-reentry.md's Known limits.

*Model selection* is used in **both** modes, for different things. Reviewers use it
everywhere: each one runs at least at the tier of the dispatch that produced the code it is
reviewing ([references/review-gates.md](references/review-gates.md)), which in Single mode is
the session's own model. **Implementer** tiers are Batch-only, because batch dispatch is the
one point where a model is chosen per unit of work: the orchestrator classifies each issue by
**content** — mechanical work runs cheaply, judgment-heavy work does not, and uncertainty and
the hard-exclusion classes resolve upward
([references/model-selection.md](references/model-selection.md)). Single mode classifies
nothing; its implementer is the session itself, on the model the user chose.

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
   run Stage 1 and Stage 2 review gates, monitor CI, then respond to the
   repository's automated reviewers (bounded wait, bounded fix/reply rounds,
   leftovers recorded), and flip the PR to ready only when gates, CI, and that
   response are done; otherwise it stays a draft with the unresolved state
   recorded.
4. **Harvest** — with the PR ready, offer the run's generalizable decisions for
   promotion in **one** batched confirmation: a repository convention becomes a
   separate PR against the agent instructions file, a cross-repository
   preference an append to user-level configuration. No candidates, no
   interaction — the usual outcome.
5. **Recap** — report the PR URL and state, every decision made, every issue
   write-back performed, any promotions made, the review-focus areas, and one
   line per gate — including which automated reviewers were handled and in how
   many rounds.

Former mid-run stops (plan approval, location choice, per-decision questions,
failing-check and self-review escalations) no longer exist: they either
resolved into the batched question or complete with the concern recorded in
the PR. **On Claude Code specifically:** plan mode is opt-in only — enter it
solely when the user explicitly asks for a plan gate; never by default.

## Batch Mode

Used for a parent issue's sub-issues, a milestone, a label, or a manual list.
See [references/batch.md](references/batch.md) for the full procedure.

Batch mode runs in one of two **merge modes**, chosen inside the execution-plan
approval — never as a separate gate, and never in Single mode:

- **Standard** — every worktree and PR is based on the default branch; each PR
  stops at ready for review and a human merges it.
- **Integration** — the batch creates one integration branch, bases every
  worktree and PR on it, and hands each ready PR to the **merge-issue-prs**
  skill, which owns the whole merge lifecycle. A dependency counts as satisfied
  only once its PR *merged into that branch and was not reverted*, so dependents
  finally build on their dependencies' code, and human review happens once, on
  the integration→main milestone PR that skill raises, instead of once per
  issue. Available where that skill is installed and the repository is on
  GitHub.

An integration-mode batch is **resumable across sessions**: before the dependency graph,
a fresh session re-derives where an earlier one stopped — from the tracker and git only,
since nothing else persists — and then starts the batch, resumes it, or stops (see
[references/batch-reentry.md](references/batch-reentry.md), invoked from batch.md B0).
Existing PRs, branches, and worktrees are never recreated; a body-recorded gate verdict
never substitutes for re-running the gate; a batch another session appears to be working
on is not dispatched at all; and dispatching an implementer needs an approved plan every
session, so an unattended resume advances existing PRs rather than starting new work.

**Summary:**

1. **Dependency graph** — collect dependencies from the platform's own
   relationship records (e.g. GitHub's `blockedBy` field) and, as a fallback,
   from `Blocked by` / `Depends on` / `After` declarations in each issue body;
   build a DAG from the union; detect cycles and ask the user how to resolve
   them; compute parallel execution groups (topological levels); visualize the
   plan; get approval via a user choice (see Environment Adaptation) with
   options Approve (standard) / Approve (integration mode, when available) /
   Reorder / Abort (Reorder collects dependency-graph edits and re-presents the
   plan — see batch.md B1-3). The plan shows the ordering edges integration mode
   would add for same-file collisions inside a group (batch.md B1-2), so the
   whole schedule is settled in that one approval; the integration branch is
   created or reused right after it (batch.md B1-4).
2. **Execution loop** — for each group, implement its issues, each in its own
   git worktree, executing [references/workflow.md](references/workflow.md) in
   the **Orchestrated** context (see that file's Invocation Contexts). Where
   the environment supports separate agent instances, dispatch one implementer
   per issue in parallel — where model selection also exists, each on the
   capability tier its issue's content calls for
   ([references/model-selection.md](references/model-selection.md)); otherwise
   implement sequentially in dependency order — the DAG, review gates, and
   failure cascade are identical either way.
   After each draft PR is created, the orchestrator runs the two-stage review
   gates ([references/review-gates.md](references/review-gates.md)), including
   **Stage 2.5 pattern propagation** across other in-flight PRs when a
   rule-violation is found, then the **automated review response**
   ([references/automated-review.md](references/automated-review.md)) with the
   reviewer set detected once for the whole batch, and flips the PR to ready
   when gates, CI, and that response are done. **In integration mode**, the
   group's ready PRs then go to the merge gate (batch.md B2-4), which merges,
   verifies, reverts, and defers; the batch records what it reports and never
   overrides it.
   Update the DAG as issues complete; on failure, mark the issue `BLOCKED`,
   cascade `SKIPPED` to its transitive dependents, and continue with
   independent issues. In integration mode a dependency that was deferred,
   reverted, or never merged cascades the same way — merged-into-integration is
   the only satisfied state.
3. **Summary and harvest** — in integration mode, first invoke the merge gate
   once more with the terminal-state declaration (batch.md B3): the dispatched
   issue set, a final status for each of its members, and the assertion that no
   implementer is still running — only the orchestrator can supply that, and a
   partial declaration counts as none. Then present a status table
   (issue, title, status, PR) covering DONE / DONE_WITH_CONCERNS /
   NEEDS_CONTEXT / BLOCKED / SKIPPED, plus MERGED / DEFERRED / NOT_ATTEMPTED /
   REVERTED in integration mode, where the deferred and reverted PRs are the
   human queue and merged issues stay open until the milestone PR merges;
   explain any blockers, and optionally post a summary comment on the parent
   issue. Then harvest generalizable decisions
   ([references/harvesting.md](references/harvesting.md)) **once for the whole
   batch** — a batch of ten issues still costs at most one confirmation.

## References

- [references/workflow.md](references/workflow.md) — Canonical autonomous pipeline (Direct context for Single mode, Orchestrated context for Batch implementers)
- [references/batch.md](references/batch.md) — Batch mode dependency graph, dispatch, and failure handling
- [references/batch-reentry.md](references/batch-reentry.md) — Resuming an integration-mode batch in a fresh session: the artifacts state is re-derived from, concurrent-session detection, and the idempotency rules
- [references/model-selection.md](references/model-selection.md) — Batch dispatch's content-based implementer tiers: the classification rubric, the default mapping, the classes never dispatched cheaply, and the repository override
- [references/review-gates.md](references/review-gates.md) — Two-stage review procedure (Stage 1 spec compliance, Stage 2 code quality, Stage 2.5 pattern propagation)
- [references/automated-review.md](references/automated-review.md) — Responding to repository-configured automated (bot/AI) reviewers before the draft → ready flip
- [references/harvesting.md](references/harvesting.md) — Post-PR promotion of generalizable decisions into repository agent instructions or user-level configuration
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog CLI commands (bee)
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
