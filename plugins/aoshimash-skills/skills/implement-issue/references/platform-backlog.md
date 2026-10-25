# Backlog Platform Guide

## Access Method

Resolved once per run as SKILL.md "Platform Access" describes: a connector for
Backlog when it covers every operation the run's mode uses, otherwise the CLI.
This choice covers the issue tracker only; the code host (GitHub) resolves on
its own.

- **CLI**: `bee` CLI (`@nulab/bee`) installed and authenticated (`bee auth login`).
- **Connector coverage**: each command below is the reference for its
  operation. A connector tool covers an operation only when its own description
  or schema shows it returns the same fields with the same completeness the
  command guarantees or performs the same write. When that cannot be confirmed,
  the operation is not covered.

## Detect Platform

Check in order:
1. The project's agent instructions (e.g. CLAUDE.md, AGENTS.md): an `## Issue Tracker` section with `platform: backlog`
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

To let the user select an issue when no identifier is provided (Phase 0 step 2):

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
bee issue list -p <project_key> --parent-issue <parent_issue_id>
```

`--parent-issue` takes the parent's numeric issue ID, not its issue key (`PROJ-123`) — read
the ID from `bee issue view <parent_issue_key> --json`.

## List Issues by Milestone

Used in Batch mode (Phase 0 source selection):

```bash
bee issue list -p <project_key> --milestone <milestone_id>
```

## Check Dependencies

Backlog does not have built-in blocking relationships. Parse the issue body for:
- `Blocked by: PROJ-123`
- `Depends on: PROJ-456`

## Read Issue Comments (research comment)

workflow.md 1-1 looks for a research comment attached by the create-issue
Design Flow. If the installed `bee` version does not expose issue comments,
skip the research comment and research fresh — do not guess at flags.

## Write Back Design Decisions to the Issue

Backlog write-backs (workflow.md 1-3) are recorded as an issue **comment**
rather than a description edit, using the verified comment command:

```bash
bee issue comment PROJ-123 -b "Design Decisions (added <date>): <decisions and rationale>"
```

## Create Branch and Worktree

**Worktree flow (the default in both modes):**

```bash
git fetch origin
grep -qxF '.worktrees/' .git/info/exclude 2>/dev/null || echo '.worktrees/' >> .git/info/exclude
git worktree add .worktrees/<branch-name> -b <branch-name> origin/<default-branch>
```

## Push Branch

```bash
git push -u origin <branch-name>
```

## Create Pull Request

PRs for Backlog issues are created on GitHub, not through Backlog itself. Use [platform-github.md](platform-github.md) — including its draft creation, automated-reviewer, ready-for-review flip, and PR-body read commands. Automated reviewers are a code-hosting concern; Backlog has no part in workflow.md 3-4. Nor in the repository-scoped promotion of workflow.md 3-7, whose PR is also on GitHub.

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

## Agent Instructions Config Example

Add to the project's agent instructions (e.g. CLAUDE.md, AGENTS.md):

```markdown
## Issue Tracker
- platform: backlog
- base_url: https://<space>.backlog.com
- project_id: PROJECT_KEY
- category_id: 12345 (optional)
```

## Notes

- Backlog uses project keys (e.g., `PROJ-123`) as issue identifiers, not just numbers.
- Backlog is used as an issue tracker only. Code and PRs are always on GitHub.
- Use `--json` flag on any command for structured JSON output.
