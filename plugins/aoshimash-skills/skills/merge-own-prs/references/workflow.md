# Workflow: Ordering, the Per-PR Loop, and the Report

Detailed procedure for Phases 1–3. Selection (Phase 0) is in [targets.md](targets.md); comment handling in [comments.md](comments.md); what happens around and after each merge in [post-merge-safety-net.md](post-merge-safety-net.md), with this skill's additions in [verification.md](verification.md); every GitHub command in [platform-github.md](platform-github.md).

## Table of Contents

- [The post-merge safety net](#the-post-merge-safety-net)
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

## The post-merge safety net

What happens around and after each merge — the deploy mechanism, drift, the verification plan's sources, the A/B/C taxonomy, the merge call's result, verification, and the stopped line — is in [post-merge-safety-net.md](post-merge-safety-net.md), a file shared byte-for-byte with any other skill that carries it. It links nothing outside itself and names **host-skill hooks** instead; in this skill they are:

| Hook | Here |
|---|---|
| Modes | Always **interactive**: the human approves every merge and every mutating apply ([verification.md](verification.md) "Always interactive"). There is no autonomous mode, so nothing falls back to interactive. An unattended launch posts and merges nothing (SKILL.md "Environment Adaptation"), so no step from the merge on runs |
| Run start | [1-1](#1-1-read-each-pr), once per repository: the safety net's "Deploy mechanism and merge method" and "Start-of-run drift". Its verification-plan section does not run here; the plan is built per PR at 2-4 |
| Plan report | [1-4](#1-4-the-plan-question); drift is flagged there and the human is asked whether to resolve it first. With one selected PR, its brief (2-5) carries the drift line and asks that question before the merge question |
| Per-PR plan sources | The PR's own test plan or verification steps; they rank after the user's request and before the repository's docs, and join the plan at [2-4](#2-4-pre-merge-gate) item 6 ([verification.md](verification.md) "The verification plan") |
| CI gate | [2-4](#2-4-pre-merge-gate) item 1 |
| Go/defer step | [2-5](#2-5-brief-and-decision): the brief carries the A/B/C proposal, any downtime confirmation, and the rollback path (or its absence), and "skip this PR" is the deferral. "No verified rollback path" is said in the brief's 戻し方 line; the human decides |
| PR documentation step | [2-6](#2-6-review-and-merge) for the pre-comment (manual steps go into the COMMENT review), [2-7](#2-7-verify) for the result and not-yet-published comments, [verification.md](verification.md) "The revert" step 5 for the revert comment |
| Report | [Phase 3](#phase-3-report); the safety net's named categories are rows there |
| Platform access | SKILL.md "Platform Access". An unknown before the merge is shown to the human; from the merge call on it stops the line |
| Platform guide | [platform-github.md](platform-github.md): workflow-file listing → "Workflow files (gated-publish recognition)"; tree listing → "CI and build configuration outside Actions (gated-publish recognition)"; PR changed files → "PR changed files"; workflow runs after a merge → "Workflow runs after a merge"; merge → "Merge"; revert PR → "Create a revert PR", then the revert's own gate reads ("CI status", "Read the selection fields of a PR") and "Merge"; PR comment → "Comment on the PR" |

Three readings of the safety net's terms hold only here. **"Never bypassing a required check or protection"** at the merge call means no bypass beyond what 2-4 item 5 put in front of the human: the merge may use the bypass in place of the approving review the author cannot give, and for another listed rule only when the human accepted it at the brief (SKILL.md principle 7). Every other required check or protection holds. **"Default branch"** means the base branch the PR merges into: this skill merges into a PR's base, which need not be the repository's default branch. **The revert PR** is the user's own PR, merged through this skill's gate and merge path on the human's "revert" answer ([verification.md](verification.md) "The revert"), not through the auto-revert procedure.

## Phase 1: Order and plan

### 1-1: Read each PR

For every selected PR read its title, description, base and head branches, changed files with their line counts, and linked issues ([platform-github.md](platform-github.md) "Read a PR"). Read each repository's agent instructions (`AGENTS.md`, `CLAUDE.md`), `README`, and deploy docs once — Phase 2 reuses them for the self-review and the verification plan. From them, run the safety net's "Deploy mechanism and merge method" and "Start-of-run drift" for each repository.

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
- the enumeration's completeness and the platform access method;
- any drift found in 1-1, flagged prominently, with whether to resolve it first.

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
7. **Pre/post work and rollback** — classify each required pre/post-merge action A, B, or C, judge whether the change is disruptive, and confirm its rollback path, as the safety net's "Pre/post work: the A/B/C taxonomy", "Downtime classification", and "Rollback-readiness check" say for interactive mode. For a gated-publish target, run the re-judgement the taxonomy section describes when the PR changes one of recognition's inputs. All of it goes into the brief.

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
未適用の変更: <drift found in 1-1>（only with one selected PR, where there is no plan question; omit otherwise）
マージ前後の作業: <B/C steps with their class, or "なし">（omit the line when there are none）
停止時間: <blast radius, expected downtime, timing>（only for a disruptive change; omit otherwise）
マージ後の確認: <the checks, and which cannot be read now>
戻し方: <revert PR, or what else undoing it takes; "なし" for an irreversible change>
```

A B-class step needs its own approval even after "merge": list it in the brief and ask for it as a separate choice before running it.

Then ask (user choice): **merge** / **skip this PR** (leave it open, continue with the next) / **stop the run**. A reply that is not one of these — a question, a change request — is answered or handled (a change request goes back to 2-3) and the brief is shown again for the new state. Silence is not approval.

### 2-6: Review and merge

Only after "merge" for this PR, on the head the brief described (2-1 first; a moved head voids the approval):

1. **Pre-merge steps** — run the B-class steps required before merging — each mutating one only after its own approval — as the safety net's "Pre-merge steps and the merge call's result" says. One that fails means no merge: show it to the human.
2. **Post a COMMENT review** — the author cannot approve their own PR, so the record of the decision is a review of type COMMENT ([platform-github.md](platform-github.md) "Post the self-review"). Write it in the language of the PR's description: the summary, risk level and blast radius, how review comments were handled, findings left unfixed, the verification plan, and that the merge was approved by the user (by login) after this review. When the PR has B or C work, the review also carries its exact steps — it is the safety net's pre-comment. Never claim an approval GitHub does not show. GitHub's docs forbid authors only to approve; that an author may submit a COMMENT review is not stated there and is unverified by this skill's evaluations — if GitHub refuses it, post the same text as a conversation comment and say so in the report.
3. **Merge** — with a method the repository and the base branch's rules allow, preferring the one the repository's docs name; pinned to the reviewed head; with the bypass only when the gate (2-4 item 5) showed the review requirement as the only unmet one, or the human accepted the listed bypassed rules ([platform-github.md](platform-github.md) "Merge"). Do not delete the head branch unless the repository's convention does — a stacked PR may still use it as its base.
4. **Confirm** — classify the merge call's result and read the PR's state as the safety net's "Pre-merge steps and the merge call's result" defines. `MERGED` → 2-7. An explicit refusal → nothing merged: show it to the human with the reason. Anything else → *merge outcome unconfirmed*: stop the line ([verification.md](verification.md) "On failure").

### 2-7: Verify

Run the safety net's "Running the pre/post work" (a B step only after its approval; a C step handed to the user, waiting for their confirmation), then its three-state verification against the plan from 2-4, with its repo-type rows and [verification.md](verification.md)'s two extra rows. Pass → post the result comment only when verification went beyond the base branch's CI (a deploy, a reconcile, an apply, a functioning check), then 2-8. Gated publish passing V-2 → post the mandatory not-yet-published comment and report the PR as merged, not yet published, then 2-8. Fail or unknown → stop the line and follow [verification.md](verification.md) "On failure".

### 2-8: Next PR

Before the next PR, re-check what the merge changed:

- **Stacked PRs** of the merged one → read their base. GitHub retargets a PR whose base branch was deleted after its merge; when the branch was kept, the stacked PR still targets it. A stacked PR still based on the merged branch gets a retarget onto the merged PR's base, proposed in its own brief, never done silently ([platform-github.md](platform-github.md) "Retarget a stacked PR").
- **Overlapping PRs** → they may now be `BEHIND` or conflicting; 2-4 handles it when their turn comes.
- **Order** → if a dependency changed, show the new remaining order in one line before continuing.

## Phase 3: Report

In the user's language, the first line saying whether the run finished, stopped, or ended early, and why.

1. **Stopped line** first, if any: the PR, what failed, what is live now, what was proposed, the worktree path.
2. One row per selected PR, in the safety net's report categories: merged & verified / merged, not yet published (the follow-up: what and who) / reverted / deferred / human queue (skipped by the human, or deferred with its reason) / merge outcome unconfirmed. Then disruptive changes executed, and follow-ups — including a gated-publish merge found at run start without its follow-up comment.
3. Per PR: replies posted, threads resolved, issues created (with links), commits pushed.
4. Excluded candidates with reasons, the enumeration's completeness, team-list completeness, the platform access method.
5. PRs the run handled but did not merge — a later run may not select them by review request ([targets.md](targets.md) "Rules that follow from the set").
6. Anything noticed outside the selected set, one line each, prefixed "別件:" (in Japanese) or "Separate:" — never acted on.
