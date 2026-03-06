# Evaluation Test Cases

## Quality Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| 1 | Config loaded or created | Existing config loaded without prompting, or first-run setup completed and saved |
| 2 | CLI availability checked | Each agent's CLI verified with `command -v` before invocation |
| 3 | Uninstalled CLIs skipped | Missing CLIs skipped gracefully, execution proceeds with available agents |
| 4 | Diff obtained correctly | PR diff via `gh pr diff` or local diff via `git diff`, saved to temp file |
| 5 | Agents run in parallel | All enabled agents invoked via Background Bash simultaneously |
| 6 | Perspectives applied | Default perspectives (or custom overrides) included in review prompt |
| 7 | Results parsed | Agent outputs parsed into structured findings |
| 8 | Deduplication applied | Same-issue findings from multiple agents merged |
| 9 | Contradictions resolved | Disagreements handled (majority rule or user decision) |
| 10 | Severity sorted | Output ordered Critical -> Warning -> Suggestion |
| 11 | Output format correct | Unified review follows the specified markdown format |
| 12 | Temp file cleaned up | Diff temp file deleted on every exit path |
| 13 | Session log written | skill-analyzer agent spawned with complete session data |
| 14 | All agents failed handled | When all agents fail, user is notified and temp file cleaned up |
| 15 | Per-agent perspectives | When agent-specific perspectives are configured, only those are used |

## Test Cases

### Case 1: First run — no configuration exists

**Scenario**: User invokes `/multi-agent-review` for the first time. No `.claude/aoshimash-skills.local.md` exists. Claude and Gemini CLIs are installed, Codex is not.

**Expected behavior**:
- Detect installed CLIs (Claude, Gemini found; Codex not found)
- Present available CLIs and ask user which to enable
- Save selection to `.claude/aoshimash-skills.local.md`
- Proceed with selected agents

**Criteria to test**: 1, 2, 3

### Case 2: Subsequent run — configuration exists

**Scenario**: User invokes `/multi-agent-review` with existing configuration (Claude and Gemini enabled).

**Expected behavior**:
- Load configuration without prompting
- Proceed directly to diff acquisition

**Criteria to test**: 1

### Case 3: PR diff review

**Scenario**: User says `/multi-agent-review #42`. PR #42 exists with changes.

**Expected behavior**:
- Obtain diff via `gh pr diff 42`
- Save to temp file
- Run agents in parallel with default perspectives
- Aggregate and present unified review
- Clean up temp file

**Criteria to test**: 4, 5, 6, 7, 8, 10, 11, 12

### Case 4: Local diff review

**Scenario**: User invokes `/multi-agent-review` without PR number. Branch has uncommitted and committed changes vs main.

**Expected behavior**:
- Detect no PR specified
- Get local diff (origin/main...HEAD + unstaged + staged)
- Run agents and produce unified review

**Criteria to test**: 4, 5, 11

### Case 5: No changes found

**Scenario**: User invokes `/multi-agent-review` but there are no changes (clean branch, on main).

**Expected behavior**:
- Detect empty diff
- Report "No changes found"
- Clean up temp file and exit

**Criteria to test**: 4, 12

### Case 6: Agents produce contradicting findings

**Scenario**: Claude says a function is safe, Gemini flags it as Critical security issue, Codex flags it as Warning.

**Expected behavior**:
- Detect contradiction
- Majority (Gemini + Codex) flagged an issue -> adopt as finding
- Note Claude's dissent
- Use highest severity (Critical) from the majority

**Criteria to test**: 8, 9, 10

### Case 7: All agents fail

**Scenario**: All configured CLIs fail (timeout, error, etc.).

**Expected behavior**:
- Report that all agents failed with details
- Clean up temp file
- Session log records the failures

**Criteria to test**: 12, 13, 14

### Case 8: One agent times out

**Scenario**: Gemini times out after 5 minutes. Claude and Codex complete successfully.

**Expected behavior**:
- Proceed with Claude and Codex results
- Note Gemini timeout in the output header
- Aggregate available results normally

**Criteria to test**: 5, 11, 13

### Case 9: Custom per-agent perspectives

**Scenario**: Configuration has Claude with only "correctness" and "security" perspectives, Codex with "architecture" and "error-handling".

**Expected behavior**:
- Claude receives prompt with only correctness + security perspectives
- Codex receives prompt with only architecture + error-handling perspectives
- Results aggregated normally despite different review scopes

**Criteria to test**: 6, 15

### Case 10: Internal use from another skill

**Scenario**: `implement-issue` skill calls `multi-agent-review` as a subagent to review implementation before creating PR.

**Expected behavior**:
- Skill loads config, gets local diff, runs agents, returns unified review
- No interactive prompts (config already exists)
- Output returned to calling skill context

**Criteria to test**: 1, 4, 5, 11

---

## Evaluation Log

(No evaluations yet)
