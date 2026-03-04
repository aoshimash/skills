# GitLab

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status`)

## Create Issue

```bash
glab issue create --title "<title>" --description "<body>" [--label "<label>"] [--assignee "<user>"]
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: gitlab
```

No additional config needed. `glab` CLI auto-detects the project from git remote.
