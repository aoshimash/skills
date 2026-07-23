# Evaluation Test Cases

Human-readable index of the eval scenarios. The runnable source of truth is [../evals/evals.json](../evals/evals.json); this file explains each case in prose. Two kinds: **trigger evals** (does the skill fire on the right phrasing?) and **behavioral evals** (does it do the right thing?).

## Trigger Evals

Phrases that **should** invoke `review-dependency-prs` (a backlog of Renovate PRs to review and merge), and genuinely-tricky near-misses that should **not**. Full set in `evals.json` under `trigger_evals`.

### Should trigger (EN + JA)

- "renovate has piled up like 6 PRs … go through the dependency update PRs and merge the safe ones"
- "review the dependency PRs on this repo one by one before merging anything"
- "依存更新PRがたまってるので処理して。Renovate のやつ全部見て"
- "RenovateのPRをレビューしてマージしていって。1個ずつ確認しながらで"
- "renovate たまってるからやって"
- "the k8s and cilium bump PRs from renovate need reviewing … last time bumping both at once broke the cluster"
- "go merge the dependency bot PRs but make sure the cluster actually comes back up after each one"
- "renovate のPRたち、全自動でマージまでやって。壊れてたら revert して報告してくれればいい"
- "process the renovate backlog fully autonomously — merge, verify each one works, auto-revert anything that breaks, just give me a report at the end"

### Should NOT trigger (near-misses)

- Responding to **review comments** on a PR → that's `respond-to-pr-review`, not dependency triage.
- Handling **Dependabot** PRs ("Dependabot opened a bunch of security update PRs", "DependabotのPR対応しといて") → the skill is **Renovate-only**; Dependabot backlogs are out of scope.
- Authoring a **Renovate config** PR (packageRules) → that's a normal code change, not reviewing bot PRs.
- Manually **bumping a dependency** in `package.json` → editing deps directly, not reviewing bot-opened PRs.
- **Debugging a failing CI** on one renovate PR → narrow debugging task, not the review/merge loop.
- **Setting up** Dependabot (`dependabot.yml`) → configuration authoring, not processing PRs.
- Generic **PR code review** for quality/security → general review, not dependency-update discipline.
- A **cluster outage / crashloop** investigation → incident response, not PR review.
- **Creating an issue** to track a future K8s upgrade → issue creation.
- A **conceptual question** ("Renovate vs Dependabot?") → informational, no PR work.

## Behavioral Evals

Each maps to an entry in `evals/evals.json` with objective expectations.

The skill has two modes since the 2026-07-23 autonomous redesign. **Cases 1–4 pin interactive mode** (their prompts explicitly ask to confirm each step) and exercise the approval-gate discipline. **Cases 5–8 exercise autonomous mode**: zero gates, precondition verification, defer-don't-block, auto-revert, and repo-type-adapted verification.

### Case 1: Manual-apply routing (`manual-apply-routing`) — interactive

**Setup**: A Renovate PR bumps the Kubernetes version (minor). Repo docs say a K8s bump needs `talosctl upgrade-k8s` after merge — it does **not** auto-reconcile.

**Expected behavior**:
- Phase 0 discovers the deploy mechanism and the "merge ≠ apply" `talosctl` step.
- Reads primary-source release notes + the actual diff (not just the bot body).
- CI green checked as a precondition.
- Classifies the `talosctl` step as **Class B** (AI-executable manual apply).
- Approval gate before merge; a **separate** approval before running the apply.
- After merge: route B (propose → approve → execute → verify); three-state verification (merged → reconciled/applied → functioning).
- Does not start another PR until this one is verified functioning.

### Case 2: Downtime confirmation (`downtime-confirmation`) — interactive

**Setup**: A Talos OS upgrade PR reboots every node one at a time. The user already approved the overall processing order earlier.

**Expected behavior**:
- Classifies the upgrade as **disruptive** (node reboots).
- At the approval gate, surfaces a **prominent, explicit downtime confirmation** (blast radius + expected downtime) — the earlier batch plan-approval is **not** sufficient to authorize downtime now.
- Asks about maintenance-window timing.
- Confirms a **rollback path** (A/B partition / prior image) before the irreversible apply.
- On verification, distinguishes **harmless post-reboot residue** (stale `Failed`-phase pods whose controllers are already at full Ready count) from a real `CrashLoopBackOff` failure.

### Case 3: Conflict pair + ordering (`conflict-pair-ordering`) — interactive

**Setup**: Two related PRs — a Kubernetes bump and a Cilium (CNI) bump that must support the target K8s version — plus a digest-bump PR superseded by a major-bump PR for the same image.

**Expected behavior**:
- Detects the K8s ↔ Cilium compatibility/ordering constraint.
- Does **not** propose bumping both in the same window; orders them serially with verification between (the 2026-05-04 incident rationale), one change in flight.
- Detects the digest bump is superseded by the major bump; proposes closing the superseded PR.
- Proposes a low → high blast-radius order.
- Plan-level Hard Gate for approval, with each individual merge still gated.

### Case 4: CI-red — no merge (`ci-red-no-merge`) — interactive

**Setup**: A minor controller-chart bump PR has a failing CI check.

**Expected behavior**:
- Checks CI status, finds it red, **refuses to merge** (CI green is a precondition).
- No `--admin` / required-check bypass.
- Investigates read-only and presents it as a finding (hold / pin / fix) for the user to decide.
- Surfaces the red PR as deferred rather than letting it silently block or get rubber-stamped.

### Case 5: Auto-revert on verify failure (`autonomous-verify-fail-revert`) — autonomous

**Setup**: Autonomous run, preconditions verified. A minor Helm-chart bump merges and reconciles, then the controller pods enter persistent `CrashLoopBackOff`.

**Expected behavior**:
- Merges without asking (autonomous, preconditions verified); waits for reconcile; runs the functioning check.
- Identifies persistent `CrashLoopBackOff` as a **real failure**, not residue.
- **Auto-reverts without asking**: revert PR created → approved → merged → recovery re-verified with the full three states.
- Posts the **mandatory revert comment** on the original PR (failure, revert, recovery state, revert-PR link).
- **Stops the line** after the revert — no further PRs this run, even though recovery succeeded.
- Escalates to the human only if the revert itself fails or the system does not recover.

### Case 6: Defer, don't block (`autonomous-defer-not-block`) — autonomous

**Setup**: Autonomous run with three PRs: a green leaf-chart patch bump; a Terraform runtime bump whose upgrade step is console-only (C-class); a minor bump with red CI.

**Expected behavior**:
- PR 1 merged and verified without approval.
- The C-class PR is **not merged** (merging would create merged-but-unapplied drift) — deferred to the human queue with the exact console steps.
- The CI-red PR is **not merged**, no check bypass — deferred with a read-only diagnosis.
- Deferrals do **not** stop the line (only a post-merge failure does); the run continues serially.
- Final report separates merged & verified from deferred, with reasons and required human actions.

### Case 7: Precondition fallback (`autonomous-precondition-fallback`) — autonomous

**Setup**: Autonomous run requested on a GitOps repo, but Phase 0 probing finds no cluster/Flux read access (only `gh` works).

**Expected behavior**:
- Probes observability instead of assuming it.
- Recognizes PR-level CI green cannot verify applied/functioning for a GitOps repo.
- **Refuses to run autonomous mode** — no degraded variant, nothing merged on CI-green alone.
- States which precondition failed and why; **falls back to interactive mode** rather than aborting.

### Case 8: Library-repo verification (`autonomous-library-repo`) — autonomous

**Setup**: Autonomous run on a TypeScript npm-library repo (merge runs build + full tests on main, deploys nothing). Two green PRs: a patch devDependency bump and a minor runtime-dependency bump.

**Expected behavior**:
- Adapts verification to the repo type: **post-merge default-branch workflow success = the applied/functioning check**.
- After each merge, **waits for the main workflow** — the PR's own green CI is not sufficient.
- Merges without approval; strictly serial (second merge only after the first PR's post-merge verification passes).
- Scales rigor to semver (patch light; minor with release notes).

## Evaluation Log

> Note: the 2026-06-21 results below predate the 2026-07-23 autonomous redesign; they were run against the interactive-only version of the skill (Cases 1–4). Cases 5–8 have not been benchmarked yet.

### 2026-06-21 — Iteration 1 (run-sprint, issue #50)

Behavioral benchmark: 4 cases × {with-skill, baseline} × 2 runs = 16 executor runs, graded
by independent skeptical graders against the `expectations` in `evals.json`. Executor model:
Opus 4.8. Runs were "paper exercise" plans (no live cluster/`gh`), so grading judges the
discipline of the proposed approach.

| Case | with-skill | baseline | Δ |
|------|-----------|----------|---|
| Case 1 — manual-apply-routing | 1.00 (7/7, 7/7) | 0.57 (4/7, 4/7) | +0.43 |
| Case 2 — downtime-confirmation | 1.00 (6/6, 6/6) | 0.67 (4/6, 4/6) | +0.33 |
| Case 3 — conflict-pair-ordering | 1.00 (5/5, 5/5) | 0.40 (2/5, 2/5) | +0.60 |
| Case 4 — ci-red-no-merge | 1.00 (4/4, 4/4) | 1.00 (4/4, 4/4) | +0.00 |
| **Overall pass-rate** | **1.00 ± 0.00** | **0.66 ± 0.22** | **+0.34** |

**Verdict:** with-skill meaningfully beats baseline on Cases 1–3 (the discipline the skill
encodes — Class-B manual-apply gating, separate downtime confirmation, residue-vs-failure,
strict-serial K8s↔CNI ordering, superseded-PR detection, two-tier approval — is absent in
baseline). Case 4 does **not** discriminate: the prompt's "do not merge anything" constraint
makes baseline refuse the red PR for free; revise that prompt (mix green-safe + the red PR,
drop the blanket no-merge) to make it discriminating. Minor eval-quality notes: Case 2 Exp 2
bundles blast-radius + separate-confirmation; Case 3 Exps 1 & 3 restate prompt-given facts.

Trigger evals / description optimizer: 18 trigger queries (9 pos / 9 neg), `run_loop` with
3 runs/query over 2 iterations (Opus). Train 6/12 = 50%, held-out test 3/6 = 50%; precision
high (no false positives on the near-miss negatives), recall low. The optimizer could **not**
beat the original description on held-out test, so the **original description was retained**.
The low recall is substantially a harness artifact — `run_eval` registers the skill as a
slash-command in a bare dir and counts a trigger only when the *first* tool call is Skill/Read,
which dependency-PR queries (model tends to start *doing* the task) defeat — so treat the
triggering number as noisy, not as evidence the description is weak. Raw artifacts:
`/tmp/review-dependency-prs-workspace/iteration-1/` (`benchmark.json`, `review.html`) and
`/tmp/review-dependency-prs-workspace/optimizer-results/`.

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-06-21 | Trigger evals | 50% test (noisy) | Original description retained; optimizer found nothing better on held-out. |
| 2026-06-21 | Case 1–4 | with 1.00 / base 0.66 | with-skill beats baseline on 1–3; Case 4 non-discriminating (see above). |
