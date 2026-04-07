# GitLab Platform Guide

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: gitlab`
2. Git remote URL contains `gitlab.com` or a known GitLab instance

## Read Issue

```bash
glab issue view <number>
```

Structured JSON:
```bash
glab issue view <number> --output json
```

## List Issues by Milestone

```bash
glab issue list --milestone "<milestone>" --output json
```

## List Issues by Label

```bash
glab issue list --label "<label>" --output json
```

## Check Dependency Links

Check related issues and blocking relationships:
```bash
glab api "projects/:id/issues/<iid>/links"
```

Also parse the issue body for `Blocked by: #N` patterns.

## Create Branch and Worktree

```bash
git fetch origin
git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
```

## Push Branch

```bash
git push -u origin <branch-name>
```

## Create Merge Request

```bash
glab mr create --title "<title>" --description "$(cat <<'EOF'
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

## Monitor CI

```bash
glab mr checks
```

## Comment on Issue

```bash
glab issue note <number> --message "<comment>"
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: gitlab
```
