# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation
2. Trigger the analyze-sessions skill
3. Follow the described scenario
4. Evaluate against the acceptance criteria listed per case
5. Record results in the Evaluation Log section at the bottom

## Test Cases

### Case 1: No session history available

- **Persona**: User with a fresh Claude Code installation
- **Setup**: No skill session files exist in the current project's session directory
- **Initial input**: "セッションを分析して"
- **Expected behavior**:
  - Skill reports no sessions found
  - Does NOT proceed to analysis or error out
- **Key criteria**: Graceful handling of empty data

### Case 2: Fewer than 3 sessions for a skill

- **Persona**: User who has used implement-issue twice
- **Setup**: 2 session files contain `aoshimash-skills:implement-issue` invocations
- **Initial input**: "analyze sessions"
- **Expected behavior**:
  - Skill lists available skills and session counts
  - When user selects implement-issue, reports insufficient data (2/3)
  - Does NOT attempt pattern analysis
- **Key criteria**: Threshold enforcement, clear messaging

### Case 3: Pattern detection with 3+ sessions

- **Persona**: User who has used create-issue 4 times, with repeated friction in step 3
- **Setup**: 4 session files with create-issue invocations; 3 sessions show user rejecting the initial draft
- **Initial input**: "analyze skill logs"
- **Expected behavior**:
  - Detects the rejection pattern at draft step
  - Presents structured report with frequency, root cause, and proposed fix
  - Findings are grouped under "Skill Improvements"
  - Asks user to choose output method (Issue / PR / Conversation only)
- **Key criteria**: Pattern detection accuracy, structured report format

### Case 4: Output method — Conversation only

- **Persona**: User who wants to review findings without external submission
- **Setup**: Same as Case 3
- **Initial input**: Choose "Conversation only" when asked for output method
- **Expected behavior**:
  - Full analysis report is presented in conversation
  - No `gh` commands are executed
  - Workflow ends cleanly
- **Key criteria**: No side effects, complete report in conversation

### Case 5: Output method — Issue creation

- **Persona**: User who wants to submit feedback as an Issue
- **Setup**: Same as Case 3
- **Initial input**: Choose "Issue" when asked for output method
- **Expected behavior**:
  - Draft issue body is shown for review before submission
  - Issue body does NOT contain raw session data or project-specific paths
  - On approval, `gh issue create` is called with appropriate title, body, and label
  - Issue URL is returned
- **Key criteria**: Privacy filtering, user confirmation before submission, correct `gh` usage

### Case 6: Output method — PR creation

- **Persona**: User who wants to submit improvements as a PR
- **Setup**: Same as Case 3
- **Initial input**: Choose "PR" when asked for output method
- **Expected behavior**:
  - Proposed SKILL.md changes are shown as a diff for review
  - On approval, branch is created, changes committed, and PR opened
  - PR URL is returned
- **Key criteria**: User confirmation before code changes, correct branch/commit/PR flow

### Case 7: User requests multi-skill analysis

- **Persona**: User with sessions across multiple skills
- **Setup**: 3+ sessions each for implement-issue and create-issue
- **Initial input**: "全スキルを分析して"
- **Expected behavior**:
  - Lists available skills with session counts
  - Prompts user to select a **single** skill to analyze (does NOT analyze all at once)
  - After analysis completes, user can re-invoke the skill for the next skill
- **Key criteria**: Single-skill enforcement, clear guidance to re-invoke for other skills

### Case 8: Permission friction pattern detection

- **Persona**: User who repeatedly approves the same tool across sessions
- **Setup**: 4 session files with implement-issue invocations; 3 sessions show the user approving `Bash(gh api:*)` with short responses ("y", "yes", "allow") multiple times
- **Initial input**: "セッションを分析して"
- **Expected behavior**:
  - Detects the permission friction pattern for `Bash(gh api:*)`
  - Findings are grouped under "Settings Proposals"
  - Proposed fix includes a specific `permissions.allow` entry (e.g., `"Bash(gh api:*)"`)
  - Proposed fix specifies the target file (`settings.json` or `settings.local.json`)
  - Configuration snippet is included in the report
- **Key criteria**: Environment-level pattern detection, actionable settings.json proposal

### Case 9: Mixed output with skill and settings proposals

- **Persona**: User with both skill-level and environment-level patterns
- **Setup**: 5 session files with create-issue invocations; 3 sessions show rejection at draft step AND 3 sessions show repeated permission approval for the same tool
- **Initial input**: "improve skills"
- **Expected behavior**:
  - Report contains both "Skill Improvements" and "Settings Proposals" sections
  - Skill improvement has type Rejection with SKILL.md fix
  - Settings proposal has type Permission Friction with settings.json fix
  - When "Issue" output is selected, both types appear in the issue body
  - When "PR" output is selected, settings.json proposals are in PR description (not auto-applied)
- **Key criteria**: Dual-target report, correct grouping, settings proposals not auto-applied

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Pass/Fail | Notes | SKILL.md revision needed? |
|------|--------|-----------|-------|---------------------------|
| 2026-03-07 | 3 | Pass | Simulated with real data (5 create-issue + 5 implement-issue sessions). Detected language friction (5/5), interrupts (2/5), rejections (5/5). Structured report format works. | No |
| 2026-03-07 | 4 | Pass | Simulated: "Conversation only" selected, no external commands executed. | No |
| 2026-03-07 | 7 | Pass | Simulated cross-skill analysis with create-issue (5) and implement-issue (5). Per-skill findings presented. | Consider adding guidance to distinguish permission rejections from user rejections |
| 2026-03-14 | 7 | Pending | Case 7 redesigned in #32 to test single-skill enforcement. Requires interactive eval after merge. | N/A |
| 2026-03-14 | 8 | Pending | New case added in #36. Requires sessions with repeated tool permission approvals for interactive eval. | N/A |
| 2026-03-14 | 9 | Pending | New case added in #36. Requires sessions with both skill-level and environment-level patterns for interactive eval. | N/A |
