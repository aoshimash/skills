# GitHub CLI / API Commands for PR Review Comments

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
  --jq '.[] | {id, path, line, body, user: .user.login, user_type: .user.type, in_reply_to_id}'
```
Only process root comments: filter out entries where `in_reply_to_id` is not null.

### Review body comments (submitted with APPROVE/REQUEST_CHANGES/COMMENT)
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --jq '.[] | {id, state, body, user: .user.login, user_type: .user.type}'
```
Skip entries where `body` is empty or whitespace-only.

### General PR comments (conversation thread)
```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --jq '.[] | {id, body, user: .user.login, user_type: .user.type}'
```

## Check if an Inline Comment is Outdated

An inline comment is outdated when its original line no longer exists in the current diff.
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id} \
  --jq '.position'
```
If `position` is `null`, the comment is outdated (the line was changed).

## Post Replies

### Reply to an inline code review comment
```bash
gh api --method POST \
  repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  --field body="YOUR REPLY TEXT"
```

### Reply to a review body comment or general PR comment
There is no "reply" concept for these — post a new general comment instead:
```bash
gh api --method POST \
  repos/{owner}/{repo}/issues/{pr_number}/comments \
  --field body="YOUR REPLY TEXT"
```
To make it clear what you're replying to, you can quote the original:
```bash
gh api --method POST \
  repos/{owner}/{repo}/issues/{pr_number}/comments \
  --field body="> @username wrote: [original snippet]

YOUR REPLY TEXT"
```

## Resolve a Thread (mark as resolved)

Resolving inline comment threads requires the GraphQL API.

First, get the thread ID:
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

Then resolve:
```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { id, isResolved }
    }
  }
' -f threadId={thread_node_id}
```

Note: Resolving threads is optional. Replying to inline comments is usually sufficient.

## Get Commit URL for a Reply

```bash
git log --oneline -1
# → abc1234 commit message
# URL: https://github.com/{owner}/{repo}/commit/abc1234
```
