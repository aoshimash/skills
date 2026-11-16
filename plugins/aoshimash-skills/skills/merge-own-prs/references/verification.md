# Verification: What This Skill Adds to the Safety Net

The post-merge procedure — the deploy mechanism, the verification plan's sources, the A/B/C taxonomy, the merge call's result, three-state verification and its repo-type rows, residue, and the interactive stop-the-line — is in [post-merge-safety-net.md](post-merge-safety-net.md), mapped to this skill's steps in [workflow.md](workflow.md) "The post-merge safety net". This file holds only what is true for this skill alone: it is always interactive, its plan is built per PR before the brief, two repository types the safety net does not list, and what the human may choose after a failure.

## Table of Contents

- [Always interactive](#always-interactive)
- [The verification plan](#the-verification-plan)
- [Repository types the safety net does not list](#repository-types-the-safety-net-does-not-list)
- [On failure](#on-failure)
  - [The revert](#the-revert)

## Always interactive

The human approves every merge, so this skill runs every section of the safety net in its **interactive** form and never its autonomous one. The autonomous-only parts never run here: the preconditions' fallback to interactive mode, the knowledge-gap deferral of an unattended launch, the [auto-revert procedure](post-merge-safety-net.md#autonomous-auto-revert-procedure), and its [wait for the revert PR's required checks](post-merge-safety-net.md#waiting-for-the-revert-prs-required-checks). Where the safety net says "autonomous: defer", this skill shows the reason in the brief and the human decides; where it says "interactive: surface", the same. Nothing in this skill reverts, fixes forward, or continues past a failure without the human's choice ([On failure](#on-failure)).

## The verification plan

Built at 2-4 item 6, per PR, before the brief — not once at run start. It takes its sources, in this order, from the safety net's [verification plan](post-merge-safety-net.md#verification-plan-and-autonomous-preconditions), with the PR as this skill's per-PR source:

1. **The user's request** — checks stated when the run started.
2. **The PR itself** — a test plan or verification steps in its description, written by the user for this change. It ranks before the repository's docs because the user wrote it for exactly this change.
3. **The repository's docs** — read in Phase 1.
4. **The repo-type baseline** — the safety net's [repo-type table](post-merge-safety-net.md#adapting-verification-to-the-repo-type), plus the rows [below](#repository-types-the-safety-net-does-not-list).

That section of the safety net is written for autonomous mode, so its knowledge-gap question and its precondition fallbacks do not apply as written. What carries over is its split of responsibility — humans say what to check, the agent probes and runs it, and never judges the plan sufficient on its own. For a `high`-risk PR whose only checks are the baseline, say so in the brief: the human may add checks or accept the baseline.

**Probe before the brief.** Run each check's read-only probe now and confirm it returns data. A probe that fails is listed in the brief as "cannot be read now", with its error. Classify the failure and identify any remediation as the safety net's section says (structural or recoverable, and "Deriving a remediation"); its rules that the agent never performs the re-authentication and that only the same probe returning data counts apply unchanged. What follows differs: nothing falls back. The human decides at the brief whether to merge without the check, or to carry out the remediation and have the same probe re-run. Two run-start limits there do not apply, because every probe here is per PR: remediation is offered for each PR's probes (not only run start's), and each PR's brief gets its own round (not one per run).

## Repository types the safety net does not list

Two rows beside the safety net's [repo-type table](post-merge-safety-net.md#adapting-verification-to-the-repo-type). A PR can touch more than one target; each gets its row.

| Repository type | V-2 (applied) | V-3 (working) |
|---|---|---|
| **VCS-driven infrastructure** (Terraform Cloud/HCP, Atlantis, a plan-and-apply workflow) | The apply for the merge commit finished successfully and applied what the PR's plan showed. | The changed resources are in the intended state; the plan's checks pass. |
| **Settings or docs only** (repository metadata, docs, comments) | Same as the library row. | Same as the library row. |

## On failure

Entered from the safety net's [interactive stop-the-line](post-merge-safety-net.md#interactive-stop-the-line) — an apply or V-2/V-3 that fails, a check that cannot be read after the merge, residue that resolves to a real failure — and also from 2-6 when the merge outcome is unconfirmed. Run that procedure: stop, surface, offer the rollback as a proposal, get the human's direction, fail closed. This skill adds three things to it, because the PR is the user's own change and the user is present:

- **The proposal** names a revert PR — what it reverts, how it is built for this merge method, how it will be verified — and, where the evidence points to one, a fix forward or a cause outside the change. Where a B-class apply ran, it also names that apply's inverse ([rollback-readiness](post-merge-safety-net.md#rollback-readiness-check-a-merge-precondition-in-autonomous-mode)).
- **The choice** (user choice) is **revert** / **fix forward** (the fix goes through a new PR the user names or opens, not this run's loop) / **hold** (leave it; the report says what is live and broken). A question or a request to investigate together is answered, and the choice is asked again. No answer is a hold, never a revert.
- **The line stays stopped** after any answer, even after a verified revert. The human may tell the run to continue; ask that explicitly, once, after recovery is verified.

Never fabricate a pass to keep the loop moving, and never retry a destructive step in a loop.

### The revert

Only on "revert":

1. Create the revert PR from the base branch at its current head ([platform-github.md](platform-github.md) "Create a revert PR", which builds the merge-method-dependent form).
2. It is the user's own PR: run its gate (2-4: CI green, no conflicts) and show a short brief — the revert's diff, CI state, and the verification it will get. The human's "revert" answer approved this merge in advance only if the revert's diff is exactly the inverse of the merged change and CI is green; otherwise ask again.
3. Post a COMMENT review recording why it reverts, merge it the same way 2-6 merged the original, and classify the call and read the state as the safety net's [merge call's result](post-merge-safety-net.md#pre-merge-steps-and-the-merge-calls-result) defines. Run a B-class inverse only after the revert has merged and only on its own approval — Git first, so a GitOps controller does not re-apply the bad version over it.
4. Verify the recovery with the safety net's [three-state verification](post-merge-safety-net.md#three-state-verification) on the reverted state.
5. Comment on the original PR with what the safety net's revert comment carries ([Safety-net PR comments](post-merge-safety-net.md#safety-net-pr-comments)): what failed, what was reverted, the recovery state, a link to the revert PR.

A revert that cannot be created, merged, or verified: stop immediately, show the full state, and wait for the human. Do not try other recoveries unprompted.
