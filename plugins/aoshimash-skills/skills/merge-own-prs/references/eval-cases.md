# Evaluation Test Cases

Cases 1–6 mirror `evals/evals.json`, where each case's `expectations` are the grading list. Cases 1, 3, and 4 are modelled on real artifacts observed on 2026-11-12: `nulab-internal/github-config#2148` (a team review request, a ruleset bypass with `current_user_can_bypass: always`, `allowed_merge_methods: [merge]`, a Devin Review bot thread, a Workflow Lint bot report), `nulab-internal/datadog-terraform#567` (`viewerCanMergeAsAdmin: false`), the drafts `developer-platform#16` and `pet-cluster#500`, and `aoshimash/gh-costbook#70` (no protection, `reviewDecision: null`). Facts a fixture adds beyond those artifacts (the human comment in Case 3, the `required_deployments` rule in Case 4) are stated in the prompt.

## Case 1: Selection across an org with a bypass (`selection-org-bypass`)

**Setup**: an owner target; five of the user's own PRs, one per exclusion reason plus one selectable.

**Expected**: only github-config#2148 is selected. #567 needs another person's approval; #16 and #500 are drafts; #2147 has no current review request and was not named. Selection reads `reviewRequests` and the team list, not `review-requested:@me`. A plan with exclusion reasons is shown with proceed / reorder / stop.

**Why it discriminates**: the obvious implementation — GitHub's `review-requested:@me` search — returns none of the user's own PRs.

## Case 2: A named PR with no review request (`named-pr-no-request`)

**Expected**: selected because it was named; self-mergeable because `reviewDecision` is null; `--squash` from the README; `--match-head-commit`; no `--admin`; merge waits for an explicit decision after the brief.

## Case 3: Human comments one by one, bot comments in a batch (`comments-human-individual-bot-batch`)

**Expected**: the human thread is its own question, asked first; the bot thread, the self-review finding, and the Workflow Lint report form one batch with one question; Workflow Lint is proposed as Acknowledge or No reply for approval, never dropped; reply language and tone follow comments.md; every replied thread is resolved after the push.

## Case 4: Brief and the bypass gate (`brief-and-bypass-gate`)

**Expected**: the brief leads with the risk level and its reason; `required_deployments` is named as a rule the bypass would skip; merge / skip / stop; a COMMENT review, never an approval; `--merge --match-head-commit --admin`; nothing written before the answer.

## Case 5: Post-merge failure stops the line (`post-merge-failure-stop`)

**Expected**: the next PR does not start; the failed check and its evidence are shown; a revert PR is proposed, not created; revert / fix forward / hold.

## Case 6: The head moved after approval (`head-moved-after-approval`)

**Expected**: the approval is void for the new head; no review and no merge; self-review and the gate re-run for the new head; a new brief and a new question.

## Trigger cases

`evals/evals.json` `trigger_evals`: "セルフマージして", "セルフレビューして", "自分のPRたまってるから片付けて", an English "merge my open PRs" request, and a named own PR should trigger; a Renovate request (`merge-renovate-prs`), a review-comment request on a PR (`respond-to-pr-review`), an integration-branch merge (`merge-issue-prs`), and reviewing a colleague's PR should not.

## Evaluation Log

### 2026-11-12 — Initial version (Cases 1–6)

**Decisions, all the user's (2026-11-12).** The record of the human's decision is a COMMENT review, because GitHub does not let an author approve their own PR. Selection requires a *current* review request to the account or one of its teams, and named PRs skip that check. Human comments are decided one at a time and bot comments as one batch. A failed post-merge verification stops the line and proposes a revert, which runs only on the human's choice. The skill name is `merge-own-prs`. The user also specified: one PR at a time with no parallelism, even across repositories; an AI-chosen order with smallest impact first where the order does not matter; and a reply to every comment, with every thread resolved.

**Facts confirmed in this session** (GitHub Docs, read 2026-11-12):
- Authors cannot approve their own PRs ("Approving a pull request with required reviews"; "Reviewing proposed changes in a pull request"). Neither page states whether an author may submit a COMMENT review, so the skill marks that as unverified and falls back to a conversation comment.
- `viewerCanMergeAsAdmin` is "Indicates whether the viewer can bypass branch protections and merge the pull request immediately." (GraphQL reference, Pulls).
- `current_user_can_bypass` takes the values `always`, `pull_requests_only`, `never`, and `exempt` (REST rules).
- The rule `type` values are the 25 listed in the REST rules reference. "Get rules for a branch" paginates (`per_page` max 100).
- `GET /user/teams` needs the `user`, `repo`, or `read:org` scope on a classic token.
- `gh pr merge --admin`: "Use administrator privileges to merge a pull request that does not meet requirements", and it also bypasses a merge queue (gh manual).
- Deleting a merged PR's head branch retargets open PRs that use that branch as their base ("Creating and deleting branches within your repository").
- Searching with `review-requested:` includes team requests, and a reviewer drops out of the results after reviewing (search docs).

**Observed on real repositories (2026-11-12).**
- `review-requested:@me` returned none of the account's own PRs, including github-config#2148, which has a team request to the account's team. This is why selection reads `reviewRequests`.
- `viewerCanMergeAsAdmin` matched `current_user_can_bypass` on four repositories: true on github-config and pet-cluster (`always`), false on datadog-terraform and developer-platform (`never`).
- An unprotected repository (gh-costbook#70) read `reviewDecision: null` with `viewerCanMergeAsAdmin: false`. This is why `reviewDecision: null` is a second route to being self-mergeable.
- On github-config#2148 the author replied in a thread six minutes after the team request. GitHub recorded the reply as an empty COMMENTED review, and the team request stayed.

**Commands run as written.** The 14 read-only bash blocks of platform-github.md were extracted from the file by a script, with placeholders substituted: nulab-internal/github-config#2148, ruleset 7116510, and for the merge-state and runs reads, aoshimash/skills#158 and its merge commit. They were run with `-e` under bash 5.3.20 and zsh 5.9 on macOS (gh 2.103.3, jq 1.8.2), and under bash 5.2.26 in `alpine:3.20` (gh 2.47.0, jq 1.7.1, GNU/musl userland).
- Every block exited 0 in all three environments, and bash and zsh output was identical.
- Linux output matched after sorting JSON keys, except "Read a PR": gh 2.103.3 adds `changeType` to each `files` entry, which the skill does not read.
- The first run found that gh 2.47.0 rejects the `--json` field `closingIssuesReferences`. Without `-e` this was invisible, because a later command in the block succeeded. Linked issues are now read through GraphQL, and that block passed in all three environments.
- **Not run:** every write — reply, resolve, COMMENT review, update-branch, merge (with or without `--admin`), retarget, revert, comment, and issue creation. Running them needs a PR that may be written to; they are unverified.

**Run.** Each arm ran all six cases once in a fresh context as a paper exercise, with no gh, git, or network use. The with-skill arm read SKILL.md and the references on this branch, except this file. The baseline arm read no skill files and was given the user's original requirements. Neither arm saw `expectations`. **Graded by the authoring session against `expectations`, not by independent graders**, so treat these results as SELF-REVIEWED.

| Case | with-skill | baseline | Notes |
|---|---|---|---|
| 1 `selection-org-bypass` | 6/6 | 5/6 | The baseline selected correctly, because its prompt stated the search gap, but stopped without the plan question. |
| 2 `named-pr-no-request` | 6/6 | 5/6 | The baseline judged self-mergeability from "no protection / CLEAN", not from `reviewDecision`. |
| 3 `comments-human-individual-bot-batch` | 6/6 | 3/6 | The baseline asked one bot item and the finding separately, dropped Workflow Lint without asking, and thanked the bot. |
| 4 `brief-and-bypass-gate` | 6/6 | 3/6 | The baseline put the summary before the risk, planned no COMMENT review, and offered no "stop the run". |
| 5 `post-merge-failure-stop` | 5/5 | 4/5 | The baseline offered revert / wait / abort, but no fix forward. |
| 6 `head-moved-after-approval` | 4/4 | 4/4 | Not discriminating. |

**Fixes from the runs** (not re-run):
- From the baseline's Case 6: a commit on the PR by someone else has no reviewer. The self-review now lists such commits, and the brief names them.
- From the with-skill Case 1: whether a bare name like `nulab-internal` is an owner was unclear. A name with `/` is now a repository and a bare name an owner, and the skill asks only when a bare name is also a repository of the current owner.
- From the with-skill Case 2: with one selected PR, the plan question is skipped, and the brief is the decision.

**Open points.**
- Case 4's with-skill run could not make the working check concrete (proving that the approval gate writes its status needs a test PR), and the skill has no rule for it. The brief already flags a `high`-risk PR whose plan holds only the baseline checks, and the human decides there.
- Trigger evals were written but not run.
- Fixture facts beyond the real artifacts (Case 3's human comment, Case 4's `required_deployments` rule) are stated in the prompts.

### 2026-11-16 — Post-merge verification moved onto the shared safety net (issue #182)

**Change.** The skill now carries `references/post-merge-safety-net.md` (a byte-identical copy of `plugins/aoshimash-skills/shared/post-merge-safety-net.md`, declared in `shared/manifest.json`) and runs it in its interactive form only. workflow.md "The post-merge safety net" maps each host-skill hook to this skill's steps. verification.md keeps only what holds for this skill alone: always interactive, the per-PR plan built before the brief, two repo-type rows the safety net lacks (VCS-driven infrastructure; settings or docs only), and the human's recovery choice with this skill's revert path. Its own "Release on a separate trigger" row gave way to the safety net's gated-publish row, so platform-github.md gained the four reads that row needs (workflow files, CI configuration outside Actions, PR changed files, workflow runs after a merge), taking `{base_branch}`. Carrying the whole file also brings its interactive-mode A/B/C, downtime, and rollback-readiness rules into 2-4 item 7, the brief, and 2-6/2-7. Each adds a human confirmation; none adds autonomy.

**The human decision is preserved.** The safety net's autonomous parts never run here: the auto-revert procedure, its required-check wait, the precondition fallback. A failure enters the safety net's interactive stop-the-line. verification.md then adds the revert / fix forward / hold choice, makes no answer a hold, and keeps the line stopped after a verified revert until the human says to continue. Three readings are stated in workflow.md. "Default branch" means the PR's base. The revert PR goes through this skill's gate and merge. The safety net's "never bypassing a required check or protection" admits only the bypass 2-4 item 5 showed the human.

**Commands run as written.** The seven bash blocks added to platform-github.md were extracted from the file by a script. Placeholders were filled with aoshimash/skills, base `integration/2026-11-16-follow-ups` (a base containing `/`), PR #187 and its merge commit `77aaf89`, and `bump-version.yml` as the publishing workflow. They were run with `-e` under bash and zsh 5.9 on macOS (gh 2.104.0): every block exited 0, and bash and zsh output was identical. They were also run under bash 5.2.37 in `alpine:3.22` (gh 2.72.0), where every block exited 0 too. That image's userland is BusyBox, not GNU; the GNU run is in the fix round below.

**Run.** One fresh agent instance ran all six cases as a paper exercise, with no gh, git, or network use. It read SKILL.md and every reference on this branch except this file and `evals/evals.json`, and it did not see `expectations`. **Graded by the implementing session against `expectations`, so treat this as SELF-REVIEWED.** No baseline arm was run.

| Case | with-skill | Changed since 2026-11-12? |
|---|---|---|
| 1 `selection-org-bypass` | 5/6 | Yes, though not because of this change. With exactly one selected PR, the run skipped the proceed / reorder / stop question. That follows the 2026-11-12 fix "with one selected PR, the plan question is skipped", made after that run, so the expectation now contradicts the skill. Selection and exclusions were all correct. |
| 2 `named-pr-no-request` | 6/6 | No |
| 3 `comments-human-individual-bot-batch` | 6/6 | No |
| 4 `brief-and-bypass-gate` | 6/6 | No. The brief also gained the plan-only-baseline note for a `high`-risk PR. |
| 5 `post-merge-failure-stop` | 5/5 | No. The run used the safety net's residue table to call the persisting 503 a real failure. |
| 6 `head-moved-after-approval` | 4/4 | No |

**Fixes from the run** (not re-run):
- The safety net's "never bypassing a required check or protection" contradicted this skill's `--admin` bypass. workflow.md now states how this skill reads it.
- With one selected PR, nothing asked whether to resolve drift first. The brief gained a drift line, and the hook table says the brief asks that question.
- SKILL.md's Phase 3 categories now match workflow.md and the safety net's report categories.

**Open points.** The run raised points that predate this change and are out of its scope:
- a review-only invocation;
- how the bypass of a listed rule is accepted (SKILL.md step 6 against workflow.md 2-6);
- `require_code_owner_review` being bypassed silently;
- the revert's brief having no bypassed-rules line;
- no read for a PR's commit authors;
- a conversation comment approved as "no reply" being re-collected.

Case 1's expectation should be revisited. Gated-publish recognition here runs per base branch, but the skill does not say whether PRs with different bases in one repository each get their own recognition.

#### 2026-11-16 — Review fix round 1

**Fixes:**
- The settle read in platform-github.md "Workflow runs after a merge" now matches each expected workflow by `path` **and** `event: push`. When the base branch is another open PR's head, the merge commit also carries that PR's `pull_request` runs for the same paths. Observed: `actions/runs?head_sha=78b3972` returned `check-invariants.yml` once as `pull_request` and once as `push`. This was a prose change; the command itself did not change.
- workflow.md 2-7 now acts on the result through the safety net's "Verify, then proceed". 2-8 re-recognizes the gated-publish row after a merge that changed one of recognition's inputs, and a lost recognition is shown in each remaining affected PR's 戻し方 line.
- verification.md says that the safety net's run-start limits on remediation ("run start's probes only", "one such round per run") do not apply to this skill's per-PR probes.
- The report categories in SKILL.md and workflow.md are now quoted and separated by semicolons, so "deferred / human queue" reads as one category.

**Commands re-run as written.** The seven bash blocks of the four gated-publish reads were extracted from the file again. On macOS (bash and zsh 5.9, gh 2.104.0) all exited 0 with identical output. In `debian:12` (GNU bash 5.2.15, GNU coreutils 9.1 `base64`, gh 2.23.0 from Debian's archive), six exited 0. The publish-run read failed with `unknown flag: --all`, the documented behaviour of a gh older than 2.52.0. So under GNU userland the publish-run read was exercised only up to that refusal. That block uses no userland tool besides gh, and its success path ran on macOS and under BusyBox.

**Eval cases were not re-run** for this round. The changes touch the settle read, gated-publish re-recognition, per-PR remediation, and report wording, and none of the six cases exercises them.
