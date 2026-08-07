# Workflow: Run-Level Preconditions, the Serial Merge Loop, and Auto-Revert

Detailed procedure for **Phase 0's run-level preconditions** and **Phase 2's merge
loop**, including post-merge verification, auto-revert, stop-the-line, and escalation.
Phase 1 triage is [eligibility.md](eligibility.md); the Phase 3 milestone PR is not
specified yet.

## Table of Contents

- [The invariant: one merge in flight](#the-invariant-one-merge-in-flight)
- [Phase 0: run-level preconditions](#phase-0-run-level-preconditions)
  - [P1: a verifiable CI signal on the integration branch](#p1-a-verifiable-ci-signal-on-the-integration-branch)
  - [P2: the merge method](#p2-the-merge-method)
  - [P3: an executable revert path](#p3-an-executable-revert-path)
  - [Human-merge mode: the fallback](#human-merge-mode-the-fallback)
- [Phase 2: the serial merge loop](#phase-2-the-serial-merge-loop)
  - [2-0: order](#2-0-order)
  - [2-1: pre-merge re-check](#2-1-pre-merge-re-check)
  - [2-2: sync with the integration branch](#2-2-sync-with-the-integration-branch)
  - [2-3: merge](#2-3-merge)
  - [2-4: post-merge verification](#2-4-post-merge-verification)
  - [2-5: the go / defer / stop table](#2-5-the-go--defer--stop-table)
- [Auto-revert](#auto-revert)
- [Escalation: when the revert itself fails](#escalation-when-the-revert-itself-fails)
- [Stop-the-line and its scope](#stop-the-line-and-its-scope)
- [The human queue at run end](#the-human-queue-at-run-end)
- [Known limits](#known-limits)

## The invariant: one merge in flight

Complete every step below — through the verification in 2-4 — before starting the next
PR. Do not batch merges. Do not sync PR N+1 while PR N is unverified. A failure must map
to exactly one merge; that is what makes the revert target unambiguous, and it is the
same hard-won discipline as merge-renovate-prs.

A PR **deferred without merging** is not in flight: deferring and moving on preserves the
invariant, and a deferral never stops the line. A **merged and unverified** PR does stop
it.

## Phase 0: run-level preconditions

These are run-level, checked once before the loop starts, and they are the machine-checkable
substitute for the human sign-off this skill removes. **A failed precondition never
produces a quieter autonomous mode** — it produces human-merge mode.

### P1: a verifiable CI signal on the integration branch

Post-merge verification is the only thing between an unreviewed merge and the integration
branch. Without a CI signal there is nothing to verify, so the run must not merge.

Probe, and record which of three outcomes applies (commands in
[platform-github.md](platform-github.md)):

| Outcome | Established by | Effect |
|---|---|---|
| **Confirmed** | At least one completed workflow run whose head branch is the integration branch **and whose triggering event is `push`** | Proceed |
| **Provisional** | No such run yet, but a workflow definition declares a trigger that fires on a commit landing on this branch | Proceed; the **first** merge's verification is the confirmation |
| **Absent** | No such run and no such workflow definition | **Precondition fails** → human-merge mode |

Three rules keep this from manufacturing a signal that never arrives:

- **`push` is the only confirming event.** Post-merge verification needs a run that fires
  *because a commit landed*. A `schedule` or `workflow_dispatch` run shows CI can execute
  on the branch, not that it will execute on a merge, so it does not confirm — fall
  through to reading the definitions. And a `pull_request`-triggered run reports the
  *head* branch of its PR rather than the base (verified against this repository's own run
  history), so the integration→main milestone PR — whose head **is** the integration
  branch — would contribute PR runs to a branch-only query and be mistaken for
  integration-branch CI.
- **Undecidable branch filters do not match.** Where a workflow's `branches:` filter
  cannot be matched against the integration branch name with certainty, treat that
  workflow as **not** matching.
- **A provisional signal is not a pass.** If the first merge produces no run within the
  verification window, that is a verification timeout — auto-revert and stop the line
  (2-4) — and the rest of the run drops to human-merge mode. "No run appeared" is never
  read as "nothing to check".

### P2: the merge method

Read the repository's enabled merge methods; never assume squash. Use the method the
repository's configuration and its own merge history establish. Record it: **the revert
form depends on it** (a merge commit is reverted against its first parent; a squash or
rebase merge produces ordinary commits reverted directly).

Never `--admin`, never a required-check bypass, in any circumstance. A merge the platform
refuses is a deferral, not something to force.

### P3: an executable revert path

Auto-revert is a promise this run has to be able to keep, so confirm before the first
merge — not after a failure — that:

1. The authenticated account has **push access** to the repository.
2. The integration branch accepts a **direct commit**: it is either unprotected, or its
   protection permits this account to push.

If direct pushes are refused, the revert path becomes a revert PR, which needs its own
merge and therefore its own preconditions. Confirm that path explicitly or fail P3. **No
confirmed revert path → human-merge mode**; do not merge on the assumption that a revert
would work.

### Human-merge mode: the fallback

Any failed precondition puts the run in human-merge mode for its whole duration:

- Run Phase 1 eligibility triage normally and report it.
- Merge **nothing**. Report the eligible set as *ready for a human to merge*, not as
  merged.
- State which precondition failed, the evidence, and what would fix it (e.g. "no workflow
  triggers on a commit landing on `integration/issue-109`; add a `push`-triggered
  workflow covering that branch").
- Do not partially merge, do not merge "the safe-looking ones", and do not weaken the
  verification to fit what is observable.

## Phase 2: the serial merge loop

Runs only when Phase 0's preconditions all hold. Input is Phase 1's **eligible** set.

### 2-0: order

Process eligible PRs in dependency order where the run knows one (batch mode supplies the
graph), otherwise ascending by PR number. Order affects how much syncing the run costs and
which PR absorbs a conflict; it never affects **whether** a PR is merged.

### 2-1: pre-merge re-check

Immediately before merging, re-run the **full** eligibility check on the PR's current
head. Eligibility is never cached, and state moves during a run — most importantly a human
can comment while the loop is running, and this re-check is what lets them win that race.

One **loop-level exclusion** is checked here as well, before anything else: a PR is
deferred without further checks if **either** it carries the revert-exclusion label
(`merge-gate:reverted` by default, overridable in the repository's agent instructions)
**or** its recorded merge commit has been reverted on the integration branch. Its content
already broke the branch once; re-merging it unchanged would reproduce the failure on the
next run, and stop-the-line only binds the run it happened in. Both signals and why there
are two: see [Auto-revert](#auto-revert) R-4.

Record the head SHA that passed — it is the value the merge is guarded on in 2-3.

### 2-2: sync with the integration branch

Read the PR's mergeability against the integration branch before touching it.

- **Unknown.** Mergeability is computed asynchronously: "If the value is null, then GitHub
  has started a background job to compute the mergeability. After giving the job time to
  complete, resubmit the request."
  ([GitHub REST docs, "Pull requests"](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28)).
  An unknown value therefore means *not yet computed*, **not** *conflict-free*. Re-read
  within a bounded window; still unknown when it closes → **defer** the PR. Unknown is not
  clean.
- **Conflicting** → **defer that PR, unmerged, and continue the loop.** Conflict
  resolution is a judgment call that can change behaviour, and GitHub's own guidance is
  that only "simple line conflicts can often be resolved on GitHub", while "more complex
  conflicts must be resolved in a local clone"
  ([GitHub Docs, "About merge conflicts"](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/about-merge-conflicts)).
  This skill resolves neither: it does not edit the branch, does not force anything, does
  not retarget the PR, and does not close it. A conflict is a human's to resolve.
- **Behind but clean** → update the PR branch from the base, using the repository's
  convention (the default update creates a merge commit; `--rebase` is the alternative).
- **Clean and current** → nothing to sync.

**Why sync at all, when the platform will merge a behind-but-clean PR without it.**
Merging unsynced means the PR's green CI was computed on a tree that no longer exists —
the combination that actually lands was never built or tested anywhere. Syncing moves the
combination onto the PR, where the PR's **own** CI validates it before it reaches the
integration branch. One extra CI cycle per merge is what buys that, and a serial loop can
afford it.

**The sync re-triggers CI.** It pushes a new head commit, returning the check rollup to a
running state. So after a sync, **repeat 2-1 against the post-sync head** and wait for the
post-sync checks within eligibility.md E4's bounded window. A PR whose post-sync checks
settle red, or do not settle in time, **defers**. Never merge on a pre-sync result.

### 2-3: merge

- Merge with the method recorded in P2, **guarded on the head SHA** that passed 2-1. If
  the head moved in between, the platform refuses the merge rather than merging something
  that was never checked — documented behaviour: `409 Conflict` "is returned if a SHA
  parameter was provided and the pull request head did not match that SHA"
  ([GitHub REST docs, "Pull requests"](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28)).
  On a head-match failure, re-run 2-1 once; if the head moves again, **defer**.
- **Never `--admin`, never a required-check bypass.** A refused merge (protection, a
  required check, a missing review the agent cannot supply) is a **deferral**.
- **Confirm the merge from platform state, not from the command's exit status:** the PR
  reports as merged, and its merge commit is reachable from the integration branch's new
  head. Record the merge commit SHA — it is both the verification target and the revert
  target.

### 2-4: post-merge verification

Verification runs against the **integration branch**, never against the PR's own pre-merge
CI. That distinction is the whole point: pre-merge CI tested the PR, post-merge CI tests
what the branch now contains.

Two states, both required:

- **V-1 — landed.** The recorded merge commit is on the integration branch (2-3).
- **V-2 — verified.** The integration branch's CI **for that merge commit** completed
  successfully, plus any checks the repository defines.

Rules:

- **Find runs by commit SHA**, not by "the latest run on the branch" — the latest run can
  belong to an earlier commit, and reading it would verify the wrong thing.
- **Wait within a bounded window** — 30 minutes per merge by default, overridable in the
  repository's agent instructions. Use background execution so the wait does not block.
- **Judge each completed run by its conclusion**, mirroring E4's asymmetry between
  "passed" and "did not run":

  | Conclusion | Effect on this merge |
  |---|---|
  | `success` | passes, **and counts as verification** |
  | `skipped`, `neutral` | does not fail the merge, and does **not** count as verification — nothing was exercised |
  | `failure`, `cancelled`, `timed_out`, `action_required`, `stale`, `startup_failure` | **verification failure** |

  V-2 holds only when **no run failed and at least one run concluded `success`.** A commit
  whose every run was skipped has been checked by nothing, and absent evidence is not
  evidence of health — treat it exactly as a timeout.
- **No run appears, no run completes, or no run verified anything, within the window →
  verification timeout**, which is handled as a verification **failure**. Fail closed: on a
  disposable integration branch a needless revert of a healthy change costs one re-merge,
  while an unverified merge that unblocks dependents costs an investigation into code
  nobody read.
- **Repo-defined checks are executed, never invented.** The baseline is integration-branch
  CI. Anything beyond it comes only from human-authored sources — the invoker's request, or
  the repository's agent instructions and runbooks. Do not substitute a weaker check for
  one a human defined, and do not claim sufficiency those sources do not claim.
- **Never fabricate a passing result to keep the loop moving.** A truthful "this failed,
  here is what was reverted" is the correct output.

On success: record the merge as **merged and verified**, and proceed to the next PR.

### 2-5: the go / defer / stop table

Every outcome of the loop, and what it does to the run. Nothing here produces "merge
anyway".

| Situation | Detected at | Outcome for the PR | The loop |
|---|---|---|---|
| Every condition holds on the post-sync head | 2-1 / 2-2 | **merge** | continues |
| Loop-level exclusion (revert label) | 2-1 | **defer** | continues |
| Any eligibility condition fails on re-check (incl. a human comment landing mid-run) | 2-1 | **defer** | continues |
| Mergeability still unknown when its window closes | 2-2 | **defer** | continues |
| **Conflict on sync** | 2-2 | **defer**, unresolved and untouched | continues |
| **CI red** on the post-sync head, or unsettled at window close | 2-1 after sync | **defer** | continues |
| Platform refuses the merge (head moved twice, required check, protection) | 2-3 | **defer** | continues |
| **Verification timeout** — no run, no completion, or nothing that concluded `success`, within the window | 2-4 | **auto-revert** | **stops** |
| **Verification failure** — a run concluded non-success, or a repo-defined check failed | 2-4 | **auto-revert** | **stops** |
| **Revert failure** — the revert cannot be created, pushed, or verified | revert | **escalate to a human** | **stops immediately** |

## Auto-revert

Entered only from a verification failure or timeout in 2-4. Serial discipline is what makes
it sound: exactly one merge is in flight, so the revert target is unambiguous.

**R-1 — Create the revert commit on the integration branch.** First confirm the branch head
is still the recorded merge commit. If it is not, something landed outside this loop, the
one-in-flight invariant is broken, and the revert target is no longer unambiguous:
**escalate instead of reverting**. Otherwise, in a clean checkout of the integration
branch, revert the recorded merge commit in the form P2's merge method requires — a merge
commit is reverted against its **first parent**, which is the integration branch's own
history; a squash or rebase merge produces ordinary commits reverted directly.

**Never reset, force-push, or rewrite the branch.** Implementers may have the integration
branch checked out as a base; rewriting its history turns one failure into many. The revert
is a new commit on top.

**R-2 — Push it and confirm it landed.** Push the revert to the integration branch and
confirm from platform state that the branch head is now the revert commit. A rejected push
— non-fast-forward, protection, permissions — is a **revert failure**.

**R-3 — Verify the recovery.** Re-run 2-4's verification against the **revert commit**. A
revert that has not been verified is just another unverified change. Recovery verification
failing, or timing out, is a **revert failure**.

**R-4 — Comment on the reverted PR. Mandatory.** Not "when useful": an unattended revert
with no durable explanation is how trust in automation dies, and the PR is the only place
its author — human or machine — will look. The comment states, in English per repository
convention:

1. What was merged, with the merge commit SHA.
2. What failed: the run or check, its conclusion, and a link.
3. What was reverted, with the revert commit SHA.
4. The integration branch's state after the revert.
5. That the PR is now in the human queue and **will not be re-merged autonomously** until
   a human clears the exclusion.

Then **record the exclusion durably**: apply the revert-exclusion label (2-1) and verify
the write by re-reading the PR's labels, exactly as eligibility.md E5 requires of its own
label. A failed comment is not a revert failure — the revert already succeeded — but an
unposted comment or an unverified label write is an **escalation in the report**, named by
PR number, so the record does not silently lapse.

**The exclusion is `label OR revert-in-history`, not the label alone.** Removing a label
needs only triage access on GitHub, so a label-only check could be cleared by an actor who
could not have merged the PR in the first place — and re-merging known-bad code is a
fail-*open*. The second signal is git: a PR's merge commit stays readable after the merge,
and a revert of it stays in the integration branch's history, so 2-1 also defers a PR whose
recorded merge commit has been reverted on the branch. State the bound honestly: this
signal holds only while the branch retains that history, so it is defence in depth for the
label, not a replacement for it. Only a human deliberately clearing the label **and**
changing the PR puts it back on the autonomous path.

**R-5 — Stop the line.** Even after a clean recovery, process no further PR this run. One
verification failure means the pre-merge gates missed something, and the rest of the queue
deserves human eyes before the automation continues.

## Escalation: when the revert itself fails

Stop immediately and return to a human when any of these holds: the branch head is not the
recorded merge commit (R-1); the revert commit cannot be created; the push is rejected
(R-2); or the recovery verification fails or times out (R-3).

Escalate with the **full state** — the PR that was merged, its merge commit, what failed,
what was attempted, and the integration branch's current head — surfaced through the run's
user-choice capability where a user is present and, either way, at the top of the run
report marked as requiring human action.

Then stop. Specifically:

- Do not retry destructive operations in a loop.
- Do not attempt creative alternative recoveries: **no force-push, no reset, no branch
  deletion, no re-creating the branch, no second revert on top of a failed one.**
- Do not continue to the next PR, and do not report the run as a completed pass.

This is the one place the autonomous path always comes back to a person.

## Stop-the-line and its scope

Stop-the-line halts **merging**, not the batch. What stops: this loop, and any further
merge into the integration branch this run. What does not stop: implementers working on
independent branches of the dependency graph — their work is unaffected by a merge failure
elsewhere.

The merge gate reports the reverted PR as **not merged**. How a batch orchestrator reacts
to a dependency that did not merge is implement-issue's rule (fail closed: dependents are
skipped), not this skill's — this skill reports, it does not reschedule implementers.

Eligible PRs the stopped loop never reached are reported as **not attempted**, kept
distinct from deferred ones: they failed no condition and need no human action beyond
re-running once the failure is understood.

## The human queue at run end

Deferred PRs accumulate through the run and are reported at the end. The queue has four
kinds of member, and the report distinguishes them:

| Kind | Source | Permanent? |
|---|---|---|
| Eligibility deferrals | eligibility.md's exclusion classes | E5 only; the rest are re-evaluated |
| Loop deferrals — conflict, red CI, unknown mergeability, refused merge | 2-2 / 2-1 / 2-3 | No — re-evaluated next run |
| Reverted | auto-revert R-4 | Yes, until a human clears the label |
| Not attempted | stop-the-line | No — the next run picks them up |

Each entry carries the PR number and title, the reason with concrete evidence, the
required human action stated **as an action** ("resolve the conflict in #123 against
`integration/issue-109`", not "conflicted"), and whether it is permanent or re-evaluated.

The queue is not a separate store: it is the labelled PRs plus each run's report, fully
re-derivable from the tracker and git. Nothing is persisted between runs.

## Known limits

State these plainly. A gate whose limits are undocumented gets trusted past them.

1. **Verification is exactly as strong as the integration branch's CI.** A green run means
   the suite did not catch a problem — not that there is none. This gate cannot judge suite
   sufficiency and does not claim to; that is what the human milestone review is for.
2. **Serial merging bounds attribution to one merge, not to one cause.** A failure that
   only appears in combination with an earlier merge is attributed to the later one, and
   reverting it restores green without identifying the real cause. The report says which
   merge was reverted, never that it was the root cause.
3. **A revert restores the branch, not the world.** Nothing outside the integration branch
   is undone. Revert is a sufficient rollback *here* precisely because this skill merges
   into a branch that ships nothing; the same procedure would not be sufficient in a repo
   where merging deploys.
4. **A verification timeout cannot distinguish "CI is broken" from "the change broke CI".**
   Both revert and stop the line. A repository with flaky or slow CI will therefore see
   reverts of healthy changes — the fix is the CI or the window, not a looser rule.
