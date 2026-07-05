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

To let the user select an issue when no identifier is provided (Single mode, Phase 0):

```bash
bee issue list -p <project_key> -S <open_status_id> -L 20
```

Fetch available statuses first:
```bash
bee status list <project_key>
```

Present the list to the user and ask them to select one.

## List Child Issues of a Parent

Used in Phase 0 (Setup and Mode Selection) to check whether a single referenced issue is a parent with open children, and in Batch mode to collect a parent's sub-issues as the source set:

```bash
bee issue list -p <project_key> --parent <parent_issue_key>
```

## List Issues by Milestone

Used in Batch mode (Phase 0 source selection):

```bash
bee issue list -p <project_key> --milestone <milestone_id>
```

## Check Dependencies

Backlog does not have built-in blocking relationships. Parse the issue body for:
- `Blocked by: PROJ-123`
- `Depends on: PROJ-456`

## Create Branch and Worktree

**New branch or current-branch flows (Single mode):**

```bash
git fetch origin
git checkout <default-branch> && git pull
git checkout -b <branch-name>
```

**Worktree flow (Single mode default, and always in Batch mode):**

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
