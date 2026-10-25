# GitHub Platform Guide — Renovate PRs

GitHub-only for v1. The commands are written for the `gh` CLI and are the reference specification of each operation (see Access Method); replace `{owner}`, `{repo}`, `{pr}` as needed.

## Table of Contents

- [Access Method](#access-method)
- [List and filter Renovate PRs](#list-and-filter-renovate-prs)
- [Read a PR: diff, files, body, branch, labels](#read-a-pr-diff-files-body-branch-labels)
- [Release age (the cooldown gate)](#release-age-the-cooldown-gate)
- [CI status (the merge gate)](#ci-status-the-merge-gate)
- [Merge (respect the repo merge method)](#merge-respect-the-repo-merge-method)
- [Create and merge a revert PR (auto-revert)](#create-and-merge-a-revert-pr-auto-revert)
- [Resolve sibling / superseded PRs](#resolve-sibling--superseded-prs)
- [main divergence: update branch](#main-divergence-update-branch)
- [Comment on the PR](#comment-on-the-pr)
- [Read bot config](#read-bot-config)

## Access Method

Resolved once per run as SKILL.md "Platform Access" describes: a connector for GitHub only when it covers **every** operation in this file and in [release-age.md](release-age.md), otherwise the CLI.

- **CLI**: `gh` installed and authenticated (`gh auth status`); the current directory is the target repo, or pass `-R {owner}/{repo}`.
- **Connector coverage**: each command is the reference for its operation. A connector tool covers an operation only when its own description or schema shows that it returns the same fields with the same completeness the command guarantees, or performs the same write. Where that cannot be confirmed, the operation is not covered, and one uncovered operation sends the whole run to the CLI. The tests below are where a connector falls short **silently**, letting a PR through that the reference read would have held, so each is covered only on positive evidence:
  - **Complete lists.** The open-PR list and the CI entries below are covered only when the tool shows it returns every item — it reads every page itself, or exposes a signal that ends the pagination (a total, a next-page cursor or link) that the run follows to the end. A page-number parameter with no such signal is not enough: a page the tool shortened by its own filtering looks exactly like the last page.
  - **The CI gate** is covered only when the connector's tools — one or several — return every entry of the rollup the reference reads: every check run **and** every commit status on the PR's head, each with its own settled state, complete by the test above. Check runs alone, or one combined state without the individual statuses, do not cover it: a failing commit status, or a failing check hidden inside a summary, would read as green.
  - **The lower-bound read** (release-age.md) is covered only by a tool returning the PR's commits with each commit's author login and `committedDate`, newest included. A list that may stop short of the newest commits gives an older bound, which makes a release look older than it is — the unsafe direction.
  - **Upstream release lookups** are covered only by a tool that reads a release **by exact tag** from a repository other than the target, with its `published_at`. A tool confined to the target repository does not cover them.
  - **The merge** is covered only by a tool that takes the repo's merge method, and the post-approval `mergeStateStatus` read only by one that returns it — without it a `BLOCKED` PR cannot be told from a mergeable one.
  - **Writes** — approving a review, merging, updating a branch with the merge or the rebase form, creating, approving and merging the revert PR, closing with a comment, commenting — are covered by a tool that performs that write and reports whether it succeeded.
- **Outside this choice**: local git (fetch, branches, revert, push) and the deploy tooling the verification plan uses (`kubectl`, Flux/Argo CLIs, `talosctl`, …) always run as written, whatever the method.

## List and filter Renovate PRs

List open PRs with the fields needed for composite detection (author, branch, labels):

```bash
gh pr list --state open --limit 100 \
  --json number,title,author,headRefName,labels,isDraft \
  --jq '.[] | {number, title, author: .author.login, isBot: .author.is_bot, branch: .headRefName, labels: [.labels[].name]}'
```

`--limit` caps what is fetched: if the number of rows returned equals it, the list may be short — raise the limit and re-read before triaging.

Filter directly by the known bot author (fast path for the common case):

```bash
gh pr list --state open --author "app/renovate" --json number,title,headRefName
```

Filter by branch prefix or label when the author is a self-hosted/custom account
(combine with the OR-detection in detection.md):

```bash
gh pr list --state open --json number,title,headRefName,labels \
  --jq '.[] | select(.headRefName | startswith("renovate/"))'

gh pr list --state open --label dependencies --json number,title
```

Read the PR body to check for Renovate signatures (Mend footer, `<!--renovate-debug-->`):

```bash
gh pr view {pr} --json body --jq '.body'
```

## Read a PR: diff, files, body, branch, labels

```bash
# Metadata in one call
gh pr view {pr} --json number,title,author,headRefName,baseRefName,labels,body,mergeable,mergeStateStatus

# The actual diff (read this, not just the changelog)
gh pr diff {pr}

# Just the changed file list
gh pr view {pr} --json files --jq '.files[].path'
```

For release notes, the bot body often links upstream; otherwise fetch the upstream
release directly (primary source):

```bash
# Releases for an upstream repo, to read notes for the target version
gh release view vX.Y.Z -R {upstream_owner}/{upstream_repo}
gh api repos/{upstream_owner}/{upstream_repo}/releases/tags/vX.Y.Z --jq '.body'
```

## Release age (the cooldown gate)

The commands for the release-age gate (workflow.md 1-3) — upstream release dates with their sanity check, the lower bound from Renovate's newest authored commit, and the cooldown-wait marker lookup — live with the procedure in [release-age.md](release-age.md), because each one is only correct together with the rule around it.

## CI status (the merge gate)

CI green is a precondition for merge (workflow.md 2-3). Read the rolled-up status:

```bash
# Human-readable checks summary
gh pr checks {pr}

# Programmatic rollup — every check must be SUCCESS (or neutral/skipped) to merge.
# The rollup is a union: a CheckRun carries status/conclusion, a StatusContext only state,
# so select __typename and both shapes or a commit status reads as nulls.
gh pr view {pr} --json statusCheckRollup \
  --jq '.statusCheckRollup[] | {type: .__typename, name: (.name // .context), status, conclusion, state}'
```

Decision:

- Every `CheckRun` `COMPLETED` with conclusion `SUCCESS`/`NEUTRAL`/`SKIPPED`, and every `StatusContext` with state `SUCCESS` → CI gate passes.
- Any `FAILURE`/`TIMED_OUT`/`CANCELLED` → **do not merge**; investigate and present as a finding.
- `PENDING`/`IN_PROGRESS` → wait, then re-check.
- An **empty** rollup, or any other value (`ERROR`, `ACTION_REQUIRED`, `STARTUP_FAILURE`, `STALE`, …) → not green: **do not merge**.

## Approve before merge

Submit a GitHub review approval after the go decision (autonomous) or user approval (interactive) at step 2-5, and before calling `gh pr merge`. This satisfies branch-protection rules requiring at least one approved review:

```bash
gh pr review {pr} --approve --body "Dependency update reviewed: release notes read, CI green, risk assessed."
```

Notes:
- The `--body` is optional but leaves a human-readable audit trail on the PR.
- GitHub prevents approving your own PRs — for Renovate-authored PRs this is never an issue.
- If the repo requires CODEOWNERS or team-based required reviewers, an agent approval may not satisfy the requirement. Check `mergeStateStatus` after approving; if it still shows `BLOCKED`, never bypass it — autonomous: defer the PR; interactive: surface the gap and ask the user to approve manually.

## Merge (respect the repo merge method)

Phase 0 determined the merge method. Use the matching flag — do not assume squash:

```bash
gh pr merge {pr} --merge     # merge commit
gh pr merge {pr} --squash    # squash
gh pr merge {pr} --rebase    # rebase
```

If the repo enforces a method, the others will be rejected — that itself confirms
the method. Add `--delete-branch` only if the repo convention deletes merged branches.

Never use `--admin` to bypass a failing required check; a red check is a signal,
not an obstacle.

**Classify the call's result, then confirm from platform state** (workflow.md 2-6).
`gh pr merge` submits the GraphQL `mergePullRequest` mutation; with `gh` (behaviour
read from source: gh v2.103.2 `pkg/cmd/pr/merge/merge.go` and `http.go`, which submit
the mutation through go-gh v2.17.0's `Mutate` — `pkg/api/graphql_client.go`,
`pkg/api/errors.go` — and cli/shurcooL-graphql v0.0.4 `graphql.go`, which turn the
response into the error string) an **explicit refusal** is a non-zero exit whose stderr
carries one of:

- a line beginning `GraphQL: ` — go-gh's rendering of an `errors[]` payload in a `200`
  response to the mutation — whose message gives a reason the merge is not allowed. An errors payload
  is not automatically a refusal: GitHub can also return one alongside partial results
  when a request exceeds resource limits, and one reporting a timeout, a resource limit,
  or an internal failure is **not a refusal**;
- `is not mergeable:` — printed by `gh` itself from the `mergeStateStatus` it read,
  before it submits the mutation; nothing was sent.

Everything else is **not a refusal**: a line beginning `non-200 OK status code:`
(shurcooL's rendering of any non-`200` response to the mutation, with the status and
body — GitHub may answer a GraphQL request it terminated after 10 seconds with a `502`
or `504`, per
[GitHub Docs, "Rate limits and query limits for the GraphQL API"](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api#timeouts)),
a line beginning `HTTP ` (go-gh's rendering of a non-2xx response to one of `gh`'s own
reads; the output does not say which call failed), a network or TLS error, a killed or
hung command, and **exit 0**. `gh` exits 0 without merging when the base branch requires
a merge queue — it submits the auto-merge mutation instead (`http.go`), so the PR joins
the queue and merges later, outside the one-in-flight loop.
Through a **connector**, the same rule: only a tool result that carries the platform's
refusal reason counts as a refusal; a tool error that does not show one is not.

After **every** merge call, refusal or not, read the PR (a read that fails is a
*merge outcome unconfirmed*):

```bash
gh pr view {pr} --json state,mergeCommit --jq '{state, merge_commit: .mergeCommit.oid}'
```

`MERGED` confirms the merge. Anything else confirms nothing unless the call was an
explicit refusal; after a call that was not, it is a *merge outcome unconfirmed*.

## Create and merge a revert PR (auto-revert)

Used by the autonomous auto-revert procedure (verification.md). Identify the
commit the merge produced on the default branch, revert it on a branch, then
open, approve, and merge the revert PR:

```bash
# The commit the merge created on the default branch (merge/squash methods)
gh pr view {pr} --json mergeCommit --jq '.mergeCommit.oid'

git fetch origin
git checkout -b revert-pr-{pr} origin/{default_branch}

# Merge-commit method — revert the merge commit against its first parent:
git revert -m 1 {merge_commit_sha} --no-edit
# Squash method — the squash produced an ordinary commit; no -m:
git revert {merge_commit_sha} --no-edit
# Rebase method — the PR's commits landed individually; identify them on the
# default branch (git log) and revert each, newest first.

git push -u origin revert-pr-{pr}
gh pr create --title "Revert: {original PR title}" \
  --body "Auto-revert of #{pr}: post-merge verification failed — {one-line cause}. Details on #{pr}."
gh pr review {revert_pr} --approve --body "Auto-revert of a failed dependency update."
gh pr merge {revert_pr} --<method>
```

Notes:

- The revert PR goes through the normal merge path (approval + required checks) —
  never `--admin`. If the revert itself is blocked (CI red on the revert, required
  reviewers), **escalate to the human** (verification.md); do not force it.
- Revert Git **before** undoing any B-class apply, so a GitOps controller does not
  re-apply the bad version over the rollback.

## Resolve sibling / superseded PRs

When a major-bump PR supersedes a digest-bump PR (workflow.md 1-2 / 2-6):

```bash
# Close the superseded PR with an explanatory comment
gh pr close {superseded_pr} --comment "Superseded by #{survivor_pr} (major bump includes this digest)."
```

Renovate rebases or recreates its own PRs on its **own schedule**, so closing the
redundant one is usually enough. If the survivor must be brought up to date with
`main` immediately, use `gh pr update-branch` (below) rather than waiting on the bot.

## main divergence: update branch

If the PR is behind `main` and a clean update is possible (workflow.md 2-6):

```bash
gh pr update-branch {pr}            # default: merge `main` into the PR branch (creates a merge commit)
gh pr update-branch {pr} --rebase   # alternative: rebase the PR branch onto `main`
```

`gh pr update-branch` has no fast-forward mode — the default creates a merge commit,
`--rebase` rebases. If either reports a conflict that needs manual resolution,
**stop and ask the user** (per the main-divergence rule) rather than resolving
conflicts unprompted.

## Comment on the PR

Documentation comments (workflow.md 2-8). Comment only when real steps or risk
exist, in English.

```bash
# Pre-comment: manual steps (B/C work) for humans and future agents
gh pr comment {pr} --body "Manual apply required after merge:
1. \`talosctl upgrade-k8s --to X.Y.Z\`
2. Verify nodes report the new version.
(Class B — agent-executable; awaiting approval.)"

# Post-comment: closing applied & verified result
gh pr comment {pr} --body "Applied & verified.
- Merged and reconciled by Flux.
- talosctl upgrade-k8s completed; all nodes on X.Y.Z.
- All workloads Ready at expected replica counts; no regression."
```

## Read bot config

For Phase 0 / detection refinement:

```bash
# Show whichever config file exists
gh api repos/{owner}/{repo}/contents/renovate.json5 -H "Accept: application/vnd.github.raw" 2>/dev/null
gh api repos/{owner}/{repo}/contents/.github/renovate.json -H "Accept: application/vnd.github.raw" 2>/dev/null
```

(Reading the files locally from the checked-out repo is equally fine and usually
simpler.)

## CLAUDE.md Config Example

```markdown
## Code Hosting
- platform: github
- merge_method: rebase
- deploy: flux   # gitops | ci | manual
```
