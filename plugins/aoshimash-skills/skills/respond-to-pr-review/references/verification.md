# Verification Gate

Detailed procedure for Phase 5 of the respond-to-pr-review skill. Verifies that implemented changes match the reviewer's intent before drafting replies.

## Purpose

Prevent replying "Fixed in abc1234" when the fix doesn't actually address the comment. Critical comments get third-party verification by a **separate agent instance** that has not seen the implementation; normal comments get self-review. When no separate agent instance is available, critical comments fall back to self-review with an explicit `SELF-REVIEWED` flag (see 5-2) so the missing guarantee stays visible.

## Procedure

### 5-1: Filter and sort

Only groups with an "Implement" decision enter the Verification Gate. Skip groups decided as Reject, Create Issue, or Skip reply — they require no code verification.

Within Implement groups, process `critical` first, then `normal`. Within each tier, process in the order they were implemented.

### 5-2: Verify critical groups (separate agent instance)

For each `critical` group with an "Implement" decision:

1. Collect the input:
   - **Comment body**: The original reviewer comment(s) in the group
   - **Diff**: `git diff <commit-before>..<commit-after>` for the commit(s) that addressed this group
   - **Context**: 30 lines before and after the changed area in each modified file

2. Dispatch a **separate agent instance with fresh context** (see Environment Adaptation in SKILL.md) — the point is a verifier that has not seen the implementation. If the environment cannot provide one, verify against the same three criteria yourself, record the resulting verdict (PASS / NEEDS_FIX / UNCERTAIN), and mark it `SELF-REVIEWED (no independent verification available)` — the marker rides on the verdict so 5-4/5-5 routing still applies; critical comments verified this way MUST be flagged as such in the reply comment (see below). Use this prompt for the verifier (or as your own checklist when self-reviewing):

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
   - PASS (broadened): The diff includes same-pattern fixes at additional locations, AND the group is tagged `rule-violation-instance`, AND the user approved the broadening in Phase 4.5
   - FAIL: The diff includes unrelated refactoring, formatting, or feature changes not covered by the above PASS conditions

3. **Side Effect**: Could the change break existing behavior?
   - PASS: The change is safe and localized
   - FAIL: The change modifies shared interfaces, removes functionality, or changes behavior beyond what was requested

Return one of:
- PASS — all 3 criteria pass
- NEEDS_FIX — at least one criterion fails (explain which and why)
- UNCERTAIN — cannot determine (explain why — e.g., insufficient context, ambiguous comment)
```

3. Record the verifier's verdict and reasoning.

**`SELF-REVIEWED` reply flag.** When a critical group was verified via the self-review fallback (no separate agent instance available), its Phase 7 reply MUST carry a visible flag containing the `SELF-REVIEWED` marker, so the reviewer knows the independent-verification guarantee did not hold. Append to the reply draft for that group:

- Human reviewer: "Note: SELF-REVIEWED — verified by self-review only, no independent verification available in this environment."
- Bot: "SELF-REVIEWED — no independent verification available."

This flag is independent of the DONE_WITH_CONCERNS caveat (5-6); a group can carry both.

### 5-3: Verify normal groups (self-review)

For each `normal` group with an "Implement" decision, run the same 3 criteria as a self-check:

- [ ] Intent Match: Does the diff address the comment?
- [ ] Scope Guard: No unrelated changes?
- [ ] Side Effect: No risk of breaking existing behavior?

If any criterion fails, mark as NEEDS_FIX with explanation.

### 5-4: Handle UNCERTAIN

When verification returns UNCERTAIN:

1. Present to the user:
   - The original comment
   - The diff
   - The verifier's reasoning for UNCERTAIN
2. Present a user choice (see Environment Adaptation in SKILL.md) with options:
   - Treat as PASS
   - Treat as NEEDS_FIX
   - Skip verification for this group

### 5-5: Fix loop

For each NEEDS_FIX result:

1. Show the failure explanation to the user (which criterion failed and why)
2. Re-implement the change to address the failure
3. Run project checks (formatter, linter, tests) until clean
4. Amend or create a new commit
5. Re-verify (separate agent instance for critical, self-review for normal)

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

Present verification results to the user via a user choice (see Environment Adaptation in SKILL.md):

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
| Scope Guard | No unrelated changes in the diff (same-pattern expansion approved in Phase 4.5 is allowed for `rule-violation-instance` groups) | Drive-by refactoring, formatting changes, bonus features |
| Side Effect | Change doesn't break existing behavior | Modified shared interface, removed used code, changed return type |
