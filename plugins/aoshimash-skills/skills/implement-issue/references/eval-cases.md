# Evaluation Test Cases

## Quality Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| 1 | Issue parsed correctly | All fields extracted (summary, motivation, proposal, acceptance criteria) |
| 2 | Codebase analyzed | Related files, patterns, conventions, and existing branches identified |
| 3 | Design decisions resolved | User consulted when multiple valid approaches exist, with options and recommendation |
| 4 | Plan covers all criteria | Every acceptance criterion has a verification method |
| 5 | Plan stays in scope | No changes unrelated to the issue |
| 6 | Plan follows conventions | Consistent with CLAUDE.md and existing patterns |
| 7 | User approval obtained | Plan presented and explicit approval received before coding |
| 8 | Implementation location chosen | User asked to choose worktree (default) / new branch / current branch |
| 9 | Branch naming correct | Follows `<type>/<issue-number>-<description>` convention |
| 10 | Implementation matches plan | No unplanned changes, no scope creep |
| 11 | Checks pass with loop | Project checks run and failures fixed in loop (max 3 attempts, then escalate) |
| 12 | AI self-review completed | Diff reviewed, issues fixed in loop (max 3 rounds, then escalate) |
| 13 | Human escalation works | User consulted when human judgment is needed, with options and recommendation |
| 14 | PR/MR well-formed | Has summary, issue link, changes list, test plan |

## Test Cases

### Case 1: Simple bug fix issue

**Scenario**: User says "implement issue #12" — issue describes a null pointer error in a specific function with clear reproduction steps and acceptance criteria.

**Expected behavior**:
- Ask implementation location (default: worktree)
- Plan is concise (1 file change), no design decisions needed (skip step 1-3)
- Fix is minimal and targeted
- Checks and review pass quickly
- PR references and closes the issue

**Criteria to test**: 1, 2, 4, 5, 8, 10, 11, 14

### Case 2: Feature request with multiple valid approaches

**Scenario**: User provides issue URL — issue requests a new API endpoint. Both REST and GraphQL are viable.

**Expected behavior**:
- Present REST vs GraphQL (or similar) as options with pros/cons and recommendation
- Wait for user's choice before drafting plan
- Plan lists all files (route, controller, model, migration, tests)
- Checks loop runs; any test failures are fixed
- AI review catches issues and fixes them
- PR created after all checks and review pass

**Criteria to test**: 3, 4, 6, 7, 10, 11, 12, 14

### Case 3: Issue with vague acceptance criteria

**Scenario**: User says "issue #45 を実装して" — issue has good motivation/proposal but acceptance criteria are vague ("it should work well").

**Expected behavior**:
- Flag the vague criteria during planning
- Propose 2-3 concrete, testable criteria for user approval
- Do not proceed with implementation until criteria are clarified

**Criteria to test**: 1, 4, 7

### Case 4: Large issue that should be split

**Scenario**: Issue describes 3+ independent features bundled together.

**Expected behavior**:
- Recognize the issue is too large for a single PR
- Suggest splitting into smaller issues/PRs
- If user insists, implement incrementally with clear scope per commit

**Criteria to test**: 5, 7, 10

### Case 5: Issue in GitLab project

**Scenario**: User says "implement issue #7" in a project with GitLab remote.

**Expected behavior**:
- Detect GitLab platform from remote URL
- Ask implementation location
- Use `glab` CLI to read issue and create MR
- MR format matches GitLab conventions

**Criteria to test**: 1, 8, 9, 14

### Case 6: Issue with existing partial implementation

**Scenario**: User says "implement #30" — there's already a stale branch with partial work.

**Expected behavior**:
- Detect existing branch during codebase analysis
- Ask user whether to build on existing branch or start fresh
- Plan accounts for already-completed work if continuing

**Criteria to test**: 2, 7, 10

### Case 7: Tests fail repeatedly during implementation

**Scenario**: Implementation causes test failures that are hard to fix. After 3 attempts, tests still fail.

**Expected behavior**:
- Attempt to fix failures up to 3 times
- After 3 attempts, escalate to user with: which checks fail, what was tried, options (continue/skip/abandon)
- Respect user's choice and proceed accordingly

**Criteria to test**: 11, 13

### Case 8: AI review finds issue needing human judgment

**Scenario**: During AI self-review, a business logic ambiguity is discovered that the issue doesn't address.

**Expected behavior**:
- Present the ambiguity to user with 2-3 options and a recommendation
- Wait for user's choice
- Apply the fix based on user's decision
- Re-run checks after fix
- Continue review loop

**Criteria to test**: 12, 13

### Case 9: Backlog issue implementation

**Scenario**: User says "PROJ-42 を実装して" in a project with Backlog configured as issue tracker and GitHub as code hosting.

**Expected behavior**:
- Detects Backlog as issue tracker from CLAUDE.md
- Fetches issue via Backlog MCP tool using key `PROJ-42`
- Updates issue status to "In Progress" on Backlog after plan approval (Phase 2, not Phase 0)
- Detects GitHub as code hosting from git remote
- Creates PR on GitHub (not Backlog)
- Posts comment on Backlog issue with PR link
- Continuous flow from Phase 2 to Phase 3 without stopping

**Criteria to test**: 1, 2, 4, 5, 8, 9, 10, 14

### Case 10: Cross-platform with issue listing

**Scenario**: User says "implement issue" without specifying an identifier, in a project with Backlog + GitHub setup.

**Expected behavior**:
- Lists open issues from Backlog
- Presents the list and asks user to select one
- After selection, proceeds with the normal implementation flow
- Issue status updated to "In Progress" on Backlog
- PR created on GitHub
- Comment posted on Backlog issue with PR link

**Criteria to test**: 1, 2, 7, 8, 14

---

## Evaluation Log

### 2026-03-05 — Initial evaluation

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (6/6) | All criteria covered by existing instructions |
| 2 | Pass (6/6) | Multi-file plan structure and convention checks adequate |
| 3 | Pass (3/3) | Fixed: added guidance to propose concrete criteria for vague acceptance criteria |
| 4 | Pass (3/3) | Fixed: added incremental implementation guidance when user declines splitting |
| 5 | Pass (3/3) | GitLab detection and MR format covered by platform guide |
| 6 | Pass (3/3) | Fixed: added existing branch detection step in codebase analysis |

**Issues found and fixed:**
1. workflow-plan.md Step 1: Changed "ask the user" to "propose concrete criteria" for vague acceptance criteria
2. SKILL.md Principle 3: Added guidance for incremental implementation within a single PR
3. workflow-plan.md Step 2: Added step 6 for detecting existing branches related to the issue

### 2026-03-05 — Second evaluation (expanded criteria & cases)

Criteria expanded from 10 to 14. Cases expanded from 6 to 8.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Simple flow covers all criteria including location choice, checks |
| 2 | Pass (8/8) | Design decision step, check loop, AI review loop all covered |
| 3 | Pass (3/3) | Vague criteria handling unchanged, still adequate |
| 4 | Pass (3/3) | Scope control unchanged, still adequate |
| 5 | Pass (4/4) | GitLab flow with new location choice covered |
| 6 | Pass (3/3) | Existing branch detection unchanged, still adequate |
| 7 | Pass (2/2) | New case: check loop max 3 + escalation with options verified |
| 8 | Pass (2/2) | New case: AI review escalation with options + recommendation verified |

No issues found. All new steps (design decisions, check loop, AI review loop, escalation) are adequately covered by the current instructions.
