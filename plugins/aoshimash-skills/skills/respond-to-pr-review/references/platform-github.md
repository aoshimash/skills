# GitHub CLI / API Commands for PR Review Comments

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)

## Detect Platform

Check in order:
1. CLAUDE.md `## Code Hosting` section with `platform: github`
2. Git remote URL contains `github.com`

## Fetch PR Info

```bash
# Get PR number and title for current branch
gh pr view --json number,title,url

# Get owner and repo
gh repo view --json owner,name
```

## Fetch Comments

### Inline code review comments (attached to lines)

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[] | {id, path, line, body, user: .user.login, user_type: .user.type, in_reply_to_id, created_at}'
```

Only process root comments: filter out entries where `in_reply_to_id` is not null.

### Review body comments (submitted with APPROVE/REQUEST_CHANGES/COMMENT)

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --jq '.[] | {id, state, body, user: .user.login, user_type: .user.type}'
```

Skip entries where `body` is empty or whitespace-only.

The `state` field maps to criticality. Note: the API returns `CHANGES_REQUESTED` as the state value, which corresponds to `REQUEST_CHANGES` (the term used throughout this skill):
- `CHANGES_REQUESTED` (= REQUEST_CHANGES) → associated comments are `critical`
- `APPROVED`, `COMMENTED` → `normal` unless multi-reviewer

### General PR comments (conversation thread)

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --jq '.[] | {id, body, user: .user.login, user_type: .user.type}'
```

## Check if an Inline Comment is Outdated

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id} \
  --jq '.position'
```

If `position` is `null`, the comment is outdated (the line was changed or removed).

## Bot Detection

Check `user.type` in the API response:
- `"Bot"` → Bot
- `"User"` → Human

## Post Replies

### Reply to an inline code review comment

```bash
gh api --method POST \
  repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  --field body="YOUR REPLY TEXT"
```

### Reply to a review body comment or general PR comment

Post a new general comment (no native reply-to for these types):

```bash
gh api --method POST \
  repos/{owner}/{repo}/issues/{pr_number}/comments \
  --field body="YOUR REPLY TEXT"
```

To quote the original:

```bash
gh api --method POST \
  repos/{owner}/{repo}/issues/{pr_number}/comments \
  --field body="> @username wrote: [original snippet]

YOUR REPLY TEXT"
```

## Resolve a Thread (optional)

Requires the GraphQL API.

Get the thread ID:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes { id, isResolved, comments(first: 1) { nodes { databaseId } } }
        }
      }
    }
  }
' -f owner={owner} -f repo={repo} -F pr={pr_number}
```

Resolve:

```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { id, isResolved }
    }
  }
' -f threadId={thread_node_id}
```

## Get Commit URL for a Reply

```bash
git log --oneline -1
# → abc1234 commit message
# URL: https://github.com/{owner}/{repo}/commit/abc1234
```

## CLAUDE.md Config Example

```markdown
## Code Hosting
- platform: github
```
