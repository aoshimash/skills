# GitHub

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: github`
2. Git remote URL contains `github.com`

## Create Issue

```bash
gh issue create --title "<title>" --body "<body>" [--label "<label>"] [--assignee "<user>"]
```

To get the issue number from the output:
```bash
gh issue create --title "<title>" --body "<body>" 2>&1 | grep -oP '#\K[0-9]+'
```

Or use JSON output:
```bash
gh issue create --title "<title>" --body "<body>" --json number --jq '.number'
```

## Add Sub-Issue to Parent

After creating a sub-issue, link it to the parent:

```bash
gh issue edit <parent-number> --add-sub-issue <sub-issue-number>
```

## Add Dependency Between Issues

Mark that one issue blocks another:

```bash
gh issue edit <blocked-issue-number> --add-sub-issue-blocked-by <blocking-issue-number>
```

Note: Dependency tracking via `blocked-by` is available when sub-issues are enabled in the repository.

If sub-issue commands are not available (older `gh` version or feature not enabled), fall back to mentioning dependencies in the issue body:

```markdown
Blocked by: #<issue-number>
```

## List Issues

```bash
gh issue list [--label "<label>"] [--milestone "<milestone>"] [--state open]
```

To list sub-issues of a parent:
```bash
gh issue view <parent-number> --json body
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: github
```

No additional config needed. `gh` CLI auto-detects the repo from git remote.
