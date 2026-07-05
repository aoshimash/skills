# Batch Mode: Dependency Graph and Parallel Execution

This procedure is used in **Batch Mode** (see SKILL.md) to implement a set of issues — from a parent issue's sub-issues, a milestone, a label, or a manual list — in parallel where their dependencies allow, with worktree isolation and two-stage review per issue.

The per-issue implementation itself is NOT duplicated here: each issue is implemented by a subagent executing [workflow.md](workflow.md) in **Autonomous mode** (see workflow.md's Execution Modes table). This file covers only the orchestration around that: building the dependency graph, dispatching subagents, running review gates, and handling failures.

## Phase B1: Dependency Graph

### B1-1. Parse Dependencies

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

### B1-2. Build DAG

1. Create a directed graph: edge from A → B means "A must complete before B can start".
2. Detect cycles using topological sort. If a cycle is found:
   - Present the cycle to the user: "Circular dependency detected: #A → #B → #C → #A"
   - Use `AskUserQuestion` with options:
     - Break the dependency between #X and #Y (for each edge in the cycle)
     - Abort the batch
3. Compute topological levels (groups of issues that can run in parallel):
   - Level 0: issues with no dependencies
   - Level 1: issues whose dependencies are all in Level 0
   - Level N: issues whose dependencies are all in Level 0..N-1

### B1-3. Visualize and Approve

Display the execution plan:

```
Batch: <N> issues, <M> parallelizable groups

Group 1 (parallel):
  #101 — Add search index [Small]
  #102 — Create user model [Small]

Group 2 (parallel, after Group 1):
  #103 — Add search endpoint [Medium] ← depends on #101
  #104 — Add user API [Medium] ← depends on #102

Group 3 (sequential, after Group 2):
  #105 — Integration tests [Medium] ← depends on #103, #104
```

Use `AskUserQuestion` — "Proceed with this execution plan?" with options: Approve / Reorder / Abort.

## Phase B2: Execution Loop

Repeat until all issues are completed or all remaining issues are blocked:

### B2-1. Per-Group Execution

Process groups in order. Within each group, dispatch all issues in parallel.

For each issue in the current group:

1. **Create worktree:**
   ```bash
   git fetch origin
   git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
   ```
   Branch naming: `<type>/<issue-number>-<short-description>`
2. **Dispatch an implementer subagent** using the prompt template below.
3. **Wait for completion** of all issues in the group before proceeding to the next group.

### B2-2. Implementer Subagent Prompt Template

Dispatch each implementer subagent with a prompt that includes:

1. The full issue body and issue number.
2. The absolute path to the worktree already created for it (step B2-1) — the subagent works there, it does not create its own.
3. The absolute paths to this skill's [workflow.md](workflow.md) and the relevant `platform-*.md` guide, with the instruction:
   > "Read these files, then execute workflow.md Phases 1–3 in **Autonomous mode** inside the given worktree. Stop after creating the PR/MR and monitoring CI (workflow.md step 3-2) — do not run the review gates yourself, the orchestrator runs them. Return exactly one status line (`DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`) plus the PR/MR URL or failure details, per workflow.md's Report Status step."
4. The project's CLAUDE.md path.

Resolve the absolute paths to `workflow.md` and the platform guide at dispatch time (they live alongside this file in the skill's `references/` directory) — do not rely on the subagent inferring them.

### B2-3. Review Gates

After each issue's PR/MR is created (and the subagent has reported):

1. Stage 1: Dispatch a **spec compliance reviewer** subagent (see [review-gates.md](review-gates.md)).
2. Stage 2: Dispatch a **code quality reviewer** subagent (see [review-gates.md](review-gates.md)).
3. Stage 2.5: **Pattern Propagation** — if a `rule-violation-instance` is found, scan other in-flight PRs for the same pattern and offer to propagate the fix (see [review-gates.md](review-gates.md)). This stage only runs in Batch mode, when 2+ issues are in flight.
4. If issues are found at Stage 1 or 2 → re-dispatch the implementer subagent to fix → re-review (max 2 fix rounds per stage).

### B2-4. Failure Handling

When an issue returns `BLOCKED` or `NEEDS_CONTEXT`:

1. Record the failure reason.
2. Find all issues that transitively depend on the failed issue.
3. Mark them all as `SKIPPED (dependency failed)`.
4. Continue with remaining independent issues.
5. Do NOT stop the batch — other independent branches of the DAG may still succeed.

### B2-5. DAG Update After Group Completion

After all issues in a group complete:

1. Update the status of each issue (DONE / DONE_WITH_CONCERNS / BLOCKED / SKIPPED).
2. Check if any issues in subsequent groups now have all dependencies met.
3. Proceed to the next group.

### B2-6. Worktree Cleanup

After each issue completes (regardless of status):

- If DONE or DONE_WITH_CONCERNS: worktree is no longer needed (branch is pushed). Remove it:
  ```bash
  git worktree remove .claude/worktrees/<branch-name>
  ```
- If BLOCKED: keep the worktree for debugging. Inform the user of the path.

## Phase B3: Summary

After all issues are processed, present a summary table:

```
Batch Complete: N/M issues implemented

| Issue | Title | Status | PR |
|-------|-------|--------|----|
| #101 | Add search index | ✅ Done | #201 |
| #102 | Create endpoint | ✅ Done | #202 |
| #103 | Add UI component | ✅ Done | #203 |
| #104 | Error handling | ❌ Blocked | — |
| #105 | Integration tests | ⏭️ Skipped (dep) | — |
```

For blocked issues, explain what went wrong and suggest next steps. If the issue tracker supports it, post a summary comment on the parent issue.
