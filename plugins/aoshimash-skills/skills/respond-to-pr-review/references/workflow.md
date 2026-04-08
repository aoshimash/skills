# Workflow: Fetch, Group, and Decide

Detailed procedures for Phases 1–3 of the respond-to-pr-review skill.

## Phase 1: Fetch and Classify Comments

### 1-1: Fetch all comment types

Fetch three categories of comments using the platform guide:

1. **Inline code review comments** — attached to specific lines in the diff
2. **Review body comments** — top-level text submitted with APPROVE / REQUEST_CHANGES / COMMENT reviews
3. **General PR/MR comments** — the conversation thread on the PR/MR

Refer to the loaded platform guide (`references/platform-github.md` or `references/platform-gitlab.md`) for the exact API commands.

### 1-2: Filter non-actionable comments

Remove comments that do not require a response:

| Filter | How to detect |
|---|---|
| Outdated inline comments | The line they pointed at no longer exists in the current diff. Check platform-specific outdated detection. |
| Existing replies | Only process root comments / thread starters. Filter by `in_reply_to_id` (GitHub) or thread structure (GitLab). |
| Informational bot comments | `user.type == "Bot"` (GitHub) or `author.bot == true` (GitLab) AND body contains no question, suggestion, or requested action. Examples: CI summaries, coverage badges, auto-generated changelogs. |
| Pure praise | Body matches patterns like "LGTM", "Looks good", "👍", "Great work" with no question or suggestion attached. |

Use judgment: a question, a suggestion, a potential issue, or a nitpick all need a response.

### 1-3: Identify comment source

For each remaining comment, record:
- **Author**: username
- **Type**: Human or Bot (check `user.type` / `author.bot`)
- **Review state**: If the comment is part of a review, record APPROVE / REQUEST_CHANGES / COMMENT
- **Location**: file path + line (if inline), or "general"

## Phase 2: Group Similar Comments

### 2-1: Group by underlying issue

Group comments that point out the same underlying issue, even if they come from different reviewers, different bots, or different lines in the code.

Grouping heuristics:
- Same file + same concern (e.g., two reviewers both noting a naming issue on the same variable)
- Same conceptual issue across files (e.g., "missing error handling" flagged in three different functions)
- Bot and human flagging the same thing (e.g., linter warning + human comment about the same code)

When in doubt, keep as separate groups — over-grouping loses context.

### 2-2: Record group metadata

For each group, record:
- All comment bodies and their API IDs (needed for posting replies)
- Reviewers involved (names + Human or Bot)
- File(s) and line(s) if inline
- Whether any reviewer submitted a REQUEST_CHANGES review

### 2-3: Tag criticality

Assign a criticality tag to each group:

| Tag | Condition |
|---|---|
| `critical` | Associated with a REQUEST_CHANGES review, OR flagged by 2+ reviewers |
| `normal` | Everything else |

Criticality determines verification routing in Phase 5 (Verification Gate).

## Phase 3: Interactive Decision Loop

### 3-1: Present groups one at a time

For each group, show:

```
[Group N/M] @reviewer1, @reviewer2          [critical] or [normal]
File: src/foo.ts:42
> "The original comment body here."
```

If inline, also show the relevant code snippet (5–10 lines of surrounding context from the current file).

### 3-2: Explain the comment

Describe what the reviewer is pointing out, why it might matter, and what the current code does. Keep it short — 2–3 sentences.

### 3-3: Ask for a decision

**Hard Gate:** Use `AskUserQuestion` with options:

- **Implement** — address the feedback in this PR
- **Reject** — decline with an explanation (when chosen, ask the user for the reason)
- **Create Issue** — valid point but out of scope; track separately
- **Skip reply** — genuinely no action expected (offer only when clearly appropriate)

### 3-4: Collect all decisions

After processing all groups, summarize the decisions before proceeding:

```
Decisions summary:
- [critical] Group 1: Implement
- [normal]   Group 2: Reject
- [normal]   Group 3: Create Issue
```

Proceed to Phase 4 with "Implement" groups, Phase 6 with "Create Issue" groups.
