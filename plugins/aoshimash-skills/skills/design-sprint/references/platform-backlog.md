# Backlog

## Prerequisites

- `bee` CLI (`@nulab/bee`) installed and authenticated (`bee auth login`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: backlog`
2. Ask the user

## Create Issue

Before creating, fetch available issue types:

```bash
bee issue-type list <project_key>
```

Then create the issue:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority>
```

Priority: `high`, `normal`, `low`.

Optional flags:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority> \
  --category <category_id> \
  -a <assignee_id>
```

## Create Child Issue (Parent-Child)

Backlog natively supports parent issues. Set the parent when creating:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority> \
  --parent <parent_issue_key>
```

Or update an existing issue to set its parent:

```bash
bee issue update <issue_key> --parent <parent_issue_key>
```

## Add Dependency Between Issues

Backlog does not have built-in dependency/blocking relationships. Use these alternatives:

1. **Mention in issue body**: Include `Blocked by: PROJ-123` in the issue description.
2. **Use milestones**: Group related issues under a milestone for ordering.

## List Issues

```bash
bee issue list -p <project_key> [--status <status_id>]
```

To list child issues of a parent:
```bash
bee issue list -p <project_key> --parent <parent_issue_key>
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
- Use `--json` flag on any command for structured JSON output.
