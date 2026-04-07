# Workflow Detail

## Phase 1: Dependency Graph

### 1-1. Parse Dependencies

For each issue, scan the body for dependency declarations:

**Pattern matching (case-insensitive):**
- `Blocked by: #N` or `Blocked by #N`
- `Depends on: #N` or `Depends on #N`
- `After: #N` or `After #N`
- Multiple: `Blocked by: #N, #M` or `Blocked by: #N and #M`

**Platform-specific:**
- GitHub: Check sub-issue `blocked-by` relationships via `gh issue view <N> --json`
- GitLab: Check issue links via `glab api "projects/:id/issues/<iid>/links"`
- Backlog: Parse issue body only (no built-in blocking)

Build a mapping: `{ issueNumber → [blockedByIssueNumbers] }`

### 1-2. Build DAG

1. Create a directed graph: edge from A → B means "A must complete before B can start".
2. Detect cycles using topological sort. If a cycle is found:
   - Present the cycle to the user: "Circular dependency detected: #A → #B → #C → #A"
   - Use `AskUserQuestion` with options:
     - Break the dependency between #X and #Y (for each edge in the cycle)
     - Abort the sprint
3. Compute topological levels (groups of issues that can run in parallel):
   - Level 0: issues with no dependencies
   - Level 1: issues whose dependencies are all in Level 0
   - Level N: issues whose dependencies are all in Level 0..N-1

### 1-3. Visualize

Display the execution plan:

```
Sprint: <N> issues, <M> parallelizable groups

Group 1 (parallel):
  #101 — Add search index [Small]
  #102 — Create user model [Small]

Group 2 (parallel, after Group 1):
  #103 — Add search endpoint [Medium] ← depends on #101
  #104 — Add user API [Medium] ← depends on #102

Group 3 (sequential, after Group 2):
  #105 — Integration tests [Medium] ← depends on #103, #104
```

## Phase 2: Execution Loop

### 2-1. Per-Group Execution

Process groups in order. Within each group, dispatch all issues in parallel.

For each issue in the current group:

1. **Create worktree:**
   ```bash
   git fetch origin
   git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
   ```
   Branch naming: `<type>/<issue-number>-<short-description>`

2. **Dispatch implementer subagent** with this context:
   - The full issue body
   - The worktree path
   - Project conventions (CLAUDE.md path)
   - Instructions to follow the per-issue implementation procedure below

3. **Wait for completion** of all issues in the group before proceeding to the next group.

### 2-2. Per-Issue Implementation (Subagent Instructions)

The implementer subagent follows this procedure:

#### A. Parse the Issue

Extract from the issue body:
- Summary, Motivation, Background
- Implementation Approach (if present — design-sprint issues include this)
- Acceptance Criteria
- Files to change

If critical information is missing, output what is missing and stop with status `NEEDS_CONTEXT`.

#### B. Plan

1. Read the files listed in the issue.
2. Analyze surrounding code for conventions.
3. Draft a brief implementation plan (internal, not presented to user):
   - What to change in each file
   - How to verify each acceptance criterion
4. If the issue includes an Implementation Approach section with code examples, use those as the primary reference.

#### C. Implement

1. Make changes following the plan.
2. Keep changes minimal — only what the issue specifies.
3. Follow existing patterns (naming, style, abstractions).
4. Regenerate derived files if source files that drive code generation were modified.

#### D. Run Project Checks

Check CLAUDE.md for project-specific commands.

**Step 0 (once):** Run auto-fix commands (formatters, linters with `--fix`).

**Loop (max 3 attempts):**
1. Run all checks (tests, lint, type-check, build).
2. If any fail, fix and re-run.
3. If still failing after 3 attempts, stop with status `BLOCKED` and the error.

#### E. Self-Review

Review the full diff:
```bash
git diff
```

Check for:
- Logic errors, off-by-one, null risks
- Security issues
- Missing error handling at system boundaries
- Inconsistency with the issue's acceptance criteria
- Code that doesn't follow project conventions

**Loop (max 3 rounds):**
1. Review diff.
2. Fix clear issues.
3. Re-run project checks after fixes.
4. Re-review.

Output: `Self-review: N round(s), N issue(s) found, N fixed`

#### F. Commit

Conventional Commit referencing the issue:

```
<type>: <description>

<body>

Refs #<issue-number>
```

#### G. Create PR

1. Push the branch:
   ```bash
   git push -u origin <branch-name>
   ```
2. Create PR with:
   - Title: concise summary (under 70 chars)
   - Body:
     ```markdown
     ## Summary
     <bullets>

     Closes #<issue-number>

     ## Changes
     <file-level changes>

     ## Test Plan
     <verification checklist>
     ```
3. Monitor CI (`gh pr checks --watch` or equivalent). If CI fails and is fixable, push a fix commit.

#### H. Report Status

Return one of:
- `DONE` — PR created, CI passing
- `DONE_WITH_CONCERNS` — PR created but with noted concerns
- `NEEDS_CONTEXT` — Missing information, cannot proceed
- `BLOCKED` — Failed after retries, with error details

### 2-3. Failure Handling

When an issue returns `BLOCKED` or `NEEDS_CONTEXT`:

1. Record the failure reason.
2. Find all issues that transitively depend on the failed issue.
3. Mark them all as `SKIPPED (dependency failed)`.
4. Continue with remaining independent issues.
5. Do NOT stop the sprint — other independent branches of the DAG may still succeed.

### 2-4. DAG Update After Group Completion

After all issues in a group complete:

1. Update the status of each issue (DONE / DONE_WITH_CONCERNS / BLOCKED / SKIPPED).
2. Check if any issues in subsequent groups now have all dependencies met.
3. Proceed to the next group.

### 2-5. Worktree Cleanup

After each issue completes (regardless of status):

- If DONE: worktree is no longer needed (branch is pushed). Remove it:
  ```bash
  git worktree remove .claude/worktrees/<branch-name>
  ```
- If BLOCKED: keep the worktree for debugging. Inform the user of the path.
