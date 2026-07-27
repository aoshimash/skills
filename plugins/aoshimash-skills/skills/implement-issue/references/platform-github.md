# GitHub Platform Guide

## Prerequisites

- `gh` CLI installed and authenticated

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: github`
2. Git remote URL contains `github.com`

## Read Issue

```bash
gh issue view <number>
```

Structured JSON:
```bash
gh issue view <number> --json title,body,labels,assignees,state
```

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

## Update PR Body (gate results)

```bash
gh pr edit <number> --body-file <body-file>
```

## Mark PR Ready for Review

Only after both review-gate stages pass and CI is green (workflow.md 3-4):

```bash
gh pr ready <number>
```

## Link PR to Issue

Include `Closes #<number>` in the PR body to auto-close the issue on merge.
Use `Relates to #<number>` if the PR only partially addresses the issue.

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

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: github
```
