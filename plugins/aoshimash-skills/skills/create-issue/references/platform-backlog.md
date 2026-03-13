# Backlog

## Prerequisites

- `bee` CLI (`@nulab/bee`) installed and authenticated (`bee auth login`)

## Create Issue

Before creating, fetch available issue types from the project:

```bash
bee issue-type list <project_key>
```

Then create the issue:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority>
```

Priority accepts: `high`, `normal`, `low`.

Optional flags:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority> \
  --category <category_id> \
  -a <assignee_id>
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

- Backlog uses project keys (e.g., `PROJ-123`) as issue identifiers, not just numbers.
- Use `--json` flag on any command for structured JSON output.
