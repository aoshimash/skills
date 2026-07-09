# Two-Stage Review Gates

## Purpose

Every PR/MR goes through two review stages before being marked as done — whether it came from Single mode (one issue, interactive) or Batch mode (many issues, orchestrated). This mirrors superpowers' two-stage review pattern:

1. **Spec compliance** — Does the implementation match what the issue asked for?
2. **Code quality** — Is the code well-written, safe, and maintainable?

These are separate concerns. Spec compliance prevents over-building and under-building. Code quality catches bugs and style issues. Combining them into one review loses signal.

**Single mode note**: with only one issue in flight, the main agent runs both stages itself (there is no separate orchestrator/reviewer split). Stage 2.5 (pattern propagation) never runs in Single mode — there are no other in-flight PRs to scan.

**Batch mode note**: the orchestrator runs a fresh reviewer per stage per issue, and Stage 2.5 is active whenever a rule violation is found with 2+ issues in flight.

## Reviewer Dispatch

A review is strongest when run by a **separate agent instance** (see Environment Adaptation in SKILL.md) with fresh context that has not seen the implementation — an independent reviewer is not anchored to the choices the implementer already made. Both stages below assume that ideal.

**Fallback when no separate agent instance is available.** Run the stage's checklist yourself and produce the stage's real verdict exactly as defined below (Stage 1: PASS/FAIL with the issue list; Stage 2: severity-tagged issue counts and PASS/NEEDS_FIXES). Then mark that verdict `SELF-REVIEWED (no independent reviewer available)`. The marker **rides on** the real result — it does not replace it — so the On-Failure fix routing (max 2 rounds, then DONE_WITH_CONCERNS in Batch / escalate in Single) applies unchanged. Record the marker next to the gate outcome in the PR/MR body so a human can see the independent-review guarantee did not hold.

## Stage 1: Spec Compliance Review

### Reviewer Instructions

Review with:

- The issue body (the "spec")
- The PR diff (`git diff origin/<default-branch>...<branch-name>`)
- Instructions below

**Batch mode**: run a dedicated reviewer with the above context — a separate agent instance where available, otherwise self-review with the `SELF-REVIEWED` marker (see Reviewer Dispatch above). **Single mode**: the main agent performs this review directly on the diff it just produced.

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

1. Fix the issues found (in Batch mode: send the review output to the implementer, which fixes and pushes; in Single mode: the main agent fixes and pushes directly).
2. Re-run spec compliance review.
3. Max 2 fix rounds. If still failing:
   - **Batch mode**: mark the issue as `DONE_WITH_CONCERNS` and include the review output in the batch summary.
   - **Single mode**: present the remaining findings to the user via a user choice (see Environment Adaptation) with options Proceed as-is / Keep fixing / Abandon instead of silently marking anything — there is a user present to decide.

## Stage 2: Code Quality Review

### Reviewer Instructions

Review with:

- The PR diff
- Project conventions (CLAUDE.md path)
- Instructions below

**Batch mode**: run a dedicated reviewer — a separate agent instance where available, otherwise self-review with the `SELF-REVIEWED` marker (see Reviewer Dispatch above). **Single mode**: the main agent performs this review directly.

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
1. [file:line] <description> | Type: rule-violation-instance | one-off-bug

Important:
1. [file:line] <description> | Type: rule-violation-instance | one-off-bug

Minor:
1. [file:line] <description> | Type: rule-violation-instance | one-off-bug

Verdict: PASS / NEEDS_FIXES
```

### On Failure

If code quality review finds Critical or Important issues:

1. Fix Critical and Important issues (Minor issues are optional). In Batch mode, send the review output to the implementer; in Single mode, the main agent fixes directly.
2. Re-run code quality review.
3. Max 2 fix rounds. If Critical issues remain:
   - **Batch mode**: mark the issue as `DONE_WITH_CONCERNS`.
   - **Single mode**: present the remaining Critical findings to the user via a user choice (see Environment Adaptation) with options Proceed as-is / Keep fixing / Abandon.

## Stage 2.5: Pattern Propagation (Batch Mode Only)

**Precondition**: run Stage 2.5 only in Batch mode, with 2+ issues in flight, when Stage 2's output contains any issue with `Type: rule-violation-instance`. In Single mode, always skip this stage — there are no other in-flight PRs to propagate a fix to.

### Classification Heuristic

Classify a violation as `rule-violation-instance` (rather than a one-off bug) when **any** of the following apply:

- The reviewer uses words like "rule", "convention", "pattern", "policy", "violates", "across", "consistently"
- The same pattern is grep-findable in other in-flight issues' diffs
- The severity is Important or Critical **and** the issue is structural (not a one-off typo)

### Propagation Procedure

1. For each other in-flight issue that has a PR branch, run:
   ```
   git diff origin/<default-branch>...<branch> | grep -n <pattern>
   ```
2. Collect all matches across in-flight branches.
3. Present findings to the user via a user choice (see Environment Adaptation):
   > "Pattern violation `<pattern>` found in N other in-flight PR(s): <list>. What would you like to do?"
   > Options: Apply fix to all / Select which PRs / Skip propagation
4. For each approved PR, run a fix pass to apply the same fix — a separate agent instance where available, otherwise directly.

### Non-Blocking Rule

Failures in propagation fixes do **not** block the original issue from completing. If a propagation fix fails, record it in the batch summary under the original issue.

## Review Flow Diagram

```
PR Created
  ↓
Stage 1: Spec Compliance
  ├─ PASS → Stage 2
  └─ FAIL → Fix (implementer in Batch / main agent in Single) → Re-review (max 2 rounds)
              ├─ PASS → Stage 2
              └─ FAIL → Batch: DONE_WITH_CONCERNS | Single: ask user
  ↓
Stage 2: Code Quality
  ├─ PASS (no Critical/Important) → Mode check
  └─ NEEDS_FIXES → Fix → Re-review (max 2 rounds)
              ├─ PASS → Mode check
              └─ Still Critical → Batch: DONE_WITH_CONCERNS | Single: ask user
  ↓
Mode check
  ├─ Single mode → DONE (Stage 2.5 always skipped)
  └─ Batch mode → Stage 2.5 check
              ├─ No rule violations → DONE
              └─ rule-violation-instance → Scan other in-flight PRs
                          ├─ No matches / user skips → DONE
                          └─ User approves → Run fix passes → DONE (failures non-blocking)
```
