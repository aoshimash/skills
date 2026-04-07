# Two-Stage Review Gates

## Purpose

Every completed issue goes through two review stages before being marked as done. This mirrors superpowers' two-stage review pattern:

1. **Spec compliance** — Does the implementation match what the issue asked for?
2. **Code quality** — Is the code well-written, safe, and maintainable?

These are separate concerns. Spec compliance prevents over-building and under-building. Code quality catches bugs and style issues. Combining them into one review loses signal.

## Stage 1: Spec Compliance Review

### Subagent Instructions

Dispatch a reviewer subagent with:

- The issue body (the "spec")
- The PR diff (`git diff origin/<default-branch>...<branch-name>`)
- Instructions below

### Review Criteria

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | All AC met | Every acceptance criterion in the issue is satisfied by the diff |
| 2 | No scope creep | No changes unrelated to the issue's scope |
| 3 | Files match | Files changed match those listed in the issue (if specified) |
| 4 | No missing pieces | No acceptance criterion is only partially addressed |
| 5 | Approach matches | If the issue specifies an implementation approach, the code follows it |

### Output Format

```
Spec Compliance Review: <PASS / FAIL>

Acceptance Criteria:
- [x] AC 1: <description> — Met: <evidence>
- [ ] AC 2: <description> — NOT MET: <what's missing>

Scope:
- [x] No scope creep
- [ ] SCOPE CREEP: <description of unrelated changes>

Verdict: PASS / FAIL with <N> issue(s)
Issues:
1. <description of issue>
2. <description of issue>
```

### On Failure

If spec compliance fails:

1. Send the review output to the implementer subagent.
2. Implementer fixes the issues.
3. Re-run spec compliance review.
4. Max 2 fix rounds. If still failing, mark issue as `DONE_WITH_CONCERNS` and include the review output in the sprint summary.

## Stage 2: Code Quality Review

### Subagent Instructions

Dispatch a reviewer subagent with:

- The PR diff
- Project conventions (CLAUDE.md path)
- Instructions below

### Review Criteria

| # | Category | What to check |
|---|----------|---------------|
| 1 | **Correctness** | Logic errors, off-by-one, null/undefined, race conditions |
| 2 | **Security** | Injection, auth bypass, data exposure, input validation |
| 3 | **Error handling** | Errors at system boundaries handled, no silent swallowing |
| 4 | **Conventions** | Naming, structure, patterns consistent with project |
| 5 | **Performance** | No obvious N+1 queries, unnecessary allocations, blocking calls |
| 6 | **Tests** | New code has appropriate test coverage |

### Severity Levels

- **Critical** — Must fix: bug, security issue, data corruption risk
- **Important** — Should fix: convention violation, missing error handling, no tests
- **Minor** — Nice to fix: naming, style, minor optimization

### Output Format

```
Code Quality Review: <N> issue(s) found

Critical:
1. [file:line] <description>

Important:
1. [file:line] <description>

Minor:
1. [file:line] <description>

Verdict: PASS / NEEDS_FIXES
```

### On Failure

If code quality review finds Critical or Important issues:

1. Send the review output to the implementer subagent.
2. Implementer fixes Critical and Important issues (Minor issues are optional).
3. Re-run code quality review.
4. Max 2 fix rounds. If Critical issues remain, mark issue as `DONE_WITH_CONCERNS`.

## Review Flow Diagram

```
PR Created
  ↓
Stage 1: Spec Compliance
  ├─ PASS → Stage 2
  └─ FAIL → Implementer fixes → Re-review (max 2 rounds)
              ├─ PASS → Stage 2
              └─ FAIL → DONE_WITH_CONCERNS
  ↓
Stage 2: Code Quality
  ├─ PASS (no Critical/Important) → DONE
  └─ NEEDS_FIXES → Implementer fixes → Re-review (max 2 rounds)
              ├─ PASS → DONE
              └─ Still Critical → DONE_WITH_CONCERNS
```
