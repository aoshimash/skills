# GitLab

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status`)

## Detect Platform

Check in order:
1. The project's agent instructions (e.g. CLAUDE.md, AGENTS.md): an `## Issue Tracker` section with `platform: gitlab`
2. Git remote URL contains `gitlab.com` or a known GitLab instance

## Check for Issue Templates

Used in SKILL.md Step 1. GitLab stores project description templates in
`.gitlab/issue_templates/` (Markdown files, one per template):

```bash
ls .gitlab/issue_templates/ 2>/dev/null
```

Read the chosen template and fill it yourself, then pass the composed body via
`--description`. `glab issue create --template <name>` pre-populates the
description from that directory for interactive creation and is not used here.

## Create Issue

```bash
glab issue create --title "<title>" --description "<body>" [--label "<label>"] [--assignee "<user>"]
```

Set `--description "-"` only when an editor is wanted; this skill always
supplies the composed body directly.

## Create Child Issue (Epic/Parent Relationship)

GitLab supports parent-child relationships through Epics (Premium) or related issues (Free).

### Using task list in parent issue (Free tier)

Include sub-issues as task list items in the parent issue body:

```markdown
## Tasks

- [ ] #<sub-issue-number>
- [ ] #<sub-issue-number>
```

### Using related issues (Free tier)

```bash
glab api --method POST "projects/:id/issues/<issue-iid>/links" -f target_project_id=<project-id> -f target_issue_iid=<related-iid> -f link_type=blocks
```

Link types: `relates_to`, `blocks`, `is_blocked_by`

### Using Epics (Premium)

```bash
glab api --method POST "groups/:id/epics" -f title="<title>" -f description="<body>"
glab api --method POST "groups/:id/epics/<epic-id>/issues" -f issue_id=<issue-id>
```

## Add Dependency Between Issues

Use the related issues API with `blocks` / `is_blocked_by`:

```bash
# Issue A blocks Issue B
glab api --method POST "projects/:id/issues/<B-iid>/links" \
  -f target_project_id=<project-id> \
  -f target_issue_iid=<A-iid> \
  -f link_type=is_blocked_by
```

## List Issues

```bash
glab issue list [--label "<label>"] [--milestone "<milestone>"]
```

## Comment on an Issue (research comment)

Used in [issue-creation.md](issue-creation.md) step 7 to attach the Design
Flow's research findings to the parent issue:

```bash
glab issue note <issue-id> --message "<comment body>"
```

`glab issue note <issue-id>` with no message opens an editor instead. GitLab
renders HTML in comments, so the collapsed `<details>` form applies here.

## Agent-Instructions Config Example

```markdown
## Issue Tracker
- platform: gitlab
```

No additional config needed. `glab` CLI auto-detects the project from git remote.
