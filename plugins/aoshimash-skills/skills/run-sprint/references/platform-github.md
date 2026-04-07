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

## List Sub-Issues of Parent

```bash
gh issue view <parent-number> --json body
```

Parse the body for sub-issue references, or use:
```bash
gh issue list --label "<sprint-label>" --state open --json number,title,body,labels,state
```

## List Issues by Milestone

```bash
gh issue list --milestone "<milestone>" --state open --json number,title,body,labels,state
```

## List Issues by Label

```bash
gh issue list --label "<label>" --state open --json number,title,body,labels,state
```

## Check Dependency Links

GitHub sub-issue blocked-by relationships:
```bash
gh issue view <number> --json body
```

Parse the body for `Blocked by: #N` patterns. Also check platform-level sub-issue blocking if available.

## Create Branch

```bash
git fetch origin
git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
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
