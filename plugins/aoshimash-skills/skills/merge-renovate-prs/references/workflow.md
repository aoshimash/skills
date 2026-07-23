# Workflow: Modes, Discovery, Triage, and the Serial Per-PR Loop

Detailed procedures for Phases 0–3 of the merge-renovate-prs skill.

## Table of Contents

- [Mode selection](#mode-selection)
- [Phase 0: Discover repo conventions & verify preconditions](#phase-0-discover-repo-conventions--verify-preconditions)
- [Phase 1: Enumerate & triage](#phase-1-enumerate--triage)
- [Phase 2: Per-PR loop (strictly serial)](#phase-2-per-pr-loop-strictly-serial)
  - [2-1: Identify and scale rigor](#2-1-identify-and-scale-rigor)
  - [2-2: Primary-source review](#2-2-primary-source-review)
  - [2-3: CI gate](#2-3-ci-gate)
  - [2-4: Classify pre/post work — the A/B/C taxonomy](#2-4-classify-prepost-work--the-abc-taxonomy)
  - [2-5: Go/defer decision (autonomous) or approval gate (interactive)](#2-5-godefer-decision-autonomous-or-approval-gate-interactive)
  - [2-6: Merge and main-divergence](#2-6-merge-and-main-divergence)
  - [2-7: Run/route the pre/post work](#2-7-runroute-the-prepost-work)
  - [2-8: Document on the PR](#2-8-document-on-the-pr)
  - [2-9: Verify, then proceed — or auto-revert / stop-the-line](#2-9-verify-then-proceed--or-auto-revert--stop-the-line)
- [Phase 3: Wrap-up](#phase-3-wrap-up)

## Mode selection

Pick the mode once, at the start of the run:

- **Autonomous (default).** Use when the user asked to process/merge the dependency PRs without asking to be consulted per step. After Phase 0's precondition verification passes, there are **no approval gates**: the run proceeds through review → merge → apply → verify → (revert on failure) unattended, and ends with a report.
- **Interactive.** Use when the user asked to confirm each step ("1個ずつ確認しながら", "check with me before merging"), or as the **fallback** when Phase 0's autonomous preconditions fail — in that case, state which precondition failed and why before continuing interactively.

The two modes share every phase below; they differ only at the marked decision points. **Autonomous never converts a gate into silent risk-taking** — where interactive mode would ask a human, autonomous mode either decides by rule or defers the PR unmerged to the human queue.

## Phase 0: Discover repo conventions & verify preconditions

Run once at the start. First confirm the repo is hosted on **GitHub** (a `github.com` remote in `git remote -v`, or `gh repo view` succeeds) — this skill is GitHub-only for v1; if the remote is GitLab or another host, say so and stop rather than guessing at non-GitHub commands. Then learn **how this repo ships a merged change to the running system** before you merge anything — because in many repos merging is only the first of several steps.

### 0-1: Learn the deploy mechanism and merge method

Read, in roughly this order, stopping when you have a confident picture:

- `AGENTS.md`, `CLAUDE.md`, `README`, and anything under `docs/` (especially `docs/runbooks/`, `docs/incidents/`, upgrade guides).
- CI config (`.github/workflows/`) and any GitOps config (Flux `Kustomization`/`HelmRelease`, Argo `Application`).

Extract:

| What | Why it matters |
|---|---|
| **Deploy mechanism** — GitOps (Flux/Argo reconcile) vs. CI pipeline deploy vs. manual apply | Determines whether a merge auto-applies (taxonomy A) or needs a follow-up step (B/C), and what "revert PR → system restored" means here. |
| **Merge method** — merge / squash / rebase | Some repos require a specific method; respect it when merging. It also determines how to build a revert commit (see platform-github.md). Check repo settings if docs are silent. |
| **Upgrade runbooks / "merge ≠ apply" cases** — e.g. `talosctl upgrade-k8s` after a K8s bump, a console-only Terraform runtime change | These are the manual steps you must route in Phase 2. Miss them and a PR is "merged" but the cluster never changed. |

### 0-2: Read the Renovate config

Read `renovate.json5` or `.github/renovate.json` if present. Capture `branchPrefix`, configured labels, package rules, and any bot-identity clues. This sharpens detection in Phase 1 and tells you what Renovate is *supposed* to do (e.g. grouping, scheduling, automerge rules). This skill is **Renovate-only**: other bots' config (e.g. `.github/dependabot.yml`) and their PRs are out of scope.

Note on native automerge: which packages Renovate automerges itself is the **user's configuration choice**, not this skill's. Do not propose moving packages between native automerge and this skill unprompted (Core Principle 5). Open Renovate PRs are in scope regardless of why they are open.

### 0-3: Detect start-of-run drift

Look for changes already merged but **not yet applied** to the live environment — for example a K8s-version PR merged last week with no record of the `talosctl` apply having run. This is unfinished business that can interact dangerously with new merges.

- **Autonomous:** do not try to resolve the drift (its failure would not map to a change made this run). **Exclude PRs touching the drifted component** from this run — defer them to the human queue with the drift as the reason — and report the drift prominently. PRs unrelated to the drifted component may proceed.
- **Interactive:** flag it prominently and ask the user whether to resolve it first.

### 0-4: Assemble the verification plan & verify autonomous preconditions (autonomous mode only)

Autonomous mode replaces human approval with machine-checkable safety. The split of responsibility: **what to check comes from humans; whether it can be checked is machine-verified; running the checks is the skill's job.** The agent never invents "sufficiency" — it executes checks humans defined.

**First, assemble the verification plan** — for each deploy target the run will touch, the concrete V-3 functioning checks — from human-authored sources, in priority order:

1. **The user's request** — checks stated at invocation ("after each merge confirm the ingress answers on :443").
2. **Repo docs** — runbooks, upgrade guides, `AGENTS.md`/`CLAUDE.md`, monitoring docs already read in 0-1. Health-check procedures written there *are* the human-given answer to "what would a human check".
3. **Repo-type baseline** — the three-state defaults from [verification.md](verification.md) (GitOps: workloads Ready + endpoints + version; CI-deploy: pipeline + smoke; library: post-merge default-branch CI).

**Knowledge-gap rule:** the baseline is sufficient on its own for low-blast-radius targets. For a **high-blast-radius target** (control plane, CNI, database, node OS, single-replica services) with **no human-defined checks** beyond the baseline: if the user is present at run start, ask once (user choice) to supply checks or accept the baseline; in a fully unattended launch, **defer that target's PRs** to the human queue. This is a knowledge gate, not an approval gate — the question is "how do I know it's broken?", never "may I?".

**Then verify the preconditions** — by probing, not by assuming:

1. **Observability.** Run the read-only probes the verification plan needs and confirm they return data:
   - GitOps repo: controller status (e.g. Flux/Argo CLI or `kubectl` reads succeed), workload health is readable.
   - CI-deploy or library repo: post-merge workflow runs on the default branch are readable (e.g. `gh run list --branch main`).
   - Any check in the plan whose probe fails (a dashboard the agent cannot read, a command that errors) is a failed precondition for the targets that depend on it.
2. **Revert path.** Merging a revert PR must actually restore the running system under this repo's deploy mechanism. GitOps reconcile and CI-deploy-from-main both qualify. If the *repo-level* mechanism does not propagate a revert (e.g. deploys are manual-only), autonomous merging has no safety net.
   - Changes that a revert PR alone cannot undo (a node OS already upgraded, an irreversible DB migration) are handled **per-PR** in 2-5 — they defer unless an alternative rollback path is verified — not here.

**If either precondition fails, fall back to interactive mode and state the reason.** Do not run a degraded autonomous mode.

## Phase 1: Enumerate & triage

### 1-1: Detect candidate Renovate PRs

Apply composite detection (see [detection.md](detection.md)). Produce the deduped candidate set. If anything is ambiguous (a borderline author, an unfamiliar self-hosted account):

- **Autonomous:** exclude the ambiguous candidate from the run and list it in the report — never auto-merge a PR you are not sure is machine-generated.
- **Interactive:** present the candidates and confirm with the user before treating them as in-scope.

### 1-2: Detect conflicts and ordering constraints

For the candidate set, look for:

- **Inter-PR conflicts** — two PRs touching the same file/line. The classic case: a digest-bump PR and a major-version PR for the same image; the major bump supersedes the digest bump. Decide which to keep.
- **Compatibility / ordering constraints** — updates that must happen in a particular order or be checked against a support matrix:
  - A Kubernetes bump vs. a CNI (Cilium) bump — the CNI version must support the target K8s version. (This pairing is exactly what caused the 2026-05-04 outage when bumped together.)
  - A CRD update that must land before the controller that consumes it.
  - A library and a plugin that must move in lockstep.

Record these as edges; they constrain the order and sometimes mean two PRs should be handled as a deliberate sequence with full verification between them.

### 1-3: Propose a processing order

Order **low → high blast radius**: digests/patches of leaf tooling first, control-plane / CNI / database / runtime changes last. Surface the conflicts and ordering constraints inline so the reasoning is visible.

Interactive mode may additionally offer to scope the set: security-only, skip majors, only a subset of packages. Autonomous mode processes the full detected set unless the user scoped it in their request.

### 1-4: Plan gate (interactive) / plan report (autonomous)

- **Autonomous:** report the plan — the PR set, the order, the constraint edges, **the verification plan per target (which checks, from which source — user request / repo docs / baseline)**, and anything excluded (ambiguous candidates, drift-blocked PRs) — then **proceed immediately**. The report is for the record, not a question; it lets the human see *what will be checked* before the unattended stretch and interrupt if the checks look wrong.
- **Interactive:** Hard Gate — present the triaged plan + order and ask the user to choose (see Environment Adaptation in SKILL.md): **Approve / Reorder / Scope down / Abort**. Approving the *plan* is a batch approval of *what* will be processed and in *what order*; it does **not** authorize any merge — each PR still hits its own approval gate at step 2-5.

## Phase 2: Per-PR loop (strictly serial)

**The invariant: one change in flight at a time.** Complete every step below — through the functioning-verification in 2-9 — before starting the next PR. Do not batch merges. Do not start reviewing PR N+1 while PR N is mid-apply. A failure must map to exactly one change; that is also what makes the auto-revert target unambiguous. (A PR *deferred without merging* is not in flight — deferring and moving on preserves the invariant.)

### 2-1: Identify and scale rigor

Identify the dependency, the update type, and the changed files. Scale review effort to the semver delta — spending equal effort on a digest bump and a major upgrade wastes attention where it matters:

| Update type | Rigor |
|---|---|
| digest / patch | **Light** — confirm the changed files are what you expect and CI is green. |
| minor | **Medium** — read the release notes for new behavior, deprecations, default changes. |
| major | **Deep** — breaking changes, migration guides, config-schema changes; read the actual diff against your usage. |

### 2-2: Primary-source review

Fetch release notes from the **primary source**: the bot PR body if it included them, otherwise the upstream GitHub Releases page or `CHANGELOG`. Renovate sometimes omits inline notes, so do not assume their absence means "nothing changed".

Then read the **actual diff/config** in the PR — what literally changed in this repo — not just the upstream prose. The changelog tells you what *could* matter; the diff tells you what *does* change here.

### 2-3: CI gate

CI green is a **precondition for merge**, not a nicety. See [platform-github.md](platform-github.md) for reading status.

- Green → proceed.
- Red or failing → **do not merge**, in either mode. A red dependency PR often means the update genuinely breaks something.
  - **Autonomous:** defer the PR to the human queue with a short read-only diagnosis of the failure, and continue with the next PR.
  - **Interactive:** investigate read-only, present it as a finding, and let the user decide (hold, pin, or fix).
- Pending → wait for it to settle before deciding.

### 2-4: Classify pre/post work — the A/B/C taxonomy

Using Phase 0's deploy mechanism and any runbook the PR references, classify **each** required pre/post-merge action into exactly one class. A single PR can have actions in more than one class.

| Class | Definition | Routing |
|---|---|---|
| **A — auto-applies on merge** | A GitOps controller reconciles, or CI deploys, with no human action. | Merge, then **verify only** — confirm the reconcile happened and the system is functioning. |
| **B — AI-executable manual apply** | A CLI step the agent can run (e.g. `talosctl upgrade-k8s`, `helm upgrade`, a migration command). | Autonomous: execute after merge, no pause. Interactive: **propose → on approval → execute** — a mutating apply needs its own approval even if the merge was approved. Then verify. |
| **C — human-only** | A UI/console operation the agent has no access to (e.g. changing the Terraform runtime version in HCP Terraform, a cloud-console toggle, a hardware action). | Autonomous: **defer the whole PR unmerged** — merging without the human step would create merged-but-unapplied drift. Interactive: **hand the user the exact documented steps, WAIT for their explicit completion confirmation, then verify.** Never attempt it. Never assume it succeeded. Never fabricate a success result. |

If a step's class is unclear, treat it as the more cautious class (prefer C over B, B over A). In interactive mode confirm with the user; in autonomous mode the C treatment means the PR defers.

### 2-5: Go/defer decision (autonomous) or approval gate (interactive)

Assemble the same package in both modes:

- Dependency + update type + a one-line "what changed".
- Risk summary (scaled to rigor): breaking changes, behavior changes, blast radius.
- Required pre/post work, each tagged A/B/C.
- Rollback plan (see [verification.md](verification.md) for the rollback-readiness check).

**Autonomous — decide go/defer by rule.** *Go* means proceed to merge. *Defer* means do **not** merge; record the PR + reason in the human queue and continue with the next PR. Defer when **any** of these holds:

1. The PR requires **C-class** work (see 2-4).
2. The change is irreversible or disruptive and **no rollback path could be verified** — a verified rollback path is a **merge precondition** in autonomous mode, not a talking point. A revert PR counts for anything GitOps/CI-deploy reverts cleanly; irreversible applies (node OS, DB migrations) need their specific path from verification.md's table confirmed to exist.
3. CI is red (already deferred at 2-3).
4. Integrating `main` needs **manual conflict resolution** (see 2-6).
5. The pre-check surfaces a risk the agent **cannot resolve or bound** — a breaking change whose impact on this repo is genuinely undecidable from the code and docs. Fail closed: defer, do not merge on hope.

**Downtime is not a gate in autonomous mode — but it is not ignored.** Classify disruption per [verification.md](verification.md). A disruptive change (node reboots, single-replica restart, DB failover, CNI restart) proceeds, with: extended settle time before judging health in 2-9, and a **prominent entry in the final report**. If the user's request constrained timing ("only during the maintenance window"), respect it — defer the disruptive PR if the constraint cannot be honored now.

**Interactive — approval gate: never merge without explicit user approval.** Even with a batch-approved plan, the merge itself is the mutating action that needs a yes. **Downtime is first-class:** if the change is disruptive, do not fold it into a routine approval — surface a prominent, explicit confirmation that spells out blast radius and expected downtime, and ask about maintenance-window timing. This holds even if the plan was batch-approved in Phase 1: batch approval covered *order*, not *"yes, take production down now"*.

### 2-6: Merge and main-divergence

On a *go* decision (autonomous) or user approval (interactive): first submit a GitHub review approval so branch-protection rules requiring at least one approved review are satisfied, then merge using the repo's merge method (see [platform-github.md](platform-github.md) for both commands).

```bash
gh pr review {pr} --approve --body "Dependency update reviewed: release notes read, CI green, risk assessed."
gh pr merge {pr} --<method>
```

If the repo enforces CODEOWNERS or team-based required reviewers that an agent cannot satisfy, never bypass the check. Autonomous: defer the PR (reason: required review the agent cannot provide). Interactive: surface it and ask the user to approve.

Resolve conflicting sibling PRs identified in 1-2: close the superseded PR. The survivor may need updating against `main`; the bot will rebase it on its **own schedule**, so if you need it current now, `gh pr update-branch` is the deterministic path.

**main-divergence rule:** if the PR is behind `main`:

- A **clean** `gh pr update-branch` (which creates a merge commit by default, or `--rebase`) that integrates `main` without conflicts → do it **without asking**, in either mode.
- A merge that needs **manual conflict resolution** → conflict resolution is a judgment call that can change behavior. Autonomous: **defer**. Interactive: **ask the user**.

### 2-7: Run/route the pre/post work

Execute each action per its class:

- **A** — nothing to run; move to verification.
- **B** — autonomous: run the CLI step now (the go decision in 2-5 covered it). Interactive: having gotten approval in 2-5, run it. Capture output. If it errors, treat as a verification failure (see 2-9).
- **C** — only reachable in interactive mode (autonomous defers C-class PRs at 2-5). Post/relay the exact steps to the user (and put them on the PR per 2-8 so they are durable), then **stop and wait**. Do not proceed to verification until the user confirms they completed the step. If they report a problem, treat it as a failure (2-9).

### 2-8: Document on the PR

Put the durable record on the PR itself so humans and future agents see it — in an unattended autonomous run, this is the audit trail. See [platform-github.md](platform-github.md) for the comment commands. Comment types:

- **Pre-comment (manual steps):** when the PR requires B or C work, post the exact steps **before/at merge** so a human following along (or a future agent) knows what to do. This doubles as the C hand-off in interactive mode.
- **Post-comment (result):** after verification passes, post a closing "applied & verified" comment summarizing what was applied and the verification result.
- **Revert comment (autonomous failures):** when a PR is auto-reverted, post on the original PR what failed, what was reverted, and the recovery state — and link the revert PR. This one is **mandatory**, not optional: an unattended revert without a durable explanation is how trust in automation dies.

Discipline:

- **Only when real steps, risk, or a revert exist.** A trivial auto-applying digest bump that verified clean needs no comment — commenting on every PR is spam and trains people to ignore the comments. (The end-of-run report covers the quiet successes.)
- **English**, regardless of conversation language (repo convention for PR comments).
- **Doc drift is surfaced, not auto-fixed.** If you notice a runbook is stale or a comment is wrong, note it for Phase 3; do not edit it as a drive-by.

### 2-9: Verify, then proceed — or auto-revert / stop-the-line

Run three-state verification (see [verification.md](verification.md)): merged → applied/reconciled → functioning, with async-wait and regression check, adapted to the repo type, and distinguish harmless residue from real failure. For disruptive changes, use the extended settle time from 2-5.

- **Functioning check passes** → post the result comment (2-8), then **proceed to the next PR**.
- **Apply or verify fails** (or residue resolves to a real failure) — **fail closed when uncertain**: if you cannot tell whether it is working, treat it as not working. Then:
  - **Autonomous: auto-revert.** Execute the revert procedure in [verification.md](verification.md): create a revert PR → approve & merge it → if a B-class apply ran, execute its verified inverse → re-run three-state verification on the *recovery*. Then **stop the line**: even after a clean recovery, do not process further PRs this run — one failure means the pre-check missed something, and the remaining queue deserves human eyes. Post the revert comment (2-8) and report. If the revert itself fails, cannot be merged, or the system does not recover: **escalate to the human immediately** with the full state — this is the one place autonomous mode always comes back to a person.
  - **Interactive: stop the line.** Do **not** proceed to the next PR. Surface the problem, offer rollback (using the path confirmed in 2-5) as a proposal, and get user direction.

Never fabricate a passing result to keep the loop moving. A truthful "this failed, here is the state, here is what was reverted" is the correct output.

## Phase 3: Wrap-up

### 3-1: Report

Present what happened across the run:

- **Merged & verified** — the PRs that completed all three states.
- **Reverted** — auto-reverted PRs (autonomous), each with the failure cause, the revert PR link, and the recovery state.
- **Deferred / human queue** — PRs held, each with its reason (C-class step, CI red, no rollback path, manual conflicts, undecidable risk, drift-blocked, ambiguous candidate) and what a human needs to do.
- **Disruptive changes executed** — flagged prominently with what downtime occurred.
- **Follow-ups** — anything that needs a human later.

### 3-2: Surface improvements (do not auto-fix)

- **Doc drift** noticed during the run → list it as a proposal.
- **Run-supplied verification checks** → if the user supplied checks at invocation or via the 0-4 knowledge-gap question, **propose** persisting them into the repo's docs/runbooks so future runs (and humans) find them in Phase 0 without asking again. Offer to open that change; do not make it unprompted.
- **Repeatedly-manual packages** → if a package needed the same manual B/C apply again, **propose** adding a Renovate `prBodyNotes` entry for it so the manual-step note appears automatically on every future PR for that package. Offer to open that change; do not make it unprompted.
