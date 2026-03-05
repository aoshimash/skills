# GitLab Platform Guide

## Prerequisites

- `glab` CLI installed and authenticated

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: gitlab`
2. Git remote URL contains `gitlab.com` or a known GitLab instance

## Read Issue

```bash
glab issue view <number>
```

To get structured output:
```bash
glab issue view <number> --output json
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

## Link MR to Issue

Include `Closes #<number>` in the MR description to auto-close the issue on merge.
Use `Relates to #<number>` if the MR only partially addresses the issue.
