# Workflow: Run-Level Preconditions, the Serial Merge Loop, and Auto-Revert

Detailed procedure for **Phase 0's run-level preconditions** and **Phase 2's merge
loop**, including post-merge verification, auto-revert, stop-the-line, and escalation.
Phase 1 triage is [eligibility.md](eligibility.md); the Phase 3 milestone PR is
[milestone-pr.md](milestone-pr.md).

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
form depends on it**, and the three methods do not produce the same revert target —

| Method | What lands on the integration branch | Revert target |
|---|---|---|
| **merge** | One merge commit | That commit, reverted against its **first parent** |
| **squash** | One ordinary commit | That commit, reverted directly |
| **rebase** | The PR's commits, **individually** | **Every** one of them, reverted **newest first** |

The rebase row is the one that bites: `mergeCommit` names a single commit, so a revert
built from it alone would undo one commit of several and leave most of the bad change on
the branch — while R-3's recovery verification could still pass on the partial result and
the run would report a successful recovery. Under rebase, **enumerate the landed commits
before reverting** (see [platform-github.md](platform-github.md)); if the enumeration
cannot be established with certainty, that is a **revert failure** — escalate rather than
revert partially. merge-renovate-prs states the same rule for the same reason.

Never `--admin`, never a required-check bypass, in any circumstance. A merge the platform
refuses is a deferral, not something to force.

### P3: an executable revert path

Auto-revert is a promise this run has to be able to keep, so confirm before the first
merge — not after a failure — that:

1. The authenticated account has **push access** to the repository.
2. The integration branch accepts a **direct commit**. Check **both** protection
   mechanisms: classic branch protection *and* repository **rulesets**. They are separate
   systems answering independently (confirmed against this repository, which returns `404
   Branch not protected` from one and `[]` from the other), so a ruleset can restrict a
   branch the classic endpoint calls unprotected. Probing only the classic endpoint lets P3
   pass on a branch that will reject the revert push — a failure that would surface as an
   R-2 revert failure *after* a bad merge had already landed, which is exactly what
   confirming beforehand exists to prevent.

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

One **loop-level exclusion** is checked here as well, before anything else: a PR
attributing to an issue in the **reverted-issue set** is deferred without further checks.
Stop-the-line binds only the run it happened in, so without this the next scheduled run
walks straight back into the merge that broke the branch.

**The exclusion is keyed to the issue, not to the PR, because a PR-keyed one cannot
fire.** Candidates are *open* PRs on the integration branch, so a reverted PR — which is
`MERGED` — is never enumerated as a candidate again; and an open PR's `mergeCommit` is
`null` while a merged PR's is populated (observed here on both). A rule reading "this PR
carries the revert label" or "this PR's merge commit was reverted" is therefore vacuous for
every input it would ever see. What *is*
reachable — and what actually re-admits the reverted content — is a **new PR for the same
issue**: an implement-issue re-run, or the author redoing the work. That PR carries neither
signal and is otherwise fully eligible.

**Build the reverted-issue set once per run**, before the loop, from the merged PRs based
on the integration branch. A merged PR counts as reverted when **either**:

- it carries a revert label (`merge-gate:reverted` for a verification failure,
  `merge-gate:unverified` for a timeout — both overridable as `reverted_label` /
  `unverified_label` in the repository's agent instructions), **or**
- its `mergeCommit` appears in a `This reverts commit <sha>` line in the integration
  branch's history — read against a **freshly fetched** ref, since a stale
  remote-tracking branch makes this half silently miss.

Attribute each such PR to its issue with E1c's rules; those issues are the set. The second
signal is what survives a stripped label: removing a label needs only triage access, and
re-admitting known-bad content is a fail-*open*.

If a reverted PR **cannot** be attributed to an issue, the exclusion has no key. Report it
as an **unrecorded exclusion**, named by PR number, exactly as an unverifiable label write
is — the run continues, but a human has to know that one reverted PR's work is not being
kept out.

State the bound rather than implying more (Known limits #5): this defers **later work on a
reverted issue**. It does not detect the same change reintroduced under a *different*
issue, and its git half holds only while the branch retains the revert commit. A human
clears it by removing the label — after which only the history signal remains, and only
while that history does.

Record the head SHA that passed — it is the value the merge is guarded on in 2-3.

### 2-2: sync with the integration branch

Read the PR's mergeability against the integration branch before touching it.

- **Unknown.** Mergeability is computed asynchronously: "If the value is null, then GitHub
  has started a background job to compute the mergeability. After giving the job time to
  complete, resubmit the request."
  ([GitHub REST docs, "Pull requests"](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28)).
  An unknown value therefore means *not yet computed*, **not** *conflict-free*. Re-read
  within a bounded window — **5 minutes per PR** by default, overridable as
  `mergeability_window` in the repository's agent instructions, and enforced the same way as
  the other two windows: polling against a wall-clock deadline the agent owns, never a
  blocking watch. Still unknown when it closes → **defer** the PR. Unknown is not clean.
- **Conflicting** → **defer that PR, unmerged, and continue the loop.** Conflict
  resolution is a judgment call that can change behaviour, and GitHub's own guidance is
  that only "simple line conflicts can often be resolved on GitHub", while "more complex
  conflicts must be resolved in a local clone"
  ([GitHub Docs, "About merge conflicts"](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/about-merge-conflicts)).
  This skill resolves neither: it does not edit the branch, does not force anything, does
  not retarget the PR, and does not close it. A conflict is a human's to resolve.
- **Behind but clean** → update the PR branch from the base. **When P2 recorded the rebase
  method, the sync must rebase too.** The default update creates a merge commit on the PR
  branch, which a rebase merge does not land as such — so R-1's count reconciliation would
  compare a commit list containing that merge commit against landed commits that do not,
  disagree systematically, and escalate on *every* revert in a rebase repository. Under the
  merge and squash methods the default update is fine.
- **Clean and current** → nothing to sync. **"Current" means the PR's merge base is the
  integration branch's present head — not that `mergeStateStatus` says `CLEAN`.** The two
  are different questions, and the enum answers the wrong one: `CLEAN` says *this would
  merge*, not *this was built against what it will merge into*.

**Once anything has merged in this run, every remaining candidate is behind — sync it,
whatever the enum says.** The loop is strictly serial, so each merge advances the integration
branch head and every candidate read before it becomes stale by construction. A candidate
still reading `CLEAN` from before that merge is exactly the case the sync exists for: its
green CI was computed against a tree that no longer exists. Re-read mergeability against the
**post-merge** head rather than trusting a pre-merge reading, and treat a candidate whose
merge base is not the current head as **behind**, `CLEAN` or not. This is not an edge case —
after the first merge of a run it is *every* candidate, so getting it wrong skips the sync on
all but one PR of every batch.

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

- Merge with the method recorded in P2, **guarded on the head SHA** that passed 2-1, so a
  PR that moved in between is refused rather than merged unchecked. The guard travels as
  `expectedHeadOid` on the platform's merge mutation (see
  [platform-github.md](platform-github.md)).
- **Discriminate a refusal by re-reading the head, not by its error text.** The mutation
  reports failures in a payload rather than as a distinct HTTP status, so there is no
  status code to branch on. After any failed merge, re-read the PR's head SHA: **changed**
  from the recorded value → the guard fired; re-run 2-1 once against the new head, and if
  it moves again, **defer**. **Unchanged** → the refusal was something else (protection, a
  required check, a review the agent cannot supply) → **defer**. Both paths defer, so a
  misread costs a deferral, never a merge.
- **Never `--admin`, never a required-check bypass.** A refused merge is a **deferral**.
- **Record the integration branch's head immediately before merging.** This is the
  *pre-merge base*, and under the rebase method it is the only thing that makes the revert
  enumerable: the landed commits are exactly `pre-merge base .. merge commit`. It has to be
  captured here, because after the merge nothing recovers it — and the obvious substitute,
  a merge base against the PR's head branch, reaches back past earlier merges whenever the
  PR was synced and would enumerate *other PRs'* commits for reverting. The one-merge-in-
  flight invariant is what makes the range exact: nothing else can land inside it.
- **Confirm the merge from platform state, not from the command's exit status:** the PR
  reports as merged, and its merge commit is reachable from the integration branch's new
  head. Record the merge commit SHA — it is the verification target, and with the pre-merge
  base it defines the revert target.

### 2-4: post-merge verification

Verification runs against the **integration branch**, never against the PR's own pre-merge
CI. That distinction is the whole point: pre-merge CI tested the PR, post-merge CI tests
what the branch now contains.

Two states, both required:

- **V-1 — landed.** The recorded merge commit is on the integration branch (2-3).
- **V-2 — verified.** The integration branch's CI **for that merge commit** completed
  successfully, plus any checks the repository defines.

Rules:

- **Find runs by commit SHA *and* `push` event.** The SHA alone is not enough, and this is
  the same miscount P1 guards against, arriving from the other side: a `pull_request` run
  reports its PR's head branch and the head-branch tip as its SHA, so once a PR whose head
  is the integration branch exists — precisely the Phase 3 milestone PR — every merge onto
  the branch re-triggers that PR's workflows with the merge commit as their SHA. Without
  the event filter, **V-2 could be satisfied by a milestone-PR review run while the
  branch's own CI never ran**, and, in the other direction, a routine `pull_request`
  failure would trigger a needless revert and stop-the-line. Filter the event server-side.
- **Never read "the latest run on the branch"** — it can belong to an earlier commit.
- **Wait within a bounded window** — 30 minutes per merge by default, overridable as
  `verification_window` in the repository's agent instructions.
  - The window needs an **enforcement mechanism the agent owns**: poll for the commit's
    runs on an interval against a wall-clock deadline. Do **not** delegate the bound to a
    blocking watch command — the platform CLI's watch has no timeout flag (verified), so a
    run stuck in `queued` would wait forever, on the one path whose expiry is supposed to
    *trigger* the auto-revert. Background execution keeps the **agent** free; it does not
    make the **wait** bounded, and only the second one matters here.
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

On success: record the merge as **merged and verified**, update the milestone PR — creating
it if this was the merge that first put the integration branch ahead of the default branch
([milestone-pr.md](milestone-pr.md) M0, M3) — and proceed to the next PR. A milestone-PR
update that fails never affects the merge: the merge landed and was verified, and the
dashboard reports that fact rather than being part of it.

### 2-5: the go / defer / stop table

Every outcome of the loop, and what it does to the run. Nothing here produces "merge
anyway".

| Situation | Detected at | Outcome for the PR | The loop |
|---|---|---|---|
| Every condition holds on the post-sync head | 2-1 / 2-2 | **merge** | continues |
| Loop-level exclusion — the PR's issue is in the reverted-issue set (label **or** revert-in-history) | 2-1 | **defer** | continues |
| Any eligibility condition fails on re-check (incl. a human comment landing mid-run) | 2-1 | **defer** | continues |
| Mergeability still unknown when its window closes | 2-2 | **defer** | continues |
| **Conflict on sync** | 2-2 | **defer**, unresolved and untouched | continues |
| **CI red** on the post-sync head, or unsettled at window close | 2-1 after sync | **defer** | continues |
| Platform refuses the merge (head moved twice, required check, protection) | 2-3 | **defer** | continues |
| **Verification timeout** — no run, no completion, or nothing that concluded `success`, within the window | 2-4 | **auto-revert** | **stops** |
| **Verification failure** — a run concluded non-success, or a repo-defined check failed | 2-4 | **auto-revert** | **stops** |
| **Revert failure** — the revert cannot be created, pushed, or verified, or (under rebase) the landed commits cannot be enumerated with certainty | revert | **record the exclusion (label, then comment), then escalate to a human** | **stops immediately** |

## Auto-revert

Entered only from a verification failure or timeout in 2-4. Serial discipline is what makes
it sound: exactly one merge is in flight, so the revert target is unambiguous.

**R-1 — Create the revert commit(s) on the integration branch.** First confirm the branch
head is still the recorded merge commit. If it is not, something landed outside this loop,
the one-in-flight invariant is broken, and the revert target is no longer unambiguous:
**escalate instead of reverting**. Otherwise, in a clean checkout of the integration
branch, revert what the merge landed, in the form P2's table requires:

- **merge** — revert the merge commit against its **first parent**, the integration
  branch's own history.
- **squash** — revert the single ordinary commit directly.
- **rebase** — the PR's commits landed **individually**. Enumerate them as the range
  **`pre-merge base .. merge commit`** recorded at 2-3, and revert **each, newest first**.
  `mergeCommit` under rebase is the branch's new *tip*, not the whole change, so reverting
  from it alone leaves the rest on the branch. Reconcile the enumerated commits against the
  PR's own non-merge commits before reverting anything. If the enumeration cannot be
  established with certainty — no pre-merge base was recorded, the PR's commit list cannot
  be read in full, or the counts disagree — that is a **revert failure**: escalate. A
  partial revert is the worst outcome available here, because R-3 can pass on it and the
  run would then report a recovery that did not happen.

**Never reset, force-push, or rewrite the branch.** Implementers may have the integration
branch checked out as a base; rewriting its history turns one failure into many. The revert
is a new commit on top.

**R-2 — Push and confirm it landed.** Push the revert to the integration branch and confirm
from platform state that the branch head is now the newest revert commit. A rejected push —
non-fast-forward, protection, permissions — is a **revert failure**, which goes to
Escalation. Note that R-4 has therefore not run yet: Escalation carries out its labelling
and comment first, precisely because a failed revert is the case where nothing else records
the exclusion.

**R-3 — Verify the recovery.** Re-run 2-4's verification against the branch head after the
revert. A revert that has not been verified is just another unverified change. Recovery
verification failing, or timing out, is a **revert failure**.

**R-4 — Comment on the reverted PR. Mandatory.** Not "when useful": an unattended revert
with no durable explanation is how trust in automation dies, and the PR is the only place
its author — human or machine — will look. The comment states, in English per repository
convention:

1. What was merged, with the merge commit SHA.
2. **The cause, named as one of two** (below): the change failed verification, or nothing
   verified it — with the run or check, its conclusion, and a link.
3. What was reverted, with the revert commit SHA(s).
4. The integration branch's state after the revert.
5. That further work on this issue **will not be merged autonomously** until a human clears
   the exclusion, and what clearing it requires — which differs by cause.

**Record the exclusion durably, split by cause.** Both causes revert and both defer, but
they blame different things and need different human action, so they are recorded with
different labels rather than one:

| Cause | Label (default) | What it means | What clears it |
|---|---|---|---|
| Verification **failure** — a run concluded non-success | `merge-gate:reverted` | The change is implicated | Fixing the change |
| Verification **timeout** — no run, no completion, or nothing concluding `success` | `merge-gate:unverified` | Nothing was proven either way; the change may be perfectly healthy | Confirming CI health, then re-running |

Collapsing the two would permanently blame a healthy PR for a slow or exhausted runner —
not hypothetical: CI capacity limits and usage limits both interrupt real runs. Apply the
label and **verify the write** by re-reading the PR's labels, exactly as eligibility.md E5
requires of its own label. A failed comment is not a revert failure — the revert already
succeeded — but an unposted comment or an unverified label write is an **escalation in the
report**, named by PR number, so the record does not silently lapse.

**Why both a label and git history feed the reverted-issue set.** Removing a label needs
only triage access on GitHub, so a label-only check could be cleared by an actor who could
not have merged in the first place — and re-admitting known-bad content is a fail-*open*.
The second signal is git: a merged PR's `mergeCommit` stays readable, and a revert of it
stays in the branch's history, so 2-1's set is built from either. What that pair does and
does not cover is stated at 2-1 and in Known limits #5 — it defers **later work on a
reverted issue**, not the same change reintroduced under a different one.

**R-5 — Stop the line.** Even after a clean recovery, process no further PR this run. One
verification failure means the pre-merge gates missed something, and the rest of the queue
deserves human eyes before the automation continues. Update the milestone PR with the
revert and the not-attempted set before reporting ([milestone-pr.md](milestone-pr.md) M3);
an outstanding escalation also blocks its ready flip (M4, F3).

## Escalation: when the revert itself fails

Stop immediately and return to a human when any of these holds: the branch head is not the
recorded merge commit (R-1); the revert commit cannot be created (R-1); **under a rebase
merge, the set of landed commits cannot be enumerated with certainty, or its count does not
reconcile against the PR's** (R-1); the push is rejected (R-2); or the recovery verification
fails or times out (R-3).

Escalating on an uncertain enumeration rather than reverting what is certain is deliberate:
a partial revert is the one failure mode that can pass R-3 and be reported as a successful
recovery.

**Record the exclusion before stopping.** "Stop immediately" governs *recovery*, not
*record-keeping*, and the distinction is load-bearing. R-4 is the last step of the revert, so
**any** escalation — R-1, R-2 or R-3 — reaches the human with R-4 never having run. A failed
revert therefore leaves the branch in the worst state this gate can produce: a bad merge still
on it, and **no** revert commit and **no** label to show for it. Both of 2-1's reverted-issue
signals are absent, so the next scheduled run finds the issue unexcluded and a new PR for it
merges straight back into the branch that is already broken. Stop-the-line does not help — it
binds only the run it happened in, and this run is ending.

So before returning to the human, in this order and best-effort:

1. **Apply the revert label** by cause (`merge-gate:reverted` / `merge-gate:unverified`,
   R-4's table) to the merged PR, and **verify the write**. This is the durable half — it is
   what 2-1 reads on the next run — and it is a label write on a PR, unaffected by whatever
   blocked the revert push.
2. **Post R-4's comment** if it can be posted. A rejected push does not imply a rejected
   comment; attempt it, and do not let its failure delay the escalation.
3. **If neither lands**, say so in the escalation itself, at the top of the report: name the
   PR and the issue by number and state in as many words that **nothing durable excludes this
   issue** and a later run will re-admit it unless a human acts. An unrecorded exclusion is
   the escalation's most urgent content, not a footnote to it.

**Say what the label means here, because on this path it does not mean what its name says.**
The revert labels were named for the case where the revert succeeded, and on the escalation
path it did not: the label is recording the **exclusion**, not a completed recovery. So the
comment and the escalation both state plainly that the merge is **still on the branch** and
was **not** reverted. A human who reads `merge-gate:reverted` and assumes the branch is clean
would be misled by the one record this step exists to leave, which would be worse than
leaving none.

None of this is a recovery attempt and none of it touches the branch: labels and comments are
platform metadata, they cannot make the branch state worse, and they are the only reason a
later run knows this happened. The prohibitions below are unchanged — there is still no
second revert, no force-push, no reset.

Escalate with the **full state** — the PR that was merged, its merge commit, what failed,
what was attempted, the integration branch's current head, and whether the exclusion record
landed — surfaced through the run's user-choice capability where a user is present and,
either way, at the top of the run report marked as requiring human action.

Then stop. Specifically:

- Do not retry destructive operations in a loop.
- Do not attempt creative alternative recoveries: **no force-push, no reset, no branch
  deletion, no re-creating the branch, no second revert on top of a failed one, and no
  partial revert of the commits you could identify.**
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

Deferred PRs accumulate through the run and are reported at the end. The queue has five
kinds of member, and the report distinguishes them:

| Kind | Source | Permanent? |
|---|---|---|
| Eligibility deferrals | eligibility.md's exclusion classes | E5 only; the rest are re-evaluated |
| Loop deferrals — conflict, red CI, unknown mergeability, refused merge | 2-2 / 2-1 / 2-3 | No — re-evaluated next run |
| **Reverted — verification failed** | auto-revert R-4 | Yes, until a human fixes the change and clears the label |
| **Reverted — unverified (timeout)** | auto-revert R-4 | Yes, until a human confirms CI health and clears the label |
| Not attempted | stop-the-line | No — the next run picks them up |

The two revert rows stay separate in the report as well as in the labels. "Reverted"
without a cause reads as "this change was bad", which is true of one row and an unfair
accusation in the other.

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
   reverts of healthy changes — the fix is the CI or the window, not a looser rule. The
   exclusion labels keep the two apart afterwards (R-4) so the blame lands correctly, but
   the revert itself cannot be avoided.
5. **The reverted-issue exclusion covers later work on a reverted issue, and nothing
   wider.** It defers a new PR attributing to an issue whose earlier PR was reverted. It
   does **not** detect the same change reintroduced under a *different* issue; once the
   label is cleared it survives only as long as the integration branch keeps the revert
   commit in its history; and because the set is keyed by attribution, it inherits E1c's
   limits — the gate infers which issue a PR belongs to, it cannot observe it. It is a
   brake on the obvious repeat, not a content check.
