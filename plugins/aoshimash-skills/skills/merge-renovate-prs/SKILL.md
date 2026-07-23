---
name: merge-renovate-prs
description: >
  Review and merge Renovate dependency PRs one at a time — discover repo
  conventions, verify that monitoring and a revert path exist, triage open
  Renovate PRs, read primary-source release notes, then run each PR through a
  uniform set: LLM pre-check → merge → post-merge verification → automatic
  revert on failure. Autonomous by default (no approval gates once
  preconditions hold); an interactive per-PR-approval mode remains for when the
  user wants to confirm each step or preconditions are not met. Strictly
  serial: one change in flight at a time. Renovate only (not Dependabot);
  GitHub only. Use when the user says "review dependency PRs", "merge the
  Renovate PRs", "process dependency updates", "依存更新PRを処理して",
  "Renovate のPRをレビューして", "依存関係の更新PRをまとめて見て",
  "renovate たまってるからやって", or otherwise wants to work through a
  backlog of Renovate pull requests on a GitHub repo. Invoke this skill even
  if the user just says "renovate 対応して" or "依存PRやって" without further
  detail.
---

# Review Dependency PRs

Process Renovate PRs with discipline. Every PR goes through the same set: LLM pre-check (release notes, diff, CI) → merge → post-merge three-state verification → automatic revert if verification fails — **strictly serially**, one change in flight at a time.

**Scope: Renovate only, GitHub only.** Limiting to one bot keeps detection and config-reading simple and predictable. PRs from other dependency bots (e.g. Dependabot) are out of scope — leave them untouched and note them in the report; if the user asks to process them, say the skill covers Renovate only.

Two modes:

- **Autonomous (default):** zero approval gates after Phase 0's precondition verification passes. The safety mechanism is machine-checkable, not human sign-off: verified observability + a verified revert path + post-merge verification + auto-revert. The user gets a report at the end.
- **Interactive:** the per-PR approval workflow (plan gate + approval before every merge and every mutating apply). Use it when the user asks to confirm each step (e.g. "1個ずつ確認しながら"), or as the fallback when autonomous preconditions fail.

Whether a given package should be merged by Renovate's native automerge or by this skill is the **user's choice, made in their Renovate config** — not this skill's concern. This skill processes whatever Renovate PRs are open, from npm library bumps to Helm charts. Its distinct value over native automerge is what happens *after* the merge: Renovate's automerge gates only on pre-merge status checks and does no post-merge verification or rollback; this skill verifies the change is actually working and reverts it if it is not.

The hard-won lesson behind the serial rule: on 2026-05-04 a homelab cluster bumped Talos and Cilium in the same window and cascaded into an outage. One change in flight at a time keeps a failure isolated and immediately revertable. That is the spine of this skill — do not parallelize merges to "save time". Serial discipline is also what makes auto-revert sound: a failure maps to exactly one change, so the revert target is unambiguous.

## Core Principles

1. **Safety by verification, not by prior approval (autonomous default).** In autonomous mode the gates are machine-checkable: Phase 0 verifies the agent can actually observe system health and that a revert path exists; every merge is followed by three-state verification; failed verification triggers an automatic revert. **What to verify is human-supplied, not agent-invented:** the functioning checks come from the user's request and the repo's runbooks/docs, on top of a repo-type baseline — the agent executes that plan, it does not judge sufficiency on its own. Anything the machine checks cannot cover — human-only steps, missing revert paths, undecidable risk, a high-blast-radius target with no human-defined checks — is **deferred to a human queue, never merged on hope**. In interactive mode, explicit user approval before every merge and every mutating apply, as before.
2. **Strictly serial execution.** One change in flight, full working-verification between merges. Never start PR N+1 until PR N is verified functioning (or cleanly deferred without merging). A failure must be isolated to a single change so the revert is unambiguous.
3. **Primary-source, read-the-diff.** The bot's PR body is a convenience, not the truth. Renovate sometimes omits inline release notes. Fetch the upstream GitHub Release / CHANGELOG and read the **actual diff/config**, not just the changelog prose.
4. **Merge ≠ deployed ≠ working.** In GitOps repos merging only updates Git. Classify each PR's apply path and verify all three states — merged, applied/reconciled, functioning — before calling it done.
5. **Autonomy is scoped to the PR loop.** Zero-gate applies to reviewing, merging, applying, verifying, and reverting dependency PRs — nothing else. Tangential improvements (doc fixes, config tidy-ups, bot-config changes) are surfaced as proposals, never done unprompted. Doc drift you notice is reported, not silently corrected.
6. **Document on the PR.** Manual steps, revert actions, and a closing "applied & verified" result go on the PR itself so humans and future agents see them — in an unattended run the PR record is the audit trail. Comment only when there are real steps, risk, or a revert — no spam.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |

(User choice is used by interactive mode's gates, by autonomous mode's escalation path — a failed revert always comes back to the human — and by the Phase 0 knowledge-gap question when a high-blast-radius target has no human-defined verification checks.)

## Workflow

### Phase 0: Discover repo conventions & verify autonomous preconditions (once per run)

Establish how this repo ships code, and whether autonomous mode is safe here, before touching any PR. See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**

1. Read `AGENTS.md` / `CLAUDE.md` / `README` / `docs/` and CI config to learn the **deploy mechanism** (GitOps Flux/Argo vs. CI pipeline vs. manual), the **merge method** (merge / squash / rebase), and any **upgrade runbooks** or known "merge ≠ apply" cases (e.g. a `talosctl upgrade-k8s` step, a console-only Terraform runtime bump).
2. Read the Renovate config — `renovate.json5` or `.github/renovate.json` — to learn configured `branchPrefix`, labels, and bot identity. This feeds detection in Phase 1.
3. Detect **start-of-run drift**: PRs already merged but not yet applied to the live environment. Autonomous: exclude PRs touching the drifted component from this run (defer to the human queue); interactive: ask whether to resolve the drift first.
4. **Assemble the verification plan & verify autonomous preconditions** (autonomous mode only): build the per-target functioning checks from **human-authored sources** — the user's request, then repo runbooks/docs, then the repo-type baseline. A high-blast-radius target with no human-defined checks: ask once at run start (user choice), or defer in an unattended launch — a knowledge gate, not an approval gate. Then verify by probing: (a) **observability** — the planned checks are actually readable (cluster/controller status, or post-merge CI on the default branch); (b) **revert path** — merging a revert PR actually restores the running system under this repo's deploy mechanism. If either fails, **fall back to interactive mode and say why**.

### Phase 1: Enumerate & triage

Find the Renovate PRs, understand how they relate, and propose an order. See [references/detection.md](references/detection.md) for composite detection and [references/workflow.md](references/workflow.md) for triage.

**Summary:**

1. Detect Renovate PRs via **composite signals** (author + branch prefix + PR-body signature + labels), refined against the Renovate config from Phase 0. Assume multiple Renovate instances (Cloud + self-hosted) may coexist; dedupe. Other bots' PRs (e.g. Dependabot) are out of scope — note them in the report, do not process them.
2. Detect inter-PR **conflicts** (same file/line — e.g. a digest-bump PR superseded by a major-bump PR) and **compatibility/ordering** constraints (e.g. a Kubernetes ↔ CNI support matrix; a CRD before its controller).
3. Propose a processing order, **low → high blast radius**.
4. **Autonomous:** report the plan (set, order, constraints, and the per-target verification plan with its sources) and proceed immediately — no gate. Ambiguous candidates are excluded and listed in the report rather than blocking the run. **Interactive:** Hard Gate — present the plan → Approve / Reorder / Scope down / Abort; ambiguous candidates are confirmed with the user.

### Phase 2: Per-PR loop (STRICTLY SERIAL — one change in flight)

For each PR, in order, run the full sequence below before starting the next. See [references/workflow.md](references/workflow.md) for the detailed per-PR procedure, [references/verification.md](references/verification.md) for verification and revert, and [references/platform-github.md](references/platform-github.md) for the `gh` commands.

**Summary per PR:**

1. **Identify** the dependency, update type (patch / minor / major / digest), and changed files.
2. **Scale review rigor to semver:** digest/patch → light (changed files + CI green); minor → read release notes; major → deep (breaking changes, migration guides).
3. **Fetch primary-source release notes** (bot body if present, else GitHub Releases / CHANGELOG / upstream) and **read the actual diff/config**.
4. **Check CI status — green is a precondition.** Never merge red. Autonomous: red → **defer to the human queue and continue** with the next PR. Interactive: investigate and present as a finding.
5. **Classify required pre/post-merge work** into the A/B/C taxonomy:
   - **A — auto-applies on merge** (GitOps reconcile / CI deploy) → verify only.
   - **B — AI-executable manual apply** (a CLI the agent can run) → autonomous: execute after merge; interactive: propose → on approval → execute.
   - **C — human-only** (UI/console op the agent cannot perform) → autonomous: **defer the whole PR unmerged** (merging without the human step would create drift); interactive: hand the user the steps and wait.
6. **Go/defer decision (autonomous) or approval gate (interactive).**
   - Autonomous **defer conditions** — any of these sends the PR to the human queue *unmerged*, and the loop continues: contains C-class work; no verified revert/rollback path for an irreversible change; CI red; manual conflict resolution needed; risk the pre-check cannot resolve. **A verified rollback path is a merge precondition.**
   - Autonomous **downtime handling:** disruptive changes (node reboots, single-replica restarts, DB failover) are *not* a gate — but they get extended settle/verification time and are flagged prominently in the report.
   - Interactive: present risk + required work + rollback plan; explicit approval before merge; prominent downtime confirmation for disruptive changes.
7. **Approve, then merge** — submit a GitHub review approval (`gh pr review {pr} --approve`) before `gh pr merge`, so branch-protection rules requiring an approved review are satisfied. Resolve conflicting sibling PRs (close superseded ones). See [references/platform-github.md](references/platform-github.md).
8. **main divergence:** a clean `gh pr update-branch` → do it without asking; manual conflict resolution needed → autonomous: defer; interactive: ask the user.
9. **Run the pre/post work** per its A/B/C class (C never reaches this step in autonomous mode).
10. **Document on the PR:** manual steps, and a closing "applied & verified" (or "reverted") comment — only when real steps/risk/revert exist, in English.
11. **Verify it is actually working — three states:** merged → applied/reconciled (poll/wait for async) → functioning (health checks, no regression). Adapt the checks to the repo type (GitOps cluster health vs. post-merge CI on the default branch). See [references/verification.md](references/verification.md).
12. **On verification failure:**
    - **Autonomous: auto-revert.** Create a revert PR → merge it → verify recovery (three states again) → **stop the line** and report; do not process further PRs after a failure. If the revert itself fails or cannot restore the system, **escalate to the human immediately**. Fail closed when uncertain.
    - **Interactive: stop the line**, surface the problem, offer rollback, get user direction.
13. **Only after the functioning check passes, proceed to the next PR.**

### Phase 3: Wrap-up

1. Report what was **merged & verified / reverted (with cause) / deferred to the human queue (with reasons) / followed up**.
2. Surface (do not auto-fix) any **doc drift** or **repeatedly-manual** packages noticed during the run. For a package that needed the same manual apply again, **propose** adding a Renovate `prBodyNotes` entry so the note appears automatically on every future PR for it.

## References

- [references/workflow.md](references/workflow.md) — Phase 0–3 detailed procedure: mode selection, precondition verification, serial loop, go/defer decisions, A/B/C routing, main-divergence, PR documentation.
- [references/detection.md](references/detection.md) — Composite Renovate-PR detection: signals, config cross-check, multi-instance dedupe, ambiguity handling.
- [references/verification.md](references/verification.md) — Three-state verification per repo type, downtime classification, rollback-readiness as a merge precondition, residue-vs-failure, auto-revert and escalation.
- [references/platform-github.md](references/platform-github.md) — `gh` commands for listing/filtering/reading/merging/commenting; CI status as a gate; creating a revert PR.
- [references/eval-cases.md](references/eval-cases.md) — Human-readable index of the eval scenarios.
