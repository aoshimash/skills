---
name: respond-to-pr-review
description: >
  Process PR/MR review comments one by one — explain each comment, confirm the
  response with the user, implement changes, verify fixes match reviewer intent,
  and post reply comments to close the loop. Groups similar/duplicate comments
  from multiple reviewers or bots. Supports GitHub and GitLab.
  Use when the user says "PRコメントに対応して", "レビューコメントに返信して",
  "respond to PR review", "handle PR comments", "PRレビュー対応",
  "review comments に答えて", "PRのレビューに返答", "MRのレビューに対応",
  or wants to systematically work through review feedback on a pull request
  or merge request. Invoke this skill even if the user just says "PRコメント対応"
  without further detail.
---

# Respond to PR Review

Process PR/MR review comments interactively: explain each one, confirm what to do, implement changes, verify fixes match intent, and close the loop with reply comments.

## Core Principles

1. **One group at a time** — Explain and confirm each comment group before moving on.
2. **Group by content** — Multiple reviewers or bots pointing out the same issue = one item.
3. **No silent ignores** — Every comment that requests a change or asks a question must receive a reply.
4. **Verify before reply** — Verify that implemented changes match the reviewer's intent before drafting replies.
5. **Reply after all actions** — Draft all replies, get user approval as a batch, then post.
6. **Scope guard** — Only implement what a specific comment requests.
7. **Match the comment's language** — Reply in the same language as the comment. Japanese comment → Japanese reply. English comment → English reply. Mixed group → majority language.

## Workflow

### Phase 0: Identify the PR

1. Detect platform:
   - Check CLAUDE.md for `## Code Hosting` config
   - If not configured, detect from `git remote -v`: `github.com` → GitHub, `gitlab.com` → GitLab
   - If ambiguous, ask user via `AskUserQuestion`
2. Load platform guide: [references/platform-github.md](references/platform-github.md) or [references/platform-gitlab.md](references/platform-gitlab.md)
3. Get PR/MR info for current branch
4. If no PR/MR found, ask user for number or URL
5. **Hard Gate:** "Working on PR #N: [title]" → Confirm / Change

### Phase 1: Fetch and Classify Comments

See [references/workflow.md](references/workflow.md) for detailed procedure.

**Summary:** Fetch all comment types (inline, review body, general). Filter out outdated, replies, informational bots, and pure praise. Identify each comment as Human or Bot.

### Phase 2: Group Similar Comments

See [references/workflow.md](references/workflow.md) for detailed procedure.

**Summary:** Group comments pointing out the same issue across reviewers/bots/lines. Record metadata (bodies, IDs, reviewers, files). Tag criticality: `critical` (REQUEST_CHANGES or 2+ reviewers) vs `normal`. Tag comment type: `rule-violation-instance` (pattern applies to multiple locations) vs `one-off-bug` (specific defect).

### Phase 3: Interactive Decision Loop

See [references/workflow.md](references/workflow.md) for detailed procedure.

**Summary:** For each group: show comment, explain it, ask for decision via `AskUserQuestion`.

**Hard Gate** per group — options:
- **Implement** — address the feedback
- **Reject** — decline with explanation
- **Create Issue** — valid but out of scope
- **Skip reply** — no action expected

### Phase 4: Implement Changes

For each "Implement" decision:

1. Make the code changes
2. Run project checks (formatter, linter, tests) until clean
3. Commit referencing the context (e.g., `fix: address review comment on foo.ts:42`)
4. Record the commit SHA for use in replies

### Phase 4.5: Pattern Broadening

See [references/workflow.md](references/workflow.md) for detailed procedure.

**Summary:** For each `rule-violation-instance` group just implemented, search the changed files for other instances of the same pattern. Present found instances to the user via `AskUserQuestion` (Apply all / Skip / Pick subset). Apply selected fixes in the same commit, or create a new commit if the previous commit is already pushed.

### Phase 5: Verification Gate

See [references/verification.md](references/verification.md) for detailed procedure.

**Summary:** Verify that Phase 4 (and 4.5) changes match the reviewer's intent.

- `critical` groups → subagent verification (3 criteria: Intent Match, Scope Guard, Side Effect)
- `normal` groups → self-review using the same 3 criteria
- For `rule-violation-instance` groups, same-pattern expansion from Phase 4.5 is considered in-scope for the Scope Guard criterion.
- NEEDS_FIX → fix loop (max 2 rounds)
- UNCERTAIN → present to user for decision
- Still failing → DONE_WITH_CONCERNS (caveat added to reply)

**Hard Gate (conditional):** If any DONE_WITH_CONCERNS → present to user: Proceed / Re-implement / Abort

### Phase 6: Create Issues

For each "Create Issue" decision:
- Create issue with title derived from the comment
- Body links back to the PR/MR comment
- Record issue URL for the reply

### Phase 7: Draft and Post Replies

Draft a reply for every group that requires a response.

**Tone by reviewer type:**

| | Human | Bot |
|---|---|---|
| Opening | Brief thanks | None |
| Formality | Casual but professional | Factual only |

**Reply content by decision:**

| Decision | Human | Bot |
|---|---|---|
| Implement | "Thanks! Fixed in [SHA] — [description]." | "Fixed in [SHA]: [description]." |
| Implement (broadened) | "Thanks! Fixed in [SHA] — applied to [original location] + [N] other instances of the same pattern." | "Fixed in [SHA]: applied to [original location] + [N] other instances of the same pattern." |
| Implement (WITH_CONCERNS) | "Thanks! Fixed in [SHA] — [description]. Please verify this matches your intent." | "Fixed in [SHA]: [description]. Verification requested." |
| Reject | "Thanks for the note. Keeping current approach because [reason]." | "Keeping current approach: [reason]." |
| Create Issue | "Good point — outside scope. Created #N to track it." | "Out of scope. Tracked in #N." |

**Hard Gate:** Show all drafts as batch → Approve all / Edit specific / Cancel. After approval, post via platform API.

## Edge Cases

- **No actionable comments**: Inform the user and exit gracefully.
- **Dirty working tree**: Stash or commit existing changes before implementing.
- **Ambiguous comment**: Show to user and ask whether to include.
- **All verifications pass**: Skip the conditional Hard Gate in Phase 5.

## References

- [references/workflow.md](references/workflow.md) — Phase 1-3 detailed procedures
- [references/verification.md](references/verification.md) — Phase 5 Verification Gate procedure
- [references/platform-github.md](references/platform-github.md) — GitHub CLI/API commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI/API commands
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
