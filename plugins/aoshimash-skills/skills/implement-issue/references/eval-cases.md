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
| 15 | Closed issue detected early | Closed/merged issues caught in Phase 0 with user options (reopen/pick another/abort) |
| 16 | "Other" free-text respected | When user selects "Other" with free-text, their text is treated as the chosen approach without re-presenting new options |
| 17 | Auto-fix runs before check loop | Auto-fix commands (formatters, linters with --fix) run once before the check loop when defined in CLAUDE.md |
| 18 | Post-PR CI monitored | CI checks monitored after PR creation; fixable failures result in a fix commit before returning the PR URL |
| 19 | Parent-issue confirmation asked | When a single referenced issue has open sub-issues, the user is asked to choose batch / this-issue-only / pick-one before proceeding |
| 20 | Review gates run in Single mode | Stage 1 (spec compliance) then Stage 2 (code quality) run after PR creation even for a single issue; Stage 2.5 is skipped |
| 21 | Batch dependency graph correct | Dependencies parsed from issue bodies/platform links form a valid DAG; cycles are surfaced to the user; parallel groups are computed correctly |
| 22 | Batch failure cascade works | A BLOCKED issue causes its transitive dependents to be marked SKIPPED; independent issues continue |
| 23 | Stage 2.5 pattern propagation offered | When a `rule-violation-instance` is found in Batch mode, other in-flight PRs are scanned and the user is offered a fix, without blocking the original issue |

## Single-Issue Test Cases

### Case 1: Simple bug fix issue

**Scenario**: User says "implement issue #12" — issue describes a null pointer error in a specific function with clear reproduction steps and acceptance criteria.

**Expected behavior**:
- Ask implementation location (default: worktree)
- Plan is concise (1 file change), no design decisions needed (skip step 1-3)
- Fix is minimal and targeted
- Checks and review pass quickly
- PR references and closes the issue
- Two-stage review gates run after PR creation (Stage 1 then Stage 2); Stage 2.5 is skipped since only one issue is in flight

**Criteria to test**: 1, 2, 4, 5, 8, 10, 11, 14, 20

### Case 2: Feature request with multiple valid approaches

**Scenario**: User provides issue URL — issue requests a new API endpoint. Both REST and GraphQL are viable.

**Expected behavior**:
- Present REST vs GraphQL (or similar) as options with pros/cons and recommendation
- Wait for user's choice before drafting plan
- Plan lists all files (route, controller, model, migration, tests)
- Checks loop runs; any test failures are fixed
- AI review catches issues and fixes them
- PR created after all checks and review pass
- Two-stage review gates run after PR creation; Stage 2.5 is skipped

**Criteria to test**: 3, 4, 6, 7, 10, 11, 12, 14, 20

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
- Fetches issue via `bee issue view` using key `PROJ-42`
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

### Case 11: Already-closed issue

**Scenario**: User says "implement issue #15" — issue #15 is already closed (e.g., fixed in a previous PR).

**Expected behavior**:
- Fetch the issue and detect that it is closed/merged in Phase 0 (before Phase 1)
- Inform the user: "Issue #15 is already closed."
- Present options via AskUserQuestion: "Reopen and implement" / "Pick another issue" / "Abort"
- If "Reopen and implement": reopen the issue and proceed with normal flow
- If "Pick another issue": return to issue selection
- If "Abort": stop without entering Phase 1

**Criteria to test**: 15

### Case 12: User selects "Other" with free-text in design decision

**Scenario**: During step 1-3, user is presented with 3 approach options (e.g., REST vs GraphQL vs gRPC) but selects "Other" and types "Use WebSocket for real-time updates".

**Expected behavior**:
- Treat "Use WebSocket for real-time updates" as the chosen approach
- Draft the plan using WebSocket — do NOT present new options like "WebSocket vs SSE vs long polling"
- Only re-ask if the text is genuinely ambiguous (e.g., too vague to implement)

**Criteria to test**: 3, 7, 16

### Case 13: User selects "Other" with free-text in plan approval

**Scenario**: Plan is presented for approval. User selects "Other" and types "Looks good but use a factory pattern instead of direct instantiation in the service layer".

**Expected behavior**:
- Treat the text as a specific change request
- Revise the plan to use factory pattern in the service layer
- Re-present the revised plan for approval — do NOT present new multiple-choice options about the factory pattern
- Only re-ask if the feedback contradicts other requirements or is too vague

**Criteria to test**: 7, 16

### Case 14: Auto-fix reduces check loop iterations

**Scenario**: CLAUDE.md defines a format auto-fix command (e.g., `prettier --write .`). Generated code has formatting violations that would fail the strict format check.

**Expected behavior**:
- Before entering the check loop, run the auto-fix command once
- Strict format check now passes on the first loop attempt instead of requiring a manual fix cycle
- Check loop completes in 1 attempt instead of 2-3

**Criteria to test**: 11, 17

### Case 15: Post-PR CI monitoring catches a fixable failure

**Scenario**: All local checks pass. PR is created. CI fails due to a check that wasn't run locally (e.g., an integration test or a stricter linting rule enabled only in CI).

**Expected behavior**:
- After PR creation, run `gh pr checks --watch` (GitHub) or `glab mr checks` (GitLab)
- Detect the CI failure and investigate
- If fixable: push a fix commit and re-monitor CI until it passes
- Return the PR URL only after CI is green (or note the failure if not fixable)

**Criteria to test**: 14, 18

## Batch Mode Test Cases

### Case 16: Simple linear batch

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

### Case 17: Parallel batch

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

### Case 18: Failure cascading

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
- [ ] Batch does NOT stop when #301 fails
- [ ] #304 completes independently
- [ ] Transitive dependencies correctly identified
- [ ] Failed worktree kept for debugging
- [ ] Summary accurately reflects all statuses

### Case 19: Two-stage review catches issues (batch)

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

### Case 20: Manual issue list (batch)

**Input:** User provides "implement these issues #501, #502, #503" (no parent issue)

**Expected behavior:**
1. Fetches all 3 issues individually
2. Parses dependencies from issue bodies
3. Builds DAG from parsed dependencies
4. Executes normally in Batch mode

**Verification:**
- [ ] Works without a parent issue
- [ ] Dependencies parsed from issue body text
- [ ] Same workflow as parent-based batch

### Case 21: Cross-platform batch (Backlog issues + GitHub PRs)

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

## Mode-Routing Test Cases (new)

### Case 22: Parent detection on plain "implement issue #N"

**Scenario**: User says "implement issue #40" — #40 has 3 open sub-issues (#41, #42, #43) and no unresolved dependencies among them.

**Expected behavior**:
- Phase 0 detects that #40 has open sub-issues (via the platform guide's sub-issue/child detection)
- Presents `AskUserQuestion`: "Implement all sub-issues (batch)" (Recommended, since 2+ children are open) / "Implement only this issue" / "Pick one sub-issue"
- If the user picks batch: proceeds to Batch mode (Phase B1 dependency graph) using #41-#43 as the source set
- If the user picks "only this issue": treats #40 as a normal single issue, does not touch #41-#43
- If the user picks "pick one": lists #41-#43 and continues in Single mode with the selected child

**Criteria to test**: 19, 21

### Case 23: Single-mode spec-compliance catch

**Scenario**: User says "implement issue #55" (a single, standalone issue with clear AC including "response is paginated"). Implementation is drafted without pagination.

**Expected behavior**:
- PR is created
- Stage 1 spec compliance review (run by the main agent, not a subagent) finds AC "paginated" not met → FAIL
- Main agent fixes and pushes directly (no orchestrator, no re-dispatch)
- Re-review: PASS
- Stage 2 code quality review runs next
- Stage 2.5 pattern propagation is explicitly NOT run — only one issue is in flight
- User sees the gate results in the final summary

**Criteria to test**: 20

### Case 24: Parent issue, user chooses "implement only this issue"

**Scenario**: User says "implement issue #60" — #60 has 2 open sub-issues, but the user explicitly wants #60 itself implemented (e.g., #60 is a tracking issue with its own small piece of work).

**Expected behavior**:
- Phase 0 detects the open sub-issues and asks the batch/this-issue-only/pick-one question
- User selects "Implement only this issue"
- Flow proceeds as normal Single mode on #60 — plan, approval, implement, PR, review gates
- The 2 sub-issues are not fetched, planned, or touched in any way

**Criteria to test**: 19

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

### 2026-03-08 — Post plan-approval-flow change (Refs #22)

Replaced `EnterPlanMode`/`ExitPlanMode` with text output + `AskUserQuestion` (Approve/Request changes/Abort). This session itself used the new flow to verify it works.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Plan presented as text, approved via AskUserQuestion — flow completed to PR |
| 2 | Pass (8/8) | Design decision (approach choice) resolved via AskUserQuestion before plan |
| 3 | Pass (3/3) | Vague criteria handling unaffected by this change |
| 4 | Pass (3/3) | Scope control unaffected by this change |
| 5 | Pass (4/4) | Platform detection unaffected by this change |
| 6 | Pass (3/3) | Existing branch detection unaffected by this change |
| 7 | Pass (2/2) | Check loop unaffected by this change |
| 8 | Pass (2/2) | AI review escalation unaffected by this change |
| 9 | Pass (8/8) | Cross-platform flow unaffected; plan approval via AskUserQuestion compatible |
| 10 | Pass (5/5) | Issue listing flow unaffected; plan approval via AskUserQuestion compatible |

**Key verification:** This session (implementing #22) served as a live test of the new AskUserQuestion-based approval flow. Plan was presented as text, user approved via AskUserQuestion, and implementation proceeded through to PR creation without abandonment.

### 2026-03-14 — Added closed-issue early detection (Refs #28)

Added Phase 0 Step 4 to check issue state before proceeding. Added criterion #15 and Case 11.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Unaffected; open issues skip the new state check |
| 2 | Pass (8/8) | Unaffected by Phase 0 change |
| 3 | Pass (3/3) | Unaffected by Phase 0 change |
| 4 | Pass (3/3) | Unaffected by Phase 0 change |
| 5 | Pass (4/4) | Unaffected by Phase 0 change |
| 6 | Pass (3/3) | Unaffected by Phase 0 change |
| 7 | Pass (2/2) | Unaffected by Phase 0 change |
| 8 | Pass (2/2) | Unaffected by Phase 0 change |
| 9 | Pass (8/8) | Unaffected by Phase 0 change |
| 10 | Pass (5/5) | Unaffected by Phase 0 change |
| 11 | Pass (1/1) | New case: closed issue detected in Phase 0, user presented with reopen/pick another/abort options |

No issues found. The new step is a simple guard clause in Phase 0 that only triggers for closed/merged issues, so all existing cases remain unaffected.

### 2026-03-14 — Other free-text handling (Refs #29)

Added guidance in workflow.md sections 1-3 and 1-6 to treat "Other" free-text as the chosen approach. Added criterion 16 and cases 12-13.

| Case | Result | Notes |
|------|--------|-------|
| 2 | Pass (8/8) | Design decision flow unaffected; new "Other" guidance is additive |
| 3 | Pass (3/3) | Vague criteria handling unaffected by this change |
| 12 | Pass (3/3) | New case: "Other" free-text in design decision treated as chosen approach, no re-presentation of options |
| 13 | Pass (2/2) | New case: "Other" free-text in plan approval treated as specific change request, plan revised directly |

No issues found. Changes are additive — existing behavior for predefined options is unchanged. New guidance only applies when user selects "Other" with free-text.

### 2026-03-22 — Auto-fix before checks and post-PR CI monitoring (Refs #39)

Added auto-fix step in §2-3 of workflow.md, regenerated-files guidance in §2-2, post-PR CI monitoring in §3-2 of workflow.md and §4 of SKILL.md Phase 3. Added platform-specific CI commands to platform-github.md and platform-gitlab.md. Added criteria #17-18 and cases 14-15.

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass (8/8) | Auto-fix step is skipped when not defined; post-PR CI monitoring is platform-agnostic |
| 2 | Pass (8/8) | Existing check loop and design decision flows unaffected |
| 3 | Pass (3/3) | Vague criteria handling unaffected |
| 4 | Pass (3/3) | Scope control unaffected |
| 5 | Pass (4/4) | GitLab now has `glab mr checks` in platform guide; MR flow unaffected |
| 6 | Pass (3/3) | Existing branch detection unaffected |
| 7 | Pass (2/2) | Check loop escalation unaffected |
| 8 | Pass (2/2) | AI review escalation unaffected |
| 9 | Pass (8/8) | Cross-platform flow unaffected; CI monitoring applies to GitHub code hosting |
| 10 | Pass (5/5) | Issue listing flow unaffected |
| 11 | Pass (1/1) | Closed issue detection unaffected |
| 12 | Pass (3/3) | "Other" free-text handling unaffected |
| 13 | Pass (2/2) | Plan revision flow unaffected |
| 14 | Pass (2/2) | New case: auto-fix runs before check loop, reducing loop iterations |
| 15 | Pass (2/2) | New case: post-PR CI monitored, fixable failures addressed before returning PR URL |

No issues found. Changes are additive and localized to §2-2, §2-3, and §3-x of workflow.md. Existing behavior unchanged for projects that don't define auto-fix commands or CI.

### 2026-07-05 — Merged run-sprint into implement-issue

Merged run-sprint's batch execution model (dependency graph, worktree-per-issue parallel dispatch, two-stage review with pattern propagation) into implement-issue as "Batch mode". Added criteria 19-23 and cases 16-24 (16-21 renumbered from run-sprint's 6 cases, 22-24 new for parent-issue detection and mode routing). Case numbering for 1-15 preserved from the original implement-issue log above.
