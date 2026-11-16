# GitHub Platform Guide — Approved PRs

GitHub only. The commands are written for the `gh` CLI and are the reference specification of each operation (see Access Method); replace `{owner}`, `{repo}`, `{pr}` and the other placeholders. Every command passes `-R {owner}/{repo}` or names the repository in its path, so none depends on the current directory.

## Table of Contents

- [Access Method](#access-method)
- [The account](#the-account)
- [List the PRs a filter names](#list-the-prs-a-filter-names)
- [Read the selection fields of a PR](#read-the-selection-fields-of-a-pr)
- [Read the reviews](#read-the-reviews)
- [Read a reviewer's permission](#read-a-reviewers-permission)
- [Read a PR](#read-a-pr)
- [CI status](#ci-status)
- [Allowed merge methods](#allowed-merge-methods)
- [List the rules on the default branch](#list-the-rules-on-the-default-branch)
- [Workflow files (gated-publish recognition)](#workflow-files-gated-publish-recognition)
- [CI and build configuration outside Actions (gated-publish recognition)](#ci-and-build-configuration-outside-actions-gated-publish-recognition)
- [PR changed files](#pr-changed-files)
- [Workflow runs after a merge](#workflow-runs-after-a-merge)
- [Merge](#merge)
- [Create and merge a revert PR](#create-and-merge-a-revert-pr)
- [Comment on the PR](#comment-on-the-pr)

## Access Method

Resolved once per run as SKILL.md "Platform Access" describes: a connector for GitHub only when it covers **every** operation in this file, otherwise the CLI.

- **CLI**: `gh` installed and authenticated (`gh auth status`).
- **Connector coverage**: each command is the reference for its operation. A connector tool covers an operation only when its own description or schema shows it returns the same fields with the same completeness (every page, where the command paginates) or performs the same write. Where that cannot be confirmed, the operation is not covered, and one uncovered operation sends the whole run to the CLI. These are the reads where a shortfall lets a PR through silently, so each needs positive evidence:
  - **The reviews** — every review, every page, each with its state, its reviewer's login and account type, and its `commit_id`. A tool that returns only the latest review, only a summary decision, or no commit cannot apply the merge decision ([targets.md](targets.md) "The merge decision").
  - **The reviewer's permission** — the collaborator-permission endpoint's answer for one login. A collaborator list or the review's author-association label does not cover it.
  - **The CI rollup** — every check run and every commit status on the head, each with its own state.
  - **The rules on the default branch**, every page — a short list hides a merge queue — and the repository's merge-queue read for the default branch.
  - **The gated-publish reads** — complete workflow-file and tree listings with a completeness signal, the PR's complete changed-file list with its count, and workflow runs on a commit and for one workflow across every branch, tag and event.
  - **The merge** — taking the repository's method **and** an expected head commit that makes the platform refuse the merge when the head moved.
  - **Writes** — merging, creating and merging the revert PR (its merge-readiness read, below, is covered only by a tool returning the PR's state, merge state status and review decision, the base ref's classic-protection `requiresStatusChecks` and the types of every ruleset rule on it (from which `base_requires_checks` is derived), and every check run and commit status on its head with whether each is required for that PR, plus a total to compare the list against), commenting — each covered by a tool that performs that write and reports whether it succeeded. No operation in this file approves a review, and none may be added.
- **Outside this choice**: local git (fetch, branch, revert, push) and the deploy tooling the verification plan uses (`kubectl`, Flux/Argo CLIs, cloud CLIs) run as written whatever the method.

## The account

```bash
gh api user --jq '{login, type}'
```

The login is the agent's account: its approvals never qualify ([targets.md](targets.md) "A qualifying approval"). Print it for the report.

## List the PRs a filter names

For a filter the user stated over one repository, express their criteria as search qualifiers and nothing more — e.g. `review:approved`, `label:ready-to-merge`, `reviewed-by:alice`:

```bash
gh search prs --repo {owner}/{repo} --state open --limit 1000 {user_qualifiers} \
  --json number,title,url,isDraft \
  --jq '.[] | {number, title, url, isDraft}'
```

Count the rows: fewer than `--limit` means the list is complete; a count equal to it may be short — 1,000 is the search API's ceiling — so report the set as possibly incomplete. The search index can lag, and a search qualifier is only a candidate filter: every PR returned is still judged on its own reviews below.

## Read the selection fields of a PR

```bash
gh api graphql -F owner={owner} -F repo={repo} -F pr={pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef { name }
    pullRequest(number: $pr) {
      number title url state isDraft
      author { login }
      baseRefName headRefName headRefOid
      reviewDecision mergeStateStatus mergeable
      mergeCommit { oid }
    }
  }
}' --jq '.data.repository'
```

- `state` other than `OPEN`, or `isDraft` true → targets.md "Exclusions".
- `baseRefName` must equal `defaultBranchRef.name`.
- `reviewDecision` is `null` when no review is required.
- `mergeStateStatus` `BEHIND` or `mergeable` `CONFLICTING` → workflow.md 2-5 condition 7.
- `headRefOid` is the head the merge decision and the merge are pinned to.

## Read the reviews

```bash
gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/reviews?per_page=100" \
  --jq '.[] | {id, user: .user.login, type: .user.type, state, commit_id, submitted_at}'
```

`--paginate` with `per_page=100` returns every page; order the reviews by `submitted_at` when deciding a standing state, and skip `PENDING` reviews, which have none. The states are those of GitHub's `PullRequestReviewState` (GraphQL reference): `APPROVED`, `CHANGES_REQUESTED`, `COMMENTED`, `DISMISSED`, `PENDING`. `type` is `User` or `Bot`. A read that fails is an unknown: the PR defers.

## Read a reviewer's permission

For each login whose standing state is `APPROVED`:

```bash
gh api "repos/{owner}/{repo}/collaborators/{login}/permission" \
  --jq '{permission, push: .user.permissions.push}'
```

`push` true → the reviewer has write access. `push` false, or `permission` `read` or `none` → the approval does not qualify. A successful call is not evidence of access: observed 2026-11-15, the endpoint answered `read` / `push: false` for a non-collaborator (`octocat` on `aoshimash/skills`), so only the returned value counts; a read that fails is an unknown, and the PR defers.

## Read a PR

The body (for the test plan), the changed files, and the issues it closes (for their acceptance criteria):

```bash
gh pr view {pr} -R {owner}/{repo} --json title,body,baseRefName,headRefOid,changedFiles,url
gh api graphql -F owner={owner} -F repo={repo} -F pr={pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      closingIssuesReferences(first: 50) { totalCount nodes { number url title body } }
    }
  }
}' --jq '.data.repository.pullRequest.closingIssuesReferences'
```

`totalCount` above the nodes returned means some linked issues were not read: the plan reports it. The linked issues come from GraphQL because older `gh` releases reject `closingIssuesReferences` as a `--json` field.

## CI status

```bash
gh pr view {pr} -R {owner}/{repo} --json headRefOid,statusCheckRollup \
  --jq '{head: .headRefOid, checks: [.statusCheckRollup[] | {type: .__typename, name: (.name // .context), status, conclusion, state}]}'
```

The rollup mixes two shapes: a `CheckRun` has `status` and `conclusion`, a `StatusContext` only `state`.

- Every `CheckRun` `COMPLETED` with `SUCCESS`, `NEUTRAL`, or `SKIPPED`, and every `StatusContext` `SUCCESS` → green.
- `QUEUED`, `IN_PROGRESS`, `PENDING`, `EXPECTED` → wait and re-read.
- An empty rollup, or any other value (`FAILURE`, `TIMED_OUT`, `CANCELLED`, `ERROR`, `ACTION_REQUIRED`, `STARTUP_FAILURE`, `STALE`) → not green.

`head` must be the approved head; if it differs, the head moved (workflow.md 2-1).

## Allowed merge methods

```bash
gh api graphql -F owner={owner} -F repo={repo} -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) { mergeCommitAllowed squashMergeAllowed rebaseMergeAllowed }
}' --jq '.data.repository'
```

A `pull_request` rule's `parameters.allowed_merge_methods` (next section) narrows these further. To see which method recent merged PRs used:

```bash
gh pr list -R {owner}/{repo} --state merged --limit 10 --json number,mergeCommit \
  --jq '.[] | {number, merge_commit: .mergeCommit.oid}'
```

then `git log -1 --format='%P' {merge_commit}` in the checkout: two parents → merge commit; one parent → squash or rebase (a rebase leaves the PR's own commits on the default branch, a squash one new commit). When the commits do not settle it, the method is undetermined (workflow.md 0-3).

## List the rules on the default branch

Every active rule that applies to the branch, from every ruleset:

```bash
gh api --paginate "repos/{owner}/{repo}/rules/branches/{default_branch}?per_page=100" \
  --jq '.[] | {type, ruleset_id, parameters}'
```

`--paginate` reads every page. An empty result means no ruleset applies; it does not show classic branch protection (workflow.md 0-5). Read `type: merge_queue`, and for `type: pull_request` the `parameters.required_approving_review_count`, `parameters.require_code_owner_review`, and `parameters.allowed_merge_methods`.

## Merge queue on the default branch

Rulesets are not the only place a merge queue is required: classic branch protection has its own "Require merge queue" setting, which the rules read above does not show. Read the queue itself:

```bash
gh api graphql -F owner={owner} -F repo={repo} -F branch={default_branch} -f query='
query($owner: String!, $repo: String!, $branch: String!) {
  repository(owner: $owner, name: $repo) { mergeQueue(branch: $branch) { url } }
}' --jq '.data.repository'
```

`Repository.mergeQueue(branch:)` is "The merge queue for a specified branch" (GitHub GraphQL reference, Repository). `null` → no merge queue (observed 2026-11-15 on `aoshimash/skills`, which has none); an object → the branch has one, and every PR defers (workflow.md 0-5). A read that fails is an unknown, and every PR defers. **Known limit:** the non-null answer has not been observed by this skill's evaluations; the `merge_queue` rule read above is the second signal, and either one defers.

## Workflow files (gated-publish recognition)

Recognition of an artifact whose publish is gated behind a separate trigger ([post-merge-safety-net.md](post-merge-safety-net.md) "Gated publish", condition (1)) reads **every** workflow file on the default branch:

```bash
gh api "repos/{owner}/{repo}/git/trees/{default_branch}:.github/workflows" \
  --jq '{truncated, files: [.tree[] | select(.type == "blob") | .path]}'
```

`truncated: false` on a read that succeeded → the listing is complete. `truncated: true`, or a read that fails (a 404 included) → the listing may be incomplete, and the row does not apply. Names are relative to the directory: prefix each with `.github/workflows/` to match the reads below, which return each workflow's `path` from the repository root. Read each file at a ref (the default branch, or the ref a reusable-workflow call names):

```bash
gh api "repos/{owner}/{repo}/contents/.github/workflows/{file}?ref={ref}" --jq .content | base64 -d
```

A file that cannot be read is a workflow whose publishing cannot be determined: the row does not apply. Which workflows can start runs at all — taken after the merge, with the settle read:

```bash
gh api --paginate "repos/{owner}/{repo}/actions/workflows?per_page=100" \
  --jq '.workflows[] | {path, state}'
```

## CI and build configuration outside Actions (gated-publish recognition)

Condition (3) of recognition looks for CI or build configuration other than GitHub Actions in the default branch's whole tree:

```bash
gh api "repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1" \
  --jq '{truncated, root: [.tree[] | select(.path | contains("/") | not) | .path],
         ci: [.tree[].path | select(test("(^|/)(\\.gitlab-ci\\.ya?ml|Jenkinsfile[^/]*|cloudbuild[^/]*\\.(ya?ml|json)|\\.travis\\.ya?ml|\\.drone\\.ya?ml|azure-pipelines[^/]*\\.ya?ml|bitbucket-pipelines\\.ya?ml|buildspec[^/]*\\.ya?ml|\\.?appveyor\\.ya?ml)$|(^|/)\\.(circleci|buildkite|tekton|woodpecker)(/|$)"))]}'
```

`truncated: false` on a read that succeeded → complete; `truncated: true` or a failed read → may be incomplete, and the row does not apply. Read every path in `ci` with the contents read above; scan `root` for configuration of any CI or build system the filter does not name. Below the root, a system the filter does not name is not caught (post-merge-safety-net.md "Gated publish", known limit).

## PR changed files

Every file the PR changes, for the gated-publish re-judgement and the drift check:

```bash
gh api "repos/{owner}/{repo}/pulls/{pr}" --jq '{head: .head.sha, changed_files}'
gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/files?per_page=100" \
  --jq '.[] | {filename, status, previous_filename}'
```

The list is complete only when the number of rows returned equals `changed_files` and is below 3000, the most files this endpoint returns; otherwise, or when a read fails, it may be incomplete. Read the head's version of a file with the contents read above at `ref={head}`.

## Workflow runs after a merge

**Settle read** — every run the merge is expected to start exists on the merge commit and has completed:

```bash
gh api --paginate "repos/{owner}/{repo}/actions/runs?head_sha={merge_commit_sha}&per_page=100" \
  --jq '.workflow_runs[] | {id, path, event, status, conclusion, html_url}'
```

GitHub creates runs asynchronously after the merge: an empty or partial result right after it means "not yet". The expected set is every active workflow whose `push` trigger admits the default branch and whose path filters admit a file the merge changed. For a library or CI-deploy repository this read is V-2 (and, for a library, V-3): every expected run completed with `success`.

**Publish-run read** (gated publish only) — no run of a publishing workflow started at or after the merge, on any branch or tag, from any event; once for each publishing workflow:

```bash
gh run list -R {owner}/{repo} --all --workflow {publishing_workflow_file} --created ">={merge_time}" \
  --json databaseId,event,status,createdAt,headBranch,url
```

No rows from every one → the check passes; any row fails it. A read that fails is verification that cannot be completed. `--all` needs gh 2.52.0 or later (added in gh v2.52.0, cli/cli#9162; `--created` dates from v2.28.0). An older gh rejects the flag (`unknown flag: --all`, observed with gh 2.23.0), so the read fails: run start records the gh version and treats a gated-publish target as unobservable before any merge (workflow.md 0-1), and a read that fails anyway after a merge fails closed as above.

## Merge

Pinned to the approved head, with the repository's method (`--merge`, `--squash`, or `--rebase`):

```bash
gh pr merge {pr} -R {owner}/{repo} --merge --match-head-commit {approved_head_sha}
```

Never `--admin`, and never `gh pr review --approve` before it. Add `--delete-branch` only where the repository's convention deletes merged branches.

Classify the result ([post-merge-safety-net.md](post-merge-safety-net.md) "Pre-merge steps and the merge call's result"). With `gh`, an **explicit refusal** is a non-zero exit whose stderr carries a line beginning `GraphQL: ` with a message giving a reason the merge is not allowed — not one reporting a timeout, a resource limit, or an internal failure — or `is not mergeable:`, which `gh` prints from the merge state it read before submitting anything. Everything else is **not a refusal**: a line beginning `non-200 OK status code:` or `HTTP `, a network or TLS error, a killed or hung command, and exit 0. `gh` exits 0 without merging when the base requires a merge queue (it enqueues the PR instead), which is why workflow.md 0-5 defers every PR there. Through a connector, only a tool result carrying the platform's refusal reason is a refusal.

After **every** merge call, read the state (a read that fails is a *merge outcome unconfirmed*):

```bash
gh pr view {pr} -R {owner}/{repo} --json state,mergeCommit,mergedAt --jq '{state, merge_commit: .mergeCommit.oid, mergedAt}'
```

`MERGED` confirms the merge; keep `merge_commit` and `mergedAt` for verification and a revert. Anything else confirms nothing unless the call was an explicit refusal.

## Create and merge a revert PR

Used by the safety net's auto-revert procedure. The revert branch is cut in its own worktree in a new, empty temporary directory, so the checkout's branch and any uncommitted work in it are untouched (the checkout is the user's own when the current directory is the target repository):

```bash
git fetch origin
git worktree add -b revert-pr-{pr} {revert_worktree_dir} origin/{default_branch}
cd {revert_worktree_dir}

# Merge-commit method: revert the merge commit against its first parent
git revert -m 1 {merge_commit_sha} --no-edit
# Squash method: the squash produced an ordinary commit; no -m
git revert {merge_commit_sha} --no-edit
# Rebase method: the PR's commits landed individually; identify them on the
# default branch (git log) and revert each, newest first

git push -u origin revert-pr-{pr}
gh pr create -R {owner}/{repo} --base {default_branch} --head revert-pr-{pr} \
  --title "Revert: {original title}" --body-file {revert_body_file}
```

Before the merge call, wait for the revert PR's pending required checks ([post-merge-safety-net.md](post-merge-safety-net.md#waiting-for-the-revert-prs-required-checks) "Waiting for the revert PR's required checks"). Its merge readiness, read right after creating it and every 30 seconds after that:

```bash
gh api graphql -F owner={owner} -F repo={repo} -F pr={revert_pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      state mergeStateStatus reviewDecision
      baseRef { branchProtectionRule { requiresStatusChecks } rules(first: 100) { totalCount nodes { type } } }
      commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 100) {
        totalCount
        nodes {
          __typename
          ... on CheckRun { name status conclusion isRequired(pullRequestNumber: $pr) }
          ... on StatusContext { context state isRequired(pullRequestNumber: $pr) }
        }
      } } } } }
    }
  }
}' --jq '.data.repository.pullRequest | (.commits.nodes[0].commit.statusCheckRollup.contexts // {totalCount: 0, nodes: []}) as $c | {state, merge_state: .mergeStateStatus, review_decision: .reviewDecision, base_requires_checks: ((.baseRef.branchProtectionRule.requiresStatusChecks == true) or ([.baseRef.rules.nodes[]?.type] | any(. == "REQUIRED_STATUS_CHECKS" or . == "REQUIRED_WORKFLOW_STATUS_CHECKS" or . == "WORKFLOWS" or . == "CODE_SCANNING"))), fetched: ($c.nodes | length), total: $c.totalCount, required: [$c.nodes[] | select(.isRequired) | {type: .__typename, name: (.name // .context), status, conclusion, state}]}'
```

How the read maps to the safety net's wait conditions:

- `state` other than `OPEN` → no longer open.
- `merge_state` `UNKNOWN` → the platform cannot yet determine whether the merge is possible. `BLOCKED` → the merge is reported blocked. Any other value (`CLEAN`, `UNSTABLE`, `HAS_HOOKS`, `BEHIND`, `DIRTY`) → not blocked: make the merge call now.
- `review_decision` `REVIEW_REQUIRED` or `CHANGES_REQUESTED` → a review the agent cannot give; null or `APPROVED` → not that.
- `fetched` below `total` → the read may be incomplete.
- `base_requires_checks` `true` → the revert PR's base is positively known to require status checks: a classic branch protection rule with required status checks, or an active repository or organization ruleset rule on the base ref of a type that makes checks report before the merge — `REQUIRED_STATUS_CHECKS`, `REQUIRED_WORKFLOW_STATUS_CHECKS`, `WORKFLOWS` (required workflows), or `CODE_SCANNING` (required code scanning results). A rule type outside these four is not counted. `false` covers both "not required" and "not readable" (a null `baseRef`, a protection rule this account cannot see, a rule past the first 100), so an empty `required` list then never counts as waiting.
- In `required`: a `CheckRun` whose `status` is not `COMPLETED`, or a `StatusContext` whose `state` is `PENDING` or `EXPECTED`, is pending. A `CheckRun` `COMPLETED` with a `conclusion` other than `SUCCESS`, `NEUTRAL`, or `SKIPPED`, or a `StatusContext` `FAILURE` or `ERROR`, has failed. An empty `required` list means no required check has reported; it is a reason to wait only when `base_requires_checks` is `true`.
- A non-zero exit, or output that does not parse into these fields → a read that fails.

A classic branch protection rule is not visible to every account: on 2026-11-16 `branchProtectionRule` read null on cli/cli and microsoft/vscode, whose PRs report required checks, so `base_requires_checks` was `false` there while `required` was non-empty; github/docs and astral-sh/uv, which require checks through rulesets, read `true`. `isRequired` takes the PR's number; the GraphQL schema describes it as "Whether this is required to pass before merging for a specific pull request." Never pass `--admin` or approve the revert PR to end the wait.

Then merge it and read its state:

```bash
gh pr merge {revert_pr} -R {owner}/{repo} --<method>
gh pr view {revert_pr} -R {owner}/{repo} --json state,mergeCommit --jq '{state, merge_commit: .mergeCommit.oid}'
```

The revert PR's body says what failed and links the original PR.

- **Never approve the revert PR.** The agent authored it, and GitHub states that "Pull request authors cannot approve their own pull requests" ([Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews)). Do not route around that with another identity the agent can reach.
- **Anything short of `MERGED` is a revert that did not land** — an explicit refusal (a required approving review, a code-owner review, red CI on the revert, any other protection), a call that was not a refusal, or a failed read. Leave the PR open and escalate with its URL and the refusal text; never retry, force, or bypass it.
- **Pending required checks are waited out, nothing else.** The merge call waits, bounded, until the read above shows no required check pending; on a repository with required status checks that pass, the revert then lands without a human. Red required checks, a required review, and any other refusal still escalate at once, and checks still pending at the bound escalate as a failed revert. The wait's known limits are the safety net's ([post-merge-safety-net.md](post-merge-safety-net.md#waiting-for-the-revert-prs-required-checks)).

## Comment on the PR

Safety-net comments and this skill's two (workflow.md 2-8), in English:

```bash
gh pr comment {pr} -R {owner}/{repo} --body-file {comment_file}
```
