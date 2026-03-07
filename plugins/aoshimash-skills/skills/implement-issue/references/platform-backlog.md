# Backlog Platform Guide

## Prerequisites

- Backlog MCP server configured and available (tool names may vary by MCP server implementation — check available tools with `mcp__backlog__*` prefix)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: backlog`
2. Ask the user (Backlog cannot be inferred from git remote)

## Read Issue

```
mcp__backlog__get_issue(issueIdOrKey: "PROJ-123")
```

## List Issues

To let the user select an issue when no identifier is provided:

```
mcp__backlog__get_issues(
  projectId: ["<project_id>"],
  statusId: [1, 2],
  count: 20
)
```

Present the list to the user and ask them to select one.

## Update Issue Status

Update the issue status to reflect progress (e.g., "In Progress"):

```
mcp__backlog__update_issue(
  issueIdOrKey: "PROJ-123",
  statusId: <in_progress_status_id>
)
```

Fetch available statuses first:

```
mcp__backlog__get_statuses(projectId: "<project_id>")
```

## Add Comment

Post a comment on the issue (e.g., with PR link):

```
mcp__backlog__add_comment(
  issueIdOrKey: "PROJ-123",
  content: "PR created: <pr_url>"
)
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

- Tool names depend on the MCP server implementation. The examples above use `mcp__backlog__*` as placeholders.
- Check available MCP tools to confirm the exact function names and parameters.
- Backlog uses project keys (e.g., `PROJ-123`) as issue identifiers, not just numbers.
- Backlog is an issue tracker only — it does not host git repositories. Code hosting is always a separate platform (GitHub, GitLab, etc.), detected from the git remote URL.
