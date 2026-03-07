# Backlog

## Prerequisites

- Backlog MCP server configured and available (tool names may vary by MCP server implementation — check available tools with `mcp__backlog__*` prefix)

## Create Issue

Use the Backlog MCP tool to create an issue. Example:

```
mcp__backlog__create_issue(
  projectId: "<project_id>",
  summary: "<title>",
  description: "<body>",
  issueTypeId: <issue_type_id>,
  priorityId: <priority_id>,
  categoryId: [<category_id>]
)
```

Before creating, fetch available issue types and priorities from the project:

```
mcp__backlog__get_issue_types(projectId: "<project_id>")
mcp__backlog__get_priorities()
```

## Built-in Issue Types

Backlog projects typically have configurable issue types. Common defaults:

- Bug
- Feature (Task)
- Technical Task
- Operation (for operational/procedural tasks)

Always fetch the actual issue types from the project before creating an issue.

## Built-in Priority Levels

Backlog has built-in priority levels:

- High
- Normal
- Low

Ask the user to confirm the priority when creating an issue.

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
