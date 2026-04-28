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
- [ ] Reject group (Group 1) reply uses factual bot format ("Keeping current approach: [reason].")
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

## Case 9: Pattern Broadening — drip-feed bot review

**Setup**: PR modifying 4 files. A bot reviewer (e.g., DeepSource) posts one comment:
- Bot (DeepSource): "Variable `data` in `src/utils.ts:12` does not follow the `camelCase` convention. Consider renaming to `userData`."
- The same naming violation (`data` instead of a descriptive camelCase name) exists at 3 other locations in the changed files (`src/api.ts:34`, `src/handler.ts:8`, `src/handler.ts:27`).

**Expected behavior**:
- Phase 2: Group tagged `normal` (single bot commenter, no REQUEST_CHANGES). Type tagged `rule-violation-instance` (bot commenter, uses "convention", grep-findable pattern).
- Phase 3: User decides Implement.
- Phase 4: Fix `src/utils.ts:12` only (as specifically requested).
- Phase 4.5:
  - Skill searches changed files for similar naming violations.
  - Finds 3 additional instances.
  - Presents them to the user via `AskUserQuestion` with Apply all / Pick subset / Skip.
  - User selects Apply all.
  - All 3 additional locations fixed and included in the same commit (or a new commit if pushed).
  - Group marked `broadened` (3 additional instances).
- Phase 5: Scope Guard passes (`broadened` + `rule-violation-instance` + user approved).
- Phase 7: Reply uses `Implement (broadened)` template — "Fixed in [SHA]: applied to `src/utils.ts:12` + 3 other instances of the same pattern."

**Verification**:
- [ ] Group type correctly classified as `rule-violation-instance`
- [ ] Phase 4 fixes only the originally flagged location
- [ ] Phase 4.5 finds exactly the 3 additional instances in changed files
- [ ] `AskUserQuestion` presented with Apply all / Pick subset / Skip options
- [ ] All 4 locations fixed after user chooses Apply all
- [ ] Scope Guard criterion passes (not FAIL) in Phase 5 verification
- [ ] Reply uses `Implement (broadened)` template with correct count and locations
- [ ] A single bot reply posted (not 4 separate replies)

---

## Evaluation Log

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-03-22 | Case 1 (PR #41) | with_skill 100% / without_skill 43% | Real Devin bot reviewed the PR (pre-refactor) |
| 2026-03-22 | Case 4 (No PR) | with_skill 100% / without_skill 50% | without_skill lacked structured next step (pre-refactor) |
| 2026-04-08 | Case 1 (PR #44) | with_skill 5/6 criteria passed | Devin bot comments on refactored skill. Bot tone correct, grouping correct, batch approval worked. Verification Gate criterion not testable (old skill version loaded from marketplace). |
| 2026-04-08 | Case 2-3, 5-8 | Not tested | Require specific PR scenarios (out-of-scope comments, informational-only, verification gate mismatch, GitLab MR) not available in current environment |
