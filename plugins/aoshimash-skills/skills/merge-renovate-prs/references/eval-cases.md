# Evaluation Test Cases

Human-readable index of the eval scenarios. The runnable source of truth is [../evals/evals.json](../evals/evals.json); this file explains each case in prose. Two kinds: **trigger evals** (does the skill fire on the right phrasing?) and **behavioral evals** (does it do the right thing?).

## Trigger Evals

Phrases that **should** invoke `merge-renovate-prs` (a backlog of Renovate PRs to review and merge), and genuinely-tricky near-misses that should **not**. Full set in `evals.json` under `trigger_evals`.

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

The skill has two modes since the 2026-07-23 autonomous redesign. **Cases 1–4 pin interactive mode** (their prompts explicitly ask to confirm each step) and exercise the approval-gate discipline. **Cases 5–9 exercise autonomous mode**: zero gates, precondition verification, defer-don't-block, auto-revert, repo-type-adapted verification, and human-supplied verification checks. **Cases 10–11** (added 2026-10-19) cover the release-age gate and grouping proposals; both fixtures are taken from real aoshimash/homelab-k8s PRs (#374, #345) with their actual tables, commits, and dates. **Cases 16–17** (added 2026-10-27) cover Renovate `prBodyNotes` as a classification input; both fixtures are real homelab-k8s PRs (#387, #374) and its config's actual notes.

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

### Case 9: Human-supplied verification checks (`human-supplied-verification`) — autonomous

**Setup**: Autonomous run, user present at start. A runbook defines postgres health checks (write acceptance, replication lag < 10s). Two PRs: a postgres image bump (runbook applies) and a CoreDNS image bump (no documented checks).

**Expected behavior**:
- Phase 0 assembles the per-target verification plan from **human-authored sources** (the runbook) plus the repo-type baseline, and reports it with sources.
- Postgres V-3 runs the **runbook's checks verbatim** — no weaker substitutes.
- CoreDNS (high blast radius, no human-defined checks): asks the present user **once at run start** to supply checks or accept the baseline — a **knowledge gate**, not an approval gate; in an unattended launch it would defer instead.
- Probes that planned checks are executable before merging.
- Never invents its own sufficiency claims.

### Case 10: Cooldown without a registry timestamp (`cooldown-without-registry-timestamp`) — autonomous

**Setup** (from homelab-k8s#374): `minimumReleaseAge: 3 days`, with `timestamp-optional` for digests and ghcr.io. A grouped "container images" PR holds a Home Assistant GHCR digest bump and a paperless-ngx 3.3.0 → 3.3.2 bump; its commits are a renovate[bot] commit and a later `update-branch` merge commit by a human. A second PR (aqua) was aged by Renovate.

**Expected behavior**:
- Takes the threshold from the config, and checks the GHCR members even though `timestamp-optional` lets Renovate skip them.
- Ages paperless-ngx from its upstream release date (~21h); ages the digest member from the lower bound — the **Renovate-authored** commit, not the human merge commit.
- The grouped PR is as young as its youngest member → **cooldown wait**: not merged, not in the human queue, reported with an "earliest" eligible date.
- Posts one cooldown-wait marker comment (first lower-bound wait); the aqua PR proceeds normally.

### Case 11: Grouping split proposal (`grouping-split-proposal`) — autonomous wrap-up

**Setup** (from homelab-k8s#345 / #348): a grouped "container images" PR mixing the actions-runner-controller charts with app images was held once for ARC, then merged and auto-reverted because of ARC — rolling back the healthy app updates too. The config's grouping rules and their comments are given.

**Expected behavior**:
- Reports the revert, its cause, and the stop-the-line.
- Proposes taking ARC out of the "container images" group, citing this run's evidence, with a concrete `packageRules` entry placed after the docker rule (later rules win).
- Addresses the config comment's rationale and states the cost of the split.
- Offers the config change without making it; proposes nothing for members that caused no problem.

### Case 12: Unauthenticated connector, authenticated CLI (`platform-access-unauthenticated-connector`) — autonomous

**Setup** (observed in a real session on 2026-10-25): the session lists a GitHub connector (`plugin:engineering:github`) among MCP servers that require authentication before their tools can be used; `gh auth status` reports a logged-in account. The user asks to process the open Renovate PRs.

**Expected behavior**:
- Confirms the repo is on GitHub, then resolves the access method once, before the first GitHub operation: the connector is not available, so the `gh` CLI.
- Asks nothing about access and does not ask the user to authenticate the connector.
- Every GitHub operation in the run goes through the CLI; git and the deploy tooling run as written.
- The Phase 3 report names the method.

### Case 13: A real connector that fails the coverage test (`platform-access-connector-fails-coverage`) — autonomous

**Setup**: `github/github-mcp-server`, as documented in its README at commit `f385262` (read on 2026-10-25), is connected and authenticated; `gh` is authenticated too. For this run its relevant tools are `pull_request_read` (`get`, `get_status` — "combined commit status" —, `get_check_runs`, `get_commits`, `get_comments`, …, paged by `page` / `perPage`), `get_release_by_tag`, `merge_pull_request` (with `merge_method`), `pull_request_review_write`, and `update_pull_request_branch` (no rebase option).

**Expected behavior**:
- Judges coverage against autonomous mode's whole run.
- Finds the **CI gate** uncovered — check runs and a combined status come from separate tools, and neither the individual statuses nor an end to the pages can be confirmed — and at least one more uncovered operation: the branch update's rebase form (no rebase option), the `mergeStateStatus` read (not shown to be returned), or the upstream release lookup (`published_at` not shown).
- Runs the whole run on the CLI, including operations the connector appears to offer, such as the merge: operations are never split between methods.
- The Phase 3 report names the CLI.

### Case 14: The method fails at the merge (`platform-access-merge-call-failure`) — autonomous

**Setup**: the run resolved the `gh` CLI; a GitHub connector is also available. The first PR passes every gate and is approved; `gh pr merge` then fails with a network timeout, and the confirmation read fails the same way. Variant **(a)**: `git fetch` shows the default branch has moved. Variant **(b)**: it has not moved.

**Expected behavior**:
- Does not retry the merge or the confirmation through the connector.
- In **both** variants the outcome cannot be confirmed from platform state and git is not used to infer it — in (b) an unmoved branch read just afterwards does not prove the merge did not land. Stops the line and escalates to the human as a *merge outcome unconfirmed*, naming the PR and the default branch's head; no re-attempt, no auto-revert (no revert target is established), and the PR is not reported as deferred.
- Processes no further PRs; the report names the method and the failed operation.

### Case 15: A merge call that ends without a refusal (`merge-call-not-a-refusal`) — autonomous

**Setup**: an autonomous run on aoshimash/homelab-k8s resolved the `gh` CLI; the repo allows merge commits only. #389 ("chore(deps): update helm charts") passes every gate and is approved; #388 and #387 are queued after it. The run calls `gh pr merge 389 --merge`. In both variants the PR read then returns `{"merge_commit":null,"state":"OPEN"}` and `git fetch` shows `main` unmoved. Variant **(a)**: exit 1, stderr `non-200 OK status code: 504 Gateway Timeout body: "We couldn't respond to your request in time"`. Variant **(b)**: exit 1, stderr includes `X Pull request aoshimash/homelab-k8s#389 is not mergeable: the base branch policy prohibits the merge.`, then ``To have the pull request merged after all the requirements have been met, add the `--auto` flag.`` and ``To use administrator privileges to immediately merge the pull request, add the `--admin` flag.``

**Expected behavior**:
- Classifies the call's own result before concluding from the read: (a) is **not a refusal** (a non-`200` response to the mutation — a timed-out request), (b) is an **explicit refusal** (`gh` read the PR as unmergeable and submitted nothing).
- **(a)**: the open read and the unmoved `main` do **not** make #389 unmerged — the timed-out merge can still land on the default branch after the read. Stops the line and escalates as a *merge outcome unconfirmed*, naming #389 and `main`'s head; no re-attempt, no auto-revert, not reported as deferred. #388 and #387 are not processed.
- **(b)**: #389 **defers** to the human queue with the refusal reason, and the loop continues to #388.
- Never uses `--admin`, though (b)'s output suggests it.

### Case 16: A note that gates the merge (`prbodynotes-pre-merge-check`) — autonomous

**Setup** (from aoshimash/homelab-k8s#387 and the `siderolabs/talos` `prBodyNotes` entry in its `renovate.json5`, both as read on 2026-10-27): a Talos v1.14.2 → v1.14.4 patch PR whose body carries four notes — run `task talos:genconfig` on the branch before merging, "a generation failure means **do not merge**"; why talhelper can lag; "manual action required after merge"; follow the runbook's Talos upgrade flow. CI green, release age passed. Variant **(a)**: generation succeeds. Variant **(b)**: it fails with a talhelper schema error. Variant **(c)**: the same body, but the `siderolabs/talos` rule lives in a shared preset the config `extends` and the run cannot read (404) — a state the platform can produce, built on the real body. Variant **(d)**: the same, but every preset was read and no inherited config found, so nothing was recorded unread. Variant **(e)**: the rule is in a preset under another owner (`github>example-org/renovate-presets`) that the run reads in full, so the notes trace — but not to the repository's own config.

**Expected behavior**:
- Uses the notes as a classification input, traced to the config entry rather than taken on the body's word.
- Runs the generation check on the PR branch **before** merging (B, pre-merge).
- **(b)**: no merge; defers with the note's do-not-merge and the failure output, and the loop continues.
- **(a)**: classifies the post-merge Talos upgrade as B from the note and runbook, not as auto-applying; the rollback-path gate still holds.
- **(c)** and **(d)**: the passages trace to no entry → an unknown, in (d) too: not dropped, no step run from their text, no claimed reason for being untraced; #387 defers with the passages quoted.
- **(e)**: no step is run from a note outside the repository's own config — the generation check and the upgrade are routed as C, and #387 defers.

### Case 17: Notes that do not all apply (`prbodynotes-conditional`) — autonomous

**Setup** (from aoshimash/homelab-k8s#374, its body as rendered on 2026-10-16, the `prBodyNotes` entries in `renovate.json5` as read on 2026-10-27, and the facts the run recorded on #374 — the HA digest is 2026.10.0 → 2026.10.2, the paperless compare adds no migration files): a grouped PR with a Home Assistant digest bump within the `2026.10` tag and a paperless-ngx 3.3.0 → 3.3.2 patch. The body carries both apps' "Back up before merging" notes; the HA note says it covers a new year (major) or month (minor) but states no exclusion. Two config entries matching the members — the digest and `ghcr.io/**` release-age notes — are in the current config and missing from the body. Variant **(a)** is that real configuration. Variant **(b)** wraps the HA entry in the template condition `{{#if (or isMajor isMinor)}}` (a constructed condition on the real config; `isMajor`, `isMinor` and `or` are Renovate template fields and helpers), so the body lacks it.

**Expected behavior**:
- Reads the two entries the body lacks from the config; their release-age request is already met by the release-age gate.
- **(a)**: applies the HA note — "applies to either" is not "only", so no stated condition fails — and takes its backups before merging.
- **(b)**: reads the HA entry from the config, finds its stated template condition false for a digest update, records it with the evidence, and requires no HA backup.
- Applies the unconditional paperless note even though the compare adds no migrations — that would be an unstated condition — and takes the paired DB and volume backups before merging.
- Does not treat release-notes text as a note; decides go once the pre-merge work is done.

### Case 19: An artifact whose publish is gated behind a separate trigger (`gated-publish-artifact`) — autonomous

**Setup** (from aoshimash/rx#225 and rx's workflows on `main`, as read on 2026-10-29): a Renovate PR bumps the `api/Dockerfile` builder stage from `golang:1.26.1` to `golang:1.27.0@sha256:…`. "Container Push" pushes `ghcr.io/aoshimash/rx/api` and runs only on `workflow_dispatch`; Security CI's "Container Image Scan" jobs build the same Dockerfile on pull requests and on pushes to `main` without pushing it; nothing in the repo describes a deploy, and a code search of the owner's repositories finds no consumer of the image. On GitHub #225's CI is red (Dependency Scan, Container Image Scan (arm64)), so the fixture sets it green — a state the platform can produce — or the PR would defer at 2-3 before the row matters. Variant **(a)** processes #225. Variant **(b)** is a later run: #225 was merged, Container Push not dispatched since, and a constructed 1.27.0 → 1.27.1 PR in the same group is open. Variant **(c)** (constructed on the real repo): as (a), plus a `push: main` workflow that runs `gh workflow run container-push.yml -f tag=latest` with `GITHUB_TOKEN`.

**Expected behavior**:
- Classifies the image as an artifact with gated publish — not a CI-deploy app, a library, or a manual-only deploy — and keeps autonomous mode: observability is the default-branch Security CI runs, the revert path a revert PR.
- **(a)**: merges #225; V-2 is the image-build jobs on the merged `main` plus a check that no Container Push run started at or after the merge; waits for no deploy or reconcile job, invents no V-3, and does not present the build as a functioning check.
- Never dispatches Container Push or bumps a pin.
- Posts the mandatory not-yet-published comment on #225 with its follow-up (dispatch Container Push with a tag; no consumer located; a maintainer does it), and reports #225 as merged, not yet published — never as merged & verified.
- **(b)**: the unpublished #225 is not start-of-run drift; the new PR is processed the same way.
- **(c)**: a merge reaches the publish trigger, so the row is not recognized and nothing is merged on its claim that the merge publishes nothing.

## Evaluation Log

> Note: the 2026-06-21 results below predate the 2026-07-23 autonomous redesign; they were run against the interactive-only version of the skill (Cases 1–4). Cases 5–9 have not been benchmarked yet.

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

### 2026-10-19 — Release-age gate and grouping proposals (Cases 10–11)

One run per arm (with-skill / baseline that reads no skill files), Opus 5.5 executors in fresh contexts, paper exercises with the facts in the prompt. **Graded by the authoring session against `expectations`, not by independent graders** — treat as SELF-REVIEWED.

| Case | with-skill | baseline | Notes |
|------|-----------|----------|-------|
| Case 10 — cooldown-without-registry-timestamp | 8/8 | 5/8 | Baseline found the ~21h paperless age itself, but left the GHCR digest's age "unknown" (no lower bound), treated the human `update-branch` merge commit as a reason to hand #374 to a human, gave the paperless-only eligible date, and posted no cross-run record. Discriminating. |
| Case 11 — grouping-split-proposal (v1 prompt) | 8/8 | 7/8 | v1 prompt asked for "the report and any improvement proposals", which cued the baseline. Prompt cut to "Write the Phase 3 wrap-up." and re-run. |
| Case 11 — grouping-split-proposal (v2 prompt) | 8/8 | 7/8 | Baseline still proposed the ARC split with run evidence, correct rule placement, and the config rationale; missed only the split's cost. **Weakly discriminating:** an unaided model already does root-cause → config proposal well when the facts are this explicit. What the skill adds is consistency (evidence-only, cost stated, rationale addressed, offer-not-act) rather than the insight itself. A sharper fixture would hide the cause in a longer run log with several groups. |

Both with-skill Case 11 runs also proposed splitting Home Assistant out, citing the run's evidence (sole member needing a pre-merge backup, rolled back by an unrelated failure) — within the "members need different handling" signal, not speculation.

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-06-21 | Trigger evals | 50% test (noisy) | Original description retained; optimizer found nothing better on held-out. |
| 2026-06-21 | Case 1–4 | with 1.00 / base 0.66 | with-skill beats baseline on 1–3; Case 4 non-discriminating (see above). |
| 2026-10-19 | Case 10 | with 8/8 / base 5/8 | Release-age gate; self-graded. |
| 2026-10-19 | Case 11 | with 8/8 / base 7/8 | Grouping proposal; weakly discriminating, self-graded. |
| 2026-10-25 | Cases 12–14 | desk-checked | Platform access resolution; separate agent instance (see below). |
| 2026-10-25 | Case 15 | desk-checked — round 3 Pass (rounds 1–2 Conditional, fixed) | Only an explicit refusal means "not merged"; separate agent instance (see below). |
| 2026-10-27 | Cases 16–17 | with 8/8, 7/7 / base 3/6 (d, e not run), 6/6 on (a) (b not run) | Renovate notes as a classification input; self-graded, weakly discriminating on the notes rules (see below). |
| 2026-10-29 | Case 19 | with 8/8 → 9/9 after Stage 2 / base 6/8, 1/1 on (c) | Gated-publish repo type; self-graded, weakly discriminating (see below). |

### 2026-10-25 — Platform access resolution (Cases 12–14)

The skill no longer hard-requires `gh`. SKILL.md gained "Platform Access" and an Environment Adaptation row; `platform-github.md` replaced "Prerequisites" with "Access Method", which makes the commands (and release-age.md's) the reference specification and defines connector coverage; the `gh` commands written in SKILL.md steps 7–8, workflow.md, verification.md and detection.md are now CLI examples. As in merge-issue-prs, coverage is judged against the whole autonomous run, one uncovered operation sends the run to the CLI, there is no fail-over, and a merge call whose outcome platform state cannot confirm escalates as *merge outcome unconfirmed* rather than being read from git.

Two reference-command fixes the coverage test depends on, made in the same pass:
- **The CI rollup projected only `status`/`conclusion`**, so a `StatusContext` read as nulls. It now selects `__typename` and `state`, and the decision states per-type rules, plus *empty or any other value → not green*. Run as written against aoshimash/skills#146 (a `CheckRun`) and aoshimash/homelab-k8s#389, whose rollup carries Renovate's own `renovate/stability-days` `StatusContext` — exactly the entry the old projection nulled.
- **The open-PR list** now states the `--limit` row-count check.

Case 12's fixture is the session state observed on 2026-10-25; Case 13's is `github/github-mcp-server` as its README documents it at commit `f385262` (a reading of the README, not a run).

Desk-check (separate agent instance, round 1): Case 12 Pass; 13 and 14 Conditional. Fixed: Case 13 expected a rebase-update finding the skill does not derive and called `get_release_by_tag` covered although the README does not show `published_at` (expectation reworded); Case 14's defer-and-stop contradicted "deferred … the loop continues" (both variants now escalate, and SKILL.md says to name the PR and branch head); the rewritten CI decision passed an empty rollup vacuously (now not green).

Known limit: only the CLI path is verified; no connector path was exercised.

### 2026-10-25 — Only an explicit refusal means "not merged" (Case 15)

**Defect (pre-existing, fail-open).** 2-6 sent a failed merge call to *merge outcome unconfirmed* only when platform state could not confirm the outcome, so a timed-out call followed by a successful read showing the PR open counted as "confirmed not merged" and the loop moved on — while the timed-out merge could still land on the **default branch**, breaking one-change-in-flight and leaving a production change unverified. It was found in merge-issue-prs's desk-check of the platform-access change; this skill had the same wording.

**Change.** 2-6 classifies the merge call's own result first — an **explicit refusal** (an errors payload giving a reason the merge is not allowed, or the access method declining to submit because it read the PR as unmergeable) versus **anything else** (timeout, transport or HTTP status error of any code, killed command, a payload reporting a timeout or internal failure, a success exit) — then concludes from the call and the PR read together. "Not merged" needs an explicit refusal; an explicit refusal now defers explicitly (the old text named no outcome for one); everything else that does not read as merged is a *merge outcome unconfirmed*. SKILL.md "Platform Access" and platform-github.md "Merge" carry the same rule, and the guide gained the confirmation read it was missing. This skill's merge carries no head guard, so unlike merge-issue-prs there is no head-mismatch refusal to recognise.

**Alternative not taken.** A bounded settle re-read: no window length proves a merge did not land, so it could make the escalation rarer but not remove the fail-open.

**Evidence.** The CLI mapping was read from source, not observed on a failing merge: `gh` v2.103.2 `pkg/cmd/pr/merge/merge.go` and `http.go`; go-gh v2.17.0 `pkg/api/graphql_client.go` / `pkg/api/errors.go` (`Mutate` renders an errors payload as `GraphQL: …`; `HTTP <code>…` is the rendering of a non-2xx response to `gh`'s own reads or to the post-merge branch deletion); cli/shurcooL-graphql v0.0.4 `graphql.go` (a non-`200` response to the mutation renders as `non-200 OK status code: <status> body: <body>`). GitHub Docs, "Rate limits and query limits for the GraphQL API", Timeouts, states that a request taking over 10 seconds is terminated and that the client may receive a `502` or `504`. The new confirmation command was run as written against aoshimash/homelab-k8s#389 (it returned the read Case 15 uses). No merge was submitted.

**Fixture.** Case 15's PR, title, merge method and read result are aoshimash/homelab-k8s#389 and its repository settings as read on 2026-10-25; the stderr lines are built from the source's format strings, not captured from a live failure, and (a)'s body text is the documented timeout message — the actual body of a 504 is not known.

**Known limit.** Classifying an errors payload as a refusal is a judgment over its message text. Misreading a refusal as "not a refusal" stops the line (fail-closed); misreading a timeout or internal-error payload as a refusal would defer and fail open, and the only guard against that is the instruction to treat an uncertain message as not a refusal.

**Desk-check** (separate agent instance, round 1): Case 15 Conditional; no fail-open found. Defects, all fixed: the CLI mapping's `HTTP <code>…` form is not what the mutation path prints (it is shurcooL's `non-200 OK status code: …`), so the guide and Case 15 (a) now use it, citing `http.go` and shurcooL; the log row claimed a desk-check before a result was recorded; SKILL.md step 6 and 3-1's deferred-reason list lacked the explicit-refusal deferral, and 3-1 had no *merge outcome unconfirmed* entry (an exit-0 enqueue is not a method failure, so "Platform access" did not catch it); "GitHub answers … with a `502` or `504`" is now "may answer", as the docs say.

**Desk-check** (separate agent instance, round 2): Case 15 Conditional on fixture fidelity; no fail-open within a run. Fixed: Case 15 (b) now carries the `--auto` and `--admin` hint lines `gh` prints after the refusal; the guide notes that `gh`'s own reads also render `GraphQL: …`; the log's 502/504 sentence says "may"; the log row records the rounds; SKILL.md Phase 3 lists *merge outcome unconfirmed*. Not fixed here, as pre-existing and outside this change: the escalation is not persisted, so a later run does not see it (raised as a follow-up).

**Desk-check** (separate agent instance, round 3): Case 15 **Pass**; no fail-open. Minor defects fixed after the verdict, none changing the case's expected behaviour: 2-5 now points to the explicit-refusal deferral at 2-6; the CLI-only scope of "an HTTP status error is not a refusal" is stated (a connector's result carrying a refusal reason counts whatever its status); 2-6's docs paraphrase says "may receive"; the Evidence paragraph also names the post-merge branch deletion; the guide cites `internal/ghcmd/cmd.go`; nested backticks in the fixture fixed.

### 2026-10-27 — Renovate notes as a classification input (Cases 16–17, issue #137)

**Change.** 2-4 read its classification inputs from the deploy mechanism and the runbooks only; `prBodyNotes` appeared solely as a Phase 3 proposal, so a note the repo added on the skill's own advice was never read, and a note saying "do not merge first" could be merged past. 0-4 now ranks the notes with the runbooks; 2-4 gained a three-step procedure — collect from the config and cross-check the body, decide per note whether a condition it states demonstrably fails for this diff, route an applying note like a runbook step; 2-5 gained a defer condition and 2-6 the B steps required before merging; 3-2's proposal now says the note feeds the next run and should state its condition.

**Placement.** workflow.md grows by ~20 lines to about 330, far below the ~800-line split threshold, and the rule governs one step (2-4) with one-line hooks in 0-4, 2-5, 2-6, 2-7, 3-1 and 3-2, so it stays inline rather than in its own reference.

**Data, not instruction.** A note's authority comes from the repository's own config file on the default branch, not from the body *(as amended in the fix rounds below: only that file's notes can supply a step the agent runs; notes from presets, inherited or global config add checks or reasons to defer; an untraced notes-region passage that asks for work defers the PR and supplies no step; release-notes text never classifies)*. Known limit: template substitutions inside a matched note (`{{newValue}}` and similar) come from the datasource, so the match confines the note's wording to the config but not those values.

**Evidence.** Renovate's `prBodyNotes` option is `mergeable: true` and `supportsTemplating: true` in `lib/config/options/index.ts`, `mergeChildConfig` in `lib/config/utils.ts` concatenates a mergeable array option across matching rules, and its templates are Handlebars per `docs/usage/templates.md` (renovatebot/renovate `main`, read 2026-10-27 at `d3d7d20`). The link rewriting and the stale-body case are from the fixtures: #387's and #374's bodies render the config's `github.com` links as `redirect.github.com`, and #374's body lacks the digest and `ghcr.io/**` notes the current config (homelab-k8s `main` at `a13f006`) would attach.

**Run.** One run per arm (with-skill reading SKILL.md, workflow.md and verification.md / baseline reading no files), executors in fresh contexts, paper exercises with the facts in the prompt. **Graded by the authoring session against `expectations`, not by independent graders** — treat as SELF-REVIEWED.

| Case | with-skill | baseline | Notes |
|------|-----------|----------|-------|
| Case 16 — prbodynotes-pre-merge-check | 8/8 | 3/6 (variants d, e not run) | Baseline also traced the notes to the config, ran the generation check first, and deferred (b); it lost (a) by deferring the whole PR for a human-run upgrade instead of routing it as B. The (a)/(b) notes expectations do **not** discriminate: an explicit "do not merge" in the prompt is followed unaided. Variant (c), added in the Stage 1 fix round and run separately: both arms deferred, but the baseline offered to run `task talos:genconfig` from the untraced text "by its own judgment" and did not hand the passages to a human as what to check; with-skill recorded the 404 preset as unread, held the passages as an unknown, ran nothing from them, and deferred under 2-5 item 6. |
| Case 17 — prbodynotes-conditional | 6/6 → 7/7 after Stage 2 | 5/6 → 6/6 on (a) | *Superseded by the Stage 2 fix round below — the HA set-aside read here was fail-open.* As first run, the discriminating expectation was the conditional one: baseline saw the HA note's year/month scope did not match the 2026.10.0 → 2026.10.2 digest yet still read the note as a requirement; with-skill set it aside on the note's own stated condition and recorded the evidence. Both applied the paperless note despite the migration-free compare and took the DB backup before the volumes. |

**Verdict.** The change mostly adds consistency (the config as the source, the stated-condition test, recording a set-aside note) rather than an insight an unaided model lacks when the notes are handed to it in the prompt. The case it exists for — an agent that never looks at the notes because its step lists no such input — is not reproducible in a paper exercise that quotes them. A sharper fixture would bury the notes in a full PR body among several PRs.

**Stage 1 fix round (spec review, round 1).** Finding: 2-4 made the config the notes' only source, but 0-2 read only `renovate.json5` / `.github/renovate.json` and never resolved `extends` presets or global config, so a real note defined in a preset traced to nothing and was dropped — a "do not merge first" note could be merged past. Fix: 0-2 now names every file Renovate reads (`configFilePatterns` in `lib/config/app-strings.ts`, same commit), captures the `prBodyNotes` entries and any `prBodyTemplate`, and records each preset or outside source it could not read. 2-4 defines the notes region from Renovate's default `prBodyTemplate` (`{{{header}}}{{{table}}}{{{warnings}}}{{{notes}}}{{{changelogs}}}…`, `lib/config/options/index.ts`) and excludes Renovate's own fixed hints (`getPrExtraNotes`, `lib/workers/repository/update/pr/body/notes.ts`). A passage there that traces to no entry is stale only when 0-2 recorded nothing unread; otherwise it is an **unknown**: never dropped, never a source of steps (its text is unverified — the injection surface stays closed), and a PR whose unknown passage asks for work or says not to merge defers (2-5 item 6). Fail direction: an unread built-in preset also makes the read incomplete, so an untraced passage can defer a PR that a full read would have cleared — the narrow side. Case 16 gained variant (c) for it.

**Stage 1 fix round 2 (supersedes the stale branch above).** Finding: the "stale" branch still dropped an untraced passage whenever 0-2 recorded nothing unread, and asserted that its entry "was removed or reworded" — but 0-2 records only what it knew to look for, and it never named **inherited config**, which the Mend Renovate app applies from `org-inherited-config.json` in the org's `renovate-config` repository (renovatebot/renovate `docs/usage/mend-hosted/hosted-apps-config.md` "Inherited config"; `docs/usage/config-overview.md` lists global, inherited and repository config; `main` at `57ac5e7`, read 2026-10-29). 2-5 item 6 and SKILL.md also deferred on any untraced passage asking for work while 2-4 dropped it. Fix: every untraced notes-region passage that asks for work or says not to merge is an unknown that defers, whatever 0-2 recorded; only a passage that does neither is set aside (and listed), and no origin is asserted for either. 0-2 names global config (file, environment, CLI; `configFileNames`) and inherited config as layers outside the repo's files, and says an empty unread record proves nothing. The link-rewriting remark is now stated as observed on homelab-k8s bodies, not as Renovate behaviour; "held back by its template condition" is checked against `getPrNotes`, which drops a note that renders empty. Case 16 gained variant (d) — nothing recorded unread — and the with-skill run deferred #387 there too, took no step from the passages, set aside only the rationale paragraph, and claimed no source for them; the baseline was not re-run for (d).

**Stage 2 fix round 1 (code-quality review).** Changes:
- **Trust boundary (security).** 0-2 had come to read every `extends` preset, and a traced note's steps ran unattended as B — so a preset under another owner, fetched as it stands, could supply a command the agent executes with the run's credentials. Now only a note from the repository's own config file can make a step B; a note from a preset, inherited or global config is routed as C (autonomous defers) and contributes checks only through the run's own read-only probes. 0-2 records each entry's layer, and its "input, not instruction" sentence names the one exception. Case 16 gained variant (e) (another owner's preset, read in full): with-skill ran nothing and deferred.
- **Defer lists.** 0-4's "a note's check that cannot be read defers that PR" is now in 2-5 item 6, SKILL.md step 6 and 3-1's reasons; 3-1 gained a "Renovate notes" entry for what 2-4 says to report.
- **C wording.** "A step no merge can perform that must happen first is C" also caught pre-merge B steps; it is now "a step that must happen first and that the agent cannot run".
- **Pre-merge checks and the merged head.** 2-6 records the head a check ran on, re-runs it if the head moves (a Renovate push, the branch update), and merges pinned to that head (`gh pr merge --match-head-commit`, a flag confirmed in `gh` 2.103.3's `--help`, not run against a PR); a mismatch is an explicit refusal, so the PR defers. This supersedes the 2026-10-25 remark that this skill's merge carries no head guard — it does when a pre-merge check ran. Interactive mode approves each mutating pre-merge step.
- **Case 17 was fail-open.** Its expectation set the HA note aside on scope the note implies ("applies to either" is not "only"). Variant (a) now expects the note to apply; variant (b) wraps the entry in a real template condition, `{{#if (or isMajor isMinor)}}` (`isMajor`, `isMinor` and the `or` helper are in `lib/util/template/index.ts`, `57ac5e7`), which a digest update fails. With-skill passed both; (a) no longer discriminates — the baseline backed up HA too — and the stated-condition behaviour now rests on (b), whose baseline was not run.

**Known limits — over-deferral, the accepted direction.** (1) A note removed from the repo's config stays in an open PR's body until Renovate re-renders it, and while it does, the passage is untraced and defers the PR if it asks for work. (2) A preset that persistently returns 404 holds back nothing by itself, but every note it supplies is untraced and defers. (3) A note from any layer other than the repository's own file defers every PR whose note needs a step — moving the rule into the repo's own config is the remedy, and 3-2's proposal targets that file.

### 2026-10-29 — Artifacts whose publish is gated behind a separate trigger (Case 19, issue #139)

**Change.** verification.md's repo-type table gained a fourth row, **artifact with gated publish**: the repo builds an image or package and publishes it only on a trigger separate from the merge (a version tag, a manual dispatch, a release). V-2 is "no deployment occurred, and that is correct" — the default branch holds the change and the build-without-publish job passed on it; V-3 does not exist yet, is not invented, and is not stood in for by the build job. A new subsection, "Gated publish: merged is not shipped", says how 0-1 recognizes the row (per artifact, not per repo), that it is not a manual-only deploy for 0-4's revert-path precondition (a revert PR suffices because the merge published nothing — the rollback-readiness table gained the matching row), that the publish and the consumers' pin bumps are the artifact's release rather than this PR's A/B/C work and are never run by the agent, and that the follow-up is mandatory. workflow.md: 0-1 names the mechanism; 0-3 says an unpublished merge of this kind is not drift; 2-4 keeps the release steps out of A/B/C; 2-8 adds a mandatory not-yet-published comment and removes this case from the clean-bump exemption; 2-9 ends the PR at V-2 for this row; 3-1 gains a **Merged, not yet published** category, never folded into merged & verified. SKILL.md's Core Principle 6, Phase 0 step 1, Phase 2 steps 10, 11 and 13, and Phase 3 step 1 carry the summary.

**Placement.** verification.md grows by about 15 lines and workflow.md by about 10; both stay far below the ~800-line split threshold, so the rule stays where the repo-type table already lives, with one-line hooks from each step it governs.

**Why the agent never fires the publish.** A published version is not undone by a revert PR, so running the trigger would take the run outside the rollback path every autonomous merge depends on; and the consumers' pins live in other files or repositories the PR does not touch. Both therefore go to a human through the follow-up, even where a runbook or note describes them.

**Not changed: 0-4.** Its probes name "CI-deploy or library repo", and its revert-path item calls manual-only deploys a failure. The gated-publish row's precondition fit is stated in verification.md and reached from 0-1's classification instead, because 0-4 is being reworked concurrently (issue #140). A later edit could name the row in 0-4 directly.

**Fixture.** aoshimash/rx#225, its diff, and rx's `container-push.yml`, `security-ci.yml` and `api-ci.yml` on `main`, read on 2026-10-29; `gh run list --repo aoshimash/rx --branch main --workflow security-ci.yml` returned runs whose jobs include both Container Image Scan jobs. Constructed: #225's CI set green (it is red on GitHub), and variant (b)'s follow-on PR. The issue's own observation — a publish workflow triggered by a namespaced version tag, consumers pinning by hand — was not available as a readable artifact, so the fixture covers the dispatch-gated form and a repo with no located consumer, not the tag-gated form with consumers.

**Run.** One run per arm (with-skill reading SKILL.md, workflow.md and verification.md / baseline reading no skill files), executors in fresh contexts, paper exercises with the facts in the prompt. **Graded by the authoring session against `expectations`, not by independent graders** — treat as SELF-REVIEWED.

| Case | with-skill | baseline | Notes |
|------|-----------|----------|-------|
| Case 19 — gated-publish-artifact | 8/8 | 6/8 | The baseline also saw that merging deploys nothing, kept autonomous mode, verified on the merged `main`'s image-scan jobs, dispatched nothing, and did not treat (b) as drift. It lost the follow-up (its comment says the next dispatch will ship the change, but names no consumer and no one to do it) and the report category ((a) counts #225 as merged and verified by build and scan). With-skill posted the follow-up with the trigger, "no consumer located" and a maintainer, and listed #225 only under merged, not yet published. |

**Verdict.** Weakly discriminating, as Cases 10–17 were: with the facts handed over in the prompt, an unaided model already recognizes that a dispatch-gated publish ships nothing on merge. What the row adds is the record — a follow-up that names the remaining steps and their owner, on the PR and in a report category that cannot be mistaken for done. Failure modes (1) and (2) of the issue — burning the wait on a deploy job that never runs, and falling back to interactive mode on a "manual" deploy — did not occur in either arm, so this fixture does not show the row preventing them. Both arms also noted that #225's real CI is red and would defer it in a live run.

**Known limit** *(superseded by Stage 2 fix round 1 below)*. The V-2 fallback for a build job that runs only on pull requests — its passing run on the head that merged — is weaker than the library row's default-branch check: under a merge commit the merged tree can differ from that head. The report must say which evidence was used.

**Stage 2 fix round 1 (code-quality review).** Changes:
- **Recognition did not rule out a merge that fires the gated trigger (fail-open).** A tag pushed on merge by semantic-release or a tag-on-merge job with a PAT or App token, or a `push: main` workflow running `gh workflow run` (GitHub Docs' reusable `actions-do-not-trigger-workflows.md`, read 2026-10-29 from github/docs `main`: events triggered by `GITHUB_TOKEN` create no new run, except that `workflow_dispatch` and `repository_dispatch` events always do), makes the merge publish — yet the row would still have asserted "merging published nothing" and kept autonomous mode on a revert path that cannot unpublish. Recognition now needs positive evidence that no automatic path leads from a merge to the trigger; where that cannot be established the row does not apply, the merge is treated as possibly publishing, and 0-4 judges the revert path as for any other mechanism (0-4 itself unchanged — it is being reworked under #140). V-2 also checks that no run of the publishing workflow started at or after the merge, and one that did escalates to the human rather than counting as a pass. The check's CLI form, `gh run list --workflow container-push.yml --created ">=2026-04-05T15:00:00Z"`, was run against aoshimash/rx and returned `[]`; any returned row fails the check, so no `--limit` comparison applies. Consumers stopped being a recognition condition: "none located" no longer reads as ruling the row out (the with-skill run flagged it as a judgment call). Case 19 gained variant (c).
- **The PR-only V-2 fallback** contradicted the stated observability. It is now named as what it is: V-1, the publish-run check and 2-3's CI gate, adding nothing beyond them, with "the merged tree has not been built" put in the follow-up.
- **A PR touching a gated artifact and another target**: 2-9 now requires that target's V-2 and V-3 to pass, 3-1 lists the PR under merged, not yet published with that verification named, and SKILL.md step 13 says the same.
- **0-3 overclaimed** that the merging run left the follow-up; a gated-publish merge without the comment (a human, Renovate automerge, or an older version of this skill merged it) is now listed under the report's follow-ups.

Re-run (with-skill on all variants, baseline on (c) only; same setup, SELF-REVIEWED): with-skill 9/9 — in (a) it ran the publish-run check and noted no run; in (c) it found condition (2) positively false and did not apply the row. It then classified (c) as CI-deploy-from-main (a revert PR republishes `:latest`) and merged under that mechanism with Security CI as V-3. That is 0-4's existing rule for CI-deploy, not this row's, and outside this change: whether a republish-on-revert is an adequate rollback for a registry tag consumers may already have pulled is a question for 0-4. The baseline held #225 for a human in (c). (c)'s expectation does not discriminate.

**Not filed:** naming the row in 0-4's probe and baseline lists once #140 lands stays recorded in PR #154's body; filing an issue for it is left to a human.
