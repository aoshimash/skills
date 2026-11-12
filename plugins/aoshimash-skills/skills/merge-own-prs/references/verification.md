# Verification: Plan, Three States, and the Stopped Line

Detailed procedure for the verification plan (Phase 2 step 4, [workflow.md](workflow.md) "2-4" item 6), post-merge verification (2-7), and what happens when it fails.

## Table of Contents

- [Merged ≠ deployed ≠ working](#merged--deployed--working)
- [The verification plan](#the-verification-plan)
- [Three-state verification](#three-state-verification)
- [Adapting to the repository type](#adapting-to-the-repository-type)
- [Residue or failure](#residue-or-failure)
- [On failure](#on-failure)
  - [The revert](#the-revert)

## Merged ≠ deployed ≠ working

"Merged and CI green" is not "live and healthy." Three states are confirmed separately:

1. **Merged** — the change is on the base branch.
2. **Deployed / applied** — it reached the running system: a GitOps controller reconciled it, a pipeline deployed it, a VCS-driven infrastructure run applied it. Often asynchronous: the merge returns at once, the deploy takes minutes.
3. **Working** — the system is healthy with the change: its checks pass and nothing that worked before broke.

The human approved the merge from the brief, which promised this verification. Cutting it short leaves that promise unkept.

## The verification plan

Built before the brief, per PR, from human-authored sources first:

1. **The user's request** — checks stated when the run started ("after each merge, check the ingress answers").
2. **The PR itself** — a test plan or verification steps in its description, written by the user for this change.
3. **The repository's docs** — runbooks, deploy docs, agent instructions read in Phase 1.
4. **The repo-type baseline** — the rows below.

The agent executes this plan; it does not judge it sufficient on its own. For a `high`-risk PR whose only checks are the baseline, say so in the brief — the human may add checks or accept the baseline.

**Probe before the brief.** Run each check's read-only probe now (a status read, a health endpoint, a workflow-run list) and confirm it returns data. A probe that fails is listed in the brief as "cannot be read now" with its error. If the error says a configured credential expired, name the login command its output or the repository's docs give: re-authenticating is the user's act in their own terminal or browser, never the agent's — the agent does not run the login, drive a browser or device flow, or accept a token in the conversation. After the user says it is done, re-run the same probe; only data counts.

## Three-state verification

### V-1: Merged

The PR reads `MERGED` and its merge commit is on the base branch ([platform-github.md](platform-github.md) "Merge").

### V-2: Deployed / applied

Wait for the mechanism the plan named, with a timeout taken from the repository's docs or, absent one, a reasonable bound for that mechanism, stated in the report. Not reaching the state within it is a failure, not a reason to wait forever.

### V-3: Working

Run the plan's checks, and a regression check: what depended on the changed component still works — not just that the component itself is up. Let transient states settle (rolling restarts, leader elections) before judging.

Only when V-3 passes is the PR done.

## Adapting to the repository type

Phase 1's reading of the deploy docs tells you which row applies. A PR can touch more than one target; each gets its row.

| Repository type | V-2 (applied) | V-3 (working) |
|---|---|---|
| **GitOps** (Flux/Argo → cluster) | The controller reports the merge's revision reconciled and healthy. | Workloads Ready at expected counts, endpoints respond, dependents healthy. |
| **CI deploy** (merge to the base branch triggers a deploy) | The deploy workflow run for the merge commit completed successfully ([platform-github.md](platform-github.md) "Runs for the merge commit"). | The deployed service's health checks or smoke tests pass; monitoring the plan names shows no regression. |
| **VCS-driven infrastructure** (Terraform Cloud/HCP, Atlantis, a plan-and-apply workflow) | The apply for the merge commit finished successfully and applied what the PR's plan showed. | The changed resources are in the intended state; the plan's checks pass. |
| **Library or no deploy** | The default branch's post-merge workflows for the merge commit completed successfully. | Nothing further exists to observe: the default branch's CI is the working check. The PR's own green CI is not a substitute. |
| **Release on a separate trigger** (a tag, a manual dispatch, a release publishes it) | The default branch's post-merge workflows passed; no publish was expected and none is started. | Does not exist yet. Report the follow-up — which trigger publishes it and who fires it. Never fire it. |
| **Settings or docs only** (repository metadata, docs, comments) | Same as library. | Same as library. |

## Residue or failure

After a disruptive change, the system can show alarming but harmless residue — failed pods left from before a restart while their controller is already at full Ready count, a restart during a rolling update that then stays Ready, errors only inside the rollout window. Judge by whether the desired state is reached and the residue is static. When you cannot tell, **fail closed**: treat it as a failure.

## On failure

Entered when V-2 or V-3 fails, a check cannot be read after the merge, or the merge outcome is unconfirmed. The human is present, so the human chooses the recovery: a revert is usual, but for the user's own change the cause may be outside it, or fixing forward may be better.

1. **Stop the line.** Start no other PR.
2. **Show** — what was merged (PR, merge commit), which check failed and its evidence, what the system looks like now.
3. **Propose** — a revert PR (what it reverts, how it is built for this merge method, how it will be verified), and, where the evidence points to one, a fix forward or the outside cause.
4. **Ask** (user choice): **revert** / **fix forward** (the fix goes through a new PR the user names or opens, not this run's loop) / **hold** (leave it; the report says what is live and broken).
5. **Never fabricate a pass** to keep the loop moving, and never retry a destructive step in a loop.

The run does not continue to the next PR after a failure, even after a successful revert. The human may tell it to continue; ask explicitly once recovery is verified.

### The revert

On "revert":

1. Create the revert PR from the base branch at its current head ([platform-github.md](platform-github.md) "Create a revert PR").
2. It is the user's own PR: run its gate (2-4: CI green, no conflicts) and show a short brief — the revert's diff, CI state, and the verification it will get. The human's "revert" answer approved this merge in advance only if the revert's diff is exactly the inverse of the merged change and CI is green; otherwise ask again.
3. Post a COMMENT review recording why it reverts, merge it the same way 2-6 merged the original, and confirm it merged.
4. Verify the recovery with the same three states on the reverted state.
5. Comment on the original PR: what failed, what was reverted, the recovery state, a link to the revert PR.

A revert that cannot be created, merged, or verified: stop immediately, show the full state, and wait for the human. Do not try other recoveries unprompted.
