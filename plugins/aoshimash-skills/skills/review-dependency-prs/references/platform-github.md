# GitHub CLI / API Commands for Dependency PRs

GitHub-only for v1. All commands use the `gh` CLI; replace `{owner}`, `{repo}`, `{pr}` as needed.

## Table of Contents

- [Prerequisites](#prerequisites)
- [List and filter dependency-bot PRs](#list-and-filter-dependency-bot-prs)
- [Read a PR: diff, files, body, branch, labels](#read-a-pr-diff-files-body-branch-labels)
- [CI status (the merge gate)](#ci-status-the-merge-gate)
- [Merge (respect the repo merge method)](#merge-respect-the-repo-merge-method)
- [Resolve sibling / superseded PRs](#resolve-sibling--superseded-prs)
- [main divergence: update branch](#main-divergence-update-branch)
- [Comment on the PR](#comment-on-the-pr)
- [Read bot config](#read-bot-config)

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`).
- The current directory is the target repo, or pass `-R {owner}/{repo}`.

## List and filter dependency-bot PRs

List open PRs with the fields needed for composite detection (author, branch, labels):

```bash
gh pr list --state open --limit 100 \
  --json number,title,author,headRefName,labels,isDraft \
  --jq '.[] | {number, title, author: .author.login, isBot: .author.is_bot, branch: .headRefName, labels: [.labels[].name]}'
```

Filter directly by known bot authors (fast path for the common case):

```bash
gh pr list --state open --author "app/renovate" --json number,title,headRefName
gh pr list --state open --author "app/dependabot" --json number,title,headRefName
```

Filter by branch prefix or label when the author is a self-hosted/custom account
(combine with the OR-detection in detection.md):

```bash
gh pr list --state open --json number,title,headRefName,labels \
  --jq '.[] | select(.headRefName | startswith("renovate/") or startswith("dependabot/"))'

gh pr list --state open --label dependencies --json number,title
```

Read the PR body to check for bot signatures (Mend footer, `<!--renovate-debug-->`, Dependabot markers):

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

## CI status (the merge gate)

CI green is a precondition for merge (workflow.md 2-3). Read the rolled-up status:

```bash
# Human-readable checks summary
gh pr checks {pr}

# Programmatic rollup — every check must be SUCCESS (or neutral/skipped) to merge
gh pr view {pr} --json statusCheckRollup \
  --jq '.statusCheckRollup[] | {name: (.name // .context), status, conclusion}'
```

Decision:

- All checks `SUCCESS`/`NEUTRAL`/`SKIPPED` → CI gate passes.
- Any `FAILURE`/`TIMED_OUT`/`CANCELLED` → **do not merge**; investigate and present as a finding.
- `PENDING`/`IN_PROGRESS` → wait, then re-check.

## Approve before merge

Submit a GitHub review approval after user approval (step 2-5) and before calling `gh pr merge`. This satisfies branch-protection rules requiring at least one approved review:

```bash
gh pr review {pr} --approve --body "Dependency update reviewed: release notes read, CI green, risk assessed."
```

Notes:
- The `--body` is optional but leaves a human-readable audit trail on the PR.
- GitHub prevents approving your own PRs — for bot-authored PRs (Renovate, Dependabot) this is never an issue.
- If the repo requires CODEOWNERS or team-based required reviewers, an agent approval may not satisfy the requirement. Check `mergeStateStatus` after approving; if it still shows `BLOCKED`, surface the gap and ask the user to approve manually.

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
# Show whichever config files exist
gh api repos/{owner}/{repo}/contents/renovate.json5 -H "Accept: application/vnd.github.raw" 2>/dev/null
gh api repos/{owner}/{repo}/contents/.github/renovate.json -H "Accept: application/vnd.github.raw" 2>/dev/null
gh api repos/{owner}/{repo}/contents/.github/dependabot.yml -H "Accept: application/vnd.github.raw" 2>/dev/null
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
