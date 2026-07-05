# GitLab

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Issue Tracker` section with `platform: gitlab`
2. Git remote URL contains `gitlab.com` or a known GitLab instance

## Create Issue

```bash
glab issue create --title "<title>" --description "<body>" [--label "<label>"] [--assignee "<user>"]
```

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

## CLAUDE.md Config Example

```markdown
## Issue Tracker
- platform: gitlab
```

No additional config needed. `glab` CLI auto-detects the project from git remote.
