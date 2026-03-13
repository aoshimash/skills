# Backlog Platform Guide

## Prerequisites

- `bee` CLI (`@nulab/bee`) installed and authenticated (`bee auth login`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: backlog`
2. Ask the user (Backlog cannot be inferred from git remote)

## Read Issue

```bash
bee issue view PROJ-123
```

To get structured JSON:
```bash
bee issue view PROJ-123 --json
```

## List Issues

To let the user select an issue when no identifier is provided:

```bash
bee issue list -p <project_key> -S <open_status_id> -L 20
```

Fetch available statuses first:
```bash
bee status list <project_key>
```

Present the list to the user and ask them to select one.

## Update Issue Status

Fetch available statuses:
```bash
bee status list <project_key>
```

Update the issue status (e.g., to "In Progress"):
```bash
bee issue edit PROJ-123 -S <in_progress_status_id>
```

## Add Comment

Post a comment on the issue (e.g., with PR link):
```bash
bee issue comment PROJ-123 -b "PR created: <pr_url>"
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: backlog
- base_url: https://<space>.backlog.com
- project_id: PROJECT_KEY
- category_id: 12345 (optional)
```

## Notes

- Backlog uses project keys (e.g., `PROJ-123`) as issue identifiers, not just numbers.
- Backlog is an issue tracker only — it does not host git repositories. Code hosting is always a separate platform (GitHub, GitLab, etc.), detected from the git remote URL.
- Use `--json` flag on any command for structured JSON output.
