---
name: respond-to-pr-review
description: >
  Process PR review comments one by one — explain each comment, confirm the
  response with the user, implement changes, and post reply comments to close
  the loop. Groups similar/duplicate comments from multiple reviewers or bots.
  Use when the user says "PRコメントに対応して", "レビューコメントに返信して",
  "respond to PR review", "handle PR comments", "PRレビュー対応",
  "review comments に答えて", "PRのレビューに返答", or wants to systematically
  work through review feedback on a pull request. Invoke this skill even if the
  user just says "PRコメント対応" without further detail.
---

# Respond to PR Review

Process PR review comments interactively: explain each one, confirm what to do,
implement changes, and close the loop with reply comments.

## Core Principles

1. **One group at a time** — Explain and confirm each comment group before moving on.
2. **Group by content** — Multiple reviewers or bots pointing out the same issue = one item.
3. **No silent ignores** — Every comment that requests a change or asks a question
   must receive a reply. Pure FYI/praise with no action implied can be skipped.
4. **Reply after all actions** — Draft all replies, get user approval as a batch, then post.
5. **Scope guard** — Only implement what a specific comment requests.
6. **Match the comment's language** — Reply in the same language as the comment.
   Japanese comment → Japanese reply. English comment → English reply.
   If a group contains both languages, use the language of the majority.

## Workflow

### Phase 0: Identify the PR

1. Run `gh pr view --json number,title,url` on the current branch.
2. If no PR is found, ask the user for a PR number or URL.
3. Extract `{owner}` and `{repo}` via `gh repo view --json owner,name`.
4. Confirm: "Working on PR #N: [title]"

### Phase 1: Fetch and Classify Comments

Fetch all three comment types (see [references/platform-github.md](references/platform-github.md)):

- **Inline code review comments** — attached to specific lines
- **Review body comments** — top-level text submitted with APPROVE / REQUEST_CHANGES / COMMENT reviews
- **General PR comments** — the conversation thread on the PR

**Filter out comments that don't need a response:**
- Outdated inline comments (the line they pointed at no longer exists)
- Existing reply comments (only process root comments / thread starters)
- Bot comments that are purely informational with no actionable content
  (e.g., CI summaries, coverage badges, auto-generated changelogs)
- Pure praise with no question or suggestion ("LGTM!", "👍", "Looks good!")

Use judgment: a question, a suggestion, a potential issue, or a nitpick all need a response.

**Identify the comment source:**
Check `user.type` in the API response — `"Bot"` vs `"User"`. This affects reply tone later.

### Phase 2: Group Similar Comments

Group comments that point out the same underlying issue, even if they come from
different reviewers, different bots, or different lines in the code.

For each group, record:
- All comment bodies and their API URLs / IDs
- Reviewers involved (names + human or bot)
- File(s) and line(s) if inline
- Whether any reviewer submitted a REQUEST_CHANGES review

### Phase 3: Interactive Decision Loop

Work through each group one at a time:

**Step 1 — Show the comment**

```
[Group N/M] @reviewer1, @bot-name
File: src/foo.ts:42
> "This function has O(n²) complexity. Consider using a Map for lookups."
```

If inline, show the relevant code snippet for context.

**Step 2 — Explain the comment**

Describe what the reviewer is pointing out, why it might matter, and what the
current code does. Keep it short — 2–3 sentences.

**Step 3 — Ask for a decision** via `AskUserQuestion`:

- **Implement** — address the feedback in this PR
- **Reject** — decline with an explanation (ask for the reason when this is chosen)
- **Create Issue** — valid point but out of scope for this PR; track separately
- **Skip reply** — genuinely no action expected (offer only when clearly appropriate)

Collect all decisions before moving to Phase 4.

### Phase 4: Implement Changes

For each "Implement" decision:

1. Make the code changes.
2. Run project checks (formatter, linter, tests) until clean.
3. Commit referencing the context (e.g., `fix: address review comment on foo.ts:42`).
4. Record the commit SHA for use in the reply.

### Phase 5: Create Issues

For each "Create Issue" decision, use the `create-issue` skill (or `gh issue create`)
with:
- A title derived from the comment's point
- A body that links back to the PR comment for context

Record the created issue URL for the reply.

### Phase 6: Draft and Post Replies

Draft a reply for every comment group that requires a response.

**Tone by reviewer type:**

| | Human | Bot |
|---|---|---|
| Opening | Brief thanks ("Thanks for catching that", "Good catch") | None |
| Formality | Casual but professional — no business-speak | Factual only |

**Reply content by decision:**

| Decision | Human example | Bot example |
|---|---|---|
| Implement | "Thanks for the suggestion! Fixed in [abc1234] — [brief description]." | "Fixed in [abc1234]: [brief description]." |
| Reject | "Thanks for the note. Keeping the current approach because [reason]." | "Keeping current approach: [reason]." |
| Create Issue | "Good point — this is outside the scope of this PR. Created #N to track it." | "Out of scope for this PR. Tracked in #N." |

Show all reply drafts together as a batch. Use `AskUserQuestion` to ask:
- Approve all and post
- Edit specific replies (user says which, then redraft)
- Cancel

After approval, post each reply. See [references/platform-github.md](references/platform-github.md)
for the exact API commands.

## Edge Cases

- **No actionable comments**: Inform the user and exit gracefully.
- **Dirty working tree**: Stash or commit existing changes before implementing.
- **A comment is ambiguous** (can't tell if action is expected): Show it to the user
  and ask whether to include it.

## References

- [references/platform-github.md](references/platform-github.md) — GitHub CLI/API commands for fetching and replying to PR comments
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
