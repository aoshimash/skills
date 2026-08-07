# GitHub Platform Guide

## Prerequisites

- `gh` CLI installed and authenticated

## Detect Platform

Check in order:
1. The project's agent instructions (e.g. CLAUDE.md, AGENTS.md): an `## Issue Tracker` section with `platform: github`
2. Git remote URL contains `github.com`

## Read Issue

```bash
gh issue view <number>
```

Structured JSON:
```bash
gh issue view <number> --json title,body,labels,assignees,state
```

## List Open Issues

To let the user select an issue when no identifier is provided (Phase 0 step 2):

```bash
gh issue list --state open --limit 20
```

Present the list to the user and ask them to select one.

## Platform-Level Issue Relationships

`gh issue view --json` and `gh issue list --json` expose issue relationships as
first-class fields. Read relationships from these fields as the primary method —
prefer them over the REST sub-issues endpoint or parsing prose out of issue bodies.

| Field | Shape | Holds |
|---|---|---|
| `parent` | object, or `null` | The parent issue, when this issue is a sub-issue |
| `subIssues` | `{nodes: [...], totalCount}` | This issue's sub-issues |
| `subIssuesSummary` | `{total, completed, percentCompleted}` | Sub-issue completion counts |
| `blockedBy` | `{nodes: [...], totalCount}` | Issues that must close before this one |
| `blocking` | `{nodes: [...], totalCount}` | Issues this one blocks |

Every node carries `number`, `title`, `state`, `url`, and `id` — enough to build a
dependency graph without a second call per issue. `state` is upper-case (`OPEN` /
`CLOSED`). `subIssues`, `blockedBy`, and `blocking` wrap their contents in `.nodes`, so a
`.subIssues[]` expression finds nothing. Nodes do NOT carry `body` or `labels`; fetch
those per issue when needed.

**Availability.** These fields need `gh` v2.94.0 or newer. Sub-issues work on
GitHub.com and GHES 3.17+; `blockedBy` / `blocking` relationships require GHES 3.19+.
Confirm what the installed `gh` supports before relying on a field — the `JSON FIELDS`
list in the help output names every field it accepts, and an unsupported field name
makes the command fail rather than return empty:

```bash
gh issue view --help
```

**Fallback.** Fall back to body parsing (see [Check Dependency Links](#check-dependency-links)) when either applies:
- The field is unavailable — older `gh`, or GHES below the versions above.
- The field comes back empty but the issue describes the relationship in prose. Structured fields only reflect relationships that were actually registered on the platform; an issue whose dependency was written as `Blocked by: #N` text and never linked has an empty `blockedBy`.

## Detect Sub-Issues of a Parent

Used in Phase 0 (Setup and Mode Selection) to check whether a single referenced issue is a parent with open sub-issues:

```bash
gh issue view <number> --json subIssuesSummary,subIssues \
  --jq '{total: .subIssuesSummary.total, sub: [.subIssues.nodes[] | {number, title, state}]}'
```

`subIssuesSummary.total` alone answers "is this a parent?"; `subIssues.nodes[].state`
identifies which sub-issues are still `OPEN` and therefore in scope for a batch.

If the fields are unavailable (see [Platform-Level Issue Relationships](#platform-level-issue-relationships)), fall back in order:

```bash
# 1. REST sub-issues endpoint
gh api repos/{owner}/{repo}/issues/<number>/sub_issues --jq '.[] | {number, title, state}'

# 2. Parse the parent issue's body for a task list or `#N` references
gh issue view <number> --json body --jq '.body'
```

## List Sub-Issues / Issues by Milestone / Issues by Label

Used in Batch mode (Phase 0 source selection and Phase B1 dependency parsing). `gh issue list`
accepts the same relationship fields, so one call per batch source yields both the issue set
and its dependency edges:

```bash
# Sub-issues of a parent — numbers and states (see above for the fallbacks)
gh issue view <parent-number> --json subIssues --jq '.subIssues.nodes[] | {number, title, state}'

# By milestone
gh issue list --milestone "<milestone>" --state open \
  --json number,title,body,labels,state,parent,blockedBy

# By label
gh issue list --label "<label>" --state open \
  --json number,title,body,labels,state,parent,blockedBy
```

For a sub-issue batch, `subIssues.nodes` carries no `body` or `labels`, so fetch each
sub-issue after listing:

```bash
gh issue view <number> --json number,title,body,labels,state,parent,blockedBy
```

## Check Dependency Links

Read the platform-level relationships from the structured fields first:

```bash
gh issue view <number> --json blockedBy,blocking \
  --jq '{blockedBy: [.blockedBy.nodes[] | {number, state}], blocking: [.blocking.nodes[].number]}'
```

Only blockers whose `state` is `OPEN` actually gate implementation — a `CLOSED`
blocker is satisfied and must not become a DAG edge.

If the fields are unavailable, the same relationships are readable from REST:

```bash
gh api repos/{owner}/{repo}/issues/<number>/dependencies/blocked_by --jq '.[] | {number, state}'
gh api repos/{owner}/{repo}/issues/<number>/dependencies/blocking --jq '.[] | {number, state}'
```

REST returns `state` lower-case (`open` / `closed`) where the JSON fields return
`OPEN` / `CLOSED` — normalize before comparing.

Then read the body, for issues whose dependencies were only ever written in prose:

```bash
gh issue view <number> --json body --jq '.body'
```

Match `Blocked by: #N`, `Depends on: #N`, and `After: #N` — see [batch.md](batch.md) B1-1 for the
full pattern list. **Union the two sources**: an issue can carry a registered
`blockedBy` link and a prose mention of a different blocker, and taking only one
source would drop a real edge.

## Create Branch

**Worktree flow (the default in both modes):**

```bash
git fetch origin
grep -qxF '.worktrees/' .git/info/exclude 2>/dev/null || echo '.worktrees/' >> .git/info/exclude
git worktree add .worktrees/<branch-name> -b <branch-name> origin/<default-branch>
```

**Batch integration mode** ([batch.md](batch.md) B1-4, B2-1) replaces the base with the
batch's integration branch, and creates that branch once at batch start:

```bash
# once, after the execution plan is approved in integration mode
git fetch origin
if git show-ref --verify --quiet refs/remotes/origin/integration/issue-<parent-number>; then
  : # already exists — reuse as-is; create nothing, push nothing
else
  git branch --no-track integration/issue-<parent-number> origin/<default-branch>
  git push -u origin integration/issue-<parent-number>
fi

# per issue, immediately before dispatching its implementer
git fetch origin
git worktree add .worktrees/<branch-name> -b <branch-name> origin/integration/issue-<parent-number>
```

The existence probe is not optional: `git branch` on a name that already exists fails with
`fatal: a branch named '<name>' already exists` and exit 128, and pushing a freshly cut
branch over a remote branch that has advanced is rejected non-fast-forward — so the create
path cannot double as the reuse path. `--no-track` keeps the new branch from inheriting the
default branch as its upstream; the `push -u` then sets the upstream to its own remote
branch. Never reset, force-push, or delete the branch while a batch is running.

To report what a reused branch already carries (batch.md B1-3, as a plan input — B1-4 acts
on what the plan established rather than discovering it), compare it against the default
branch — `ahead_by` and `behind_by` are reported independently, so a branch can be both:

```bash
gh api repos/{owner}/{repo}/compare/<default-branch>...integration/issue-<parent-number> \
  --jq '{ahead: .ahead_by, behind: .behind_by, status: .status}'
```

## Push Branch

```bash
git push -u origin <branch-name>
```

## Read Issue Comments (research comment)

Used in workflow.md 1-1 to find a research comment attached by the create-issue
Design Flow:

```bash
gh issue view <number> --comments
```

Structured: `gh issue view <number> --json comments`.

## Write Back Design Decisions to the Issue

Used in workflow.md 1-3 to append batched-question answers to the issue's
`## Design Decisions` section (create the section if absent):

```bash
gh issue view <number> --json body --jq '.body' > <tmpfile>
# append the new decisions under "## Design Decisions" in <tmpfile>
gh issue edit <number> --body-file <tmpfile>
```

## Check for a PR Template

A repository template, when present, is the PR body skeleton (workflow.md 3-1).
Look for `.github/PULL_REQUEST_TEMPLATE.md`, `PULL_REQUEST_TEMPLATE.md`,
`docs/PULL_REQUEST_TEMPLATE.md`, or a `.github/PULL_REQUEST_TEMPLATE/` directory.

## Create Draft Pull Request

PRs are always created as drafts (workflow.md 3-1); the body sections come from
workflow.md 3-1 (or the repository's PR template when one exists):

```bash
gh pr create --draft --title "<title>" --body-file <body-file>
```

In batch **integration mode** the base is the batch's integration branch, named in the
implementer's dispatch ([batch.md](batch.md) B2-2) — never the default branch:

```bash
gh pr create --draft --base integration/issue-<parent-number> --title "<title>" --body-file <body-file>
```

## Update PR Body (gate results)

```bash
gh pr edit <number> --body-file <body-file>
```

## Read PR Body (decision log)

Used by Batch mode's harvesting step (batch.md B3-1) to read each PR's
`Decisions & Deviations` section back out:

```bash
gh pr view <number> --json body --jq '.body'
```

## Automated Reviewers

Used in workflow.md 3-4 ([automated-review.md](automated-review.md)) to detect
the repository's automated reviewers, wait for them, and read their findings.

**Detect (step A).** After the declared `## Automated Reviewers` section in the
project's agent instructions, in order of signal strength:

```bash
# Workflows that run on pull_request events (read each one's `types:` — a
# reviewer gated on ready_for_review cannot post while the PR is a draft)
grep -rl "pull_request" .github/workflows/ 2>/dev/null

# Review-posting jobs that already ran on this PR show up as checks
gh pr checks <pr-number> --json name,workflow,bucket

# Bot accounts requested as reviewers on this PR
gh pr view <pr-number> --json reviewRequests

# Bot reviewers seen on recent merged PRs (logins ending in `[bot]`)
gh pr list --state merged --limit 10 --json number,reviews \
  --jq '.[] | {number, reviewers: [.reviews[].author.login]}'
```

**Wait (step B).** A reviewer that runs as a check finishes when its check
finishes — `gh pr checks --watch` (see [Monitor CI](#monitor-ci)) is the
completion signal, no separate polling. For a reviewer with no check run, poll
the endpoints below within the wall-clock cap.

**Read findings (step C).** The same three comment surfaces the
respond-to-pr-review skill uses; `user.type` is the authoritative bot flag
(`"Bot"` / `"User"`):

```bash
# Reviews (APPROVE / CHANGES_REQUESTED / COMMENT, with their body)
gh api repos/{owner}/{repo}/pulls/<pr-number>/reviews \
  --jq '.[] | {id, state, body, user: .user.login, user_type: .user.type}'

# Inline review comments (skip entries whose `in_reply_to_id` is non-null)
gh api repos/{owner}/{repo}/pulls/<pr-number>/comments \
  --jq '.[] | {id, path, line, position, body, user: .user.login, user_type: .user.type, in_reply_to_id}'

# Conversation comments
gh api repos/{owner}/{repo}/issues/<pr-number>/comments \
  --jq '.[] | {id, body, user: .user.login, user_type: .user.type}'
```

An inline comment whose `position` is `null` is outdated — drop it.

**Reply (step E).** Reply commands (inline-comment replies, general comments,
optional thread resolution) are the respond-to-pr-review skill's, unchanged:
see [`../../respond-to-pr-review/references/platform-github.md`](../../respond-to-pr-review/references/platform-github.md)
"Post Replies".

## Mark PR Ready for Review

Only after both review-gate stages pass, CI is green, and the automated review
response has completed (workflow.md 3-5):

```bash
gh pr ready <number>
```

## Link PR to Issue

Include `Closes #<number>` in the PR body to auto-close the issue on merge.
Use `Relates to #<number>` if the PR only partially addresses the issue.

**Closing keywords act only on PRs that target the default branch.** GitHub's
documentation is explicit: "If the pull request targets any other branch, then these
keywords are ignored, no links are created, and merging the PR has no effect on the
issues"
([Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)).
So in batch integration mode, where every per-issue PR targets the integration branch,
merging a PR never closes its issue, and `gh pr view <number> --json
closingIssuesReferences` returns an empty list for it. Keep the keyword in the body
regardless: it is the attribution signal the merge gate reads, and the closing reference
the milestone PR carries. Do not retarget a per-issue PR at the default branch to make it
fire, and do not treat an open issue after a merged PR as a fault.

## Confirm a PR Merged into the Integration Branch — and Was Not Reverted

Used by [batch.md](batch.md) B2-4 to confirm a merge from platform state rather than from
the merge gate's report alone. **Two reads, both required.**

**1. The merge.**

```bash
gh pr view <number> --json number,state,baseRefName,mergeCommit,labels \
  --jq '{number, state, base: .baseRefName, merge: .mergeCommit.oid,
         labels: [.labels[].name]}'
```

`state` must be `MERGED` and `base` must be the batch's integration branch. `mergeCommit`
is `null` while the PR is open, so treat a null merge commit as "not merged", never as
"merged without a commit".

**2. The revert check — this is what makes the first read mean anything.** An auto-revert
adds a *new commit on top* of the branch; it does not reopen the PR or change its base. A
PR whose merge was reverted therefore still reports `MERGED` against the integration
branch, and a check that stops at read 1 would report reverted work as merged and let a
dependent branch from a base that no longer contains it. A merge counts only when
**neither** revert signal is present:

```bash
# a. a revert label on the PR (read from the `labels` field above; the merge gate's
#    defaults, both overridable in the repository's agent instructions)
#      merge-gate:reverted    — verification failed
#      merge-gate:unverified  — nothing verified it

# b. a revert of this merge commit in the branch's history — fetch first, or a stale
#    remote-tracking ref makes this half silently miss
git fetch origin
git log origin/integration/issue-<parent-number> --grep="This reverts commit <mergeCommit>" --oneline
```

Either signal present → **not merged** for the batch's purposes. Both are needed because
they fail differently: a label can be stripped by anyone with triage access, and the
history signal survives only while the branch keeps the revert commit. This is the same
pair the merge gate uses to build its own reverted-issue set — reuse it rather than
inventing a third rule.

## List the PRs on the Integration Branch

Used by [batch.md](batch.md) B3 to check that the merge gate's report **covers** every PR
on the branch, before the human queue is published. This checks coverage only — the reason
for each verdict comes from the report, never from re-deriving it here:

```bash
gh pr list --base integration/issue-<parent-number> --state all --limit 100 \
  --json number,title,state,isDraft,labels,baseRefName
```

`--limit` is a **cap**, not a page size (it defaults to 30). Compare the number of rows
returned against the limit you passed: equal means the list may have been truncated, so
re-read with a higher limit before concluding anything from it. A coverage check built on a
truncated list fails open — it under-reports the human queue.

## Re-derive a Batch's State (re-entry)

Used by [batch-reentry.md](batch-reentry.md) to rebuild a batch's state in a session that
has no memory of it. Every read here is read-only.

**1. Find the integration branch when its name cannot be computed** (batch-reentry.md R2).
`integration/issue-<parent-number>` is derivable from a parent-issue batch source;
`integration/<date>-<slug>`, used for a milestone, a label, or a manual list, is not — its
date is the day the first session ran. Enumerate instead, and match on the slug:

```bash
git fetch origin --prune
git ls-remote --heads origin 'refs/heads/integration/*'
```

`git ls-remote` returns the complete ref list in one response, so no pagination rule
applies to it. Corroborate a candidate by checking that read 2 returns PRs attributing to
this batch's issues; more than one surviving candidate is a stop, never a guess.

**2. Every PR based on the integration branch, in any state** — the primary artifact, and
the same result serves the recency check, the per-issue mapping, and the gate budget:

```bash
gh pr list --base <integration-branch> --state all --limit 200 \
  --json number,title,state,isDraft,baseRefName,headRefName,createdAt,mergeCommit,labels,body
```

`state` is `OPEN` / `MERGED` / `CLOSED`. `mergeCommit` is `null` while a PR is open and
carries `.oid` once it merged. `body` carries the Gate Results section, which is where a
resumed run reads each stage's remaining fix rounds — never a verdict it may act on
([batch-reentry.md](batch-reentry.md) R6). Apply the truncation rule of
[List the PRs on the Integration Branch](#list-the-prs-on-the-integration-branch) — a row
count equal to `--limit` means the read may be short, and a short read here fails **open**:
a hidden PR is one re-entry would re-implement.

`createdAt`, not `updatedAt`, is the recency field. `updatedAt` moves on any comment or
label change, including from the repository's own automated reviewers, so keying on it
would stop every unattended run in a repository with routine bot activity.

**3. The milestone PR** — the integration branch as the **head**, not the base:

```bash
gh pr list --head <integration-branch> --base <default-branch> --state all \
  --limit 200 --json number,state,isDraft,url,title,body
```

This read survives the branch's deletion: `--head` matched a PR whose head branch had
already been deleted when this was checked against this repository on 2026-08-07 (PR #120,
head `feat/115-integration-mode`, absent from `git ls-remote --heads origin`). That is what
lets a merged milestone be distinguished from a batch that never started, both of which
present as "the integration branch does not exist". `body` carries the
`## Needs Human Attention` section, where the merge gate records an escalation that has to
outlive the session it was reported to.

**4. Remote branches an earlier session pushed** — including per-issue branches that never
became a PR:

```bash
git ls-remote --heads origin
```

Match the batch's branch naming (`<type>/<issue-number>-…`) against read 2: a branch with
no PR is an orphan ([batch-reentry.md](batch-reentry.md) R7), never a base to build on.

**5. Timestamps for the recency check** ([batch-reentry.md](batch-reentry.md) R3). GitHub
returns `createdAt` as ISO-8601 UTC with a `Z` suffix, and such timestamps compare
lexicographically without conversion. `git log --format=%cI` does **not** — it carries the
local offset (`2026-08-07T15:21:25+09:00`), which sorts wrongly against a `Z` string.
Normalize the integration branch's head and the per-issue branch heads into that shape:

```bash
git fetch origin --prune

# the integration branch's head time
TZ=UTC0 git log -1 --format=%cd --date=format-local:%Y-%m-%dT%H:%M:%SZ \
  origin/<integration-branch>

# every remote branch head time in one pass — ref name and time together
TZ=UTC0 git for-each-ref \
  --format='%(refname:short) %(committerdate:format-local:%Y-%m-%dT%H:%M:%SZ)' \
  'refs/remotes/origin/*'

# now, for the comparison
date -u +%Y-%m-%dT%H:%M:%SZ
```

`git ls-remote` returns SHAs rather than times, which is why the per-branch times come from
`for-each-ref` over freshly fetched remote-tracking refs. Filter its output down to the
branches matching this batch's per-issue naming, over the issue set R1 established.

## Monitor CI

```bash
gh pr checks --watch
```

Exits 0 if all checks pass, non-zero if any fail.

## Comment on Issue

```bash
gh issue comment <number> --body "<comment>"
```

## Update Issue State

```bash
gh issue close <number>
gh issue reopen <number>
```

## Agent Instructions Config Example

Add to the project's agent instructions (e.g. CLAUDE.md, AGENTS.md):

```markdown
## Issue Tracker
- platform: github
```
