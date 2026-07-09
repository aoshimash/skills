---
name: review-dependency-prs
description: >
  Review and merge dependency-bot PRs (Renovate, Dependabot) one at a time —
  discover repo conventions, triage open bot PRs, read primary-source release
  notes, summarize risk, gate on explicit user approval, follow the PR's
  documented pre/post-merge work, and verify the change is actually *working*
  before moving to the next PR. Strictly serial: one change in flight at a time.
  GitHub only. Use when the user says "review dependency PRs",
  "merge the Renovate PRs", "handle the Dependabot PRs", "process dependency
  updates", "依存更新PRを処理して", "Renovate のPRをレビューして",
  "Dependabot のPRをマージして", "依存関係の更新PRをまとめて見て",
  "renovate たまってるからやって", or otherwise wants to work through a backlog
  of dependency-update pull requests on a GitHub repo. Invoke this skill even if
  the user just says "renovate 対応して" or "依存PRやって" without further detail.
---

# Review Dependency PRs

Process Renovate/Dependabot PRs with discipline: discover how the repo deploys, triage the open bot PRs, then handle each one **strictly serially** — review → present risk → get explicit approval → merge → run/route any manual apply → verify it is actually working — before touching the next PR.

The hard-won lesson behind the serial rule: on 2026-05-04 a homelab cluster bumped Talos and Cilium in the same window and cascaded into an outage. One change in flight at a time keeps a failure isolated and immediately rollback-able. That is the spine of this skill — do not parallelize merges to "save time".

## Core Principles

1. **Approval before every merge and every mutating apply.** Read-only investigation (reading diffs, release notes, CI status, cluster state) is free and encouraged. Anything outward or mutating — merge, comment, `apply`, delete, push — is proposed first and waits for explicit user approval. Batch approval of the *plan* is fine; **execution stays strictly serial**.
2. **Strictly serial execution.** One change in flight, full working-verification between merges. Never start PR N+1 until PR N is verified functioning. A failure must be isolated to a single change so rollback is unambiguous.
3. **Primary-source, read-the-diff.** The bot's PR body is a convenience, not the truth. Renovate sometimes omits inline release notes. Fetch the upstream GitHub Release / CHANGELOG and read the **actual diff/config**, not just the changelog prose.
4. **Merge ≠ deployed ≠ working.** In GitOps repos merging only updates Git. Classify each PR's apply path and verify all three states — merged, applied/reconciled, functioning — before calling it done.
5. **Minimal autonomy / surface-don't-fix.** Tangential improvements (doc fixes, cleanup, config tidy-ups) are surfaced as proposals, never done unprompted. Doc drift you notice is reported, not silently corrected.
6. **Document on the PR.** Manual steps and a closing "applied & verified" result go on the PR itself so humans and future agents see them. Comment only when there are real steps or risk — no spam.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |

## Workflow

### Phase 0: Discover repo conventions (once per run)

Establish how this repo ships code before touching any PR. See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**

1. Read `AGENTS.md` / `CLAUDE.md` / `README` / `docs/` and CI config to learn the **deploy mechanism** (GitOps Flux/Argo vs. CI pipeline vs. manual), the **merge method** (merge / squash / rebase), and any **upgrade runbooks** or known "merge ≠ apply" cases (e.g. a `talosctl upgrade-k8s` step, a console-only Terraform runtime bump).
2. Read bot config — `renovate.json5`, `.github/renovate.json`, `.github/dependabot.yml` — to learn configured `branchPrefix`, labels, and bot identities. This feeds detection in Phase 1.
3. Detect **start-of-run drift**: PRs already merged but not yet applied to the live environment. Flag these prominently before triaging new work — they are unfinished business.

### Phase 1: Enumerate & triage

Find the bot PRs, understand how they relate, and propose an order. See [references/detection.md](references/detection.md) for composite detection and [references/workflow.md](references/workflow.md) for triage.

**Summary:**

1. Detect dependency-bot PRs via **composite signals** (author + branch prefix + PR-body signature + labels), refined against the repo bot config from Phase 0. Assume multiple bot instances may coexist; dedupe. When ambiguous, present the candidate set and confirm with the user.
2. Detect inter-PR **conflicts** (same file/line — e.g. a digest-bump PR superseded by a major-bump PR) and **compatibility/ordering** constraints (e.g. a Kubernetes ↔ CNI support matrix; a CRD before its controller).
3. Propose a processing order, **low → high blast radius**. Optionally let the user scope the set (security-only, skip majors, etc.).
4. **Hard Gate:** present the triaged plan and proposed order → Approve / Reorder / Scope down / Abort. Approving the plan does **not** authorize execution — each merge still gates in Phase 2.

### Phase 2: Per-PR loop (STRICTLY SERIAL — one change in flight)

For each PR, in order, run the full sequence below before starting the next. See [references/workflow.md](references/workflow.md) for the detailed per-PR procedure, [references/verification.md](references/verification.md) for verification, and [references/platform-github.md](references/platform-github.md) for the `gh` commands.

**Summary per PR:**

1. **Identify** the dependency, update type (patch / minor / major / digest), and changed files.
2. **Scale review rigor to semver:** digest/patch → light (changed files + CI green); minor → read release notes; major → deep (breaking changes, migration guides).
3. **Fetch primary-source release notes** (bot body if present, else GitHub Releases / CHANGELOG / upstream) and **read the actual diff/config**.
4. **Check CI status — green is a precondition.** Investigate red; never merge red. See [references/platform-github.md](references/platform-github.md).
5. **Classify required pre/post-merge work** into the A/B/C taxonomy:
   - **A — auto-applies on merge** (GitOps reconcile / CI deploy) → verify only.
   - **B — AI-executable manual apply** (a CLI the agent can run) → propose → on approval → execute → verify.
   - **C — human-only** (UI/console op the agent cannot perform) → hand the user the exact documented steps, **wait for their completion confirmation**, then verify. Never attempt it; never fake success.
6. **Present** a risk summary + required work + rollback plan. **Approval gate: never merge without explicit user approval.**
   - **Downtime is first-class.** If the change causes disruption (node reboot, single-replica restart, DB failover, control-plane disruption), require a **prominent, explicit confirmation** spelling out blast radius + expected downtime — even if the plan was batch-approved in Phase 1. Ask about maintenance-window timing.
7. **Before any irreversible/disruptive apply, confirm a rollback path exists** (etcd snapshot, revert PR, A/B partition, `helm rollback`, DB backup). See [references/verification.md](references/verification.md).
8. **Approve, then merge** — submit a GitHub review approval (`gh pr review {pr} --approve`) before calling `gh pr merge`, so branch-protection rules requiring at least one approved review are satisfied. Resolve conflicting sibling PRs (close superseded ones, or let the bot rebase). See [references/platform-github.md](references/platform-github.md).
9. **main divergence:** if a clean `gh pr update-branch` (merge commit, or `--rebase`) integrates `main` without conflicts, do it **without asking**; if manual conflict resolution is needed, **ask the user**.
10. **Run/route the pre/post work** per its A/B/C class.
11. **Document on the PR:** a comment with the manual steps (for humans too) and a closing "applied & verified" comment — only when real steps/risk exist (no spam), in English.
12. **Verify it is actually working — three states:** merged → applied/reconciled (poll/wait for async) → functioning (health checks, no regression). Distinguish harmless residue from real failure. See [references/verification.md](references/verification.md).
13. **Only after the functioning check passes, proceed to the next PR.** If apply/verify fails: **stop the line** — do not proceed; surface the problem, offer rollback, get user direction. Fail closed when uncertain.

### Phase 3: Wrap-up

1. Summarize what was **merged / applied / verified / deferred**, plus follow-ups.
2. Surface (do not auto-fix) any **doc drift** or **repeatedly-manual** packages noticed during the run. For a package that needed the same manual apply again, **propose** adding a Renovate `prBodyNotes` entry so the note appears automatically on every future PR for it.

## References

- [references/workflow.md](references/workflow.md) — Phase 0–3 detailed procedure: serial loop, approval gates, A/B/C routing, main-divergence, PR documentation.
- [references/detection.md](references/detection.md) — Composite bot-PR detection: signals, repo-config cross-check, multi-instance dedupe, ambiguity handling.
- [references/verification.md](references/verification.md) — Three-state verification, downtime classification, rollback-readiness, residue-vs-failure, stop-the-line.
- [references/platform-github.md](references/platform-github.md) — `gh` commands for listing/filtering/reading/merging/commenting; CI status as a gate.
- [references/eval-cases.md](references/eval-cases.md) — Human-readable index of the eval scenarios.
