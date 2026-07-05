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

`gh issue create` prints the issue URL to stdout. To capture the issue number for later use (e.g., linking sub-issues):

```bash
number=$(gh issue create --title "<title>" --body "<body>" | grep -oE '[0-9]+$')
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
gh api repos/{owner}/{repo}/issues/<parent-number>/sub_issues --jq '.[] | {number, title, state}'
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: github
```

No additional config needed. `gh` CLI auto-detects the repo from git remote.
