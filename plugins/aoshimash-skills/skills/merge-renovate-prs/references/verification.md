# Verification, Downtime, Rollback, Auto-Revert, and Escalation

Detailed procedure for Phase 2's verification step (workflow.md 2-9), the downtime classification and rollback-readiness check used by the go/defer decision (2-5), and the autonomous auto-revert procedure.

## Table of Contents

- [The core distinction: merged ≠ deployed ≠ working](#the-core-distinction-merged--deployed--working)
- [Three-state verification](#three-state-verification)
- [Adapting verification to the repo type](#adapting-verification-to-the-repo-type)
- [Harmless residue vs. real failure](#harmless-residue-vs-real-failure)
- [Downtime classification](#downtime-classification)
- [Rollback-readiness check (a merge precondition in autonomous mode)](#rollback-readiness-check-a-merge-precondition-in-autonomous-mode)
- [Failure handling: auto-revert (autonomous) / stop-the-line (interactive)](#failure-handling-auto-revert-autonomous--stop-the-line-interactive)

## The core distinction: merged ≠ deployed ≠ working

"Merged the PR and CI is green" is not "the change is live and the system is healthy." Three separate states must each be confirmed:

1. **Merged** — the change is in Git. (Easy; the PR's merged state confirms it — with the CLI, `gh pr view`.)
2. **Deployed / applied** — the change reached the running system: a GitOps controller reconciled it, CI deployed it, or a manual apply ran. In GitOps repos this is **asynchronous** — the merge returns instantly but Flux/Argo may take minutes to reconcile.
3. **Functioning** — the system is actually healthy after the change: health checks pass, the app responds, no regression appeared.

A "post-merge check passed" that only confirmed state 1 (or even 2) is a false sense of done. The 2026-05-04 outage looked "merged and applied" while the cluster was cascading into failure. In autonomous mode this distinction carries the whole safety story: the post-merge verification is what replaced the human approval, so cutting it short is not an optimization — it is removing the brakes.

## Three-state verification

For each PR, after merge and after running any A/B/C apply:

### V-1: Confirm merged

Confirm the PR is merged and the expected commit is on the default branch.

### V-2: Confirm deployed/applied (async-wait)

Confirm the change reached the environment. This depends on the deploy mechanism from Phase 0:

- **GitOps (Flux/Argo):** poll the controller until it reports the new revision reconciled — do **not** assume reconcile is instant. Wait for the reconcile to complete (or the controller's healthy/synced status), with a sane timeout. If it does not reconcile, that is a failure, not "give it more time forever".
- **CI deploy:** confirm the deploy job ran and succeeded.
- **Manual apply (B/C):** confirm the apply command's output indicates success, or the user confirmed the C step.

### V-3: Confirm functioning (health + regression)

Confirm the system is healthy *because of and despite* the change:

- Run the checks from the **verification plan** assembled in Phase 0-4 — the human-supplied checks (user request, repo runbooks/docs) plus the repo-type baseline (pods Ready at expected replica count, endpoints responding, the upgraded component reporting the new version, etc.). Do not substitute weaker checks for ones a human defined, and do not invent sufficiency the plan does not claim.
- **Regression check:** confirm nothing that worked before is now broken — not just that the upgraded component is up. An upgrade can be "applied successfully" and still break a dependent service.
- Wait for transient states to settle (rolling restarts, leader elections) before judging health. For changes classified **disruptive** (see below), use an extended settle window.

Only when V-3 passes is the PR done. Then proceed (workflow.md 2-9). The one exception is an artifact whose publish is gated behind a separate trigger, which has no V-3 yet — see [Gated publish](#gated-publish-merged-is-not-shipped).

## Adapting verification to the repo type

The three states are universal; what implements V-2/V-3 differs by what the repo ships. Phase 0's deploy-mechanism discovery tells you which row applies:

| Repo type | V-2 (applied) | V-3 (functioning) |
|---|---|---|
| **GitOps** (Flux/Argo → cluster) | Controller reports the new revision reconciled/synced. | Workloads Ready at expected counts, endpoints respond, upgraded component reports the new version, no regression in dependents. |
| **CI-deploy app** (merge to main triggers deploy) | The post-merge deploy workflow on the default branch succeeded. | The deployed service's health checks / smoke tests pass; monitoring shows no regression. |
| **Library / no deploy** (e.g. an npm package repo where merge ships nothing) | The post-merge workflow (build + full test suite) on the default branch succeeded. | Nothing beyond V-2 exists to observe — the default-branch CI **is** the functioning check. Do not invent one; do not skip waiting for it either. The PR's own green CI is *not* a substitute: verify the suite on the merged default branch. |
| **Artifact with gated publish** (the repo builds a container image or package, and publishes it only on a trigger separate from the merge — a version tag, a manual dispatch, a release; consumers pin the published version) | **No deployment occurred, and that is correct.** Confirm the default branch holds the change and the artifact-build job — the one that builds without publishing — succeeded on the merged default branch. Where that job runs only on pull requests, its passing run on the head that merged is the evidence; say so in the report. Do not wait for a reconcile or deploy job: none will run. | **Does not exist yet.** The registry and every consumer still hold the previously published artifact. Do not invent a V-3, and do not substitute the build job for one. The PR is done at V-2 but is **not** "merged & verified": it always leaves a follow-up (below). |

This is why autonomous mode's Phase 0 precondition is stated as *observability*, not "cluster access": for a library repo, being able to read post-merge workflow results on the default branch is sufficient observability. The same holds for the gated-publish row.

### Gated publish: merged is not shipped

The gated-publish row is the one where merged ≠ deployed ≠ working bites hardest, because every state the run can check comes back clean while the change is in no running system. It differs from the library row in that something downstream exists — the registry and the consumers — and is still running the previous artifact, indefinitely, until someone acts.

- **Recognize it in Phase 0 (workflow.md 0-1).** The workflow that pushes the artifact triggers on `push: tags`, `release`, or `workflow_dispatch`, never on a push to the default branch; a separate job builds the same artifact on pull requests or pushes without publishing it; consumers reference the artifact by version or digest, in this repository or elsewhere. Decide per artifact the PR changes, not per repo: a repo can auto-deploy one target and gate another, and a PR touching both gets both rows.
- **It is not a manual-only deploy for 0-4's revert-path precondition.** Merging published nothing, so a revert PR restores the source and there is nothing else to undo; observability is the default-branch workflow runs, as for a library repo. Do not fall back to interactive mode for this row.
- **The publish and the consumers' pin bumps are not this PR's work.** They are the artifact's release: the trigger is deliberately separate from the merge, so merging without them creates no drift, and they are not classified A/B/C (workflow.md 2-4). The agent never fires the publish trigger or bumps a consumer's pin, even where a runbook or Renovate note describes the step: a published version is not undone by a revert PR, so running it would leave the run without the rollback path its merges depend on. Those steps go in the follow-up, for a human.
- **The follow-up is mandatory.** For every PR this row covers, record what reaching the running system still takes and who does it: fire the publish trigger (name it — the tag pattern, the workflow to dispatch, or the release to create), then bump each consumer's pin (name the consumers found, or say none were located). "Who" is the role or document the repo names for releasing, else a maintainer. It goes on the PR (workflow.md 2-8) and in the report's own category (3-1).

## Harmless residue vs. real failure

After disruptive changes (especially reboots), the system often shows **alarming-but-harmless residue**. Misreading it either way is bad: panicking over residue causes needless reverts; dismissing a real failure as residue ships an outage. Distinguish deliberately:

| Looks alarming | Likely harmless residue when… | Likely real failure when… |
|---|---|---|
| `Failed`-phase pods after a node reboot | Their controller (Deployment/DaemonSet/StatefulSet) is **already at full Ready count** — the `Failed` pods are stale replicas from before the reboot that the scheduler hasn't garbage-collected. | The controller is **not** at its desired Ready count, or new pods keep entering `Failed`. |
| Pods restarting | A one-time restart during a rolling update that then stays `Running`/`Ready`. | `CrashLoopBackOff` — restart count climbing, never reaching `Ready`. |
| Brief endpoint errors | Errors only during the rollout window, clearing once pods are Ready. | Errors persisting after the rollout settled. |

The deciding question is usually: **is the controller at its desired ready state, and is the residue static (not growing)?** If yes, it is residue — note it and move on. If the failure indicators are live and growing, it is real — go to failure handling. When you genuinely cannot tell, **fail closed**: treat it as a real failure. (In autonomous mode, fail-closed means an auto-revert — a needless revert of a healthy change is recoverable; a dismissed outage is not.)

## Downtime classification

Classify every change's disruption. The classification is used differently per mode (workflow.md 2-5):

| Class | Examples | Autonomous | Interactive |
|---|---|---|---|
| **Non-disruptive** | Rolling update with surge, multi-replica deployment, additive config. | Proceed normally. | Normal approval. |
| **Disruptive** | Node reboot (Talos/OS upgrade), single-replica restart, DB failover, control-plane disruption, CNI restart affecting networking. | **Not a gate** — proceed, but: use an extended settle window in V-3, respect any timing constraint the user gave (defer if it cannot be honored now), and flag the change prominently in the final report. | **Prominent, explicit downtime confirmation** spelling out blast radius + expected downtime + maintenance-window timing — even if the plan was batch-approved. |

When in doubt about whether a change reboots a node or restarts a singleton, treat it as disruptive.

## Rollback-readiness check (a merge precondition in autonomous mode)

Before merging (autonomous) or before any irreversible/disruptive apply (interactive), confirm a rollback path actually exists — *before* pulling the trigger, not after it fails. Match the path to the change:

| Change | Rollback path to confirm |
|---|---|
| App/manifest change (GitOps) | A **revert PR** restores the prior state, and the controller will reconcile it. |
| App change (CI deploy) | A **revert PR** redeploys the prior version via the pipeline. |
| Library dependency bump | A **revert PR** restores the prior lockfile/manifest. (Trivially true; the check is quick.) |
| Artifact with gated publish (source of an image or package published on a separate trigger) | A **revert PR** restores the source. The merge published nothing, so nothing else needs undoing — as long as the agent does not fire the publish trigger, which it never does ([Gated publish](#gated-publish-merged-is-not-shipped)). |
| Helm release (B-class apply) | `helm rollback` to the prior revision is available. |
| etcd / control-plane mutation | A current **etcd snapshot** exists. |
| Node OS / kernel | An **A/B partition** or prior image is available to boot back into. |
| Database migration | A **backup** taken immediately before, and the migration is reversible (or a down-migration exists). |

Mode difference:

- **Autonomous:** a verified rollback path is a **merge precondition**. Revert-PR-based paths are usually verifiable from Phase 0's deploy mechanism alone; the non-git paths (snapshot, A/B partition, backup) must be confirmed to exist for the specific change. **No verified path → defer the PR unmerged** (workflow.md 2-5). Additionally, for B-class applies, identify the **inverse operation** before running the forward one — if no safe inverse exists and no other path covers it, defer.
- **Interactive:** if no rollback path exists for an irreversible change, **say so at the approval gate** — that materially changes the risk and the user may choose to defer or to create a rollback path first.

## Failure handling: auto-revert (autonomous) / stop-the-line (interactive)

Entered from workflow.md 2-9 when an apply or verification fails, or residue resolves to a real failure. In both modes the serial discipline is why this works: the failure maps to exactly one change, so the revert target is unambiguous.

### Autonomous: auto-revert procedure

1. **Revert in Git.** Create a revert PR for the merged change (see [platform-github.md](platform-github.md) for the commands, including the merge-method-dependent revert form), approve it, and merge it. Do not wait for the bot or a human — this is the pre-verified rollback path being exercised.
2. **Undo any B-class apply.** If a manual apply ran (2-7), execute the inverse operation identified during the rollback-readiness check (e.g. `helm rollback`). Order matters: revert Git first so a GitOps controller does not re-apply the bad version over your rollback.
3. **Verify the recovery.** Re-run the full three-state verification on the *reverted* state: revert merged → reconciled/deployed → system functioning again. A revert that has not been verified is just another unverified change.
4. **Document and stop the line.** Post the mandatory revert comment on the original PR (what failed, what was reverted, recovery state, link to the revert PR — workflow.md 2-8). Then stop processing further PRs this run, even though recovery succeeded: one verification failure means the pre-check missed something, and the remaining queue deserves human eyes before the automation continues. Report per Phase 3.
5. **Escalate when the revert path fails.** If the revert PR cannot be created or merged, the inverse apply errors, or the recovery verification does not pass: **stop immediately and escalate to the human** with the full state — what was merged, what failed, what was attempted, what the system looks like now. Do not retry destructive operations in a loop. Do not attempt creative alternative recoveries unprompted. This is the one place autonomous mode always comes back to a person.

### Interactive: stop-the-line

1. **Stop.** Do **not** proceed to the next PR. The serial discipline exists precisely so that a failure is isolated to one change; carrying on would compound it (the 2026-05-04 lesson).
2. **Surface** the problem clearly: what was applied, what failed, what the current state is.
3. **Offer rollback** using the path confirmed at the approval gate. Present it as a proposal (rollback is itself a mutating action that needs approval), with the steps.
4. **Get user direction** — roll back, investigate together, or hold.
5. **Fail closed when uncertain.** If you cannot determine whether the change is working, do not optimistically continue. Treat unknown as failed and stop.

Never fabricate a passing result to keep the loop moving. A truthful "this failed, here is the state, here is what was reverted (or the rollback proposal)" is the correct output.
