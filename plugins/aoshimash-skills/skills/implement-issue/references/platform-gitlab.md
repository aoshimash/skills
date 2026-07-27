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
glab issue view <number> --comments
```

## Write Back Design Decisions to the Issue

Used in workflow.md 1-3 to append batched-question answers to the issue's
`## Design Decisions` section (create the section if absent). Fetch the current
description (`glab issue view <number> --output json`), append the decisions,
then:

```bash
glab issue update <number> --description "<updated body>"
```

## Check for an MR Template

A repository template, when present, is the MR body skeleton (workflow.md 3-1).
Look for `.gitlab/merge_request_templates/` (the default template is usually
`Default.md`).

## Create Draft Merge Request

MRs are always created as drafts (workflow.md 3-1); the body sections come from
workflow.md 3-1 (or the repository's MR template when one exists):

```bash
glab mr create --draft --title "<title>" --description "<body>"
```

## Update MR Description (gate results)

```bash
glab mr update <number> --description "<updated body>"
```

## Mark MR Ready for Review

Only after both review-gate stages pass and CI is green (workflow.md 3-4):

```bash
glab mr update <number> --ready
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

## Reopen Issue

Used by Phase 0's closed-issue check ("Reopen and implement"):

```bash
glab issue reopen <number>
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: gitlab
```
