# Workflow: Discover, Triage, and the Serial Per-PR Loop

Detailed procedures for Phases 0–3 of the review-dependency-prs skill.

## Table of Contents

- [Phase 0: Discover repo conventions](#phase-0-discover-repo-conventions)
- [Phase 1: Enumerate & triage](#phase-1-enumerate--triage)
- [Phase 2: Per-PR loop (strictly serial)](#phase-2-per-pr-loop-strictly-serial)
  - [2-1: Identify and scale rigor](#2-1-identify-and-scale-rigor)
  - [2-2: Primary-source review](#2-2-primary-source-review)
  - [2-3: CI gate](#2-3-ci-gate)
  - [2-4: Classify pre/post work — the A/B/C taxonomy](#2-4-classify-prepost-work--the-abc-taxonomy)
  - [2-5: Present and the approval gate](#2-5-present-and-the-approval-gate)
  - [2-6: Merge and main-divergence](#2-6-merge-and-main-divergence)
  - [2-7: Run/route the pre/post work](#2-7-runroute-the-prepost-work)
  - [2-8: Document on the PR](#2-8-document-on-the-pr)
  - [2-9: Verify, then proceed or stop-the-line](#2-9-verify-then-proceed-or-stop-the-line)
- [Phase 3: Wrap-up](#phase-3-wrap-up)

## Phase 0: Discover repo conventions

Run once at the start. First confirm the repo is hosted on **GitHub** (a `github.com` remote in `git remote -v`, or `gh repo view` succeeds) — this skill is GitHub-only for v1; if the remote is GitLab or another host, say so and stop rather than guessing at non-GitHub commands. Then learn **how this repo ships a merged change to the running system** before you merge anything — because in many repos merging is only the first of several steps.

### 0-1: Learn the deploy mechanism and merge method

Read, in roughly this order, stopping when you have a confident picture:

- `AGENTS.md`, `CLAUDE.md`, `README`, and anything under `docs/` (especially `docs/runbooks/`, `docs/incidents/`, upgrade guides).
- CI config (`.github/workflows/`) and any GitOps config (Flux `Kustomization`/`HelmRelease`, Argo `Application`).

Extract:

| What | Why it matters |
|---|---|
| **Deploy mechanism** — GitOps (Flux/Argo reconcile) vs. CI pipeline deploy vs. manual apply | Determines whether a merge auto-applies (taxonomy A) or needs a follow-up step (B/C). |
| **Merge method** — merge / squash / rebase | Some repos require a specific method; respect it when merging. Check repo settings if docs are silent. |
| **Upgrade runbooks / "merge ≠ apply" cases** — e.g. `talosctl upgrade-k8s` after a K8s bump, a console-only Terraform runtime change | These are the manual steps you must route in Phase 2. Miss them and a PR is "merged" but the cluster never changed. |

### 0-2: Read the bot config

Read `renovate.json5`, `.github/renovate.json`, and `.github/dependabot.yml` if present. Capture `branchPrefix`, configured labels, package rules, and any bot identities. This sharpens detection in Phase 1 and tells you what the bots are *supposed* to do (e.g. grouping, scheduling, automerge rules).

### 0-3: Detect start-of-run drift

Look for changes already merged but **not yet applied** to the live environment — for example a K8s-version PR merged last week with no record of the `talosctl` apply having run. This is unfinished business that can interact dangerously with new merges. Flag it prominently and ask the user whether to resolve it first.

## Phase 1: Enumerate & triage

### 1-1: Detect candidate bot PRs

Apply composite detection (see [detection.md](detection.md)). Produce the deduped candidate set. If anything is ambiguous (a borderline author, an unfamiliar self-hosted account), present the candidates and confirm with the user before treating them as in-scope.

### 1-2: Detect conflicts and ordering constraints

For the candidate set, look for:

- **Inter-PR conflicts** — two PRs touching the same file/line. The classic case: a digest-bump PR and a major-version PR for the same image; the major bump supersedes the digest bump. Decide which to keep.
- **Compatibility / ordering constraints** — updates that must happen in a particular order or be checked against a support matrix:
  - A Kubernetes bump vs. a CNI (Cilium) bump — the CNI version must support the target K8s version. (This pairing is exactly what caused the 2026-05-04 outage when bumped together.)
  - A CRD update that must land before the controller that consumes it.
  - A library and a plugin that must move in lockstep.

Record these as edges; they constrain the order and sometimes mean two PRs should be handled as a deliberate, separately-confirmed sequence.

### 1-3: Propose a processing order

Order **low → high blast radius**: digests/patches of leaf tooling first, control-plane / CNI / database / runtime changes last. Surface the conflicts and ordering constraints inline so the user sees the reasoning.

Optionally offer to scope the set: security-only, skip majors, only a subset of packages.

### 1-4: Hard Gate — approve the plan

Present the triaged plan + order and ask the user to choose (see Environment Adaptation in SKILL.md): **Approve / Reorder / Scope down / Abort**.

Approving the *plan* is a batch approval of *what* will be processed and in *what order*. It does **not** authorize any merge — each PR still hits its own approval gate at step 2-5. This is how the skill honors minimal-autonomy without forcing a separate conversation for every trivial digest bump.

## Phase 2: Per-PR loop (strictly serial)

**The invariant: one change in flight at a time.** Complete every step below — through the functioning-verification in 2-9 — before starting the next PR. Do not batch merges. Do not start reviewing PR N+1 while PR N is mid-apply. A failure must map to exactly one change.

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
- Red or failing → investigate. Do not merge red. A red dependency PR often means the update genuinely breaks something; treat it as a finding, present it, and let the user decide (hold, pin, or fix).
- Pending → wait for it to settle before merging.

### 2-4: Classify pre/post work — the A/B/C taxonomy

Using Phase 0's deploy mechanism and any runbook the PR references, classify **each** required pre/post-merge action into exactly one class. A single PR can have actions in more than one class.

| Class | Definition | Routing |
|---|---|---|
| **A — auto-applies on merge** | A GitOps controller reconciles, or CI deploys, with no human action. | Merge, then **verify only** — confirm the reconcile happened and the system is functioning. |
| **B — AI-executable manual apply** | A CLI step the agent can run (e.g. `talosctl upgrade-k8s`, `helm upgrade`, a migration command). | **Propose → on approval → execute → verify.** This is a mutating apply, so it needs its own approval even if the merge was approved. |
| **C — human-only** | A UI/console operation the agent has no access to (e.g. changing the Terraform runtime version in HCP Terraform, a cloud-console toggle, a hardware action). | **Hand the user the exact documented steps, then WAIT for their explicit completion confirmation, then verify.** Never attempt it. Never assume it succeeded. Never fabricate a success result. |

If a step's class is unclear, treat it as the more cautious class (prefer C over B, B over A) and confirm with the user.

### 2-5: Present and the approval gate

Present a concise package for the PR:

- Dependency + update type + a one-line "what changed".
- Risk summary (scaled to rigor): breaking changes, behavior changes, blast radius.
- Required pre/post work, each tagged A/B/C.
- Rollback plan (see [verification.md](verification.md) for the rollback-readiness check).

**Approval gate — never merge without explicit user approval.** Even with a batch-approved plan, the merge itself is the mutating action that needs a yes.

**Downtime is first-class.** If the change is disruptive — node reboot, single-replica restart, control-plane disruption, DB failover, anything that interrupts service — do not fold it into a routine approval. Surface a **prominent, explicit confirmation** that spells out the blast radius and expected downtime, and ask about maintenance-window timing. This holds **even if the plan was batch-approved in Phase 1** — batch approval covered *order*, not *"yes, take production down now"*.

### 2-6: Approve, merge, and main-divergence

On approval, first submit a GitHub review approval so branch-protection rules requiring at least one approved review are satisfied, then merge using the repo's merge method (see [platform-github.md](platform-github.md) for both commands).

```bash
gh pr review {pr} --approve --body "Dependency update reviewed: release notes read, CI green, risk assessed."
gh pr merge {pr} --<method>
```

If the repo enforces CODEOWNERS or team-based required reviewers that an agent cannot satisfy, surface this and ask the user to approve instead — never bypass a required check.

Resolve conflicting sibling PRs identified in 1-2: close the superseded PR. The survivor may need updating against `main`; the bot will rebase it on its **own schedule**, so if you need it current now, `gh pr update-branch` is the deterministic path.

**main-divergence rule:** if the PR is behind `main`:

- A **clean** `gh pr update-branch` (which creates a merge commit by default, or `--rebase`) that integrates `main` without conflicts → do it **without asking**. This is trivial and asking would be noise.
- A merge that needs **manual conflict resolution** → **ask the user**. Conflict resolution is a judgment call that can change behavior, so it deserves a gate.

### 2-7: Run/route the pre/post work

Execute each action per its class:

- **A** — nothing to run; move to verification.
- **B** — having gotten approval in 2-5, run the CLI step. Capture output. If it errors, treat as stop-the-line (see 2-9).
- **C** — post/relay the exact steps to the user (and put them on the PR per 2-8 so they are durable), then **stop and wait**. Do not proceed to verification until the user confirms they completed the step. If they report a problem, that is stop-the-line.

### 2-8: Document on the PR

Put the durable record on the PR itself so humans and future agents see it. See [platform-github.md](platform-github.md) for the comment commands. Two comment types:

- **Pre-comment (manual steps):** when the PR requires B or C work, post the exact steps **before/at merge** so a human following along (or a future agent) knows what to do. This doubles as the C hand-off.
- **Post-comment (result):** after verification passes, post a closing "applied & verified" comment summarizing what was applied and the verification result.

Discipline:

- **Only when real steps or risk exist.** A trivial auto-applying digest bump needs no comment — commenting on every PR is spam and trains people to ignore the comments.
- **English**, regardless of conversation language (repo convention for PR comments).
- **Doc drift is surfaced, not auto-fixed.** If you notice a runbook is stale or a comment is wrong, note it for Phase 3; do not edit it as a drive-by.

### 2-9: Verify, then proceed or stop-the-line

Run three-state verification (see [verification.md](verification.md)): merged → applied/reconciled → functioning, with async-wait and regression check, and distinguish harmless residue from real failure.

- **Functioning check passes** → post the result comment (2-8), then **proceed to the next PR**.
- **Apply or verify fails** → **stop the line.** Do **not** proceed to the next PR. Surface the problem, offer rollback (using the rollback path confirmed in 2-5), and get user direction. **Fail closed when uncertain** — if you cannot tell whether it is working, treat it as not working.

## Phase 3: Wrap-up

### 3-1: Summarize

Present what happened across the run:

- **Merged / applied / verified** — the PRs that completed all three states.
- **Deferred** — PRs held (CI red, downtime not yet scheduled, scoped out).
- **Follow-ups** — anything that needs a human later.

### 3-2: Surface improvements (do not auto-fix)

- **Doc drift** noticed during the run → list it as a proposal.
- **Repeatedly-manual packages** → if a package needed the same manual B/C apply again, **propose** adding a Renovate `prBodyNotes` entry for it so the manual-step note appears automatically on every future PR for that package. Offer to open that change; do not make it unprompted.
