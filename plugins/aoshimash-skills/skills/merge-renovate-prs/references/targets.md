# Targets, Selection, and Multi-Repository Runs

How a run decides which repositories it works in and which Renovate PRs in them it may act on, and how a run over several repositories dispatches one agent instance per repository. Everything a single repository's run does — Phases 0–3 — is unchanged and lives in [workflow.md](workflow.md); this file only decides what that run is pointed at.

## Table of Contents

- [Target forms](#target-forms)
- [The selected set](#the-selected-set)
- [A local checkout per repository](#a-local-checkout-per-repository)
- [Multi-repository runs](#multi-repository-runs)
  - [M-1: Enumerate](#m-1-enumerate)
  - [M-2: Dispatch one instance per repository](#m-2-dispatch-one-instance-per-repository)
  - [M-3: Relay questions](#m-3-relay-questions)
  - [M-4: Aggregate the report](#m-4-aggregate-the-report)
- [Known limits](#known-limits)

## Target forms

Resolve the target once, from the user's request, before Phase 0:

| The user names | The run covers | Selected set |
|---|---|---|
| nothing | the repository in the current directory | review-requested |
| a repository (`owner/repo`, or its URL) | that repository | review-requested |
| one or more PRs (a PR URL, `owner/repo#N`, or a bare `#N` — in the repository this conversation already targets, else the current directory's) | the repository of each PR | exactly the named PRs |
| an owner — an organization or a user account (`my-org`, `github.com/my-org`) | every repository of that owner with at least one PR in the review-requested search | review-requested |

- **One repository** → a single-repository run: Phases 0–3 as written, here, in this context.
- **More than one repository** — an owner, or PRs in different repositories → a [multi-repository run](#multi-repository-runs).
- A name that could be either a repository or an owner, or a PR reference whose repository cannot be told, is not guessed: ask (user choice); with no user reachable, stop and report.

## The selected set

The **selected set** is the set of PRs the run may act on: approve, merge, update, close, comment on, revert. Every other open PR in the repository is **context only** — read for detection (1-1), conflicts and ordering (1-2), and nothing else.

**review-requested** — an open PR is selected when the account the platform access method authenticates as is requested to review it, directly or through a team it belongs to: GitHub's `review-requested:@me` search qualifier ([platform-github.md](platform-github.md) "List the review-requested PRs"). This is how the user delegates a PR to this skill: Renovate, CODEOWNERS, or a teammate requested their review.

**Named PRs** — naming a PR is itself the selection, so the review request is not checked for it.

In both forms selection only narrows: a selected PR still has to pass composite Renovate detection (1-1) and every gate after it. Naming a PR does not make it a Renovate PR, and a review request does not make it one either — a human-authored PR in the review-requested search is out of scope, counted in the report and otherwise untouched.

Rules that follow from the set:

- **Never act on a PR outside it.** A superseded sibling (1-2) outside the set is not closed: report the pair, and that the sibling can be closed by whoever owns it. A Renovate PR whose ordering edge (1-2) puts it before a selected one but is not itself selected blocks that selected PR: autonomous defers it (reason: an unselected prerequisite), interactive surfaces it.
- **An empty set is a result, not a failure.** Report how many Renovate PRs the repository has open and that none requests the user's review (or that the named PRs are closed or not Renovate PRs), and end the run. Do not widen the set to find work.
- **Settle emptiness before the probes.** Read the selected set before Phase 0. Empty → end there. Otherwise read the Renovate config (0-2) and run detection (1-1) first; if no selected PR is a Renovate PR, end before the drift check and the precondition probes (0-3, 0-4), which exist only to make merging safe.
- **Reviewing removes the request.** GitHub stops listing a PR under `review-requested` once the requested account reviews it, and this skill approves before every merge (2-6). A PR the run approved but did not merge — the merge was refused, or its outcome is unconfirmed — is therefore not selected by the next run. The report lists each such PR under its outcome with that consequence, so it is not lost.

## A local checkout per repository

Local git steps (the revert branch, [platform-github.md](platform-github.md) "Create and merge a revert PR") and Phase 0's reading of the repository's docs and CI config need a working tree of the target repository at its default branch.

- The current directory is a clone of the target (its `origin` remote is that GitHub repository) → use it.
- Otherwise → clone the repository into a new, empty temporary directory, and run every local step for that repository there. Never reuse one clone for two repositories, and never clone into the current directory's working tree.

Report the clone's path, so a human can pick up a stopped line from it.

## Multi-repository runs

Each repository is processed by its own **separate agent instance**, running the single-repository workflow (Phases 0–3) on that repository's selected set. Instances run **in parallel, with no cap and no ordering between repositories**. The serial invariant — one change in flight — holds **within each repository**, not across them: see [Known limits](#known-limits).

This context is the **parent**: it enumerates, dispatches, relays questions, and aggregates. It never merges, approves, or reverts a PR itself while instances are running.

### M-1: Enumerate

1. Confirm GitHub and resolve the platform access method once for the whole run (SKILL.md "Platform Access"). Every instance uses this method; none resolves its own.
2. **Owner target** → run the review-requested search across the owner ([platform-github.md](platform-github.md) "List the review-requested PRs"), excluding archived repositories, and group the hits by repository. **PR targets** → group the named PRs by repository.
3. The owner search is complete only when every page reports `incomplete_results: false`, the total is at most 1,000 (the search API returns no more), and the number of hits fetched equals that total. An incomplete enumeration only misses repositories — they are not processed, which is the safe direction — so the run proceeds with the hits it has and the report says the enumeration was incomplete and why.
4. A hit is not yet a Renovate PR: detection happens in each repository's instance, against that repository's own Renovate config (detection.md). Report the plan — the repositories and their hit counts — and dispatch. In interactive mode the per-repository plan gates (1-5) arrive through the relay.

### M-2: Dispatch one instance per repository

Start one instance per repository, all at once. Each brief contains, and only contains:

- The repository, and the path of the new, empty directory the parent assigned for its clone ([A local checkout per repository](#a-local-checkout-per-repository)). The parent assigns it, rather than the instance choosing it, so the path is known even if the instance never reports.
- The selection: review-requested, or the named PR numbers.
- The mode (autonomous, or interactive if the user asked to confirm each step).
- Every verification check the user stated in the request, quoted verbatim (0-4 source 1): the instance uses the ones that concern its own targets.
- The platform access method. An instance that cannot use it — the method's tools are not available to it — stops and reports before its first GitHub operation, merging nothing; it never fails over to another method.
- Whether a user is reachable through the parent ([M-3](#m-3-relay-questions)).
- The return format: the Phase 3 report (workflow.md 3-1), with the clone's path.

Use the same skill instructions in every instance; the brief carries only what is specific to its repository.

If the environment cannot run separate agent instances, run the repositories **one after another in this context**, each as a complete single-repository run (Phases 0–3) before the next starts, asking questions directly.

### M-3: Relay questions

An instance cannot ask the user. Where the single-repository workflow would use **user choice** — the knowledge-gap and credential questions (0-4), interactive gates (1-5, 2-5, 2-7), an escalation that needs a human decision (2-9) — the instance does this instead:

1. It stops at a point where waiting is safe — before a merge, or with the line already stopped — and returns the question to the parent: the repository, the step, the question written to stand alone (what was found, each option with its effect), and what is in flight (nothing, or the PR whose line is stopped).
2. The parent asks the user (user choice), one question at a time, in arrival order. Other instances keep running.
3. The parent continues **the same instance** with the answer, quoted verbatim and marked as the user's.

What an answer can do is bounded by the question: it picks one of the options the instance offered, or supplies what the question asked for (verification checks). It never widens the selected set, and it never grants what the workflow reserves to the user's own act — re-authentication is done by the user in their own terminal or browser, and the instance then re-probes (0-4).

Fallbacks — each makes the instances behave as an **unattended launch** (no user reachable), which the workflow already defines: a question resolves the way its unattended rule says (defer the target's PRs, fall back without merging), and the instance returns its report instead of a question:

- The parent itself has no user reachable (a scheduled or unattended run).
- The environment cannot continue an instance it started. A fresh instance does not inherit the stopped one's state, so the parent does not resume through one.

The parent lists every question it could not relay in the aggregated report, with its repository, so the next attended run can clear them.

**On Claude Code**, an instance is a subagent, and continuing it with the answer is a `SendMessage` to that subagent's ID, which resumes it with its context intact (observed in Claude Code's tool descriptions, 2026-11-12).

### M-4: Aggregate the report

When every instance has returned its report:

1. **Stop-the-line first.** A repository whose line stopped — auto-revert, failed revert, merge outcome unconfirmed — or whose outcome is unknown (below) leads the report, with its clone path. The parent reports it as soon as it learns of it, not only at the end.
2. A table: one row per repository — merged & verified / merged, not yet published / reverted / cooldown wait / deferred / unconfirmed counts, and out-of-scope hits (human-authored or not detected as Renovate).
3. Each instance's Phase 3 report, unedited, under its repository's heading — including its improvement and grouping proposals (3-2, 3-3), which stay per repository.
4. The enumeration's completeness (M-1 step 3), the platform access method, and the unrelayed questions (M-3).

An instance that ends without returning a report — it crashed, or its run was cut off — has an **unknown outcome**: it may have merged, or have a merge in flight. Report the repository as *outcome unknown* with its clone path, and that a human must check its open and recently merged Renovate PRs. Never re-dispatch it automatically: a second instance could act on a change the first left in flight.

## Known limits

- **Cross-repository serial discipline.** Repositories run in parallel with no ordering by the user's decision (2026-11-12): speed over isolation across repositories. Two repositories that deploy to the same live target — a cluster's GitOps repository and an application repository that ships into the same cluster, two Terraform repositories sharing a workspace's dependencies — can have changes in flight at the same time. A verification failure in one may then be caused by the other, and its auto-revert reverts its own change, whichever one broke the target. Within one repository the invariant is unchanged.
- **The review-request search is GitHub's search index.** A request made moments ago can be missing from it, and a request whose reviewer already reviewed is gone from it by design. Both only shrink the selected set.
- **A team request is shared.** Another member of the requested team can review or merge the same PR while the run handles it. If they merge it first, the PR reads as merged after the run's merge call, and 2-6 continues as for the run's own merge — so the run verifies, and on failure reverts, a merge it did not make. The change is the same one it reviewed, so the revert target is still that PR's merge commit.
