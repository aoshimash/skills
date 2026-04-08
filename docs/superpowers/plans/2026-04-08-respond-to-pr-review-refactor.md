# respond-to-pr-review Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the `respond-to-pr-review` skill to match the quality bar of `design-sprint` and `run-sprint` — modular reference files, GitHub + GitLab support, explicit Hard Gates, and a new Verification Gate.

**Architecture:** SKILL.md becomes a ~120-line summary of 8 phases (0-7). Detailed procedures live in `references/workflow.md` and `references/verification.md`. Platform-specific API commands live in `references/platform-github.md` and `references/platform-gitlab.md`. Eval cases expanded from 4 to 8.

**Tech Stack:** Markdown (SKILL.md + reference files), `gh` CLI (GitHub), `glab` CLI (GitLab)

**Design spec:** `docs/superpowers/specs/2026-04-08-respond-to-pr-review-refactor-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `plugins/aoshimash-skills/skills/respond-to-pr-review/SKILL.md` | Rewrite | Phase summaries, Core Principles, references links |
| `plugins/aoshimash-skills/skills/respond-to-pr-review/references/workflow.md` | Create | Phase 1-3 detailed procedures (Fetch, Group, Decision Loop) |
| `plugins/aoshimash-skills/skills/respond-to-pr-review/references/verification.md` | Create | Phase 5 Verification Gate procedure |
| `plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-github.md` | Rewrite | GitHub API commands (expand existing) |
| `plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-gitlab.md` | Create | GitLab API commands |
| `plugins/aoshimash-skills/skills/respond-to-pr-review/references/eval-cases.md` | Rewrite | 8 test cases with verification checklists |

---

### Task 1: Create references/workflow.md

Extract Phase 1-3 detailed procedures from the current SKILL.md into a dedicated reference file. Add criticality tagging to Phase 2.

**Files:**
- Create: `plugins/aoshimash-skills/skills/respond-to-pr-review/references/workflow.md`

- [ ] **Step 1: Create workflow.md with Phase 1 (Fetch and Classify)**

Write `references/workflow.md` with the following content. This covers the detailed fetch procedure, filtering rules, and comment source identification. The file uses platform-agnostic descriptions and defers API commands to the platform guides.

```markdown
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
```

- [ ] **Step 2: Review the file for completeness**

Read back `references/workflow.md` and verify:
- Phase 1 covers all three comment types + four filter rules + source identification
- Phase 2 covers grouping heuristics + metadata recording + criticality tagging
- Phase 3 covers presentation format + explanation + Hard Gate + decision collection
- No TBD/TODO/placeholders

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/references/workflow.md
git commit -m "feat: add references/workflow.md for respond-to-pr-review"
```

---

### Task 2: Create references/verification.md

The new Verification Gate (Phase 5). This is the core new feature — checking that code changes actually match the reviewer's intent.

**Files:**
- Create: `plugins/aoshimash-skills/skills/respond-to-pr-review/references/verification.md`

- [ ] **Step 1: Create verification.md**

```markdown
# Verification Gate

Detailed procedure for Phase 5 of the respond-to-pr-review skill. Verifies that implemented changes match the reviewer's intent before drafting replies.

## Purpose

Prevent replying "Fixed in abc1234" when the fix doesn't actually address the comment. Critical comments get third-party (subagent) verification; normal comments get self-review.

## Procedure

### 5-1: Sort by criticality

Process `critical` groups first, then `normal` groups. Within each tier, process in the order they were implemented.

### 5-2: Verify critical groups (subagent)

For each `critical` group with an "Implement" decision:

1. Collect the input:
   - **Comment body**: The original reviewer comment(s) in the group
   - **Diff**: `git diff <commit-before>..<commit-after>` for the commit(s) that addressed this group
   - **Context**: 30 lines before and after the changed area in each modified file

2. Dispatch a subagent with this prompt:

```
Review Comment: "{comment body}"
Reviewer: {reviewer name} ({Human/Bot})
File: {path}:{line}

Diff:
{git diff output}

Context (surrounding code):
{30 lines before and after the changed area}

Check these 3 criteria:

1. **Intent Match**: Does the diff address what the comment asked for?
   - PASS: The change directly addresses the reviewer's request
   - FAIL: The change is unrelated, partial, or misinterprets the request

2. **Scope Guard**: Does the diff contain changes NOT requested by the comment?
   - PASS: All changes are directly related to the comment
   - FAIL: The diff includes unrelated refactoring, formatting, or feature changes

3. **Side Effect**: Could the change break existing behavior?
   - PASS: The change is safe and localized
   - FAIL: The change modifies shared interfaces, removes functionality, or changes behavior beyond what was requested

Return one of:
- PASS — all 3 criteria pass
- NEEDS_FIX — at least one criterion fails (explain which and why)
- UNCERTAIN — cannot determine (explain why — e.g., insufficient context, ambiguous comment)
```

3. Record the subagent's verdict and reasoning.

### 5-3: Verify normal groups (self-review)

For each `normal` group with an "Implement" decision, run the same 3 criteria as a self-check:

- [ ] Intent Match: Does the diff address the comment?
- [ ] Scope Guard: No unrelated changes?
- [ ] Side Effect: No risk of breaking existing behavior?

If any criterion fails, mark as NEEDS_FIX with explanation.

### 5-4: Handle UNCERTAIN

When a subagent returns UNCERTAIN:

1. Present to the user:
   - The original comment
   - The diff
   - The subagent's reasoning for UNCERTAIN
2. Use `AskUserQuestion` with options:
   - Treat as PASS
   - Treat as NEEDS_FIX
   - Skip verification for this group

### 5-5: Fix loop

For each NEEDS_FIX result:

1. Show the failure explanation to the user (which criterion failed and why)
2. Re-implement the change to address the failure
3. Run project checks (formatter, linter, tests) until clean
4. Amend or create a new commit
5. Re-verify (subagent for critical, self-review for normal)

**Maximum 2 fix rounds.** If still NEEDS_FIX after round 2, proceed to 5-6.

### 5-6: Escalation (DONE_WITH_CONCERNS)

When a group remains NEEDS_FIX after 2 fix rounds:

1. Mark the group as DONE_WITH_CONCERNS
2. Modify the reply draft for this group:
   - Human reviewer: append "Please verify this matches your intent."
   - Bot: append "Verification requested."
3. Record the concern for the conditional Hard Gate

### 5-7: Conditional Hard Gate

**Only triggered if any group is DONE_WITH_CONCERNS.**

Present verification results to the user via `AskUserQuestion`:

```
Verification complete. N groups with concerns:

Group 2 [critical]: Intent Match failed — comment asked for rename,
  but implementation also changed logic. Fix attempts exhausted.

Options:
```

- **Proceed** — post replies with caveat notes as-is
- **Re-implement** — user provides specific guidance for the concerned groups
- **Abort** — stop without posting replies

If "Re-implement": apply user guidance, re-verify once more (no round limit for user-guided fixes), then return to this gate.

## Verification Criteria Reference

| Criterion | Checks | Common failures |
|---|---|---|
| Intent Match | Change addresses the reviewer's request | Partial fix, misinterpreted request, wrong file |
| Scope Guard | No unrelated changes in the diff | Drive-by refactoring, formatting changes, bonus features |
| Side Effect | Change doesn't break existing behavior | Modified shared interface, removed used code, changed return type |
```

- [ ] **Step 2: Review the file for completeness**

Read back `references/verification.md` and verify:
- All 7 substeps (5-1 through 5-7) are present
- Subagent prompt template is complete with all 3 criteria
- UNCERTAIN handling is documented
- Fix loop has max 2 rounds
- DONE_WITH_CONCERNS escalation is clear
- Conditional Hard Gate has 3 options
- No TBD/TODO/placeholders

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/references/verification.md
git commit -m "feat: add references/verification.md with verification gate procedure"
```

---

### Task 3: Rewrite references/platform-github.md

Expand the existing GitHub platform guide to match the section structure of other platform guides, and add the `## Detect Platform` section.

**Files:**
- Modify: `plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-github.md`

- [ ] **Step 1: Rewrite platform-github.md**

Rewrite the file with the standardized section structure. Keep all existing API commands but reorganize and add missing sections.

```markdown
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

The `state` field maps to criticality:
- `CHANGES_REQUESTED` → associated comments are `critical`
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
```

- [ ] **Step 2: Review and verify**

Read back the file and verify all sections are present:
Prerequisites, Detect Platform, Fetch PR Info, Fetch Comments (3 types), Check Outdated, Bot Detection, Post Replies (2 types), Resolve Thread, Get Commit URL, CLAUDE.md Config Example.

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-github.md
git commit -m "refactor: restructure platform-github.md with standardized sections"
```

---

### Task 4: Create references/platform-gitlab.md

New file for GitLab MR review comment operations.

**Files:**
- Create: `plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-gitlab.md`

- [ ] **Step 1: Create platform-gitlab.md**

```markdown
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

```bash
glab api "projects/:id/merge_requests/{mr_iid}/notes/{note_id}" \
  --jq '.resolved'
```

Also check if the position still maps to a valid diff location:

```bash
glab api "projects/:id/merge_requests/{mr_iid}/discussions" \
  --jq '.[] | select(.notes[0].id == {note_id}) | .notes[0].position'
```

If the position references a line no longer in the current diff, the comment is outdated.

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
  --jq '.[] | select(.notes[].id == {note_id}) | .id'
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
```

- [ ] **Step 2: Review and verify**

Read back and verify all sections match the platform-github.md structure:
Prerequisites, Detect Platform, Fetch MR Info, Fetch Comments, Check Outdated, Bot Detection, Post Replies (2 types), Resolve Thread, Get Commit URL, CLAUDE.md Config Example.

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/references/platform-gitlab.md
git commit -m "feat: add references/platform-gitlab.md for GitLab MR support"
```

---

### Task 5: Rewrite references/eval-cases.md

Expand from 4 to 8 test cases, adding verification gate and GitLab scenarios. Follow the eval-cases format from design-sprint and run-sprint (Verification checkboxes + Evaluation Log table).

**Files:**
- Modify: `plugins/aoshimash-skills/skills/respond-to-pr-review/references/eval-cases.md`

- [ ] **Step 1: Rewrite eval-cases.md**

```markdown
# Evaluation Test Cases

## Case 1: Mixed comments — implement + reject

**Setup**: PR with 3 comment groups:
1. Bot (CodeClimate): "Method `processData` has cognitive complexity of 15 (threshold: 10)"
2. Human reviewer: "This variable name `d` is unclear. Could you rename it to `durationMs`?"
3. Human reviewer: "The error message doesn't include the original error. Should propagate it."
   + Same from another human: "Agree, we need the cause in the error chain."

**Expected behavior**:
- Phase 0: PR identified, platform detected as GitHub
- Phase 1: All 3 comments fetched, classified (1 bot, 2 human threads)
- Phase 2: Comments 3a and 3b grouped (same issue). Group 3 tagged `critical` (2 reviewers)
- Phase 3: User decides — Group 1: Reject, Group 2: Implement, Group 3: Implement
- Phase 4: Two commits made (rename + error propagation)
- Phase 5: Group 3 verified by subagent (critical), Group 2 self-reviewed (normal)
- Phase 7: Bot reply (no thanks, factual), Human replies (brief thanks + commit link)

**Verification**:
- [ ] Bot comment reply has no opening thanks and is factual
- [ ] Human comment replies include brief thanks and commit SHA link
- [ ] Group 3 (2 reviewers) presented as one group, tagged `critical`
- [ ] Verification Gate executed: subagent for critical, self-review for normal
- [ ] Reply batch shown for approval before posting

---

## Case 2: Out-of-scope valid suggestion

**Setup**: PR adding a new API endpoint. One reviewer comments:
"While you're here, the auth middleware is missing rate limiting. This could be a security issue."

**Expected behavior**:
- Skill identifies this as potentially out of scope
- Presents "Create Issue" as a natural option
- User chooses "Create Issue"
- Issue created linking back to the PR comment
- Reply posted: "Good catch — outside scope for this PR. Created #42 to track it."

**Verification**:
- [ ] Issue body contains link to the original PR comment
- [ ] Reply includes the created issue number
- [ ] No code changes made for this group

---

## Case 3: Purely informational comments — no reply needed

**Setup**: PR with comments:
1. GitHub Actions bot: "Coverage report: 87.3% (+0.2%)"
2. Dependabot: "This PR resolves 2 security advisories"
3. Human: "LGTM! Great work 🎉"

**Expected behavior**:
- All three filtered out in Phase 1 as not requiring a response
- Skill reports: "No actionable comments found." and exits

**Verification**:
- [ ] All 3 comments correctly filtered out
- [ ] No reply drafts generated
- [ ] Graceful exit message shown

---

## Case 4: No PR found

**Setup**: User is on `main` branch with no open PR.

**Expected behavior**:
- Skill detects no PR for current branch
- Asks user for PR number or URL via `AskUserQuestion`
- Continues normally after user provides it

**Verification**:
- [ ] `AskUserQuestion` used (not just a text prompt)
- [ ] Workflow continues normally after user provides PR info

---

## Case 5: Verification Gate catches intent mismatch

**Setup**: PR with one comment:
- Human reviewer (REQUEST_CHANGES): "Please rename `getData` to `fetchUserProfile` to better describe what it does."
- Implementation renames the function but also refactors its internals (extracting a helper function).

**Expected behavior**:
- Phase 2: Tagged `critical` (REQUEST_CHANGES)
- Phase 5: Subagent verification detects:
  - Intent Match: PASS (function renamed)
  - Scope Guard: FAIL (helper extraction not requested)
  - Side Effect: PASS
  - Result: NEEDS_FIX
- Fix loop round 1: Remove the helper extraction, keep only the rename
- Re-verify: PASS
- Reply includes only the rename commit

**Verification**:
- [ ] Subagent dispatched for this critical group
- [ ] Scope Guard failure correctly identified
- [ ] Fix loop executed (max 1 round in this case)
- [ ] Final diff contains only the rename, no extra refactoring
- [ ] Reply references the correct (fixed) commit SHA

---

## Case 6: DONE_WITH_CONCERNS flow

**Setup**: PR with one comment:
- Human reviewer (REQUEST_CHANGES): "The caching logic should use LRU eviction instead of FIFO."
- The codebase has a complex caching layer. Implementation attempts to switch to LRU but verification fails twice (Intent Match keeps failing — partial LRU implementation).

**Expected behavior**:
- Phase 5: NEEDS_FIX on round 1 and round 2
- After round 2: marked DONE_WITH_CONCERNS
- Conditional Hard Gate triggered — user presented with options:
  - Proceed (replies with caveat)
  - Re-implement (user provides guidance)
  - Abort
- If Proceed: reply includes "Please verify this matches your intent."

**Verification**:
- [ ] Fix loop runs exactly 2 rounds before escalating
- [ ] DONE_WITH_CONCERNS status correctly assigned
- [ ] Conditional Hard Gate shown with 3 options
- [ ] Reply draft includes caveat note about verification

---

## Case 7: Critical vs normal verification routing

**Setup**: PR with 3 comment groups:
1. Human reviewer (REQUEST_CHANGES): "Missing null check on `user.email`" → `critical`
2. Human reviewer + Bot (ESLint): same unused import flagged → `critical` (2 reviewers)
3. Human reviewer (COMMENT): "Nitpick: prefer `const` over `let` here" → `normal`

**Expected behavior**:
- Phase 2: Groups 1 and 2 tagged `critical`, Group 3 tagged `normal`
- Phase 5:
  - Groups 1 and 2: subagent verification (separate subagent per group)
  - Group 3: self-review (3-criteria checklist)

**Verification**:
- [ ] Criticality tags correctly assigned based on REQUEST_CHANGES and multi-reviewer
- [ ] Subagents dispatched for groups 1 and 2
- [ ] Self-review used for group 3
- [ ] All 3 criteria checked for every group regardless of method

---

## Case 8: GitLab MR review

**Setup**: GitLab project with open MR. MR has:
1. Inline discussion thread: "This query will cause N+1 — use eager loading."
2. General MR note: "Can you add a test for the edge case where the list is empty?"

**Expected behavior**:
- Phase 0: Platform detected as GitLab, `references/platform-gitlab.md` loaded
- Phase 1: Notes fetched via `glab api`, classified into inline (resolvable) and general
- Phase 2-4: Normal flow (group, decide, implement)
- Phase 5: Verification runs normally
- Phase 7: Replies posted via GitLab notes API, inline thread resolved

**Verification**:
- [ ] Platform correctly detected as GitLab
- [ ] `glab` CLI used for all API interactions (not `gh`)
- [ ] Inline reply posted to the correct discussion thread
- [ ] General reply posted as a new MR note
- [ ] Thread resolution attempted after reply

---

## Evaluation Log

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-03-22 | Case 1 (PR #41) | with_skill 100% / without_skill 43% | Real Devin bot reviewed the PR |
| 2026-03-22 | Case 4 (No PR) | with_skill 100% / without_skill 50% | without_skill lacked structured next step |
```

- [ ] **Step 2: Review and verify**

Read back and verify:
- 8 cases present, each with Setup / Expected behavior / Verification
- Cases 5-7 cover Verification Gate scenarios
- Case 8 covers GitLab
- Evaluation Log preserves existing entries
- No TBD/TODO/placeholders

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/references/eval-cases.md
git commit -m "feat: expand eval-cases.md from 4 to 8 cases with verification and GitLab scenarios"
```

---

### Task 6: Rewrite SKILL.md

Rewrite the main SKILL.md as a summary-only file (~120 lines) that delegates details to references. This is the final task because it references all the files created in Tasks 1-5.

**Files:**
- Modify: `plugins/aoshimash-skills/skills/respond-to-pr-review/SKILL.md`

- [ ] **Step 1: Rewrite SKILL.md**

```markdown
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

**Summary:** Group comments pointing out the same issue across reviewers/bots/lines. Record metadata (bodies, IDs, reviewers, files). Tag criticality: `critical` (REQUEST_CHANGES or 2+ reviewers) vs `normal`.

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

### Phase 5: Verification Gate

See [references/verification.md](references/verification.md) for detailed procedure.

**Summary:** Verify that Phase 4 changes match the reviewer's intent.

- `critical` groups → subagent verification (3 criteria: Intent Match, Scope Guard, Side Effect)
- `normal` groups → self-review using the same 3 criteria
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
| Implement (WITH_CONCERNS) | "Fixed in [SHA] — [description]. Please verify this matches your intent." | "Fixed in [SHA]: [description]. Verification requested." |
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
```

- [ ] **Step 2: Count lines and verify structure**

Read back `SKILL.md` and verify:
- Line count is ~120 (not over 150)
- Frontmatter has only `name` and `description`
- All 7 Core Principles present
- All 8 Phases (0-7) present with summaries
- Each Phase 1-3 and Phase 5 links to the correct reference file
- 4 Hard Gates present (Phase 0, Phase 3, Phase 5 conditional, Phase 7)
- Edge Cases section present
- References section lists all 5 reference files
- No TBD/TODO/placeholders

- [ ] **Step 3: Commit**

```bash
git add plugins/aoshimash-skills/skills/respond-to-pr-review/SKILL.md
git commit -m "refactor: rewrite SKILL.md as summary with references delegation"
```

---

### Task 7: Final review and cleanup

Verify all files are consistent and the skill is complete.

**Files:**
- All files in `plugins/aoshimash-skills/skills/respond-to-pr-review/`

- [ ] **Step 1: Cross-reference check**

Read all 6 files and verify:
- Every reference link in SKILL.md points to an existing file
- Phase numbers are consistent across SKILL.md, workflow.md, and verification.md
- Criticality tags (`critical`/`normal`) are defined in workflow.md and consumed in verification.md
- Platform guides have identical section structure
- Eval cases reference the correct phase numbers

- [ ] **Step 2: Delete the workspace directory**

The `respond-to-pr-review-workspace/` directory contains old iteration data that is no longer needed.

```bash
rm -rf plugins/aoshimash-skills/skills/respond-to-pr-review-workspace/
```

- [ ] **Step 3: Final commit**

```bash
git add -A plugins/aoshimash-skills/skills/respond-to-pr-review/
git status
git commit -m "chore: final cleanup for respond-to-pr-review refactor"
```
