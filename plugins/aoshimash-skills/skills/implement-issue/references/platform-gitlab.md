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

## Detect Child Items of a Parent

Used in Phase 0 (Setup and Mode Selection) to check whether a single referenced issue is a parent with open children. GitLab Free has no native sub-issue API — check issue links and task lists:

```bash
glab api "projects/:id/issues/<iid>/links"
```

Also parse the issue body for a `## Tasks` task list (`- [ ] #N`) — this is how the create-issue skill's Design Flow represents children on GitLab.

## List Issues by Milestone / by Label

Used in Batch mode (Phase 0 source selection):

```bash
glab issue list --milestone "<milestone>" --output json
glab issue list --label "<label>" --output json
```

## Check Dependency Links

Check related issues and blocking relationships:
```bash
glab api "projects/:id/issues/<iid>/links"
```

Also parse the issue body for `Blocked by: #N` patterns.

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
