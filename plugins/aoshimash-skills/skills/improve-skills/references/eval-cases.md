# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation
2. Trigger the improve-skills skill
3. Follow the described scenario
4. Evaluate against the acceptance criteria listed per case
5. Record results in the Evaluation Log section at the bottom

## Test Cases

### Case 1: No session history available

- **Persona**: User with a fresh Claude Code installation
- **Setup**: No skill session files exist in the current project's session directory
- **Initial input**: "スキルを改善して"
- **Expected behavior**:
  - Skill reports no sessions found
  - Does NOT proceed to analysis or error out
- **Key criteria**: Graceful handling of empty data

### Case 2: Fewer than 3 sessions for a skill

- **Persona**: User who has used implement-issue twice
- **Setup**: 2 session files contain `aoshimash-skills:implement-issue` invocations
- **Initial input**: "improve skills"
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

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Pass/Fail | Notes | SKILL.md revision needed? |
|------|--------|-----------|-------|---------------------------|
| 2026-03-07 | 3 | Pass | Simulated with real data (5 create-issue + 5 implement-issue sessions). Detected language friction (5/5), interrupts (2/5), rejections (5/5). Structured report format works. | No |
| 2026-03-07 | 4 | Pass | Simulated: "Conversation only" selected, no external commands executed. | No |
| 2026-03-07 | 7 | Pass | Simulated cross-skill analysis with create-issue (5) and implement-issue (5). Per-skill findings presented. **Note**: Case 7 was redesigned in #32 to test single-skill enforcement instead of cross-skill batch analysis. Previous result no longer applies. | Consider adding guidance to distinguish permission rejections from user rejections |
