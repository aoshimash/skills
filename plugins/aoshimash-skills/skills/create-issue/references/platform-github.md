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

Parent and dependency relationships can also be set at creation time, avoiding a
follow-up `gh issue edit`:

```bash
gh issue create --title "<title>" --body "<body>" --parent <parent-number> --blocked-by <blocking-number>
```

Both flags accept a comma-separated list of issue numbers or URLs.

## Add Sub-Issue to Parent

After creating a sub-issue, link it to the parent:

```bash
gh issue edit <parent-number> --add-sub-issue <sub-issue-number>
```

Equivalently, from the child's side: `gh issue edit <sub-issue-number> --parent <parent-number>`.

Counterparts: `--remove-sub-issue <number>`, `--remove-parent`.

## Add Dependency Between Issues

Mark that one issue blocks another:

```bash
gh issue edit <blocked-issue-number> --add-blocked-by <blocking-issue-number>
```

Counterparts: `--remove-blocked-by <number>`, `--add-blocking <number>`, `--remove-blocking <number>`.

Note: issue dependencies (`blocked by` / `blocking`) are a separate GitHub feature
from sub-issues — neither requires the other, and GitHub's docs describe no
repository setting to enable either. Dependencies went generally available in
August 2025; the `gh` flags above were added in `gh` v2.94.0. Up to 50 issues can
be linked per relationship type.

If the flags are rejected as unknown (older `gh` version), fall back to mentioning dependencies in the issue body:

```markdown
Blocked by: #<issue-number>
```

## List Issues

```bash
gh issue list [--label "<label>"] [--milestone "<milestone>"] [--state open]
```

To inspect an issue's hierarchy and dependency links:
```bash
gh issue view <number> --json number,parent,subIssues,blockedBy,blocking
```

Or via the REST API, to list sub-issues of a parent:
```bash
gh api repos/{owner}/{repo}/issues/<parent-number>/sub_issues --jq '.[] | {number, title, state}'
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: github
```

No additional config needed. `gh` CLI auto-detects the repo from git remote.
