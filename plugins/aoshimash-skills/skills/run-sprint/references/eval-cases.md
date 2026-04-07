# Evaluation Test Cases

## Test Case 1: Simple Linear Sprint

**Input:** Parent issue #100 with 3 sub-issues (#101 → #102 → #103, linear dependencies)

**Expected behavior:**
1. Fetches sub-issues of #100
2. Builds DAG: #101 → #102 → #103
3. Executes sequentially: #101 first, then #102, then #103
4. Each issue gets its own worktree
5. Two-stage review after each
6. Summary shows all 3 completed with PR links

**Verification:**
- [ ] Correct dependency graph displayed
- [ ] Issues executed in correct order
- [ ] Each PR references the correct issue
- [ ] Two-stage review ran for each issue
- [ ] Worktrees cleaned up after completion
- [ ] Summary table accurate

## Test Case 2: Parallel Sprint

**Input:** Parent issue #200 with 4 sub-issues:
- #201 (no deps), #202 (no deps) — parallel
- #203 (depends on #201), #204 (depends on #202) — parallel after their deps

**Expected behavior:**
1. Builds DAG with 2 groups: {#201, #202} then {#203, #204}
2. Group 1: #201 and #202 dispatched in parallel (separate worktrees)
3. Group 2: #203 and #204 dispatched in parallel after Group 1 completes
4. All 4 PRs created

**Verification:**
- [ ] #201 and #202 run in parallel (concurrent subagents)
- [ ] #203 waits for #201 to complete
- [ ] #204 waits for #202 to complete
- [ ] No worktree conflicts between parallel issues

## Test Case 3: Failure Cascading

**Input:** 4 issues: #301 (no deps), #302 (depends on #301), #303 (depends on #302), #304 (no deps)

**Scenario:** #301 fails (tests don't pass after 3 attempts)

**Expected behavior:**
1. #301 and #304 start in parallel
2. #301 fails → marked BLOCKED
3. #302 marked SKIPPED (depends on #301)
4. #303 marked SKIPPED (transitively depends on #301)
5. #304 continues and completes normally
6. Summary shows: 1 done, 1 blocked, 2 skipped

**Verification:**
- [ ] Sprint does NOT stop when #301 fails
- [ ] #304 completes independently
- [ ] Transitive dependencies correctly identified
- [ ] Failed worktree kept for debugging
- [ ] Summary accurately reflects all statuses

## Test Case 4: Two-Stage Review Catches Issues

**Input:** Issue #401 with clear AC: "search returns paginated results"

**Scenario:** Implementation doesn't include pagination

**Expected behavior:**
1. Issue implemented without pagination
2. Spec compliance review (Stage 1): FAIL — AC "paginated results" not met
3. Implementer subagent fixes: adds pagination
4. Re-review: PASS
5. Code quality review (Stage 2): runs on updated code
6. Final status: DONE (after fix round)

**Verification:**
- [ ] Spec compliance correctly identifies missing AC
- [ ] Fix round addresses the issue
- [ ] Code quality review runs after spec compliance passes
- [ ] Status reflects the fix round in summary

## Test Case 5: Manual Issue List

**Input:** User provides "implement #501, #502, #503" (no parent issue)

**Expected behavior:**
1. Fetches all 3 issues individually
2. Parses dependencies from issue bodies
3. Builds DAG from parsed dependencies
4. Executes normally

**Verification:**
- [ ] Works without a parent issue
- [ ] Dependencies parsed from issue body text
- [ ] Same workflow as parent-based sprint

## Test Case 6: Cross-Platform (Backlog Issues + GitHub PRs)

**Input:** Backlog project issues, code hosted on GitHub

**Expected behavior:**
1. Detects Backlog as issue tracker
2. Fetches issues with `bee`
3. Detects GitHub as code hosting from git remote
4. Creates PRs with `gh`
5. Comments on Backlog issues with PR links

**Verification:**
- [ ] Correct platform detection for both issue tracker and code hosting
- [ ] Uses `bee` for issue operations
- [ ] Uses `gh` for PR operations
- [ ] Backlog issue gets comment with GitHub PR link

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Criteria passed | Criteria failed | Notes | SKILL.md revision needed? |
|------|--------|-----------------|-----------------|-------|---------------------------|
