# GitLab CLI / API Commands for MR Review Comments

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Code Hosting` section with `platform: gitlab`
2. Git remote URL contains `gitlab.com` or a known self-hosted GitLab instance

## Fetch MR Info

```bash
# Get MR number and title for current branch
glab mr view --output json
```

Extract: `iid` (MR number), `title`, `web_url`.

Get project ID (needed for API calls):

```bash
glab api "projects/:id" --jq '.id'
```

## Fetch Comments

GitLab uses a unified "notes" system for all comment types on MRs. Notes are differentiated by their properties.

### All MR notes

```bash
glab api "projects/:id/merge_requests/{mr_iid}/notes?sort=asc" \
  --jq '.[] | {id, body, author: .author.username, bot: .author.bot, type, system, resolvable, resolved, position}'
```

### Classify notes into comment types

| Type | Detection |
|---|---|
| Inline code review comment | `resolvable == true` AND `position` is not null |
| Review body comment | Part of a review submission. Check if the note was created alongside an approval/rejection action. Use the MR approvals API (see below). |
| General MR comment | `resolvable == false` AND `system == false` AND `position` is null |
| System note | `system == true` — always skip (merge status changes, label changes, etc.) |

### Check for REQUEST_CHANGES equivalent

GitLab uses approvals rather than review states. To check if a reviewer has requested changes:

```bash
glab api "projects/:id/merge_requests/{mr_iid}/approvals" \
  --jq '{approved_by: [.approved_by[].user.username], approvals_required: .approvals_required, approvals_left: .approvals_left}'
```

If a reviewer has NOT approved and has left resolvable comments → treat as equivalent to REQUEST_CHANGES for criticality tagging.

## Check if an Inline Comment is Outdated

Check if the position still maps to a valid diff location using the discussions API:

```bash
glab api "projects/:id/merge_requests/{mr_iid}/discussions" \
  --jq --arg nid "{note_id}" '.[] | select(.notes[0].id == ($nid | tonumber)) | .notes[0].position'
```

If `position` is null or references a line no longer in the current diff, the comment is outdated.

Note: `.resolved` on a note indicates whether the thread was manually resolved by a user, NOT whether the comment is outdated. Do not use `.resolved` for outdated detection.

## Bot Detection

Check `author.bot` in the note response:
- `true` → Bot
- `false` → Human

Fallback: if `author.bot` is not present, check if `author.username` matches known bot patterns (e.g., ends with `[bot]` or `_bot`).

## Post Replies

### Reply to an inline comment (discussion thread)

Find the discussion ID for the note:

```bash
glab api "projects/:id/merge_requests/{mr_iid}/discussions" \
  --jq --arg nid "{note_id}" '.[] | select(.notes[].id == ($nid | tonumber)) | .id'
```

Post a reply to the discussion:

```bash
glab api --method POST \
  "projects/:id/merge_requests/{mr_iid}/discussions/{discussion_id}/notes" \
  --field body="YOUR REPLY TEXT"
```

### Reply to a general MR comment

Post a new note on the MR:

```bash
glab api --method POST \
  "projects/:id/merge_requests/{mr_iid}/notes" \
  --field body="YOUR REPLY TEXT"
```

To quote the original:

```bash
glab api --method POST \
  "projects/:id/merge_requests/{mr_iid}/notes" \
  --field body="> @username wrote: [original snippet]

YOUR REPLY TEXT"
```

## Resolve a Thread

```bash
glab api --method PUT \
  "projects/:id/merge_requests/{mr_iid}/discussions/{discussion_id}" \
  --field resolved=true
```

## Get Commit URL for a Reply

```bash
git log --oneline -1
# → abc1234 commit message
```

Determine the GitLab instance URL from the remote:

```bash
git remote get-url origin
# → https://gitlab.com/owner/repo.git or git@gitlab.com:owner/repo.git
# URL: https://gitlab.com/{owner}/{repo}/-/commit/abc1234
```

## CLAUDE.md Config Example

```markdown
## Code Hosting
- platform: gitlab
```
