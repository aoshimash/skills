# Re-entry: Resuming a Batch in a Fresh Session

A batch can outlive the session that started it — an interruption, a context or session
limit, or a deliberate one-session-at-a-time schedule all end with the batch half-done
and the session's own picture of it gone. This file is how the **next** session rebuilds
that picture, and it rebuilds it from the tracker and git alone, because that is all
there is: nothing in this pipeline writes batch state anywhere else.

Invoked from [batch.md](batch.md) Phase B0, which states when it runs and what it hands
back. This file is the procedure.

**What it resumes is an integration-mode batch.** The artifacts re-entry keys on — an
integration branch, its merge history, and the pull requests based on it — exist only in
that mode, so a standard-mode batch has nothing here to re-derive. The **probe** of R2
still runs in every batch-mode run (B0), because a session cannot know which mode an
earlier one chose without looking; where it finds those artifacts but integration mode is
no longer available, the outcome is a Stop.

**R1–R7 are read-only.** Nothing is created, pushed, dispatched, or invoked until the
state is established; a run that stops in R2 or R3 has written nothing at all. R8 is
where the session rejoins the pipeline and starts acting.

**Steps are ordered by cost and by what stops the run.** R1 and R2 are a handful of list
reads and carry every stop condition, so a batch that must not continue stops before
anything expensive runs. The dependency graph (R4) is the costly step — B1-2's
same-file analysis iterates over the codebase to a fixed point — and it runs only once
the run is known to be continuing.

## The artifacts, and what each one establishes

The left column is the whole list of what re-entry may read. Anything not on it is not
batch state.

| Artifact | How it is read | What it establishes |
|---|---|---|
| The batch source — a parent issue's sub-issues, a milestone, a label, or the explicit list | platform guide, "List Sub-Issues / Issues by Milestone / Issues by Label" | The issue set this batch covers (R1) |
| Remote refs under `integration/` | platform guide, "Re-derive a Batch's State (re-entry)" | Which integration branch this batch is on, when its name is not computable (R2) |
| Whether that branch exists, and how far ahead of / behind the default branch it is | platform guide, "Create Branch" | Whether a batch was ever started under this name, and what a reused branch already carries |
| The branch's commit history, freshly fetched | platform guide, "Confirm a PR Merged into the Integration Branch — and Was Not Reverted" | Which merges landed, and which of them were reverted |
| Every PR whose **base** is the integration branch, in any state — `state`, `isDraft`, `headRefName`, `labels`, `createdAt`, `mergeCommit`, `body` | platform guide, "Re-derive a Batch's State (re-entry)" | Per-issue progress: whether an issue has a PR at all, whether it merged, whether it was reverted, and how many gate fix rounds have been spent on it |
| The milestone PR — the integration branch as **head**, the default branch as base — including its `## Needs Human Attention` section | same | Whether the milestone is still running, under review, abandoned, or finished, and whether an escalation is outstanding against the branch |
| Head commit times of the per-issue branches in this batch's naming | same | Whether another session has written recently (R3) |
| Each issue's `blockedBy` links, and the dependency declarations in its body | [batch.md](batch.md) B1-1 | The DAG — rebuilt from scratch, never remembered (R4) |
| Comments on each merged issue | platform guide, "Read Issue Comments" | Whether B2-4's per-merge comment was already posted for that merge commit |

**One PR list read serves R2, R3, R5 and R6.** It is the same
`gh pr list --base <branch> --state all` query with the fields above; read it once per
run and reuse the result. "Re-derived on every run" means nothing is carried between
*runs*, not that the same call is repeated within one.

### What is not batch state, however much it looks like it

- **A gate verdict recorded in a PR body.** The two review stages are internal to the run
  — [review-gates.md](review-gates.md) says their findings "exist only in this session" —
  so no platform artifact records that a stage ran, and the Gate Results section is
  written by the implementer (workflow.md 3-1) and editable by anyone with write access.
  R6 is what re-entry does instead; it never reads a verdict as a licence to skip a stage.
- **Worktrees.** `git worktree list --porcelain` reports a path, a branch, and a HEAD —
  and nothing about outcome. Read in this clone on 2026-08-07, it listed five worktrees —
  among them one for a live implementation and one whose branch still sat at the default
  branch's tip with no commits on it, in identical form. An abandoned attempt and an
  interrupted one are the same record. Worktrees are equally unusable as a **recency**
  signal (R3), for a different reason: they are local to one clone, so a session running
  elsewhere leaves none here, and their presence or absence says nothing comparable
  across sessions. See R7 for what re-entry does with the directories themselves.
- **An issue being open or closed.** Closing keywords act only on PRs targeting the
  default branch (platform guide, "Link PR to Issue"), and every per-issue PR here
  targets the integration branch — so a merged issue stays open. Read here on
  2026-08-07: four PRs were `MERGED` against `integration/issue-109` while
  `gh issue view 109` reported `0/7` sub-issues completed. Keying re-entry on issue state
  would have re-implemented all four.
- **Whatever a previous session decided and did not write down.** `BLOCKED`,
  `NEEDS_CONTEXT`, and `SKIPPED` (B2-6) are judgments that reach a chat summary, not an
  artifact. R5 resolves that by re-deriving them rather than recovering them.
- **A fix-round count no PR body carries.** R6.

There is no state file, and re-entry must not introduce one — neither on disk nor as a
tracker comment written for the machine's own benefit. Everything above is an artifact
that exists for its own reasons and that a human reads too.

## R1. The issue set

Read the batch source and take the issue set as it stands now — one list read, the same
source B1-1 uses. The **graph** is not built here; it is the run's expensive step and
waits for R4.

The set is not assumed stable between sessions: an issue may have been closed, re-scoped,
or added to the parent since the first one ran. Both directions matter later — R2 uses the
set to identify which branch this batch is on, and R8 treats an issue with no evidence
behind it as newly entering the batch, because nothing durable records which issues the
first session's plan actually covered.

## R2. The integration branch, the milestone PR, and the stop conditions

### Locating the branch

B1-4 derives the branch name from the batch source, and only one of its two forms can be
recomputed later:

- **Parent issue** → `integration/issue-<parent-number>`. Deterministic; compute it.
- **Milestone, label, or manual list** → `integration/<date>-<slug>`. The slug is
  re-derivable by B1-4's reduction of the source's name to lower-case letters, digits and
  hyphens. **The date is not** — it is the day the first session ran. Recomputing it from
  today's date yields a different name every day, so a batch resumed the next day would
  read *Fresh* and cut a second branch while its merged work sat on the first.

For those three sources, **discover the branch instead of computing it**: list the remote
refs under `integration/`, keep the ones whose name ends in the derived slug, and
corroborate each against R1's set — this batch's branch is the one whose PRs attribute
(R5) to issues in that set.

- Exactly one match → that is the branch.
- More than one → **Stop**, naming them. Never guess which branch machine merges land on.
- No match → **do not conclude Fresh yet.** A branch that was deleted leaves no ref to
  match on, so "no ref" covers both "never created" and "destroyed mid-batch" — and only
  the parent-issue form can tell them apart by name. List this repository's pull requests
  whose base begins with `integration/` and check whether any attributes (R5) to an issue
  in R1's set. None do → **Fresh**. Some do → the branch they name was this batch's and is
  gone → **Stop**, reporting the branch name, those PRs and their states.

### Reading the milestone PR

Read it before drawing any conclusion from the branch. When a human merges it, the merge
gate deletes the integration branch ([merge-issue-prs](../../merge-issue-prs/SKILL.md)
Phase 3), so a finished milestone and a never-started one both present as "branch does not
exist" — and B1-4's create path, given the second reading, would re-implement a milestone
already on the default branch.

The read survives that deletion: `gh pr list --head <integration branch>` matched a PR
whose head branch had already been deleted when this was checked against this repository
on 2026-08-07 (PR #120, head `feat/115-integration-mode`, absent from
`git ls-remote --heads origin`).

Also read its `## Needs Human Attention` section, where the gate records escalations
([milestone-pr.md](../../merge-issue-prs/references/milestone-pr.md) M2, M3). It is body
content, trusted in one direction only: it can **stop** this run and can never license
anything.

**What to look for, and what not to.** That section aggregates deferrals, blocked issues,
reverted issues *and* escalations, so most of it stops nothing. The stopping kind is the
one B2-4's table calls an escalation that leaves the branch's contents **not established**
— a revert that could not be created, pushed or verified, a branch head that is no longer
the merge commit the gate recorded, or rebase commits it could not enumerate. An
**unrecorded exclusion** is the other kind and stops nothing. Read the cause, not the word.

**Corroborate it with a signal that is not prose.** A revert that never landed has an
observable shape in the artifacts already read: a merged PR whose recorded `mergeCommit` is
**not** an ancestor of the freshly fetched branch head, or is the head's own commit with no
`This reverts commit <sha>` above it — the merge landed and the revert did not. Where either
the prose or that signal indicates an incomplete revert, stop.

Do **not** key this on the revert label. `merge-issue-prs` writes that label at R-4, which
runs only after R-1 (create), R-2 (push) and R-3 (verify) have all succeeded, while the
escalation this section exists for stops at R-1, R-2 or R-3 — so on a genuine incomplete
revert there is no label, and wherever a label exists the revert landed. A label-keyed check
narrows nothing.

**A missing section is not an all-clear.** Absence can mean no escalation, an unparseable
body, a failed read, or a body update the gate was permitted to abandon
([milestone-pr.md](../../merge-issue-prs/references/milestone-pr.md) M3 retries once, then
records a stale-dashboard concern and continues). So treat absence as *no evidence of an
escalation*, not as evidence of none: proceed, and record in the resume report that the
escalation surface could not be confirmed. The label-versus-history signal above is what
narrows the gap; it does not close it (Known limits).

### The outcome

**One stop condition is checked first, before the table, and it ends the run whatever the
table would say:** an **outstanding unestablished-branch escalation** (above). B2-4 requires
that batch to create no worktrees, dispatch no implementers, and invoke the gate no further,
and that instruction has to survive the session that received it or the next one walks
straight back onto a branch a human is repairing. It has to be checked first because it is a
property of the branch rather than of the milestone PR's state: a mid-flight batch — an
`OPEN` draft milestone PR over a **present** branch — matches the ordinary Resumable row, so
a table-ordered check would never reach it.

The other branch-level stop, **the branch was destroyed** (below), stays *inside* the table
and must not be promoted the same way. It only ever competes with rows whose branch is
absent, and there the table's order is doing real work: a normally completed batch — the
milestone merged, then `merge-issue-prs` M5 deleted the integration branch — leaves an absent
branch with merged PRs still carrying its `baseRefName`, which matches a destroyed-branch
check exactly. Ordering is what makes that read **Stop — finished** rather than a report that
merged work "is gone with it". So: read the table top to bottom, and **the first matching row
is the outcome**; the destroyed-branch reading lives in one row and applies only there — the
state a branch-only check would mistake for Fresh.

| Milestone PR | Integration branch | Outcome |
|---|---|---|
| none | absent, and no PR was ever based on it | **Fresh.** Nothing this mode creates exists; treat it as a new batch |
| none | **absent**, while PRs based on it exist | **Stop — the branch was destroyed** (below). This row sits above Resumable and below Fresh deliberately: it is the only place the destroyed-branch reading applies, because every other absent-branch state is already explained by the milestone PR's own state |
| none, or `OPEN` draft | present | **Resumable.** The batch is mid-flight. A milestone PR's absence is not evidence that nothing landed — the gate creates it at the first moment the branch is ahead of the default branch, so a batch whose gate has not run yet has none |
| `MERGED` | absent, or present | **Stop — finished.** The milestone landed on the default branch |
| `OPEN`, ready for review | present | **Stop — under review.** Not because the batch is provably terminal: only the orchestrator can declare that ([milestone-pr.md](../../merge-issue-prs/references/milestone-pr.md) F1) and a human can flip any PR to ready by hand. The reason is narrower and sufficient — a reviewer is reading that diff, and resuming would move it under them |
| `OPEN`, either state | **absent** | **Stop — inconsistent.** An open milestone PR whose branch is gone is a state this pipeline does not produce; report both and let a human resolve it |
| `CLOSED` unmerged | either | **Stop — abandoned.** A human closed the milestone without merging it; what happens to the branch is that human's call, not this batch's |

**A destroyed branch is not a fresh batch.** Deleting a branch does not leave its pull
requests open: GitHub's documentation states that "If the branch is associated with at
least one open pull request, deleting the branch closes the pull requests", and the
separate automatic-retargeting rule is scoped to deleting the **head** branch of a
*merged* pull request — it does not apply to a base branch deleted mid-batch
([Creating and deleting branches](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository),
read 2026-08-07). Those PRs keep their `baseRefName`, so the list read still returns them
and their absence is not what signals the deletion — the missing branch is. Whatever
merged there is gone with it. Report the branch, the PRs, and their states, and stop:
restarting would re-implement everything, and reading the closures as human decisions
(R5) would write the whole batch off as deliberate.

**This reading applies only to the row above — no milestone PR, branch absent, PRs based on
it.** An absent branch alongside a *merged* milestone PR is the ordinary end of a batch, not
a destroyed one: `merge-issue-prs` M5 deletes the integration branch after the milestone
merges, and the per-issue PRs keep their `baseRefName` afterwards, so the two states look
identical to a branch-only check. What separates them is the milestone PR, which is why the
table is read in order rather than this check being hoisted above it.

On any **Stop**, report and stop: create no branch, cut no worktree, dispatch no
implementer, invoke no merge gate. Where R1's set still holds open issues that never
produced a PR, report them as outside this milestone rather than picking them up — a new
milestone is a new batch, and starting one is the user's decision at B1-3.

On **Resumable**, B1-4 reuses the branch under its existing rules (probe, never recreate,
never reset or force-push).

## R3. Recency check — is another session already working on this batch?

Two sessions advancing one batch would dispatch the same issue twice, produce two PRs for
it, and hand the merge gate two candidates for one issue — which its policy has no rule
for (checked against [eligibility.md](../../merge-issue-prs/references/eligibility.md) and
[workflow.md](../../merge-issue-prs/references/workflow.md)). Nothing in the tracker or git
is a lock, so what is available is **evidence of recent writing**, and re-entry acts on it
before it writes anything of its own.

**Read only the writes this pipeline itself performs:**

1. The integration branch's head commit time — the gate's merges and reverts.
2. The head commit time of every remote branch in this batch's per-issue naming, taken
   over R1's issue set.
3. `createdAt` on the PRs based on the branch.

**Not `updatedAt`, on anything.** That field moves whenever anyone comments or changes a
label — including the repository's own automated reviewers, which this pipeline waits for
by design. Keyed on `updatedAt`, a repository with routine bot activity would stop every
unattended run indefinitely.

Take the newest of the three and compare it against the current time. Within the
**freshness window** — 30 minutes by default, overridable as `reentry_freshness_window`
in the repository's agent instructions — treat the batch as **possibly attended**:

- Dispatch nothing, create no branch or worktree, and do not invoke the merge gate.
- Ask the user to choose (see Environment Adaptation in SKILL.md), showing which artifact
  carried the timestamp and how old it is: **wait one window and re-check** (at most
  once, then stop) / **proceed anyway** (the user asserts nothing else is running) /
  **abort**.
- **Where no user is reachable** — no user-choice capability, or an unattended or
  scheduled invocation — **stop and report.** A skipped cycle costs one scheduling
  interval; a double dispatch costs two open PRs for one issue. Do not downgrade the stop
  because the invocation was unattended: unattended is the case it exists for.

**Run it once, before this session's first write.** After R8 starts acting, every signal
above carries this session's own timestamps and the check means nothing.

**What this does not cover.** It is evidence, not exclusion. Two sessions starting inside
the same window each see the other's silence and both proceed. A session that has been
implementing for longer than the window without pushing is invisible to it. A gate run
that only defers writes no commit, so it leaves no trace here either. And it cannot tell
another orchestrator from a human pushing to the branch by hand; both are reasons to stop,
so it treats them alike.

**Consecutive stops cannot be counted** — counting them would need persisted state. What
bounds the cost instead is the tightness of the signal set above, plus a stop report that
names the artifact and its timestamp, so a recurring stop is visible to whoever reads it.
Where a repository writes to these artifacts on a cadence tighter than the window, lower
`reentry_freshness_window` rather than widening what is read.

## R4. The dependency graph

Only now, and only on **Resumable**. Rebuild it exactly as B1-1 and B1-2 do — the same
sources, the same union, the same cycle handling, and the same same-file ordering edges,
iterated to B1-2's fixed point. A resumed session does not inherit a graph; it derives
one, from issue bodies and relationship links that have not moved.

B1-1 and B1-2 are not run again afterwards: this **is** that step, and B1-3 receives its
output. On the **Fresh** path B0 hands nothing back and B1 runs normally.

## R5. Per-issue state from the PRs

### Attribution

Attribution follows the merge gate's **E1c**
([eligibility.md](../../merge-issue-prs/references/eligibility.md)), which is the
security-critical policy and is not restated here. Read it and apply it — with one
difference, which is the direction the residue falls in:

**For the gate, an unattributed PR defers and nothing happens. For re-entry, an
unattributed PR makes an issue look unimplemented and gets it dispatched — producing a
second PR for an issue that already has one.** So uncertainty resolves the other way:
**do not dispatch.**

- Read `headRefName` first, in whatever form the branch takes, including a host-provided
  one embedding `issue-<number>`. E1c is explicit that requiring the
  `<type>/<issue>-<slug>` convention "would permanently exclude a large class of genuine
  pipeline PRs".
- Where the branch carries no issue number, fall through to the body's **linking-keyword**
  references under E1c's rules — never to bare `#N` mentions, which pipeline bodies use
  as ordinary prose.
- Signals disagreeing, references resolving to more than one issue in R1's set, or a
  reference pointing outside that set → attribute the PR to nothing **and dispatch none of
  the issues it could plausibly belong to.** Report it.
- Two PRs attributing to one issue → do not dispatch that issue; report both.

Only issues in R1's set are attributable. That set comes from platform relationships,
which no PR author can edit.

### The mapping

| What the artifacts show | Status (B2-6) | What R8 does with it |
|---|---|---|
| PR `MERGED` against the branch, and neither revert signal present | `MERGED` | Nothing. Its code is in the base; dependents are unblocked |
| PR `MERGED`, and a revert label **or** a `This reverts commit <mergeCommit>` in the freshly fetched history | `REVERTED` | Nothing. A candidate attributing to an issue in the gate's reverted-issue set is deferred without further checks ([workflow.md](../../merge-issue-prs/references/workflow.md) 2-1), so re-implementing produces a PR the gate defers on sight. Human queue; dependents cascade `SKIPPED` |
| PR `OPEN`, not a draft | *(the gate decides)* | Leave it and let R8's gate invocation rule on it. Re-entry does not re-derive why an earlier run left it unmerged — eligibility belongs to the merge gate, which re-decides it every run |
| PR `OPEN`, still a draft | from R6 | Re-run the gates under R6's budget |
| PR `CLOSED`, unmerged, **while the branch exists** | *(none — human action)* | Do not re-dispatch. Closing a PR without merging it is not something this pipeline does, so with the branch intact it is a human's decision. Report it; dependents cascade `SKIPPED` |
| PR `CLOSED`, unmerged, **branch absent** | — | Not reached: R2 has already stopped the run. The closure is the platform's side effect of the base branch being deleted, not a decision about the PR |
| No PR, but a remote branch matching the issue's naming | *(none)* | R7: dispatch on a fresh branch name, leave the orphan alone |
| No PR, no remote branch | *(none)* | Dispatch, subject to R8's approval rule. Indistinguishable from an issue an earlier session reported `BLOCKED` or `NEEDS_CONTEXT` — see below |

**Re-dispatch is how `BLOCKED` and `NEEDS_CONTEXT` are recovered, not a failure to
recover them.** Neither status leaves an artifact, so an issue that ended in one looks
exactly like an issue that was never reached. Re-dispatching resolves the ambiguity by
re-deriving the verdict: an implementer reading the same issue against a codebase that has
only moved forward reaches its own conclusion, and an issue that is still underspecified
reports `NEEDS_CONTEXT` again. The cost is one implementer run per such issue, per resume.
Any cheaper answer would mean writing the previous session's verdict into a durable store,
which is the state file this design does not have.

**Post B2-4's per-merge comment only where it is missing.** A resumed session cannot
remember whether it commented, so read the merged issue's comments and skip only when one
already names that merge commit. Where the read is inconclusive, post: a duplicate comment
is noise, and a missing one loses the only per-issue record that the merge happened.

## R6. The review gates on a resumed PR

A draft PR is the normal shape of an interrupted batch, not an edge case — an implementer
finishes, the orchestrator starts gating, and the session ends mid-round. Two questions
arise about it, and they have different answers.

**"Has this stage passed?" is never answered from the PR body. Both stages are re-run on
every PR that is still an unmerged draft.** No platform artifact records a gate verdict — the stages
are internal to the run ([review-gates.md](review-gates.md)) — so the only thing a body's
`Stage 1: PASS` establishes is that something wrote that text, and anyone with write
access can. Treating it as a licence to skip would close a loop with no human in it: skip
both stages, and B2-3 step 6 flips the PR to ready on gates it never ran; the merge gate's
**E3** then reads that platform ready-state as the machines' verdict and merges. E3's own
safeguard — "a body claiming everything passed never substitutes for the platform state" —
holds only while the platform state is set by something other than the body, and a skip
rule is exactly what breaks that.

**A PR that already reached ready for review is not re-gated.** Re-gating it has no defined
outcome: R6's remedy for a failing stage is "the PR stays a draft", and nothing in this
pipeline moves a PR from ready back to draft. Note the reason is *not* that ready implies
both stages passed — B2-3 step 6 is one way a PR gets there, but a human can flip any draft
by hand. The backstop for that is the merge gate's E3, which defers on a `Gate Results`
section recording an unresolved failure whatever the platform state says. It would also be actively harmful — a fix
push immediately before R8's gate invocation re-triggers CI, and the merge gate's
re-evaluation defers a PR whose rollup is running
([eligibility.md](../../merge-issue-prs/references/eligibility.md)), so a daily schedule
would push, defer, and never progress. A ready PR goes to the merge gate; R5's mapping
already says so.

Re-running is cheap relative to what it guards: two reviewer instances per resumed draft,
against an autonomous merge of unreviewed code.

**"How many fix rounds have already been spent?" is read from the body**, because a count
can only ever make this session stricter. A low count grants fix rounds, which costs time;
a high or absent one withholds them, which leaves the PR a draft. What the count cannot do
is skip a review: the stages run either way, so the most an edited count achieves is to put
a PR that had exhausted its budget back on the autonomous path *with its gates actually
re-run*. It cannot merge **unreviewed** code, which is the property that matters here; it
can spend more machine time.

| Gate Results line for a stage | Fix rounds remaining |
|---|---|
| `pending` | The full budget. `pending` is what the implementer writes at PR creation (workflow.md 3-1), so it positively records that the stage has not run |
| A verdict with a round count below the cap — `FAIL (round 1/2)` | The remainder of the cap |
| A verdict with the count at the cap — `FAIL (round 2/2)` | None |
| A verdict with no count at all | **None.** Fail closed — a body written before B2-3 recorded counts, or by something else, gives no way to tell a stage that has spent nothing from one that has spent everything, and a fresh budget per resume would let a PR consume unbounded rounds across sessions |

**Re-running a stage is not a fix round.** A re-run that passes costs nothing further. One
that fails spends a fix round if any remain; with none remaining, the PR stays a draft with
its findings recorded, is reported `DONE_WITH_CONCERNS`, and goes to the human queue —
the same outcome as exhausting the budget inside one session.

CI is not budgeted this way: re-watch it (workflow.md 3-3). Reading the current check state
costs one call and does not depend on what an earlier session saw.

## R7. Idempotency — what re-entry never recreates

1. **A pull request is adopted, never duplicated.** An issue with a PR on the branch is
   never given a fresh implementation run. The implementer is re-invoked only as a gate
   fix round against that same PR (B2-3), which pushes to the existing branch.
2. **The integration branch is probed, not created.** B1-4 already branches on the probe's
   answer; R2 is what keeps that probe from being asked about a branch the gate deleted
   after a merged milestone, or about a name that was never this batch's.
3. **A per-issue branch with no PR is not adopted.** Dispatch the issue on a fresh branch
   name, leave the orphan branch untouched on the remote, and report it. Adopting it would
   mean building on commits whose provenance the artifacts do not carry — an abandoned
   attempt reads exactly like an interrupted one — and the failure modes are not
   symmetric: re-implementing costs one implementer run, while resurrecting discarded work
   costs a PR nobody can account for. Deriving the fresh name by appending a short
   distinguishing suffix to the convention (`feat/112-resumable-reentry-r2`) keeps the
   issue number readable, which R5's attribution depends on.
4. **A worktree is never reused, and never removed by re-entry.** It is not a signal, so
   it cannot be adopted; and it may belong to a session that is still running, which R3 can
   suggest but not settle, so removing it is not re-entry's call. Cut each new worktree at a
   fresh path alongside the fresh branch name, and list any left-behind directories in the
   summary so a human can clear them.
5. **A stopped run produces no writes at all.** Every R2 and R3 stop ends the run before
   B1-3 draws a plan.
6. **The merge gate is invoked, not second-guessed.** Re-entry never merges, retargets,
   closes, or labels anything to move a PR toward eligibility, and never reconstructs an
   earlier run's deferral reasons — B2-4's report is where those come from, this session as
   much as any other.

## R8. Rejoin the pipeline

### 1. What the integration branch licenses, and what it does not

B1-4 creates the branch only after an integration-mode approval, so a branch under this
batch's name is evidence about the **mode**: which base to use, and that the merge gate is
the consumer of the ready flip. That is the whole of it, and three facts bound it:

- **Any account with write access can push a branch by that name.** The branch establishes
  what to do *if* the batch continues, not that it may.
- **B1-3's approval covers which issues get implemented, and nothing records that.**
  Reorder can *exclude an issue from the batch* (batch.md B1-3), and the exclusion lives in
  that session only — so R1's re-derived set contains the issue again.
- **The set can widen between sessions.** Adding a sub-issue link needs only triage access
  ([eligibility.md](../../merge-issue-prs/references/eligibility.md) Known limits #3).

**So dispatching an implementer requires an approved plan, every session.** The mode is
settled and is not asked again; the plan is not.

- **With a user reachable:** present the resume plan and take the same approval, with the
  same options. Mark every issue the artifacts show no evidence for — no PR, no branch — as
  **newly entering the batch this session**, so an exclusion made earlier is visible to be
  made again, and so an issue linked into the set since the last run is seen before it is
  implemented.
- **With no user reachable** — an unattended or scheduled invocation: **dispatch no new
  implementer.** Advance what a plan already produced — re-run the gates on the unmerged
  drafts (R6), which includes re-invoking an implementer for a gate fix round against a PR
  that already exists, invoke the merge gate, post the merge comments, report — and name
  the issues waiting on an approved plan. Merging needs no approval here: it is
  merge-issue-prs' own autonomous remit under its own policy, and it acts only on PRs a
  plan already produced.

The boundary is scope, not caution: an unattended session may finish work a human
approved, and may not start work nobody did.

**What a resume cannot recover is a Reorder.** Its edits — an excluded issue, a dropped
stale edge, a forced ordering — live in the session that made them. R4 rebuilds the
unmodified graph plus B1-2's own collision edges, and R1 the unmodified set. The exclusion
is the consequential one and is handled by the approval rule above; of the graph edits, a
dropped edge coming back costs ordering, and a forced one going missing can put two issues
in one group the user wanted apart, which B1-2 step 4 re-derives where the collision is
visible in the codebase and which otherwise surfaces as a deferral. Say in the summary that
the set and the graph were re-derived, so a reader knows the earlier Reorder is not in
force.

### 2. Invoke the merge gate before dispatching anything

Whenever the branch carries an open PR that is not a draft. An earlier session can end with
ready PRs the gate never saw, and merging them first is what makes their dependents'
worktrees contain their code. It is a full B2-4 — report read the same way, statuses
updated under the same precedence, merges confirmed by the same two-part read — and it
carries **no terminal-state declaration**: issues are about to be dispatched, so there is
nothing truthful to declare, and B2-4 treats a partial declaration as worse than none.

### 3. Continue

At B2-1, with the DAG advanced by whatever merged, dispatching only the issues R5 left
unsettled and R8 item 1 permits. From here the batch is an ordinary batch, with one rule
added at B3.

**The terminal-state declaration is sent only when every member of the batch's dispatched
set carries a final B2-6 status.** That set is what the *batch* dispatched across all its
sessions — R5's re-derivation establishes it from the artifacts, and this session's own work
adds to it — not what this one session happened to dispatch, because F1's part (a) exists as
a scope cross-check against the gate's own vetted set and a per-session set would not serve
it. It is equally **not** R1's whole set: R8 item 1 keeps Reorder available on a resume, and
Reorder can exclude an issue from the batch, so an excluded issue sits in R1's set with no
B2-6 status and never acquires one. Keying the declaration to R1's set would mean no
declaration is ever sendable and the milestone PR never leaves draft — on this run and every
later one. An issue in scope that the batch never dispatched is reported in the summary, not
declared.

**Waiting on a plan approval is not a B2-6 status**, so a session that could not obtain one
cannot complete part (b). It therefore sends **no declaration at all** — and in particular
**never an empty dispatched set.** An empty set carries all three parts structurally, so
[milestone-pr.md](../../merge-issue-prs/references/milestone-pr.md) F1 would treat it as a
real declaration and use it *instead of* the standalone derivation whose whole purpose is
that "a vetted issue with no PR at all is not terminal standalone". The gate would flip the
milestone PR to ready, R2 would return **Stop — under review** on every later run, and the
batch would end permanently with issues never implemented.

Sending nothing is the safe form of the same fact: F1 treats a missing declaration as *not
declared*, falls back to that derivation, and leaves the milestone PR a draft naming the
issues it is waiting on — which is exactly the batch's true state. B3's closing invocation
still runs; it merges what it can and carries no declaration, for the same reason a
per-group invocation carries none.

The summary describes work this session did not do, so it names the resume, which issues
arrived already settled, anything waiting on an approval, and whether a declaration was
sent.

## Known limits

- **R3 is evidence, not a lock**, with the coverage gaps stated there. It is the
  concurrency signal available without persisting state, not a mutual exclusion, and its
  consecutive stops cannot be counted for the same reason.
- **A `BLOCKED` or `NEEDS_CONTEXT` verdict costs an implementer run to recover** (R5), once
  per resume, for as long as the issue keeps producing it. Both gate stages likewise re-run
  on every resumed unmerged **draft** PR (R6); neither cost is recoverable without a state
  file.
- **An unattended session cannot start new work** (R8), so a scheduled run drains the PRs a
  plan already produced and then waits for a human. Scheduling advances a batch; it does not
  approve one. The bound is **artifact evidence, not plan membership**: an interruption after
  group 1 leaves groups 2 and later undispatchable unattended even though the user approved
  them at B1-3, because nothing records that they were approved. That is a real narrowing of
  what unattended operation delivers, and it is the price of having no durable record of the
  plan.
- **A dispatch that produced no artifact is indistinguishable from one that never happened.**
  The declared set is inferred from PRs and branches, so an issue an earlier session
  dispatched whose implementer returned `BLOCKED` before pushing anything leaves nothing
  behind and drops out of it. Harmless on the attended path — R5 sees no PR and no remote
  branch, re-dispatches, and the issue acquires a status before B3 — but it means the
  declared set is "what left a trace", not "what was attempted".
- **An escalation the milestone PR never received is invisible** (R2). A body update the gate
  abandoned, an unparseable section, or a failed read all present as "no escalation", and the
  label-versus-history corroboration narrows that without closing it.
- **An escalation with no milestone PR has nowhere durable to live** (R2). Where the gate
  escalated before anything ever merged, no milestone PR exists to carry it, and the next
  session cannot see it.
- **A batch whose source changed shape between sessions is re-derived, not reconciled**
  (R1). The resume plan shows the user the set; nothing diffs it against the one the first
  session approved, because that set was never recorded.
- **Re-entry reads content anyone with write access can edit** — PR bodies, issue comments,
  branch names, the milestone PR's escalation section. Every use of it is arranged to run in
  one direction: content can withhold fix rounds, stop the run, or make an issue look
  already handled and drop it from a dispatch, and it can never skip a review stage, start
  an implementation, or merge **unreviewed** code. Restoring a spent fix-round budget is the
  one edit that adds machine work rather than removing it, and what it buys is more review,
  not less. The residue is a missing implementation or a
  stalled batch, both visible in the summary.
- **An artifact read only for stopping can still be removed.** Deleting the escalation from
  the milestone PR's `## Needs Human Attention` section leaves a resumed session reading a
  healthy branch, which is the behaviour this file had before it read that section at all.
  Its absence is therefore not evidence of safety, only the lack of evidence of danger —
  the same asymmetry the merge gate states for a stripped revert label, and, like it, not
  closed here.
- **Branch discovery (R2) trusts a pushed branch exactly as B1-4 does.** Only an account
  with write access can create one, which is the boundary the merge gate's E1a already
  rests on, and a planted branch with no PRs attributing to this batch's issues fails the
  corroboration and is not adopted. What discovery does not add is a way to tell a
  legitimately-created integration branch from one an account at the same trust level
  created.
