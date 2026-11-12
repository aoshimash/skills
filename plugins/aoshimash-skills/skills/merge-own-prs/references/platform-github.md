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
- [Merge](#merge)
- [Runs for the merge commit](#runs-for-the-merge-commit)
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

## Merge

Pinned to the reviewed head, with the chosen method (`--merge`, `--squash`, or `--rebase`):

```bash
gh pr merge {pr} -R {owner}/{repo} --merge --match-head-commit {sha}
```

When the gate decided the merge uses the bypass ([workflow.md](workflow.md) "2-4" item 5), add `--admin`. `--admin` merges a PR that does not meet the base branch's requirements, so it is used only after the gate showed every other requirement met, or the human accepted the listed ones. It also skips a merge queue — never use it where the base branch has a `merge_queue` rule.

Classify the result, then **always** read the state:

```bash
gh pr view {pr} -R {owner}/{repo} --json state,mergeCommit,mergedAt --jq '{state, merge_commit: .mergeCommit.oid, mergedAt}'
```

- `MERGED` → merged; keep `merge_commit` for verification and a revert.
- Not merged, after a non-zero exit whose output gives GitHub's reason the merge is not allowed (a `GraphQL: ` line stating a reason, or `is not mergeable:`) → an explicit refusal: nothing merged.
- Anything else — a timeout, a network or HTTP error, a non-`MERGED` state after exit 0 (a merge queue took it), a failed read — → *merge outcome unconfirmed*: stop the line.

Do not pass `--delete-branch` unless the repository's convention deletes merged branches.

## Runs for the merge commit

```bash
gh api --paginate "repos/{owner}/{repo}/actions/runs?head_sha={merge_commit_sha}&per_page=100" \
  --jq '.workflow_runs[] | {id, name, path, event, status, conclusion, html_url}'
```

GitHub creates runs shortly after the merge: an empty or partial list right after it means "not yet". Wait until every workflow the plan expects has a run and every run has `status: completed`.

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

The revert PR's body says what failed and links the original PR. It then goes through the same gate, review, and merge as any PR ([verification.md](verification.md) "The revert").

## Comment on the PR

The verified comment after 2-7, and the failure comment after a revert:

```bash
gh pr comment {pr} -R {owner}/{repo} --body-file {comment_file}
```

## Create an issue for a tracked comment

```bash
gh issue create -R {owner}/{repo} --title "{title}" --body-file {issue_body_file}
```

The body links the comment it came from and the PR. Follow the repository's issue templates when it defines them.
