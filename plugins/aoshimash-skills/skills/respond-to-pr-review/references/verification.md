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
