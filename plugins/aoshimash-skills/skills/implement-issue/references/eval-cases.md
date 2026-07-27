# Evaluation Test Cases

Cases 1–15 evaluate Single mode's autonomous flow (workflow.md, Direct
context). Cases 16–21 evaluate Batch mode, 22–24 evaluate mode routing.

## Quality Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| 1 | Zero routine interactions | On a well-formed issue, no user question is asked between invocation and the recap |
| 2 | Issue fully read | Body, parent context, and any attached research comment are read; with a research comment, only the delta is re-verified |
| 3 | Settled decisions followed | Decisions recorded in the issue, its parent, repository agent instructions, or user-level config are followed without re-asking |
| 4 | Local decisions logged | Unrecorded reversible decisions are made by repository convention and appear in the PR body's Decisions & Deviations |
| 5 | Batched question + write-back | Genuinely undecidable decisions produce exactly one batched question; answers are appended to the issue's Design Decisions before implementation proceeds |
| 6 | Worktree without asking | Implementation happens in a worktree by default (or one already prepared for the run); no location question |
| 7 | Branch naming correct | `<type>/<issue-number>-<description>` convention |
| 8 | Checks loop, then record | Auto-fix once, checks loop max 3 attempts; on persistent failure the run continues with the failure recorded in the PR (Direct) or reports BLOCKED (Orchestrated) |
| 9 | Self-review visible, non-blocking | Diff reviewed max 3 rounds with a visible summary line; remaining concerns recorded in the PR, never escalated mid-run |
| 10 | Security review gates the push | Security review runs after checks/self-review and before any push; unresolved Critical/High findings block the push; the outcome appears in the PR body |
| 11 | Review-first draft PR | PR created as a draft; body leads with Decisions & Deviations and Risk Areas, maps each AC to evidence, puts mechanical change lists last; a repository PR template, when present, is the skeleton |
| 12 | Review gates run | Stage 1 then Stage 2 on every PR; failures after max fix rounds are recorded and the PR stays a draft |
| 13 | CI monitored | Checks watched after PR creation; fixable failures get a fix commit |
| 14 | Ready only when done | Draft flips to ready only after both gates and CI pass; otherwise it stays a draft with the state recorded |
| 15 | Recap complete | Recap reports PR URL and state, every decision made, every issue write-back, review-focus areas, and one line per gate |
| 16 | Plan mode opt-in only | Plan mode entered only on explicit user request, never by default |
| 17 | Closed issue detected early | Closed/merged issues caught in Phase 0 with user options (reopen / pick another / abort) |
| 18 | Parent-issue routing asked | A single referenced issue with open sub-issues triggers the batch / this-issue-only / pick-one question |
| 19 | Batch DAG correct | Platform relationship records and body declarations unioned; closed blockers excluded; cycles surfaced; parallel groups correct |
| 20 | Batch failure cascade | BLOCKED issues cascade SKIPPED to transitive dependents; independent issues continue |
| 21 | Stage 2.5 propagation offered | Rule violations in Batch mode trigger a scan of other in-flight PRs and an offer to propagate, without blocking the original issue |
| 22 | Orchestrated statuses replace questions | The Orchestrated context never asks the user: NEEDS_CONTEXT / BLOCKED / DONE_WITH_CONCERNS statuses instead; the orchestrator runs the gates and performs the ready flip |

## Single-Mode Test Cases

### Case 1: Well-formed issue, zero interactions

**Scenario**: "implement issue #12" — the issue has motivation, proposal, and
binary acceptance criteria; all needed decisions are recorded or conventional.

**Expected behavior**: no user question at any point. Worktree created without
asking, implementation and verification run straight through, a draft PR with
the review-first body appears, gates and CI pass, the PR flips to ready, and
the recap reports PR/decisions/write-backs/focus/gates.

**Criteria to test**: 1, 2, 6, 7, 11, 12, 13, 14, 15

### Case 2: Decisions settled in the parent issue

**Scenario**: A sub-issue's parent records "use REST, not GraphQL" in its
Design Decisions.

**Expected behavior**: parent fetched in 1-1; REST followed without any
question and without re-litigating; no entry needed in the PR's Decisions
section for it (it is a settled decision, not an implementation-time one).

**Criteria to test**: 2, 3

### Case 3: Genuinely undecidable decision

**Scenario**: The issue requires choosing between two storage schemas with
materially different migration costs; no store records a preference and no
convention points either way.

**Expected behavior**: exactly one batched question (this and any other
undecidable points together), each with numbered options and a recommendation.
Answers are appended to the issue's `## Design Decisions` via the platform
write-back command **before** implementation starts; the recap lists the
write-back.

**Criteria to test**: 1, 5, 15

### Case 4: Vague acceptance criteria

**Scenario**: "issue #45 を実装して" — good motivation/proposal, but AC says
"it should work well".

**Expected behavior**: concrete binary criteria are derived from the
motivation and proposal without asking; they appear in the PR's AC → Evidence
section. Only if the intent itself is ambiguous does it join the batched
question.

**Criteria to test**: 1, 2, 11

### Case 5: Checks still failing after 3 attempts

**Scenario**: A test failure survives the auto-fix pass and 3 fix attempts.

**Expected behavior**: no user escalation. The failure and what was tried are
recorded under Risk Areas; the run continues to the PR, CI fails, the PR stays
a draft, and the recap flags it prominently.

**Criteria to test**: 8, 14, 15

### Case 6: Self-review finds an ambiguous concern

**Scenario**: Self-review surfaces a business-rule edge the issue does not
address, after the batched-question window has passed.

**Expected behavior**: resolved by convention if one applies (logged under
Decisions), otherwise recorded under Risk Areas for the reviewer; the visible
`Self-review complete: …` line is printed; the run does not stop.

**Criteria to test**: 4, 9

### Case 7: Security review finds a Critical issue before push

**Scenario**: The pending diff contains a hard-coded credential.

**Expected behavior**: the security review (run after checks and self-review,
before any push) catches it; the finding is fixed and the review re-run before
anything is pushed. If it cannot be resolved in 2 rounds, nothing is pushed
and the run stops with a report. The review outcome appears in Gate Results.

**Criteria to test**: 10

### Case 8: Review gate fails past its fix rounds

**Scenario**: Stage 2 keeps finding a Critical issue after 2 fix rounds.

**Expected behavior**: the findings are recorded in Risk Areas and Gate
Results, the PR remains a draft, and the recap's review-focus areas lead with
them. No mid-run user question.

**Criteria to test**: 12, 14, 15

### Case 9: CI catches what local checks missed

**Scenario**: Local checks pass; CI fails on a stricter rule.

**Expected behavior**: failure investigated, fix commit pushed (max 1 round),
CI re-watched; the ready flip happens only after CI is green.

**Criteria to test**: 13, 14

### Case 10: Repository defines a PR template

**Scenario**: The repository has `.github/PULL_REQUEST_TEMPLATE.md`.

**Expected behavior**: the template is the skeleton — its sections filled,
review-first content mapped into semantically matching sections, unmatched
sections appended after the template body. The recap still carries the
decisions-first reading path.

**Criteria to test**: 11, 15

### Case 11: User explicitly asks for a plan gate

**Scenario**: "issue #50 を実装して。まずプランをレビューさせて"

**Expected behavior**: the explicit request makes plan mode (or a plan
presentation) opt-in for this run; without such a request, no plan is ever
presented for approval.

**Criteria to test**: 16

### Case 12: Already-closed issue

**Scenario**: "implement issue #15" — #15 is closed.

**Expected behavior**: detected in Phase 0; the user chooses reopen / pick
another / abort. This is an anomaly gate, not a routine interaction.

**Criteria to test**: 17

### Case 13: Cross-platform (Backlog issues + GitHub PRs)

**Scenario**: "PROJ-42 を実装して" with Backlog as tracker, GitHub as host.

**Expected behavior**: issue fetched via `bee`, status set to In Progress
after decisions are resolved, draft PR created via `gh`, decision write-backs
posted as Backlog comments, PR link commented on the issue, ready flip via
`gh pr ready`.

**Criteria to test**: 5, 11, 14, 15

### Case 14: Research comment attached

**Scenario**: The issue's parent carries a research comment from the
create-issue Design Flow, dated three weeks ago.

**Expected behavior**: the comment is read first; only the delta since its
date is re-verified against the current code instead of re-researching from
scratch.

**Criteria to test**: 2

### Case 15: GitLab project

**Scenario**: "implement issue #7" in a GitLab-hosted project.

**Expected behavior**: platform detected from the remote; draft MR created
with `glab mr create --draft`; ready flip with `glab mr update --ready`;
write-backs via `glab issue update --description`.

**Criteria to test**: 6, 11, 14

## Batch Mode Test Cases

### Case 16: Simple linear batch

**Input:** Parent issue #100 with 3 sub-issues (#101 → #102 → #103, linear).

**Expected behavior**: DAG built from platform records ∪ body declarations;
issues executed in order, each in its own worktree, each producing a draft PR;
the orchestrator runs both gates per issue and flips each PR to ready when its
gates and CI pass; summary table accurate.

**Criteria to test**: 19, 22

### Case 17: Parallel batch

**Input:** 4 sub-issues: #201, #202 independent; #203 ← #201, #204 ← #202.

**Expected behavior**: two groups; group members dispatched in parallel where
separate agent instances exist, sequentially otherwise; no worktree conflicts;
identical DAG semantics either way.

**Criteria to test**: 19, 22

### Case 18: Failure cascading

**Input:** #301 fails its checks after 3 attempts; #302 ← #301, #303 ← #302,
#304 independent.

**Expected behavior**: #301 reports BLOCKED (no user question), #302/#303
marked SKIPPED, #304 completes; batch continues; blocked worktree kept for
debugging.

**Criteria to test**: 8, 20, 22

### Case 19: Spec-compliance catch in batch

**Input:** #401's AC requires pagination; the implementation omits it.

**Expected behavior**: Stage 1 FAIL → implementer re-invoked → fix pushed →
re-review PASS → Stage 2 runs → PR flipped to ready only after both stages and
CI pass.

**Criteria to test**: 12, 14, 22

### Case 20: Manual issue list

**Input:** "implement these issues #501, #502, #503" (no parent).

**Expected behavior**: dependencies parsed from platform records and bodies;
normal batch flow.

**Criteria to test**: 19

### Case 21: Stage 2.5 pattern propagation

**Input:** Stage 2 flags a `rule-violation-instance` while 3 issues are in
flight.

**Expected behavior**: other in-flight PR diffs scanned for the pattern; user
offered Apply to all / Select / Skip; propagation failures do not block the
original issue.

**Criteria to test**: 21

## Mode-Routing Test Cases

### Case 22: Parent detection on "implement issue #N"

**Scenario**: #40 has 3 open sub-issues.

**Expected behavior**: sub-issues detected in Phase 0; the user chooses batch
(recommended for 2+) / only this issue / pick one. This scope question is
asked even though Single mode itself is autonomous.

**Criteria to test**: 18

### Case 23: Single-mode gate results in the recap

**Scenario**: A standalone issue implemented in Single mode; Stage 1 finds and
fixes one AC miss.

**Expected behavior**: main agent runs both gates itself, fixes and pushes
directly; Stage 2.5 not run; the recap's gate lines show the fix round; ready
flip after gates and CI pass.

**Criteria to test**: 12, 14, 15, 22

### Case 24: Parent issue, user picks "only this issue"

**Scenario**: #60 has 2 open sub-issues, but the user wants #60 itself.

**Expected behavior**: after the routing question, #60 proceeds through the
normal autonomous Single flow; sub-issues untouched.

**Criteria to test**: 1, 18

---

## Evaluation Log

### 2026-03-05 — Initial evaluation

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (6/6) | All criteria covered by existing instructions |
| 2 | Pass (6/6) | Multi-file plan structure and convention checks adequate |
| 3 | Pass (3/3) | Fixed: added guidance to propose concrete criteria for vague acceptance criteria |
| 4 | Pass (3/3) | Fixed: added incremental implementation guidance when user declines splitting |
| 5 | Pass (3/3) | GitLab detection and MR format covered by platform guide |
| 6 | Pass (3/3) | Fixed: added existing branch detection step in codebase analysis |

**Issues found and fixed:**
1. workflow-plan.md Step 1: Changed "ask the user" to "propose concrete criteria" for vague acceptance criteria
2. SKILL.md Principle 3: Added guidance for incremental implementation within a single PR
3. workflow-plan.md Step 2: Added step 6 for detecting existing branches related to the issue

### 2026-03-05 — Second evaluation (expanded criteria & cases)

Criteria expanded from 10 to 14. Cases expanded from 6 to 8.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Simple flow covers all criteria including location choice, checks |
| 2 | Pass (8/8) | Design decision step, check loop, AI review loop all covered |
| 3 | Pass (3/3) | Vague criteria handling unchanged, still adequate |
| 4 | Pass (3/3) | Scope control unchanged, still adequate |
| 5 | Pass (4/4) | GitLab flow with new location choice covered |
| 6 | Pass (3/3) | Existing branch detection unchanged, still adequate |
| 7 | Pass (2/2) | New case: check loop max 3 + escalation with options verified |
| 8 | Pass (2/2) | New case: AI review escalation with options + recommendation verified |

No issues found. All new steps (design decisions, check loop, AI review loop, escalation) are adequately covered by the current instructions.

### 2026-03-08 — Post plan-approval-flow change (Refs #22)

Replaced `EnterPlanMode`/`ExitPlanMode` with text output + `AskUserQuestion` (Approve/Request changes/Abort). This session itself used the new flow to verify it works.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Plan presented as text, approved via AskUserQuestion — flow completed to PR |
| 2 | Pass (8/8) | Design decision (approach choice) resolved via AskUserQuestion before plan |
| 3 | Pass (3/3) | Vague criteria handling unaffected by this change |
| 4 | Pass (3/3) | Scope control unaffected by this change |
| 5 | Pass (4/4) | Platform detection unaffected by this change |
| 6 | Pass (3/3) | Existing branch detection unaffected by this change |
| 7 | Pass (2/2) | Check loop unaffected by this change |
| 8 | Pass (2/2) | AI review escalation unaffected by this change |
| 9 | Pass (8/8) | Cross-platform flow unaffected; plan approval via AskUserQuestion compatible |
| 10 | Pass (5/5) | Issue listing flow unaffected; plan approval via AskUserQuestion compatible |

**Key verification:** This session (implementing #22) served as a live test of the new AskUserQuestion-based approval flow. Plan was presented as text, user approved via AskUserQuestion, and implementation proceeded through to PR creation without abandonment.

### 2026-03-14 — Added closed-issue early detection (Refs #28)

Added Phase 0 Step 4 to check issue state before proceeding. Added criterion #15 and Case 11.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Unaffected; open issues skip the new state check |
| 2 | Pass (8/8) | Unaffected by Phase 0 change |
| 3 | Pass (3/3) | Unaffected by Phase 0 change |
| 4 | Pass (3/3) | Unaffected by Phase 0 change |
| 5 | Pass (4/4) | Unaffected by Phase 0 change |
| 6 | Pass (3/3) | Unaffected by Phase 0 change |
| 7 | Pass (2/2) | Unaffected by Phase 0 change |
| 8 | Pass (2/2) | Unaffected by Phase 0 change |
| 9 | Pass (8/8) | Unaffected by Phase 0 change |
| 10 | Pass (5/5) | Unaffected by Phase 0 change |
| 11 | Pass (1/1) | New case: closed issue detected in Phase 0, user presented with reopen/pick another/abort options |

No issues found. The new step is a simple guard clause in Phase 0 that only triggers for closed/merged issues, so all existing cases remain unaffected.

### 2026-03-14 — Other free-text handling (Refs #29)

Added guidance in workflow.md sections 1-3 and 1-6 to treat "Other" free-text as the chosen approach. Added criterion 16 and cases 12-13.

| Case | Result | Notes |
|------|--------|-------|
| 2 | Pass (8/8) | Design decision flow unaffected; new "Other" guidance is additive |
| 3 | Pass (3/3) | Vague criteria handling unaffected by this change |
| 12 | Pass (3/3) | New case: "Other" free-text in design decision treated as chosen approach, no re-presentation of options |
| 13 | Pass (2/2) | New case: "Other" free-text in plan approval treated as specific change request, plan revised directly |

No issues found. Changes are additive — existing behavior for predefined options is unchanged. New guidance only applies when user selects "Other" with free-text.

### 2026-03-22 — Auto-fix before checks and post-PR CI monitoring (Refs #39)

Added auto-fix step in §2-3 of workflow.md, regenerated-files guidance in §2-2, post-PR CI monitoring in §3-2 of workflow.md and §4 of SKILL.md Phase 3. Added platform-specific CI commands to platform-github.md and platform-gitlab.md. Added criteria #17-18 and cases 14-15.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Auto-fix step is skipped when not defined; post-PR CI monitoring is platform-agnostic |
| 2 | Pass (8/8) | Existing check loop and design decision flows unaffected |
| 3 | Pass (3/3) | Vague criteria handling unaffected |
| 4 | Pass (3/3) | Scope control unaffected |
| 5 | Pass (4/4) | GitLab now has `glab mr checks` in platform guide; MR flow unaffected |
| 6 | Pass (3/3) | Existing branch detection unaffected |
| 7 | Pass (2/2) | Check loop escalation unaffected |
| 8 | Pass (2/2) | AI review escalation unaffected |
| 9 | Pass (8/8) | Cross-platform flow unaffected; CI monitoring applies to GitHub code hosting |
| 10 | Pass (5/5) | Issue listing flow unaffected |
| 11 | Pass (1/1) | Closed issue detection unaffected |
| 12 | Pass (3/3) | "Other" free-text handling unaffected |
| 13 | Pass (2/2) | Plan revision flow unaffected |
| 14 | Pass (2/2) | New case: auto-fix runs before check loop, reducing loop iterations |
| 15 | Pass (2/2) | New case: post-PR CI monitored, fixable failures addressed before returning PR URL |

No issues found. Changes are additive and localized to §2-2, §2-3, and §3-x of workflow.md. Existing behavior unchanged for projects that don't define auto-fix commands or CI.

### 2026-07-05 — Merged run-sprint into implement-issue

Merged run-sprint's batch execution model (dependency graph, worktree-per-issue parallel dispatch, two-stage review with pattern propagation) into implement-issue as "Batch mode". Added criteria 19-23 and cases 16-24 (16-21 renumbered from run-sprint's 6 cases, 22-24 new for parent-issue detection and mode routing). Case numbering for 1-15 preserved from the original implement-issue log above.

### 2026-07-10 — Capability-based gates and plan-mode notes (Refs #61)

Converted the interactive surface to agent-neutral capability terms so any
spec-compliant agent can follow it. Every `AskUserQuestion` gate site (Phase 0
routing, design decisions, plan approval, check/self-review escalations,
Single-mode review-gate escalations, the Stage 2.5 pattern-propagation prompt,
and the batch dependency-graph approval) now asks the user to choose via the
**User choice** capability, referencing the new Environment Adaptation section
in SKILL.md. Plan-mode instructions
(`EnterPlanMode`/`ExitPlanMode`) became "On Claude Code specifically" conditional
notes. The Execution Modes table's Interactive column now names a "user choice
gate" instead of `AskUserQuestion`. Subagent/batch wording is intentionally
unchanged (follow-up #66), so `references/batch.md` still has 2 bare user-choice
sites. Earlier Evaluation Log entries keep their original tool names as a
historical record, not as instructions.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (9/9) | Location choice and plan approval now via the user-choice capability; questions and options unchanged |
| 11 | Pass (1/1) | Closed-issue options presented via a user choice; wording aligned |
| 22 | Pass (2/2) | Parent-issue routing question presented via a user choice; wording aligned |
| 23 | Pass (1/1) | Single-mode gate escalations reference the user-choice capability |

No behavioral change: each gate asks the same question with the same options;
only the mechanism is now described as a capability. Verified by grep that no
bare `AskUserQuestion`/`EnterPlanMode`/`ExitPlanMode` instruction remains in the
four modified files outside the Environment Adaptation section, the "On Claude
Code specifically" notes, and the historical Evaluation Log entries above.

### 2026-07-10 — Agent-instance fallback and neutral worktree path (Refs #66)

Made Batch mode and the review gates runnable — degraded but correct — on agents
without separate-agent-instance support, and moved the worktree location off the
product-specific `.claude` directory to a neutral `.worktrees/`:

- `batch.md` states the execution model up front: dispatch a whole dependency group
  as separate agent instances in parallel where supported, otherwise implement each
  group's issues **sequentially in dependency order** in the current context. The DAG,
  review gates, and failure cascade are unchanged; only wall-clock parallelism is lost.
  The 2 deferred bare user-choice sites (cycle resolution in B1-2, plan approval in
  B1-3) now reference the User choice capability, closing the gap left by #61.
- `review-gates.md` adds a "Reviewer Dispatch" note: run each reviewer as a separate
  agent instance where available, otherwise self-review and mark the gate's real
  verdict `SELF-REVIEWED (no independent reviewer available)`. The marker rides on the
  verdict — it does not replace it — so the fix routing is unchanged.
- All `git worktree` commands (workflow.md, batch.md, platform-github/gitlab/backlog.md)
  now use `.worktrees/` with a `.git/info/exclude` guard, so the ignore stays local to
  the clone and never lands in a user PR.
- Subagent/Task-tool vocabulary replaced with "separate agent instance" per AGENTS.md.
  SKILL.md's unused **Background execution** capability row was removed (nothing in the
  skill runs background commands).

Consistency edits in this file, outside the historical log: Cases 17 and 23 now use neutral
"agent instance" wording, and Case 19 drops the stray "subagent" qualifier ("Implementer
subagent fixes" → "Implementer fixes").

| Case | Result | Notes |
|------|--------|-------|
| 16 | Pass | Linear batch runs identically whether parallel or sequential; worktree path now `.worktrees/` |
| 17 | Pass | Parallel path unchanged where separate agent instances are available; sequential fallback preserves group-then-dependency order |
| 18 | Pass | Failure cascade (BLOCKED → SKIPPED dependents) is identical in both execution models |
| 19 | Pass | Two-stage review runs per issue; reviewer falls back to the `SELF-REVIEWED` marker when no separate instance is available |

No behavioral change for environments with separate agent instances (e.g. Claude Code):
parallel dispatch, worktree isolation, and the review gates work exactly as before — only
the worktree directory moved. Verified by grep that no product-specific `.claude` worktree
path remains anywhere under the skill directory.

### 2026-07-16 — Align with the reader-agnostic issue axis (AGENTS.md "Issue Skill Design Axis")

create-issue no longer emits Implementation Approach sections or Files tables in
issue bodies — issues now carry why/what plus recorded design decisions, and
implementation planning is this skill's job at implementation time. Aligned the
references that assumed the old sub-issue format:

- `workflow.md` 1-1 adds a **Parent context** step: when the issue references a
  parent (`Parent: #N` or platform link), fetch the parent and read its
  Background, Design Decisions, and Task Overview as shared context. Under the
  old format each sub-issue was self-contained via Implementation Approach;
  under the new one, shared decisions live in the parent.
- `workflow.md` 1-3 (both modes): decisions already recorded in the issue or its
  parent are settled — Interactive mode does not re-ask the user; Autonomous
  mode follows them and only falls back to project conventions for decisions
  not recorded. The "Implementation Approach section if present" fallback is
  replaced accordingly (Execution Modes table row 1-3 and the 1-3 Autonomous
  note).
- `batch.md` B2-2: the implementer instruction set now includes the parent
  issue's body when the batch source is a parent issue.
- `review-gates.md` Stage 1: reviewer context includes the parent issue's body
  when one exists; criterion 5 reworded from "Approach matches" to "Decisions
  honored" (recorded design decisions/constraints are followed).

No changes to the plan/implement/PR pipeline itself — drafting the
implementation plan (Files to Change, approach, edge cases) at implementation
time is exactly the division of responsibility the axis prescribes.

Also added a **Model selection** capability (SKILL.md Environment Adaptation)
and a "Reviewer model" recommendation (review-gates.md Reviewer Dispatch,
referenced from batch.md B2-3): where the environment supports per-instance
model selection, run reviewers on a model at least as capable as — ideally more
capable than — the implementer's. Since issues carry no implementation detail,
the implementer derives the plan itself; a stronger reviewer is the cheapest
guard against derivation errors when implementers run on a faster model. The
fallback (no model selection) runs everything on the session default with the
workflow unchanged. Full eval re-run pending.

### 2026-07-26 — Read GitHub relationships from structured JSON fields (follow-up to #84)

`gh issue view --json` / `gh issue list --json` now expose `parent`, `subIssues`,
`subIssuesSummary`, `blockedBy`, and `blocking` as first-class fields. The GitHub guide
predated this: it read sub-issues through the REST `sub_issues` endpoint and dependencies
by parsing `Blocked by: #N` out of issue bodies ("check platform-level sub-issue blocking
if available" — with no field named). Neither was broken; both were the weaker option.

Verified before writing, on `gh` 2.96.0 (2026-07-02):

- `gh issue view --help` and `gh issue list --help` both list all five fields under `JSON FIELDS`.
- Live against this repo: `gh issue view 83 --json number,parent,subIssues,blockedBy,blocking`
  returns `parent` = #81 and `blockedBy` = [#82] as full node objects (`id`, `number`,
  `title`, `state`, `url`). `gh issue view 81` returns `subIssuesSummary.total` = 2 with
  both children as nodes. `gh issue list --json` accepts the same relationship fields.
- Every command written into the guide was then run verbatim, `--jq` expressions included.
- Availability, per the [gh v2.94.0 release notes](https://github.com/cli/cli/releases/tag/v2.94.0)
  ("brings GitHub's advanced issue features to `gh issue create`, `edit`, `view`, and
  `list`"): fields need `gh` v2.94.0+; sub-issues work on GitHub.com and GHES 3.17+;
  `blockedBy` / `blocking` relationships require GHES 3.19+.

Changes:

- `platform-github.md` gains a **Platform-Level Issue Relationships** section — the five
  fields with their shapes, the node contents, the version/GHES availability constraints,
  how to confirm support (`gh issue view --help` fails on an unknown field rather than
  returning empty), and the two fallback triggers.
- "Detect Sub-Issues of a Parent" reads `subIssuesSummary,subIssues`; the REST `sub_issues`
  endpoint and body parsing drop to ordered fallbacks.
- "List Sub-Issues / …" uses `subIssues` for the parent case and adds `parent,blockedBy` to
  the milestone/label `gh issue list` calls, so one call per batch source yields the issue
  set and its edges. Notes that `subIssues.nodes` carries no `body`/`labels`, so a sub-issue
  batch still fetches each issue.
- "Check Dependency Links" reads `blockedBy,blocking` as primary, keeps body parsing as the
  prose fallback, and states two things the old text left implicit: only `OPEN` blockers
  become DAG edges, and the two sources must be **unioned** (a registered link and a prose
  mention can name different blockers).
- `batch.md` B1-1 renamed Parse → **Collect Dependencies** and restructured into
  primary (platform records, per-platform pointers) + fallback (body patterns), building the
  mapping from the union. The old text named no GitHub field at all.
- `SKILL.md` Batch summary step 1 corrected: it claimed platform-specific links were parsed
  "from each issue body", which was never true of the platform records and is now clearly wrong.

| Case | Result | Notes |
|------|--------|-------|
| 16 | Pass | Linear sub-issue batch: `subIssues` + `blockedBy` produce the same DAG the body scan did, without depending on the author having written `Blocked by:` |
| 17 | Pass | Parallel groups unchanged; issues with `blockedBy.totalCount` 0 land in Level 0 |
| 18 | Pass | Failure cascade untouched — B1-1 only changes how edges are collected, not the DAG or cascade semantics |
| 22 | Pass | Parent detection now one call: `subIssuesSummary.total` ≥ 1 answers "is this a parent?", `nodes[].state` filters to open children |
| 24 | Pass | "This issue only" path unaffected; the detection call fetches no sub-issue bodies |

Regression check on the fallback path: an issue whose dependency exists only as
`Blocked by: #N` prose has `blockedBy.totalCount` 0, so a structured-only reader would
drop the edge — this is why B1-1 keeps body parsing and unions rather than treating an
empty field as "no dependencies". Called out explicitly in both files.

A REST fallback for dependencies was added alongside the body fallback:
`repos/{owner}/{repo}/issues/<n>/dependencies/blocked_by` and `/blocking` both exist and
return the relationships (verified live on #83 → [{number: 82, state: "open"}]). This was
initially going to be documented as "no REST equivalent exists"; testing the endpoint
disproved that. REST reports `state` lower-case where the JSON fields report `OPEN` /
`CLOSED`, so the guide says to normalize before comparing.

`create-issue`'s `platform-github.md` was given the matching treatment in the same change —
see that skill's own evaluation log entry for the same date.

### 2026-07-27 — Autonomous Single mode rewrite (Refs #93)

Wholesale rewrite per the settled decisions in #91/#93: Single mode is now a
single autonomous flow with zero routine interactions. Criteria and cases 1–24
above were rewritten for the new flow; the entries below this one evaluate the
pre-rewrite interactive skill and are historical.

Structural changes:

- `workflow.md`: the Interactive/Autonomous Execution Modes table became
  **Invocation Contexts** — Direct (Single) and Orchestrated (Batch) run the
  same autonomous pipeline and differ only at seven divergence points. Plan
  approval, the location question, and per-decision questions are gone;
  decision resolution follows the store order (issue → parent → repository
  agent instructions → user-level config), undecidable decisions become one
  batched question whose answers are written back to the issue, and a security
  review (new step 2-6) gates the push. Phase 3 creates a draft PR with a
  review-first body and flips it to ready only after both gates and CI pass.
- `SKILL.md`: principles and description rewritten; Environment Adaptation
  gains a **Security review** capability row; plan mode is opt-in only.
- `review-gates.md`: Single-mode "ask the user" escalations replaced with
  record-in-PR + stay-draft; the flow diagram ends at the ready flip.
- `batch.md`: implementer instruction updated (draft PR, stop after CI
  monitoring at 3-3); the orchestrator now also flips PRs to ready (B2-3
  step 5).
- Platform guides: verified draft/ready/write-back/comment commands added
  (`gh` verified locally on 2.x; `glab` flags verified against the official
  CLI docs; Backlog write-backs use the already-verified comment command
  rather than unverified description-edit flags).

Plan-mode claim re-evaluation (required by #93): the old prohibition cited
accidental rejections in the plan-approval UI with no feedback path. That
claim was not re-verified against the current UI — it no longer needs to be
load-bearing: with the plan gate removed, plan mode is opt-in regardless of
UI quality, because any unrequested gate is a round trip. The skill text
therefore justifies opt-in by round-trip cost alone and no longer asserts the
UI-misfire claim.

Desk-check of the rewritten cases against the new texts:

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass | Happy path has no question site: worktree without asking (2-1), no plan gate (1-4), draft PR (3-1), ready flip (3-4), recap (3-6) |
| 2 | Pass | Parent context in 1-1; settled-decision rule in 1-3 category 1 |
| 3 | Pass | 1-3 category 3: one batched question, write-back before implementation; platform guides carry the write-back commands |
| 4 | Pass | 1-1 derives binary criteria itself; only intent-level ambiguity joins the batched question |
| 5 | Pass | 2-4 Direct: record in Risk Areas, continue; PR stays draft via 3-4; recap flags it |
| 6 | Pass | 2-5 resolves by convention or records under Risk Areas; visible summary line retained |
| 7 | Pass | 2-6 runs before any push; Critical/High blocks push in both contexts; outcome lands in Gate Results |
| 8 | Pass | review-gates.md On Failure records findings, PR stays draft, recap flags |
| 9 | Pass | 3-3 fix loop; 3-4 requires CI green |
| 10 | Pass | 3-1 template-precedence paragraph; template lookup in platform guides |
| 11 | Pass | 1-4 and SKILL.md: plan mode only on explicit request |
| 12 | Pass | Phase 0 step 4 unchanged from previous version |
| 13 | Pass | Backlog guide: status update, comment write-back, code-host draft/ready delegation |
| 14 | Pass | 1-1 research-comment paragraph: read first, re-verify delta only |
| 15 | Pass | GitLab guide: `--draft`, `--ready`, `--description` all doc-verified |
| 16–21 | Pass | Batch orchestration semantics unchanged; B2-2/B2-3 updated for draft→ready; statuses replace questions (criterion 22) |
| 22–24 | Pass | Routing and closed-issue questions retained as scope/anomaly gates |

All 24 cases pass the desk-check. This entry records a static evaluation
(instructions inspected against expected behavior); the first live run of the
autonomous flow is the session that produced this rewrite's own PR, which
followed the new pipeline (no plan gate, security review before push, draft
PR with review-first body, gates, ready flip, recap).
