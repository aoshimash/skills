# Verification, Downtime, Rollback, and Stop-the-Line

Detailed procedure for Phase 2's verification step (workflow.md 2-9), plus the downtime classification and rollback-readiness check referenced from the approval gate (2-5).

## Table of Contents

- [The core distinction: merged ≠ deployed ≠ working](#the-core-distinction-merged--deployed--working)
- [Three-state verification](#three-state-verification)
- [Harmless residue vs. real failure](#harmless-residue-vs-real-failure)
- [Downtime classification](#downtime-classification)
- [Rollback-readiness check (before irreversible applies)](#rollback-readiness-check-before-irreversible-applies)
- [Stop-the-line failure handling](#stop-the-line-failure-handling)

## The core distinction: merged ≠ deployed ≠ working

"Merged the PR and CI is green" is not "the change is live and the system is healthy." Three separate states must each be confirmed:

1. **Merged** — the change is in Git. (Easy; a `gh pr view` confirms it.)
2. **Deployed / applied** — the change reached the running system: a GitOps controller reconciled it, CI deployed it, or a manual apply ran. In GitOps repos this is **asynchronous** — the merge returns instantly but Flux/Argo may take minutes to reconcile.
3. **Functioning** — the system is actually healthy after the change: health checks pass, the app responds, no regression appeared.

A "post-merge check passed" that only confirmed state 1 (or even 2) is a false sense of done. The 2026-05-04 outage looked "merged and applied" while the cluster was cascading into failure.

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

- Run the relevant health checks (pods Ready at expected replica count, endpoints responding, the upgraded component reporting the new version, etc.).
- **Regression check:** confirm nothing that worked before is now broken — not just that the upgraded component is up. An upgrade can be "applied successfully" and still break a dependent service.
- Wait for transient states to settle (rolling restarts, leader elections) before judging health.

Only when V-3 passes is the PR done. Then proceed (workflow.md 2-9).

## Harmless residue vs. real failure

After disruptive changes (especially reboots), the system often shows **alarming-but-harmless residue**. Misreading it either way is bad: panicking over residue causes needless rollbacks; dismissing a real failure as residue ships an outage. Distinguish deliberately:

| Looks alarming | Likely harmless residue when… | Likely real failure when… |
|---|---|---|
| `Failed`-phase pods after a node reboot | Their controller (Deployment/DaemonSet/StatefulSet) is **already at full Ready count** — the `Failed` pods are stale replicas from before the reboot that the scheduler hasn't garbage-collected. | The controller is **not** at its desired Ready count, or new pods keep entering `Failed`. |
| Pods restarting | A one-time restart during a rolling update that then stays `Running`/`Ready`. | `CrashLoopBackOff` — restart count climbing, never reaching `Ready`. |
| Brief endpoint errors | Errors only during the rollout window, clearing once pods are Ready. | Errors persisting after the rollout settled. |

The deciding question is usually: **is the controller at its desired ready state, and is the residue static (not growing)?** If yes, it is residue — note it and move on. If the failure indicators are live and growing, it is real — go to stop-the-line. When you genuinely cannot tell, **fail closed**: treat it as a real failure.

## Downtime classification

Used at the approval gate (workflow.md 2-5) to decide whether a change needs the prominent downtime confirmation. Classify the change's disruption:

| Class | Examples | Gate |
|---|---|---|
| **Non-disruptive** | Rolling update with surge, multi-replica deployment, additive config. | Normal approval. |
| **Disruptive** | Node reboot (Talos/OS upgrade), single-replica restart, DB failover, control-plane disruption, CNI restart affecting networking. | **Prominent, explicit downtime confirmation** spelling out blast radius + expected downtime + maintenance-window timing — even if the plan was batch-approved. |

When in doubt about whether a change reboots a node or restarts a singleton, treat it as disruptive and confirm.

## Rollback-readiness check (before irreversible applies)

Before any **irreversible or disruptive** apply, confirm a rollback path actually exists — *before* pulling the trigger, not after it fails. Match the path to the change:

| Change | Rollback path to confirm |
|---|---|
| etcd / control-plane mutation | A current **etcd snapshot** exists. |
| App/manifest change (GitOps) | A **revert PR** restores the prior state, and the controller will reconcile it. |
| Node OS / kernel | An **A/B partition** or prior image is available to boot back into. |
| Helm release | `helm rollback` to the prior revision is available. |
| Database migration | A **backup** taken immediately before, and the migration is reversible (or a down-migration exists). |

If no rollback path exists for an irreversible change, **say so at the approval gate** — that materially changes the risk and the user may choose to defer or to create a rollback path first.

## Stop-the-line failure handling

When an apply or verification fails (workflow.md 2-9), or residue resolves to a real failure:

1. **Stop.** Do **not** proceed to the next PR. The serial discipline exists precisely so that a failure is isolated to one change; carrying on would compound it (the 2026-05-04 lesson).
2. **Surface** the problem clearly: what was applied, what failed, what the current state is.
3. **Offer rollback** using the path confirmed at the approval gate. Present it as a proposal (rollback is itself a mutating action that needs approval), with the steps.
4. **Get user direction** — roll back, investigate together, or hold.
5. **Fail closed when uncertain.** If you cannot determine whether the change is working, do not optimistically continue. Treat unknown as failed and stop.

Never fabricate a passing result to keep the loop moving. A truthful "this failed, here's the state, here's the rollback option" is the correct output.
