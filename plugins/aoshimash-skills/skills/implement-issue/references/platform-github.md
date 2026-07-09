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

## Detect Sub-Issues of a Parent

Used in Phase 0 (Setup and Mode Selection) to check whether a single referenced issue is a parent with open sub-issues:

```bash
gh api repos/{owner}/{repo}/issues/<number>/sub_issues --jq '.[] | {number, title, state}'
```

If the sub-issues API is unavailable (older `gh` version, feature not enabled, or the endpoint 404s), fall back to parsing the parent issue's body for a task list or `#N` references:

```bash
gh issue view <number> --json body --jq '.body'
```

## List Sub-Issues / Issues by Milestone / Issues by Label

Used in Batch mode (Phase 0 source selection and Phase B1 dependency parsing):

```bash
# Sub-issues of a parent (preferred — see above)
gh api repos/{owner}/{repo}/issues/<parent-number>/sub_issues --jq '.[] | {number, title, state}'

# By milestone
gh issue list --milestone "<milestone>" --state open --json number,title,body,labels,state

# By label
gh issue list --label "<label>" --state open --json number,title,body,labels,state
```

## Check Dependency Links

GitHub sub-issue blocked-by relationships:
```bash
gh issue view <number> --json body
```

Parse the body for `Blocked by: #N` patterns. Also check platform-level sub-issue blocking if available.

## Create Branch

**New branch or current-branch flows (Single mode):**

```bash
git checkout main && git pull
git checkout -b <branch-name>
```

**Worktree flow (Single mode default, and always in Batch mode):**

```bash
git fetch origin
grep -qxF '.worktrees/' .git/info/exclude 2>/dev/null || echo '.worktrees/' >> .git/info/exclude
git worktree add .worktrees/<branch-name> -b <branch-name> origin/<default-branch>
```

## Push Branch

```bash
git push -u origin <branch-name>
```

## Create Pull Request

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<bullets>

Closes #<issue-number>

## Changes
<file-level changes>

## Test Plan
<verification checklist>
EOF
)"
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
