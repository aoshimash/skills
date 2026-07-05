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

Create each sub-issue using the platform CLI.

**Grandchild issues**: if the user approved a nested split for a task in Step 0 (that task was itself decomposed further), treat that task as a **child that is also a parent**: create it using the Sub-Issue template (with `Parent: #<parent-issue-number>`) plus its own `## Task Overview` table for its grandchildren, then create each grandchild using the Sub-Issue template with `Parent: #<child-issue-number>`. Link grandchildren to the child the same way children are linked to the parent (see platform guide). Maximum depth is 3 levels (parent → child → grandchild) — if a grandchild would still be Large, return to Task Decomposition and redesign instead of nesting further.

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
