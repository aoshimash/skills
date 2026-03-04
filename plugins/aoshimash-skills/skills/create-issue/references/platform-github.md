# GitHub

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)

## Create Issue

```bash
gh issue create --title "<title>" --body "<body>" [--label "<label>"] [--assignee "<user>"]
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: github
```

No additional config needed. `gh` CLI auto-detects the repo from git remote.
