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
