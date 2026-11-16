# GitHub Platform Guide — Own PRs

The commands are written for the `gh` CLI and are the reference specification of each operation (see Access Method). Replace `{owner}`, `{repo}`, `{pr}`, `{branch}`, `{sha}` as needed; every command names the repository with `-R` or in its path, so the current directory does not have to be the target.

## Table of Contents

- [Access Method](#access-method)
- [The account](#the-account)
- [List candidate PRs](#list-candidate-prs)
- [List the account's teams](#list-the-accounts-teams)
- [Read the selection fields of a PR](#read-the-selection-fields-of-a-pr)
- [Read a PR](#read-a-pr)
- [Read review threads](#read-review-threads)
- [Read reviews and conversation comments](#read-reviews-and-conversation-comments)
- [Reply](#reply)
- [Resolve a thread](#resolve-a-thread)
- [CI status](#ci-status)
- [Update the branch](#update-the-branch)
- [List the rules on the base branch](#list-the-rules-on-the-base-branch)
- [Allowed merge methods](#allowed-merge-methods)
- [Post the self-review](#post-the-self-review)
- [Workflow files (gated-publish recognition)](#workflow-files-gated-publish-recognition)
- [CI and build configuration outside Actions (gated-publish recognition)](#ci-and-build-configuration-outside-actions-gated-publish-recognition)
- [PR changed files](#pr-changed-files)
- [Workflow runs after a merge](#workflow-runs-after-a-merge)
- [Merge](#merge)
- [Retarget a stacked PR](#retarget-a-stacked-pr)
- [Create a revert PR](#create-a-revert-pr)
- [Comment on the PR](#comment-on-the-pr)
- [Create an issue for a tracked comment](#create-an-issue-for-a-tracked-comment)

## Access Method

Resolved once per run as SKILL.md "Platform Access" describes: a connector for GitHub only when it covers **every** operation in this file, otherwise the CLI.

- **CLI**: `gh` installed and authenticated (`gh auth status`). Reading the account's teams needs a token that may read organization membership (a classic token's `read:org` scope); without it, team requests cannot be judged ([targets.md](targets.md)).
- **Connector coverage**: each command is the reference for its operation. A connector tool covers an operation only when its own description or schema shows it returns the same fields with the same completeness (every page, where the command paginates) or performs the same write. Where that cannot be confirmed, the operation is not covered, and one uncovered operation sends the whole run to the CLI. The reads where a shortfall is silent and unsafe, so each needs positive evidence:
  - **The selection fields** — `viewerCanMergeAsAdmin`, `reviewDecision`, and the review requests with each requested team's organization and slug. A tool without `viewerCanMergeAsAdmin` cannot tell a bypass-mergeable PR from one that needs another person.
  - **Review threads** with `isResolved` and every thread's comments, every page; **the CI rollup** with every check run and every commit status, each with its own state. A short list reads as "no open threads" or "CI green".
  - **The rules on the base branch**, every page — a short list hides a rule the bypass would skip.
  - **Writes**: a COMMENT-type review, a reply inside a review thread, resolving a thread, merging with a chosen method pinned to a head commit (and with the bypass), updating a branch, editing a PR's base, creating a PR or issue, commenting. Each is covered by a tool that performs that exact write and reports whether it succeeded.
- **Outside this choice**: local git (worktree, clone, commit, push, revert) and the deploy tooling a verification plan uses (`kubectl`, Flux/Argo CLIs, cloud CLIs) always run as written.

## The account

```bash
gh api user --jq .login
```

`@me` in searches is this account. Print it for the report.

## List candidate PRs

Open, non-draft PRs authored by the account. For an owner:

```bash
gh search prs --author @me --state open --draft=false --archived=false --owner {owner} --limit 1000 \
  --json repository,number,title,url \
  --jq '.[] | {repo: .repository.nameWithOwner, number, title, url}'
```

For one repository, replace `--owner {owner}` with `--repo {owner}/{repo}`. Archived repositories are skipped: nothing merges there. Count the rows: fewer than `--limit` means the list is complete; a count equal to it may be short — 1,000 is the search API's ceiling, so report the enumeration as possibly incomplete. Draft state is read again per PR (below) — the search index can lag.

## List the account's teams

```bash
gh api user/teams --paginate --jq '.[] | "\(.organization.login)/\(.slug)"'
```

`--paginate` reads every page. A failed read (HTTP 403 or 404, typically a token without organization-read access) means team requests cannot be judged for this run.

## Read the selection fields of a PR

One query gives everything [targets.md](targets.md) needs, plus the head commit the loop pins to:

```bash
gh api graphql -F owner={owner} -F repo={repo} -F pr={pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef { name }
    pullRequest(number: $pr) {
      number title url state isDraft
      author { login }
      baseRefName headRefName headRefOid
      reviewDecision mergeStateStatus mergeable viewerCanMergeAsAdmin
      reviewRequests(first: 100) {
        totalCount
        nodes { requestedReviewer {
          __typename
          ... on User { login }
          ... on Team { slug organization { login } }
        } }
      }
    }
  }
}' --jq '.data.repository'
```

- `reviewRequests.totalCount` greater than the nodes returned → the request list is short: the PR is not selected by request (report it).
- A requested `Team` matches when `"{organization.login}/{slug}"` is in the team list.
- `reviewDecision` is `null` when no review is required; `viewerCanMergeAsAdmin` is `true` when the account can bypass the base branch's protections and merge.

## Read a PR

```bash
gh pr view {pr} -R {owner}/{repo} \
  --json title,body,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,files,url
gh pr diff {pr} -R {owner}/{repo}
gh api graphql -F owner={owner} -F repo={repo} -F pr={pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      closingIssuesReferences(first: 50) { totalCount nodes { url title body } }
    }
  }
}' --jq '.data.repository.pullRequest.closingIssuesReferences'
```

The linked issues come from GraphQL because older `gh` releases do not accept `closingIssuesReferences` as a `--json` field (gh 2.47.0 rejects it; 2.103.3 accepts it).

`files` lists at most 100 files; when `changedFiles` is larger, read the full list with `gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/files?per_page=100" --jq '.[].filename'`.

## Read review threads

Every thread, every page:

```bash
gh api graphql --paginate -F owner={owner} -F repo={repo} -F pr={pr} -f query='
query($owner: String!, $repo: String!, $pr: Int!, $endCursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first: 100) {
            totalCount
            nodes { databaseId url body createdAt author { __typename login } }
          }
        }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[]
  | {id, isResolved, isOutdated, path, line, count: .comments.totalCount,
     comments: [.comments.nodes[] | {databaseId, url, author: .author.login, type: .author.__typename, body}]}'
```

- `author.__typename` is `Bot` for a GitHub App or bot account. A deleted account has a null `author`: treat it as `Human`.
- A thread whose `count` exceeds the comments returned was not read in full: treat it as unhandled, show the human its link, and let them decide its reply.
- The first comment's `databaseId` is the id a reply targets.

## Read reviews and conversation comments

```bash
gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/reviews?per_page=100" \
  --jq '.[] | {id, html_url, state, user: .user.login, type: .user.type, submitted_at, body}'

gh api --paginate "repos/{owner}/{repo}/issues/{pr}/comments?per_page=100" \
  --jq '.[] | {id, html_url, user: .user.login, type: .user.type, created_at, body}'
```

`--paginate` with `per_page=100` returns every page. `type` is `Bot` or `User`. An item is handled when a later comment by the account contains its `html_url` ([comments.md](comments.md) "C-1").

## Reply

Inside a review thread (to the thread's first comment's `databaseId`):

```bash
gh api --method POST "repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies" \
  -f body="$(cat {reply_file})"
```

To a review body or a conversation comment — a new conversation comment that starts with the link:

```bash
gh pr comment {pr} -R {owner}/{repo} --body-file {reply_file}
```

Write each reply to a file first and pass the file, so quotes and backticks survive the shell.

## Resolve a thread

```bash
gh api graphql -F threadId={thread_id} -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) { thread { id isResolved } }
}' --jq '.data.resolveReviewThread.thread'
```

`isResolved: true` in the response confirms it; anything else is reported as unresolved.

## CI status

```bash
gh pr view {pr} -R {owner}/{repo} --json headRefOid,statusCheckRollup \
  --jq '{head: .headRefOid, checks: [.statusCheckRollup[] | {type: .__typename, name: (.name // .context), status, conclusion, state}]}'
```

The rollup mixes two shapes: a `CheckRun` has `status` and `conclusion`, a `StatusContext` only `state`.

- Every `CheckRun` `COMPLETED` with `SUCCESS`, `NEUTRAL`, or `SKIPPED`, and every `StatusContext` `SUCCESS` → green.
- `QUEUED`, `IN_PROGRESS`, `PENDING`, `EXPECTED` → wait and re-read.
- An empty rollup, or any other value (`FAILURE`, `TIMED_OUT`, `CANCELLED`, `ERROR`, `ACTION_REQUIRED`, `STARTUP_FAILURE`, `STALE`) → not green.

Read the rollup for the head the brief will describe: if `head` differs from the head the loop pinned, the head moved ([workflow.md](workflow.md) "2-1").

## Update the branch

```bash
gh pr update-branch {pr} -R {owner}/{repo}
```

Merges the base into the PR branch (a merge commit). Use `--rebase` only when the repository's convention rebases PR branches. Either moves the head. A conflict means the update did not happen: report it, never resolve conflicts unprompted.

## List the rules on the base branch

Every active rule that applies to the branch, from every ruleset:

```bash
gh api --paginate "repos/{owner}/{repo}/rules/branches/{branch}?per_page=100" \
  --jq '.[] | {type, ruleset_id, ruleset_source, parameters}'
```

`--paginate` reads every page. This read does not include classic branch protection. To see why the account may bypass a ruleset:

```bash
gh api "repos/{owner}/{repo}/rulesets/{ruleset_id}" --jq '{name, enforcement, current_user_can_bypass}'
```

For `required_signatures`, read whether every commit is verified (this endpoint returns at most 250 commits; a PR with more cannot be judged and the rule goes to the brief as bypassed):

```bash
gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/commits?per_page=100" \
  --jq '.[] | {sha, verified: .commit.verification.verified}'
```

## Allowed merge methods

```bash
gh api graphql -F owner={owner} -F repo={repo} -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) { mergeCommitAllowed squashMergeAllowed rebaseMergeAllowed }
}' --jq '.data.repository'
```

A `pull_request` rule's `parameters.allowed_merge_methods` (previous section) narrows these further. Use a method both allow. When several remain, use the one the repository's docs name; when the docs are silent, the one its recent merged PRs used; when that cannot be told either, ask the human in the brief.

## Post the self-review

A review of type COMMENT (the author cannot approve or request changes on their own PR):

```bash
gh pr review {pr} -R {owner}/{repo} --comment --body-file {review_file}
```

## Workflow files (gated-publish recognition)

The safety net's "default branch" is the PR's base branch in this skill ([workflow.md](workflow.md) "The post-merge safety net"), so these reads take `{base_branch}`.

Recognition of an artifact whose publish is gated behind a separate trigger ([post-merge-safety-net.md](post-merge-safety-net.md) "Gated publish", condition (1)) reads **every** workflow file on the base branch:

```bash
gh api "repos/{owner}/{repo}/git/trees/{base_branch}:.github/workflows" \
  --jq '{truncated, files: [.tree[] | select(.type == "blob") | .path]}'
```

`truncated: false` on a read that succeeded → the listing is complete. `truncated: true`, or a read that fails (a 404 included) → the listing may be incomplete, and the row does not apply. Names are relative to the directory: prefix each with `.github/workflows/` to match the reads below, which return each workflow's `path` from the repository root. Read each file at a ref (the base branch, or the ref a reusable-workflow call names):

```bash
gh api "repos/{owner}/{repo}/contents/.github/workflows/{file}?ref={ref}" --jq .content | base64 -d
```

A file that cannot be read is a workflow whose publishing cannot be determined: the row does not apply. Which workflows can start runs at all — taken after the merge, with the settle read:

```bash
gh api --paginate "repos/{owner}/{repo}/actions/workflows?per_page=100" \
  --jq '.workflows[] | {path, state}'
```

## CI and build configuration outside Actions (gated-publish recognition)

Condition (3) of recognition looks for CI or build configuration other than GitHub Actions in the base branch's whole tree:

```bash
gh api "repos/{owner}/{repo}/git/trees/{base_branch}?recursive=1" \
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

GitHub creates runs asynchronously after the merge: an empty or partial result right after it means "not yet". The expected set is every active workflow whose `push` trigger admits the base branch and whose path filters admit a file the merge changed. Match each expected workflow to a row by `path` **and** `event: push`. When the base branch is itself another open PR's head (a stacked PR's base, an integration branch with its milestone PR), the merge commit also carries that PR's `pull_request` runs for the same paths, and those never stand in for the merge's `push` run. For a library or CI-deploy repository this read is V-2 (and, for a library, V-3): every expected run completed with `success`; for a CI-deploy repository, the deploy workflow's run is the one V-2 names.

**Publish-run read** (gated publish only) — no run of a publishing workflow started at or after the merge, on any branch or tag, from any event; once for each publishing workflow:

```bash
gh run list -R {owner}/{repo} --all --workflow {publishing_workflow_file} --created ">={merge_time}" \
  --json databaseId,event,status,createdAt,headBranch,url
```

No rows from every one → the check passes; any row fails it. A read that fails is verification that cannot be completed. `--all` needs gh 2.52.0 or later (added in gh v2.52.0, cli/cli#9162; `--created` dates from v2.28.0). An older gh rejects the flag (`unknown flag: --all`, observed with gh 2.23.0), so the read fails: the probe at 2-4 item 6 ([workflow.md](workflow.md) "2-4") runs it before the merge, so an older gh shows in the brief as a check that cannot be read now, and a read that fails anyway after a merge fails closed as above.

## Merge

Pinned to the reviewed head, with the chosen method (`--merge`, `--squash`, or `--rebase`):

```bash
gh pr merge {pr} -R {owner}/{repo} --merge --match-head-commit {sha}
```

When the gate decided the merge uses the bypass ([workflow.md](workflow.md) "2-4" item 5), add `--admin`. `--admin` merges a PR that does not meet the base branch's requirements, so it is used only after the gate showed every other requirement met, or the human accepted the listed ones. It also skips a merge queue — never use it where the base branch has a `merge_queue` rule.

Classify the result as [post-merge-safety-net.md](post-merge-safety-net.md) "Pre-merge steps and the merge call's result" defines, then **always** read the state:

```bash
gh pr view {pr} -R {owner}/{repo} --json state,mergeCommit,mergedAt --jq '{state, merge_commit: .mergeCommit.oid, mergedAt}'
```

- `MERGED` → merged; keep `merge_commit` for verification and a revert.
- Not merged, after a non-zero exit whose output gives GitHub's reason the merge is not allowed (a `GraphQL: ` line stating a reason, or `is not mergeable:`) → an explicit refusal: nothing merged.
- Anything else — a timeout, a network or HTTP error, a non-`MERGED` state after exit 0 (a merge queue took it), a failed read — → *merge outcome unconfirmed*: stop the line.

Do not pass `--delete-branch` unless the repository's convention deletes merged branches.

## Retarget a stacked PR

```bash
gh pr edit {pr} -R {owner}/{repo} --base {new_base_branch}
```

Proposed in the stacked PR's brief, run only after the human's "merge" for it, and followed by a fresh 2-2 to 2-4: the diff and CI change with the base.

## Create a revert PR

In the run's worktree for the repository:

```bash
gh pr view {pr} -R {owner}/{repo} --json mergeCommit --jq '.mergeCommit.oid'

git fetch origin
git switch -c revert-pr-{pr} origin/{base_branch}

# Merge-commit method: revert the merge commit against its first parent
git revert -m 1 {merge_commit_sha} --no-edit
# Squash method: the squash commit is an ordinary commit
git revert {merge_commit_sha} --no-edit
# Rebase method: revert each of the PR's commits on the base branch, newest first

git push -u origin revert-pr-{pr}
gh pr create -R {owner}/{repo} --base {base_branch} --head revert-pr-{pr} \
  --title "Revert: {original title}" --body-file {revert_body_file}
```

The revert PR's body says what failed and links the original PR. It then goes through the same gate, review, and merge as any PR, on the human's "revert" answer only ([verification.md](verification.md) "The revert"); the safety net's auto-revert procedure and its required-check wait do not run in this skill.

## Comment on the PR

The safety net's comments — the result and not-yet-published comments after 2-7, and the revert comment — in English:

```bash
gh pr comment {pr} -R {owner}/{repo} --body-file {comment_file}
```

## Create an issue for a tracked comment

```bash
gh issue create -R {owner}/{repo} --title "{title}" --body-file {issue_body_file}
```

The body links the comment it came from and the PR. Follow the repository's issue templates when it defines them.
