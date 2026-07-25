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
bee issue-type list -p <project_key>
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

## Create Child Issue (Parent-Child)

Backlog natively supports parent issues. Set the parent when creating:

```bash
bee issue create -p <project_key> -t "<title>" -d "<body>" -T <issue_type_id> -P <priority> \
  --parent-issue <parent_issue_id>
```

Or edit an existing issue to set its parent:

```bash
bee issue edit <issue_key> --parent-issue <parent_issue_id>
```

`--parent-issue` takes the numeric issue ID, not the issue key.

This also applies to grandchild issues — set `--parent-issue <child_issue_id>` when creating a grandchild.

## Add Dependency Between Issues

Backlog does not have built-in dependency/blocking relationships. Use these alternatives:

1. **Mention in issue body**: Include `Blocked by: PROJ-123` in the issue description.
2. **Use milestones**: Group related issues under a milestone for ordering.

## List Issues

```bash
bee issue list -p <project_key> [-S <status_id>]
```

To list child issues of a parent:
```bash
bee issue list -p <project_key> --parent-issue <parent_issue_id>
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
- Use the `--json` flag on any command for structured JSON output. It optionally takes a comma-separated list of field names to filter by.
