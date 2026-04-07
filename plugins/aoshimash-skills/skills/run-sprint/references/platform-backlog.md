# Backlog Platform Guide

## Prerequisites

- `bee` CLI (`@nulab/bee`) installed and authenticated (`bee auth login`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: backlog`
2. Ask the user

## Read Issue

```bash
bee issue view <issue_key>
```

With JSON output:
```bash
bee issue view <issue_key> --json
```

## List Child Issues of Parent

```bash
bee issue list -p <project_key> --parent <parent_issue_key>
```

## List Issues by Milestone

```bash
bee issue list -p <project_key> --milestone <milestone_id>
```

## Check Dependencies

Backlog does not have built-in blocking relationships. Parse the issue body for:
- `Blocked by: PROJ-123`
- `Depends on: PROJ-456`

## Create Branch and Worktree

```bash
git fetch origin
git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
```

## Push Branch

```bash
git push -u origin <branch-name>
```

## Create Pull Request

Backlog PRs are created through the code hosting platform (GitHub/GitLab), not through Backlog itself. Detect the code hosting platform from the git remote URL and use the appropriate CLI.

## Update Issue Status

```bash
bee issue update <issue_key> --status <status_id>
```

Common status IDs vary by project. Fetch available statuses:
```bash
bee status list -p <project_key>
```

## Comment on Issue

```bash
bee issue comment <issue_key> -c "<comment>"
```

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: backlog
- base_url: https://<space>.backlog.com
- project_id: PROJECT_KEY
```

## Notes

- Backlog uses project keys (e.g., `PROJ-123`) as issue identifiers.
- The code hosting platform may differ from the issue tracker (e.g., Backlog for issues + GitHub for PRs).
- Use `--json` flag for structured output.
