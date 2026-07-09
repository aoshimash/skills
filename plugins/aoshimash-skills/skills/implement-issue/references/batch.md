# Batch Mode: Dependency Graph and Dependency-Ordered Execution

This procedure is used in **Batch Mode** (see SKILL.md) to implement a set of issues — from a parent issue's sub-issues, a milestone, a label, or a manual list — in dependency order (in parallel where the environment allows), with worktree isolation and two-stage review per issue.

The per-issue implementation itself is NOT duplicated here: each issue is implemented by running [workflow.md](workflow.md) in **Autonomous mode** (see workflow.md's Execution Modes table). This file covers only the orchestration around that: building the dependency graph, running the implementer for each issue, running review gates, and handling failures.

**Separate agent instances are an optimization, not a requirement.** Where the environment supports separate agent instances (see Environment Adaptation in SKILL.md), the orchestrator runs each issue's implementer and each review gate as its own instance, and dispatches an entire dependency group at once for wall-clock parallelism. Where it does not, the orchestrator runs the same steps sequentially in dependency order in the current context. The dependency DAG, review gates, and failure cascade below are identical either way — only wall-clock parallelism is lost in the sequential case.

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
   - Ask the user to choose (see Environment Adaptation in SKILL.md) with options:
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

Ask the user to choose (see Environment Adaptation in SKILL.md) — "Proceed with this execution plan?" with options: Approve / Reorder / Abort.

## Phase B2: Execution Loop

Repeat until all issues are completed or all remaining issues are blocked.

**Execution model — parallel or sequential.** When the environment can run separate agent instances in parallel, dispatch a whole group's issues at once and wait for the group to finish before starting the next. When it cannot, implement each group's issues **sequentially in dependency order** in the current context, still using one worktree per issue. The DAG, review gates, and failure cascade are unchanged; only wall-clock parallelism is lost. The steps below are written for the parallel case; in the sequential case, "dispatch"/"run the implementer" means "execute those same instructions yourself, one issue at a time, in group-then-dependency order."

### B2-1. Per-Group Execution

Process groups in dependency order. Within a group the issues are independent of each other, so run them in parallel where the environment supports it, otherwise one after another.

For each issue in the current group:

1. **Create worktree** (keep the worktree directory out of version control with a per-clone git exclude — `.git/info/exclude` is local to the clone, so it never appears in the PR the way editing `.gitignore` would):
   ```bash
   git fetch origin
   grep -qxF '.worktrees/' .git/info/exclude 2>/dev/null || echo '.worktrees/' >> .git/info/exclude
   git worktree add .worktrees/<branch-name> -b <branch-name> origin/<default-branch>
   ```
   Branch naming: `<type>/<issue-number>-<short-description>`
2. **Run the implementer** using the instruction template below — as a separate agent instance where available, otherwise by executing those same instructions yourself in the issue's worktree.
3. **Wait for completion** of all issues in the current group before proceeding to the next group.

### B2-2. Implementer Instruction Template

Run each issue's implementer with an instruction set that includes:

1. The full issue body and issue number.
2. The absolute path to the worktree already created for it (step B2-1) — the implementer works there, it does not create its own.
3. The absolute paths to this skill's [workflow.md](workflow.md) and the relevant `platform-*.md` guide, with the instruction:
   > "Read these files, then execute workflow.md Phases 1–3 in **Autonomous mode** inside the given worktree. Stop after creating the PR/MR and monitoring CI (workflow.md step 3-2) — do not run the review gates yourself, the orchestrator runs them. Return exactly one status line (`DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`) plus the PR/MR URL or failure details, per workflow.md's Report Status step."
4. The project's CLAUDE.md path.

Resolve the absolute paths to `workflow.md` and the platform guide before starting the implementer (they live alongside this file in the skill's `references/` directory) — do not rely on the implementer inferring them. When running as a separate agent instance, pass this as its dispatch prompt; when running in the current context, follow it directly.

### B2-3. Review Gates

After each issue's PR/MR is created (and the implementer has reported):

1. Stage 1: Run a **spec compliance reviewer** (see [review-gates.md](review-gates.md)).
2. Stage 2: Run a **code quality reviewer** (see [review-gates.md](review-gates.md)).
3. Stage 2.5: **Pattern Propagation** — if a `rule-violation-instance` is found, scan other in-flight PRs for the same pattern and offer to propagate the fix (see [review-gates.md](review-gates.md)). This stage only runs in Batch mode, when 2+ issues are in flight.
4. If issues are found at Stage 1 or 2 → re-run the implementer to fix → re-review (max 2 fix rounds per stage).

Run each reviewer as a separate agent instance with fresh context where the environment supports one; otherwise self-review and mark the gate result `SELF-REVIEWED` — see review-gates.md's "Reviewer Dispatch" note for the exact procedure and marker semantics.

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
  git worktree remove .worktrees/<branch-name>
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
