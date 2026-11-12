# Workflow: Ordering, the Per-PR Loop, and the Report

Detailed procedure for Phases 1–3. Selection (Phase 0) is in [targets.md](targets.md); comment handling in [comments.md](comments.md); post-merge verification in [verification.md](verification.md); every GitHub command in [platform-github.md](platform-github.md).

## Table of Contents

- [Phase 1: Order and plan](#phase-1-order-and-plan)
  - [1-1: Read each PR](#1-1-read-each-pr)
  - [1-2: Hard dependencies](#1-2-hard-dependencies)
  - [1-3: Impact order](#1-3-impact-order)
  - [1-4: The plan question](#1-4-the-plan-question)
- [Phase 2: Per-PR loop](#phase-2-per-pr-loop)
  - [2-1: Refresh](#2-1-refresh)
  - [2-2: Self-review](#2-2-self-review)
  - [2-3: Comments](#2-3-comments)
  - [2-4: Pre-merge gate](#2-4-pre-merge-gate)
  - [2-5: Brief and decision](#2-5-brief-and-decision)
  - [2-6: Review and merge](#2-6-review-and-merge)
  - [2-7: Verify](#2-7-verify)
  - [2-8: Next PR](#2-8-next-pr)
- [Phase 3: Report](#phase-3-report)

## Phase 1: Order and plan

### 1-1: Read each PR

For every selected PR read its title, description, base and head branches, changed files with their line counts, and linked issues ([platform-github.md](platform-github.md) "Read a PR"). Read each repository's agent instructions (`AGENTS.md`, `CLAUDE.md`), `README`, and deploy docs once — Phase 2 reuses them for the self-review and the verification plan.

### 1-2: Hard dependencies

An order is required, not preferred, when:

- **Stacked** — a PR's base branch is another selected PR's head branch → the base PR first. A base PR outside the selected set blocks the stacked one ([targets.md](targets.md) "Rules that follow from the set").
- **Consumes** — a PR uses something another selected PR introduces (a module output, an API, a config key, a published version; the description says "depends on #N" or the diff references it) → the producer first. Across repositories too: a Terraform module change before the stack that pins it.
- **Overlaps** — two PRs change the same lines or the same generated file → the one whose merge leaves the other a smaller rebase first; note that the second will need a branch update after the first merges.

A dependency cycle, or a dependency you are not sure of, is shown in the plan as such — never silently broken.

### 1-3: Impact order

Among PRs with no hard dependency between them, order by impact, smallest first, so that the cheapest merges build confidence before the costly ones and a failure early in the queue costs little:

1. **Risk level** (as 2-2 defines it), low before high.
2. **Blast radius** — no runtime effect (docs, tests, CI-only) before one service before shared infrastructure (networking, auth, cluster-wide config, org-wide settings).
3. **Size** — fewer changed lines first.

The order is the agent's judgement from what 1-1 read; the plan states the reason for each position in one line.

### 1-4: The plan question

Show, in the user's language:

- the queue — one line per PR: `owner/repo#N title` and why it sits there (dependency, or its impact);
- the excluded candidates and their reasons ([targets.md](targets.md));
- the enumeration's completeness and the platform access method.

Ask once (user choice): **proceed in this order** / **reorder** (the user gives the new order) / **stop**. With exactly one selected PR there is no order to approve: show the exclusions and go straight to Phase 2 — its brief is the question. The order may change later only when a merge changes a dependency (2-8), and the change is shown before the next PR starts.

## Phase 2: Per-PR loop

One PR at a time, steps in order. "Stop the line" anywhere below means: do not start another PR, report the state, and wait for the human.

### 2-1: Refresh

Re-read the PR's selection fields and head commit ([platform-github.md](platform-github.md) "Read the selection fields of a PR"). Re-run this before every step that writes (a push, a reply, the review, the merge).

- Merged by someone else → record it and go to 2-7: the change is live either way.
- Closed, converted to draft, or no longer mergeable without approval → record it as skipped with the reason; next PR.
- Head commit changed since the last read → whatever was reviewed or approved for the old head is void for the new one; continue from 2-2.

### 2-2: Self-review

Dispatch a **separate agent instance** with: the repository and PR, the diff at the current head, the PR description, the linked issue bodies, the repository's agent instructions, and the criteria below — and nothing from this conversation. Without separate instances, run it here and mark the result `SELF-REVIEWED` in the brief.

It returns:

- **Summary** — what the PR changes and why, in two or three sentences a human who has not opened it can follow.
- **Findings** — each with location, what is wrong, why it matters, and severity: `blocker` (wrong behaviour, data loss, security, broken deploy), `should-fix` (a real defect with limited reach, missing test for changed behaviour), `nit`. Check intent match (does the diff do what the description and issue say, nothing missing), correctness, security (secrets, injection, permission widening), operational risk (migrations, irreversible steps, deletions), and test coverage of changed behaviour.
- **Risk level** — `low`, `medium`, or `high`, with a one-line reason:
  - `low` — no runtime effect, or a reversible change to one non-critical component whose revert restores it fully;
  - `medium` — runtime change to one service or shared config, reversible by a revert;
  - `high` — shared infrastructure, security boundaries, data or schema changes, anything a revert does not fully undo, or anything the reviewer could not judge.
- **Blast radius** — which systems, environments, users, or repositories the change reaches when merged, and whether merging deploys it (from the deploy docs 1-1 read).
- **Commits by others** — every commit on the PR whose author is not the account (a teammate's push, a bot's fix-up), with what it changes. This skill's premise is that the human is merging their own change; another person's commit has had no reviewer but this self-review, so the brief names it and the human decides knowing it.

Findings join the comment batch in 2-3 as items with a proposed action. A `blocker` the human chooses not to fix stays in the brief.

### 2-3: Comments

Follow [comments.md](comments.md): collect unhandled comments, propose an action and a reply for each, get the human's decisions (human comments one at a time, bot comments plus self-review findings as one batch), implement the approved fixes in the worktree ([targets.md](targets.md) "A local checkout per repository"), run the repository's own checks (formatter, linter, tests the docs name), commit following the repository's message convention, push without force, post the approved replies, and resolve every thread.

After a push, wait for CI and for bots that review on push, then collect again. Repeat at most **three rounds** per PR. Anything still open after the third round goes into the brief as open, with its proposed action; the human decides there.

A fix-up that cannot be made cleanly (the checks fail and the cause is not the fix, a conflict, a push rejected) stops that fix: report it in the brief and let the human choose.

### 2-4: Pre-merge gate

Every item must hold on the **current head** ([platform-github.md](platform-github.md) for each read):

1. **CI green** — every check run completed with `SUCCESS`, `NEUTRAL`, or `SKIPPED`, and every commit status `SUCCESS`. Pending → wait (background execution) and re-read. Failed, empty, or any other value → not green: do not merge; a failure the PR caused becomes a finding for another 2-3 round, and one it did not cause (a flaky or infrastructure failure) is shown in the brief with the evidence.
2. **No conflicts** — `mergeable` is `MERGEABLE`.
3. **Threads closed** — no unresolved review thread remains (2-3's work, re-read here).
4. **Base up to date where required** — `mergeStateStatus` `BEHIND` → update the branch without force ([platform-github.md](platform-github.md) "Update the branch"), which moves the head: back to 2-2 for the new head, though only the base's changes need re-reviewing. A conflicting update stops the fix and goes to the brief.
5. **What a bypass would skip** — when `reviewDecision` is not empty, the merge will use the bypass. List the base branch's active rules ([platform-github.md](platform-github.md) "List the rules on the base branch"). The bypass is clean when every rule is one of: `pull_request` (the review requirement the bypass stands in for), `required_status_checks` (item 1 covers it), `deletion`, `non_fast_forward`, `creation`, `update`, `required_linear_history` (respected by the merge method chosen in 2-6), and `required_signatures` when every commit on the PR is verified. Any other rule — `merge_queue`, `required_deployments`, `workflows`, `code_scanning`, `code_quality`, `code_coverage`, `copilot_code_review`, `license_compliance_scanning`, the commit-message, author/committer-email and name patterns, file path, extension, size and length restrictions, or a type you do not recognize — would also be bypassed: name it in the brief as bypassed, so the human decides knowing it. A `merge_queue` rule is never bypassed: the brief offers enqueue or skip (SKILL.md Edge Cases). Classic branch protection is not listed by this read — a known limit, said in the brief when the repository has no ruleset that explains the bypass.
6. **Verification plan ready** — assemble it and probe each check ([verification.md](verification.md) "The verification plan"). A check that cannot be read now is shown in the brief: the human decides whether to merge without it.

### 2-5: Brief and decision

Write the brief in the user's language, short enough to read in under a minute. Order: what to decide first, details after.

```
<owner/repo>#<N> <title>  —  危険度: <low/medium/high>（<one-line reason>）
概要: <two or three sentences: what changes and why>
影響範囲: <systems / environments / users reached; whether merging deploys it>
コメント対応: <n> 件返信・<m> スレッド resolve（修正 <a> / 見送り <b> / issue 化 <c>）、未解決 <k>
セルフレビュー: <blockers and should-fix left unfixed, or "指摘なし">（SELF-REVIEWED when it was not independent）
他者のコミット: <author and what each changes, or "なし">（omit the line when there are none）
マージ前チェック: CI <state> / 競合 <none> / バイパスで省略されるルール <none or list>
マージ後の確認: <the checks, and which cannot be read now>
戻し方: <revert PR, or what else undoing it takes>
```

Then ask (user choice): **merge** / **skip this PR** (leave it open, continue with the next) / **stop the run**. A reply that is not one of these — a question, a change request — is answered or handled (a change request goes back to 2-3) and the brief is shown again for the new state. Silence is not approval.

### 2-6: Review and merge

Only after "merge" for this PR, on the head the brief described (2-1 first; a moved head voids the approval):

1. **Post a COMMENT review** — the author cannot approve their own PR, so the record of the decision is a review of type COMMENT ([platform-github.md](platform-github.md) "Post the self-review"). Write it in the language of the PR's description: the summary, risk level and blast radius, how review comments were handled, findings left unfixed, the verification plan, and that the merge was approved by the user (by login) after this review. Never claim an approval GitHub does not show. GitHub's docs forbid authors only to approve; that an author may submit a COMMENT review is not stated there and is unverified by this skill's evaluations — if GitHub refuses it, post the same text as a conversation comment and say so in the report.
2. **Merge** — with a method the repository and the base branch's rules allow, preferring the one the repository's docs name; pinned to the reviewed head; with the bypass only when the gate (2-4 item 5) showed the review requirement as the only unmet one, or the human accepted the listed bypassed rules ([platform-github.md](platform-github.md) "Merge"). Do not delete the head branch unless the repository's convention does — a stacked PR may still use it as its base.
3. **Confirm** — read the PR's state. `MERGED` → 2-7. An explicit refusal → nothing merged: show it to the human with the reason. Anything else → *merge outcome unconfirmed*: stop the line.

### 2-7: Verify

Run the three-state verification ([verification.md](verification.md)). Pass → post a verified comment on the PR only when verification went beyond the default branch's CI (a deploy, a reconcile, a functioning check), then 2-8. Fail or unknown → stop the line and follow [verification.md](verification.md) "On failure".

### 2-8: Next PR

Before the next PR, re-check what the merge changed:

- **Stacked PRs** of the merged one → read their base. GitHub retargets a PR whose base branch was deleted after its merge; when the branch was kept, the stacked PR still targets it. A stacked PR still based on the merged branch gets a retarget onto the merged PR's base, proposed in its own brief, never done silently ([platform-github.md](platform-github.md) "Retarget a stacked PR").
- **Overlapping PRs** → they may now be `BEHIND` or conflicting; 2-4 handles it when their turn comes.
- **Order** → if a dependency changed, show the new remaining order in one line before continuing.

## Phase 3: Report

In the user's language, the first line saying whether the run finished, stopped, or ended early, and why.

1. **Stopped line** first, if any: the PR, what failed, what is live now, what was proposed, the worktree path.
2. One row per selected PR: merged & verified / merged, follow-up needed (what and who) / skipped by the human / deferred (reason) / reverted / outcome unconfirmed.
3. Per PR: replies posted, threads resolved, issues created (with links), commits pushed.
4. Excluded candidates with reasons, the enumeration's completeness, team-list completeness, the platform access method.
5. PRs the run handled but did not merge — a later run may not select them by review request ([targets.md](targets.md) "Rules that follow from the set").
6. Anything noticed outside the selected set, one line each, prefixed "別件:" (in Japanese) or "Separate:" — never acted on.
