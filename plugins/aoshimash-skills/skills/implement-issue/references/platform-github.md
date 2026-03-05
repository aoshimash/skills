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

To get structured JSON:
```bash
gh issue view <number> --json title,body,labels,assignees,state
```

## Create Branch

```bash
git checkout main && git pull
git checkout -b <branch-name>
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
