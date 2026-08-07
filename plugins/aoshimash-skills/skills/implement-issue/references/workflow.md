# Workflow Detail

The canonical implementation pipeline: understand the issue, resolve decisions,
implement, verify, and deliver a review-first draft PR/MR that is flipped to
ready once the machines are done. The pipeline is **autonomous**: it runs from
invocation to report without routine user interaction. Decisions are resolved
from the decision stores or by repository convention and **logged, not asked**.

## Invocation Contexts

The same pipeline runs in one of two contexts:

- **Direct** (Single mode) — the main agent executes this workflow itself. The
  user is interrupted for exactly three reasons: the single batched question of
  step 1-3 (genuinely undecidable decisions only), an unresolvable
  Critical/High security finding (step 2-6, which blocks the push), and the
  batched harvesting confirmation of step 3-7 — which comes after the PR is
  delivered and only when the run produced generalizable decisions. Everything
  else completes with concerns recorded in the PR and surfaced in the recap.
- **Orchestrated** (Batch mode) — an implementer executes this workflow with no
  user access, coordinated by the orchestrator in [batch.md](batch.md) (as a
  separate agent instance where the environment supports one, sequentially in
  the current context otherwise). Anything Direct would ask the user becomes a
  terminal status instead.

| Divergence point | Direct | Orchestrated |
|---|---|---|
| Undecidable decision / missing critical field (1-1, 1-3) | One batched question; answers written back to the issue | Stop, report `NEEDS_CONTEXT` |
| Working environment (2-1) | Worktree by default; reuse one already prepared for this run | Always the worktree the orchestrator created |
| PR/MR base branch (3-1) | The default branch | The base branch the dispatch names — the integration branch under batch integration mode (batch.md B2-2) |
| Checks still failing after 3 attempts (2-4) | Record the failure in the PR body, continue; the PR stays draft | Stop, report `BLOCKED` |
| Unresolved Critical/High security finding (2-6) | Stop before pushing, report to the user | Stop before pushing, report `BLOCKED` |
| Review gates (3-2) | Main agent is responsible for both stages (dispatch per review-gates.md) | Skipped here — the orchestrator runs them after the implementer reports |
| Automated review response (3-4) | Main agent runs it | Skipped here — the orchestrator runs it per PR before the flip |
| Draft → ready flip (3-5) | Main agent flips after gates + CI + automated review response | Orchestrator flips after gates + CI + automated review response |
| Decision harvesting (3-7) | Main agent runs it after the flip | Skipped here — the orchestrator runs it once for the whole batch (batch.md B3-1) |
| Final report (3-8) | Chat recap | One status line to the orchestrator |

## Phase 1: Understand and Decide

### 1-1. Read the Issue

Extract from the issue body: summary, motivation, background/constraints,
proposal (desired end state), and acceptance criteria.

**Parent context.** If the issue references a parent (`Parent: #N` line or a
platform-level parent link), fetch the parent and read its Background, Design
Decisions, and Task Overview — decisions recorded there bind this task.

**Research comment.** Check the issue (and its parent) for an attached research
comment — the create-issue Design Flow persists its research findings as an
issue comment. If one exists, read it first and re-verify only the **delta**
against the current code (what changed since the comment's date) instead of
re-researching from scratch. See the platform guide for how to read comments;
if the platform's CLI does not expose comments, research fresh.

**Missing or vague critical fields** (no acceptance criteria, or criteria like
"works well" that cannot be verified): draft concrete, binary-testable
criteria yourself from the motivation and proposal. If the issue is too vague
even for that — the intent itself is ambiguous — treat it as an undecidable
decision: Direct context folds it into the batched question of 1-3;
Orchestrated context stops with `NEEDS_CONTEXT` and a specific description of
what is missing.

### 1-2. Analyze the Codebase

Investigate what the issue touches: related files and patterns, project
conventions (agent instructions, existing code), dependencies and their
constraints, test conventions, and any project commands (checks, auto-fix,
codegen).

**Existing branches**: check for branches referencing the issue number. If a
stale partial implementation exists, default to a fresh start from the default
branch and note the branch and the choice under Decisions in the PR body.

### 1-3. Resolve Decisions

Decisions are resolved in this order, and only the last category ever reaches
the user:

1. **Settled** — recorded in a decision store: the issue body, its parent's
   body (Design Decisions, Background), the repository's agent instructions,
   or user-level configuration. Follow them as written; never re-ask, never
   re-litigate.
2. **Local and reversible** — naming, choices among roughly equivalent designs,
   tactical details. Decide now: choose the option most consistent with
   existing repository conventions, and log the decision and rationale in the
   PR body's Decisions section. A constraint tied to one piece of code goes in
   a code comment; commit a lightweight ADR under `docs/adr/` only when a
   decision contradicts an existing rule or binds future work.
3. **Genuinely undecidable** — no store records it, no convention points one
   way, and the outcome materially changes the result (structural shape,
   irreversibility, cross-task consistency).
   - **Direct**: collect **all** such decisions and ask them as **one batched
     question** (user choice, numbered options with a recommendation per
     decision). Immediately append the answers to the issue's `## Design
     Decisions` section (create it if absent) using the platform guide's
     write-back command, then proceed. This is the only **routine** stop before
     the PR is delivered — an unresolvable security finding can still halt the
     push (2-6) — and the harvesting confirmation of 3-7 comes after it.
   - **Orchestrated**: stop and report `NEEDS_CONTEXT` listing the decisions.

When in doubt whether a decision is undecidable or merely local, treat it as
local and log it — the PR review is the safety net.

### 1-4. Plan Internally

Form an implementation plan before editing: files to change and how, new
dependencies, edge cases, how each acceptance criterion will be verified, and
what is explicitly out of scope. The plan is working state, not a deliverable —
there is no approval gate and it is not presented for review. Its visible
residue is the PR body: the AC → evidence mapping and the Decisions section.

**On Claude Code specifically:** plan mode is opt-in only — enter it solely
when the user explicitly asked for a plan gate in this run; never by default.
An unrequested plan gate converts an autonomous run back into a round trip.

## Phase 2: Implement and Verify

### 2-1. Prepare the Working Environment

**Direct**: work in a git worktree by default — do not ask. If the session was
already started on a branch or worktree prepared for this issue (e.g. by the
host environment), use it as-is and note the branch name under Decisions if it
deviates from the naming convention below.

```bash
git fetch origin
grep -qxF '.worktrees/' .git/info/exclude 2>/dev/null || echo '.worktrees/' >> .git/info/exclude
git worktree add .worktrees/<branch-name> -b <branch-name> origin/<default-branch>
cd .worktrees/<branch-name>
```

**Orchestrated**: `cd` into the worktree the orchestrator already created —
never create one.

Branch naming: `<type>/<issue-number>-<short-description>` — type from the
issue's label or content (`fix/`, `feat/`, `refactor/`, `chore/`).

### 2-2. Update Issue Status

If the issue tracker supports status updates (e.g. Backlog), set the issue to
"In Progress" now — after decisions are resolved, before code changes. See the
platform guide.

### 2-3. Implement

Implement the plan. Guidelines:

- **Follow existing patterns** — match surrounding code in naming, structure,
  and idiom.
- **Stay in scope** — no refactoring or "improvements" beyond the issue.
- **No over-engineering** — the simplest solution that satisfies the
  acceptance criteria.
- **Secure by default** — validate input, avoid injection, handle errors at
  system boundaries.
- **Regenerate derived files** — if sources that drive code generation changed
  (schemas, protos, OpenAPI), run the project's regeneration command before
  checks.

### 2-4. Run Project Checks (loop, max 3 attempts)

Run the auto-fix commands the project defines (formatters, linters with
`--fix`) once, then loop the project's check suite (tests, lint, type check,
build): run, fix failures, re-run — until green or 3 attempts are spent.

**Still failing after 3 attempts** — **Direct**: stop fixing, record exactly
what fails and what was tried in the PR body's Risk Areas, and continue; CI
will fail, so the PR remains a draft and the recap flags it prominently.
**Orchestrated**: stop and report `BLOCKED` with the failing checks and
attempts.

If the project defines no checks, note that in the PR body.

### 2-5. Self-Review (loop, max 3 rounds)

Review the full diff (`git diff`) for: logic errors and edge cases, missing
error handling at boundaries, drift from the issue's decisions and acceptance
criteria, and convention violations. Fix what has a clear correct solution,
re-run checks after fixes, re-review. A concern that would previously have
been escalated (ambiguous business rule, UX trade-off) is resolved by
convention like any local decision and logged — or, if truly undecidable, it
belongs in 1-3's batched question, which has already passed: record it under
Risk Areas instead and let the reviewer rule.

After the loop, output one visible line:

```
Self-review complete: N round(s), N issue(s) found, N fixed, N remaining
```

### 2-6. Security Review (before any push)

The push is the leak boundary — a secret or exploitable defect that leaves the
machine cannot be recalled by a later fix commit. After checks and self-review
pass and **before pushing anything**, run a security review of the pending
changes (see the Security review capability in SKILL.md's Environment
Adaptation; on Claude Code, run `/security-review`). At minimum it must cover:
secrets or credentials in the diff, injection, authn/authz changes, data
exposure, unsafe deserialization, and SSRF.

- **Critical/High findings**: fix, re-run checks, re-review — max 2 rounds. If
  a Critical/High finding remains, **do not push**: Direct reports it to the
  user and stops; Orchestrated reports `BLOCKED`.
- **Lower-severity findings**: fix or record under Risk Areas.
- Record the outcome (tool used, findings, resolution) — it goes in the PR
  body's Gate Results.

### 2-7. Commit

Conventional Commit referencing the issue:

```
<type>: <description>

<what changed and why>

Refs #<issue-number>
```

Subject under 72 characters; use `Closes #N` only in the PR body, never the
commit.

## Phase 3: Pull/Merge Request

### 3-1. Push and Create a Draft PR/MR

Detect the code hosting platform from the git remote (it may differ from the
issue tracker — e.g. Backlog issues + GitHub PRs), push the branch, and create
the PR/MR **as a draft** (see the platform guide; title under 70 characters,
no Conventional Commit prefix). Draft status is the "machines still working"
signal: it is removed only in 3-5.

**Base branch.** Default-branch base unless the dispatch names another one.
**Orchestrated**: use the base branch given in the dispatch — under batch integration
mode that is the batch's integration branch, and targeting the default branch instead
puts the PR outside the merge gate's candidate set entirely. The closing reference stays
in the body either way; on a non-default base the platform ignores it (see the platform
guide's "Link PR to Issue"), and it is still what attributes the PR to its issue.

**PR/MR body — ordered for the reviewer.** Human judgment concentrated at the
PR is the trade for autonomous execution, so the body leads with what needs
judgment and ends with what doesn't:

```markdown
## Decisions & Deviations
<implementation-time decisions with rationale; deviations from the issue text;
"None" if none — the section is always present>

## Risk Areas
<what deserves reviewer attention: unresolved concerns, failing checks,
subtle changes; "None" if none>

## Acceptance Criteria → Evidence
- [x] <criterion> — <how it was verified: test name, command output, diff ref>

## Gate Results
- Self-review: <N rounds, N found, N fixed>
- Security review: <tool, findings, resolution>
- Spec compliance (Stage 1): <pending → result>
- Code quality (Stage 2): <pending → result>
- CI: <pending → result>
- Automated review: <pending → reviewer(s), N round(s), M addressed, K remaining | none configured>

## Changes
<mechanical file-level list — last, it needs the least judgment>

Closes #<issue-number>
```

**Repository PR/MR templates take precedence.** When the repository defines a
template, the template is the skeleton: fill its sections, map the content
above into semantically matching sections, and append whatever has no match as
clearly delimited sections after the template body. Review-first ordering
yields to template order; the chat recap always carries the decisions-first
reading path regardless.

### 3-2. Review Gates

**Direct**: run Stage 1 (spec compliance) then Stage 2 (code quality) per
[review-gates.md](review-gates.md), fixing and pushing between rounds. Update
the Gate Results section as each stage completes.

**Orchestrated**: skip this step — the orchestrator runs the gates and
re-invokes this implementer for fix rounds. Continue with 3-3 and 3-6, then
report (3-8); never perform the 3-4 automated review response, the 3-5 flip, or
the 3-7 harvesting.

### 3-3. Monitor CI

Watch the PR/MR checks (see the platform guide). On failure: investigate, push
a fix commit if fixable (max 1 fix round), re-watch. If not fixable or CI is
not configured, record it under Risk Areas and in Gate Results.

### 3-4. Automated Review Response

The repository's own automated reviewers are machines too, so they finish
before the human starts: detect them, wait (bounded) for their findings,
address them (fix, push, reply) for a bounded number of rounds, and record
what is left. See [automated-review.md](automated-review.md) for the full
procedure. The contract it holds to:

- **Automated reviewers only.** Human review comments are never auto-addressed
  — they go through the interactive respond-to-pr-review skill. Ambiguous
  authorship counts as human.
- **Bounded everywhere.** Detection is a few reads; waiting has a completion
  signal or a wall-clock cap; fix/reply rounds max out at 2. With no automated
  reviewer configured, the step records that and ends immediately.
- **Nothing silently dropped.** Every collected finding gets a reply, and
  findings left after the last round are recorded in the PR body (Risk Areas)
  rather than chased.
- **Findings are decided, not obeyed.** Each one is resolved by the same rules
  as any implementation-time decision (1-3) and logged the same way; a bot
  does not reopen a settled decision.

**Orchestrated**: skip this step — the orchestrator runs it per PR before the
flip (batch.md B2-3).

### 3-5. Flip Draft to Ready

Only when **both** review-gate stages pass, CI is green, **and** the automated
review response of 3-4 has completed, mark the PR/MR ready for review (see the
platform guide). If a gate or CI never passes within its fix rounds, the PR
**stays a draft** with the unresolved state recorded in Gate Results / Risk
Areas — a draft with honest concerns beats a "ready" PR that isn't. Automated
review findings recorded as remaining do **not** hold the draft (see
[automated-review.md](automated-review.md) F).

**Orchestrated**: the orchestrator performs this flip after it runs the gates
and the automated review response (see batch.md B2-3).

### 3-6. Comment on the Issue

If the issue tracker supports comments (e.g. Backlog, or cross-platform setups
where the PR is not auto-linked), post the PR/MR link on the issue.

**Orchestrated, batch integration mode**: post it. A closing keyword in a PR that targets
a non-default branch creates no link (see the platform guide's "Link PR to Issue"), so the
comment is the issue's own record of which PR implements it. What happens to that PR
afterwards is reported by the orchestrator, not here (batch.md B2-4).

### 3-7. Harvest Generalizable Decisions

The run's decisions are already logged where a reviewer of *this* issue will see
them; the ones that are really rules belong somewhere a *later run* will see
them. Scan them, and offer whatever generalizes for promotion into a durable
store. See [harvesting.md](harvesting.md) for the full procedure. The contract it
holds to:

- **Silent by default.** Most runs produce no candidates, and the step then
  produces nothing at all — no question, no recap section.
- **Gated on a delivered PR.** It runs only when the PR/MR reached ready for
  review; a run that ends with a draft skips it with one recap line.
- **Exactly one batched confirmation**, covering every offered candidate, with
  the exact rule text and destination path in the question. Nothing is written
  to a durable store without it, and a decline is written nowhere.
- **Repository scope means a separate PR/MR**, branched from the default branch
  in its own worktree, touching only the agent instructions file. The
  implementation PR/MR is never the vehicle for a rules change.
- **User scope means an append** to the user's own agent configuration, reported
  verbatim in the recap.

**Orchestrated**: skip this step — the orchestrator runs it once for the whole
batch (batch.md B3-1).

### 3-8. Report

**Direct — chat recap**, the session-side report. It must contain:

- **PR**: URL and state — ready for review, or still draft and why.
- **Decisions**: every implementation-time decision made (the PR body has the
  rationale; the recap lists them).
- **Issue write-backs**: every write performed against the issue (Design
  Decisions appended, status changes, comments).
- **Promotions** (3-7): each promoted rule and where it went — the promotion
  PR/MR URL, or the user-level file path with the exact appended text — plus
  candidates skipped, already recorded, or not offered. Omitted entirely when
  there were no candidates.
- **Review focus**: the few places a human reviewer should look first.
- **Gates**: one line per gate — self-review rounds/findings, security review,
  Stage 1, Stage 2, CI, and automated review (which reviewers were handled, how
  many rounds, what remains — or that none were configured).

**Orchestrated — one status line** to the orchestrator, plus the PR/MR URL or
failure details. **The return is bounded at one status token, one URL, and at
most 10 further lines** ([context-budget.md](context-budget.md) C1) — the
orchestrator accumulates one of these per issue for the whole batch, while
everything longer already has a durable home: the PR body for a run that pushed,
the kept worktree for a `BLOCKED` stop that did not. Name where it is instead of
reproducing it; a `NEEDS_CONTEXT` return lists one line per missing decision. The
statuses:

- `DONE` — draft PR created, CI passing; gates not yet run (orchestrator runs them)
- `DONE_WITH_CONCERNS` — draft PR created with concerns recorded (unfixable CI
  failure, remaining self-review issue)
- `NEEDS_CONTEXT` — undecidable decision or missing critical field (1-1, 1-3)
- `BLOCKED` — checks failed after retries (2-4) or unresolved Critical/High
  security finding (2-6)
