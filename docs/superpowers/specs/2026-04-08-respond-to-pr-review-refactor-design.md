# Design: respond-to-pr-review Refactor

## Goal

Refactor the `respond-to-pr-review` skill to match the quality bar of `design-sprint` and `run-sprint`: modular reference files, multi-platform support (GitHub + GitLab), explicit Hard Gates, and a new Verification Gate that checks whether code changes actually match the reviewer's intent.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Verification timing | Verification Phase (Phase 5) after all implementations | Consistent with run-sprint's review-gates pattern; verification logic cleanly separable into references/verification.md |
| Verification method | Self-review + subagent for critical groups | Balances cost and accuracy; critical comments (REQUEST_CHANGES or multi-reviewer) get third-party verification, minor comments get self-review |
| Verification criteria | 3 criteria: Intent Match, Scope Guard, Side Effect | Minimal set that covers the most common failure modes |
| Platform support | GitHub + GitLab (no Backlog) | PR review is a code-hosting feature; Backlog's PR review is too limited (no REQUEST_CHANGES, no thread resolution) |
| Structure pattern | SKILL.md = summary, references/ = detail | Matches design-sprint and run-sprint conventions |
| Hard Gates | 4 explicit gates | Phase 0 (PR confirm), Phase 3 (per-group decision), Phase 5 (verification results), Phase 7 (reply batch approval) |

## File Structure

```
respond-to-pr-review/
├── SKILL.md                          # ~120 lines. Phase summaries + Core Principles
└── references/
    ├── workflow.md                    # Phase 1-3 detailed procedure (Fetch, Group, Decision Loop)
    ├── verification.md               # Phase 5 verification gate (NEW)
    ├── platform-github.md            # GitHub API commands (existing, expanded)
    ├── platform-gitlab.md            # GitLab API commands (NEW)
    └── eval-cases.md                 # Test cases (existing, expanded 4 → 8)
```

## Workflow Overview

```
Phase 0: Identify the PR (+ platform detection)
Phase 1: Fetch and Classify Comments
Phase 2: Group Similar Comments (+ criticality tagging)
Phase 3: Interactive Decision Loop
Phase 4: Implement Changes
Phase 5: Verification Gate              ← NEW
Phase 6: Create Issues
Phase 7: Draft and Post Replies
```

## Core Principles (7)

1. **One group at a time** — Explain and confirm each comment group before moving on.
2. **Group by content** — Multiple reviewers or bots pointing out the same issue = one item.
3. **No silent ignores** — Every comment requesting a change or asking a question must receive a reply.
4. **Verify before reply** — Verify that implemented changes match the reviewer's intent before drafting replies.
5. **Reply after all actions** — Draft all replies, get user approval as a batch, then post.
6. **Scope guard** — Only implement what a specific comment requests.
7. **Match the comment's language** — Reply in the same language as the comment.

## Phase 0: Identify the PR

1. Detect platform:
   - Check CLAUDE.md for `## Code Hosting` or `## Issue Tracker` config
   - If not configured, detect from `git remote -v`:
     - `github.com` → GitHub
     - `gitlab.com` or self-hosted GitLab patterns → GitLab
   - If ambiguous, ask user via `AskUserQuestion`
2. Load platform guide: `references/platform-github.md` or `references/platform-gitlab.md`
3. Get PR/MR info for current branch
4. If no PR/MR found, ask user for number or URL
5. **Hard Gate:** "Working on PR #N: [title]" → Confirm / Change

## Phase 1: Fetch and Classify Comments

See [references/workflow.md] for detailed procedure.

**Summary:**

Fetch all comment types (platform-specific):
- Inline code review comments (attached to specific lines)
- Review body comments (submitted with APPROVE / REQUEST_CHANGES / COMMENT)
- General PR/MR comments (conversation thread)

Filter out:
- Outdated inline comments (line no longer exists)
- Existing reply comments (only process root comments / thread starters)
- Bot comments that are purely informational (CI summaries, coverage badges)
- Pure praise with no question or suggestion

Identify comment source: Bot vs Human (affects reply tone).

## Phase 2: Group Similar Comments

See [references/workflow.md] for detailed procedure.

**Summary:**

Group comments pointing out the same underlying issue, even across reviewers/bots/lines.

For each group, record:
- All comment bodies and their API IDs
- Reviewers involved (names + human or bot)
- File(s) and line(s) if inline
- Whether any reviewer submitted a REQUEST_CHANGES review

**Criticality tagging (NEW):**
- `critical`: Associated with REQUEST_CHANGES review OR flagged by 2+ reviewers
- `normal`: Everything else

Criticality determines verification routing in Phase 5.

## Phase 3: Interactive Decision Loop

See [references/workflow.md] for detailed procedure.

**Summary:**

Work through each group one at a time:

1. Show the comment (with code snippet if inline)
2. Explain what the reviewer is pointing out (2-3 sentences)
3. **Hard Gate:** Ask for decision via `AskUserQuestion`:
   - Implement — address the feedback
   - Reject — decline with explanation (ask for reason)
   - Create Issue — valid but out of scope
   - Skip reply — no action expected

Collect all decisions before Phase 4.

## Phase 4: Implement Changes

For each "Implement" decision:

1. Make the code changes
2. Run project checks (formatter, linter, tests) until clean
3. Commit referencing the context (e.g., `fix: address review comment on foo.ts:42`)
4. Record the commit SHA for use in replies

## Phase 5: Verification Gate (NEW)

See [references/verification.md] for detailed procedure.

**Summary:**

Verify that Phase 4 changes match the reviewer's intent.

**5-1: Sort by criticality** (critical first)

**5-2: Critical groups** — subagent verification per group:
- Input: comment body, git diff (commit range), surrounding file context (30 lines)
- 3 criteria:
  1. **Intent Match** — Does the diff address what the comment asked for?
  2. **Scope Guard** — Does the diff contain changes NOT requested by the comment?
  3. **Side Effect** — Could the change break existing behavior?
- Output: PASS / NEEDS_FIX (with explanation) / UNCERTAIN (with reason)

**5-3: Normal groups** — self-review using the same 3 criteria as a checklist

**5-4: Handle UNCERTAIN** — Present the comment, diff, and subagent's reasoning to the user. User decides: treat as PASS, treat as NEEDS_FIX, or skip verification for this group.

**5-5: Fix loop** — NEEDS_FIX → re-implement → re-verify (max 2 rounds)

**5-6: Escalation** — Still NEEDS_FIX after 2 rounds → mark DONE_WITH_CONCERNS
- Add note to reply draft: "Modified, but please verify this matches your intent"

**Hard Gate (conditional):** If any group is DONE_WITH_CONCERNS, present verification results to user:
- Proceed (post replies with caveat notes)
- Re-implement (user provides guidance)
- Abort

## Phase 6: Create Issues

For each "Create Issue" decision:
- Create issue with title derived from the comment's point
- Body links back to the PR comment for context
- Record created issue URL for the reply

## Phase 7: Draft and Post Replies

Draft a reply for every comment group that requires a response.

**Tone by reviewer type:**

| | Human | Bot |
|---|---|---|
| Opening | Brief thanks | None |
| Formality | Casual but professional | Factual only |

**Reply content by decision:**

| Decision | Human example | Bot example |
|---|---|---|
| Implement | "Thanks for the suggestion! Fixed in [abc1234] — [brief description]." | "Fixed in [abc1234]: [brief description]." |
| Implement (WITH_CONCERNS) | "Thanks! Fixed in [abc1234] — [description]. Please verify this matches your intent." | "Fixed in [abc1234]: [description]. Verification requested." |
| Reject | "Thanks for the note. Keeping the current approach because [reason]." | "Keeping current approach: [reason]." |
| Create Issue | "Good point — outside scope for this PR. Created #N to track it." | "Out of scope. Tracked in #N." |

**Hard Gate:** Show all reply drafts as a batch via `AskUserQuestion`:
- Approve all and post
- Edit specific replies
- Cancel

After approval, post each reply using platform-specific API.

## Edge Cases

- **No actionable comments**: Inform the user and exit gracefully.
- **Dirty working tree**: Stash or commit existing changes before implementing.
- **Ambiguous comment**: Show to user and ask whether to include.
- **Platform detection fails**: Ask user explicitly.
- **All verifications pass**: Skip the conditional Hard Gate in Phase 5; proceed directly to Phase 6.

## Eval Cases (8)

| # | Scenario | Key verification |
|---|---|---|
| 1 | Mixed comments — implement + reject + create issue | Full workflow, tone by reviewer type |
| 2 | Out-of-scope valid suggestion | Create Issue flow, issue links back to comment |
| 3 | Purely informational — no reply needed | Filtering accuracy |
| 4 | No PR found | PR detection + user prompt |
| 5 | Verification Gate catches intent mismatch | Scope Guard detects extra changes → NEEDS_FIX → fix loop → PASS |
| 6 | DONE_WITH_CONCERNS flow | 2 fix rounds fail → caveat in reply → conditional Hard Gate |
| 7 | Critical vs normal verification routing | REQUEST_CHANGES → subagent; nitpick → self-review |
| 8 | GitLab MR review | MR notes fetch, reply posting, thread resolution |

## Platform Comparison

| Operation | GitHub | GitLab |
|---|---|---|
| PR/MR info | `gh pr view` | `glab mr view` |
| Inline comments | REST `pulls/{n}/comments` | REST `merge_requests/{n}/notes` |
| Review body | REST `pulls/{n}/reviews` | MR notes with `type: review` |
| General comments | REST `issues/{n}/comments` | MR notes |
| Post reply | `comments/{id}/replies` | POST note (reply) |
| Bot detection | `user.type == "Bot"` | `author.bot == true` |
| Resolve thread | GraphQL `resolveReviewThread` | PUT note `resolved: true` |
| REQUEST_CHANGES | `review.state` | MR approval rules |
