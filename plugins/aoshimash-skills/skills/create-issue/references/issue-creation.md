# Issue Creation

## Purpose

This procedure is used in the **Design Flow** (see SKILL.md Step 2) to convert the approved plan into issues on the tracker. After this phase, the plan and research files are deleted — the issues hold all information needed for implementation.

## Procedure

### 0. Confirm the Split Proposal

Splitting is always a user-confirmed proposal, never automatic — even after the annotation cycle is approved. Before creating anything, present the plan's `## Split Proposal` section (see SKILL.md "Split Proposal" for the criteria) as an ASCII tree with sizes and dependencies, for example:

```
Proposed hierarchy:
  Parent — Add user search feature
  ├─ Add pg_trgm index to users table (Small)
  ├─ Create search endpoint (Medium, blocked by 1)
  ├─ Add search UI component (Small, blocked by 1)
  │   ├─ Add search input component (Small)      ← proposed grandchild split
  │   └─ Add results list component (Small)       ← proposed grandchild split
  └─ Add search integration tests (Small, blocked by 2, 3)
```

Then use `AskUserQuestion`:
- **Create parent + sub-issues** (mark "(Recommended)" when 2+ tasks are independently implementable and reviewable) — proceed to Step 1.
- **Create a single issue** — skip the hierarchy. Compose ONE issue using the Feature Request or Technical Task template from [templates.md](templates.md), with the plan's Goal as Motivation/Proposal and the task breakdown included as a `## Task Breakdown` section (titles, files, approach, AC per task, as subsections). Then go directly to Step 4 (Clean Up).
- **Adjust the breakdown** — return to the Design phase's Task Decomposition step with the user's feedback, then re-present this gate.

Do NOT create parent/sub-issues, or grandchild issues, without this explicit confirmation.

### 1. Create the Parent Issue

The parent issue represents the entire feature/initiative. Compose it using the **Parent Issue** template from [templates.md](templates.md), filled in from the plan:

- Summary — 1-2 sentences
- Motivation — from the design discussion
- Background — from research, non-obvious context only (no implementation details)
- Proposal — the plan's Goal section
- Task Overview — the task table with dependencies and sizes
- Design Decisions — from the plan's Design Decisions table

Create the parent issue using the platform CLI. Record the issue number.

### 2. Create Sub-Issues

For each task in the plan, create a sub-issue using the **Sub-Issue** template from [templates.md](templates.md):

- Title — the task title (imperative form, under 70 chars)
- `Parent: #<parent-issue-number>`
- Motivation — why this task exists, in context of the parent feature
- Background / Files — task-specific context and exact file paths
- Implementation Approach — the plan's concrete approach with code examples
- Acceptance Criteria — from the task
- Dependencies — `Blocked by: #<issue-number>` for any blocking sub-issues

Create each sub-issue using the platform CLI. As you create each sub-issue, record the mapping from its plan-local index (the `#` column value in the Task Overview table: 1 for the first task, 2 for the second, etc.) to the real issue number assigned by the platform. You will need this mapping in Step 2.5.

**Grandchild issues**: if the user approved a nested split for a task in Step 0 (that task was itself decomposed further), treat that task as a **child that is also a parent**: create it using the Sub-Issue template (with `Parent: #<parent-issue-number>`) plus its own `## Task Overview` table for its grandchildren, then create each grandchild using the Sub-Issue template with `Parent: #<child-issue-number>`. Link grandchildren to the child the same way children are linked to the parent (see platform guide). Maximum depth is 3 levels (parent → child → grandchild) — if a grandchild would still be Large, return to Task Decomposition and redesign instead of nesting further. For each child-that-is-also-a-parent, maintain a separate local-to-real mapping for its grandchildren, to be used in Step 2.5.

### 2.5. Update Task Overview Tables

After all sub-issues (and grandchild issues) are created, the plan-local placeholder references in Task Overview tables must be replaced with real issue numbers. Platforms like GitHub auto-link any `#N` in issue bodies — leaving plan-local numbers like `#1` causes them to link to unrelated issues that happen to hold those numbers in the repository.

**Parent issue update:**

Using the local-to-real mapping collected in Step 2:

1. Fetch the current parent issue body (e.g., `gh issue view <number> --json body -q '.body'`).
2. In the `## Task Overview` table:
   - **Task column**: prepend the real issue reference to each title — change `<title>` to `#<real-number> — <title>`
   - **Dependencies column**: replace each plan-local reference (`#1`, `#2`, etc.) with the corresponding real issue number (`#259`, `#260`, etc.)
   - Replace only within the Task Overview table rows — do not modify other sections of the body (e.g., References, Background).
3. Update the parent issue body using the platform CLI (e.g., `gh issue edit <parent-number> --body "$(updated body)"`).

Example — before (plan-local numbers):

| # | Task | Dependencies | Size |
|---|------|--------------|------|
| 1 | Add pg_trgm index | — | Small |
| 2 | Create search endpoint | #1 | Medium |
| 3 | Add search UI | #1 | Small |
| 4 | Add integration tests | #2, #3 | Medium |

Example — after (real issue numbers #259–#262):

| # | Task | Dependencies | Size |
|---|------|--------------|------|
| 1 | #259 — Add pg_trgm index | — | Small |
| 2 | #260 — Create search endpoint | #259 | Medium |
| 3 | #261 — Add search UI | #259 | Small |
| 4 | #262 — Add integration tests | #260, #261 | Medium |

**Grandchild case:**

If any child issue was itself decomposed into grandchild issues and has its own `## Task Overview` table, apply the same update to that child issue's body after all its grandchildren are created, using the grandchild local-to-real mapping collected for that child in Step 2.

### 3. Link Issues to Their Parent

After all sub-issues (and any grandchild issues) are created, establish the hierarchy:

- **GitHub**: Use sub-issue linking (see platform guide) — link each child to its parent, and each grandchild to its child.
- **GitLab**: Use parent-child relationship or related issues.
- **Backlog**: Use the parent issue field.

Also establish dependency links between sibling issues where specified.

### 4. Clean Up Local Files

Delete the temporary plan and research files:

```bash
rm <plan-dir>/YYYY-MM-DD-<topic-slug>.md
rm <plan-dir>/research-<topic-slug>.md
```

If the plan directory is now empty, delete it too (unless it's a permanent project directory like `docs/plans/`).

### 5. Return Result

Output:
- Parent issue URL (or the single issue URL, if the user declined the split)
- List of sub-issue and grandchild-issue URLs with their titles and dependency relationships
- The dependency graph (ASCII), including any grandchild level

```
Created issue hierarchy:
  Parent: #100 — Add user search feature
  ├─ #101 — Add pg_trgm index to users table
  ├─ #102 — Create search endpoint (blocked by #101)
  ├─ #103 — Add search UI component (blocked by #101)
  │   ├─ #106 — Add search input component
  │   └─ #107 — Add results list component
  └─ #104 — Add search integration tests (blocked by #102, #103)
```
