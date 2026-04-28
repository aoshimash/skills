---
name: run-sprint
description: >
  Fetch a set of issues, build a dependency graph, and implement them with
  parallel dispatch (git worktrees + subagents) and two-stage review per issue.
  Use when the user says "run sprint", "スプリント実行", "これらの issue を実装",
  "implement these issues", "start the sprint", "issue を順に実装して",
  "sprint を回して", or wants to batch-implement a set of related issues.
---

# Run Sprint

Fetch a set of issues, resolve dependencies, implement them in parallel where possible, and deliver PRs with two-stage review per issue.

## Core Principles

1. **Issues are the source of truth** — Each issue defines the scope. Do not add unrelated changes. Do not deviate from the issue's acceptance criteria.
2. **Dependency-driven parallelism** — Issues with no unresolved dependencies run in parallel. Issues with dependencies wait. The dependency graph is the scheduler.
3. **Worktree isolation** — Each issue gets its own git worktree. No cross-contamination between parallel implementations.
4. **Two-stage review with pattern propagation** — Every completed issue goes through spec compliance review (does the diff match the issue?) then code quality review. If a `rule-violation-instance` is found, other in-flight PRs are scanned for the same pattern and the user is offered a fix. All stages happen before marking complete.
5. **Fail fast, report clearly** — If an issue fails after retries, mark it blocked and continue with independent issues. Never block the entire sprint on one failure.

## Workflow

### Phase 0: Collect Issues

1. Determine the issue source. Use `AskUserQuestion` if unclear:
   - **Parent issue** — Fetch all sub-issues of a given issue number/URL
   - **Milestone** — Fetch all open issues in a milestone
   - **Label** — Fetch all open issues with a given label
   - **Manual list** — User provides a list of issue numbers/URLs
2. Detect the **issue tracker** platform (check CLAUDE.md → git remote → ask). Load the platform guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog: [references/platform-backlog.md](references/platform-backlog.md)
3. Fetch all issues. For each, extract: number, title, body, state, labels.
4. Filter: skip closed/merged issues. If all issues are closed, inform the user and stop.

### Phase 1: Dependency Graph

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**

1. Parse each issue body for dependency declarations:
   - `Blocked by: #N` or `Blocked by #N`
   - `Depends on: #N` or `Depends on #N`
   - Platform-specific blocking links (GitHub sub-issue blocked-by, GitLab issue links)
2. Build a DAG (directed acyclic graph) of issue dependencies.
3. Detect circular dependencies. If found, present them to the user and ask how to resolve (break a link or abort).
4. Display the dependency graph:

```
Sprint: 6 issues, 3 parallelizable groups

Group 1 (parallel): #101, #102
Group 2 (parallel): #103, #104  ← after #101
Group 3 (sequential): #105      ← after #103, #104
                      #106      ← after #105
```

5. Use `AskUserQuestion` — "Proceed with this execution plan?" with options: Approve / Reorder / Abort.

### Phase 2: Execution Loop

See [references/workflow.md](references/workflow.md) for the detailed procedure.

**Summary:**

Repeat until all issues are completed or all remaining issues are blocked:

1. **Identify ready issues** — Issues whose dependencies are all completed.
2. **Dispatch in parallel** — For each ready issue, launch a subagent:
   - Create a git worktree for isolation
   - Subagent reads the issue, plans, implements, self-reviews, commits, creates PR
   - See [references/workflow.md](references/workflow.md) for the per-issue implementation procedure
3. **Two-stage review** — After each issue's PR is created:
   - Stage 1: Dispatch a **spec compliance reviewer** subagent (see [references/review-gates.md](references/review-gates.md))
   - Stage 2: Dispatch a **code quality reviewer** subagent (see [references/review-gates.md](references/review-gates.md))
   - Stage 2.5: **Pattern Propagation** — If a `rule-violation-instance` is found, scan other in-flight PRs for the same pattern and offer to propagate the fix (see [references/review-gates.md](references/review-gates.md))
   - If issues found → implementer subagent fixes → re-review (max 2 fix rounds)
4. **Update DAG** — Mark completed issues. Check if new issues are now unblocked.
5. **Handle failures** — If an issue fails after retries:
   - Mark it as BLOCKED with reason
   - Also mark all issues that depend on it as SKIPPED (transitively)
   - Continue with remaining independent issues

### Phase 3: Summary

After all issues are processed:

1. Present a summary table:

```
Sprint Complete: N/M issues implemented

| Issue | Title | Status | PR |
|-------|-------|--------|----|
| #101 | Add search index | ✅ Done | #201 |
| #102 | Create endpoint | ✅ Done | #202 |
| #103 | Add UI component | ✅ Done | #203 |
| #104 | Error handling | ❌ Blocked | — |
| #105 | Integration tests | ⏭️ Skipped (dep) | — |
```

2. For blocked issues, explain what went wrong and suggest next steps.
3. If the issue tracker supports it, post a summary comment on the parent issue.

## References

- [references/workflow.md](references/workflow.md) — Dependency graph and per-issue execution procedure
- [references/review-gates.md](references/review-gates.md) — Two-stage review procedure
- [references/platform-github.md](references/platform-github.md) — GitHub issue and PR commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab issue and MR commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog issue commands
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
