# Issue Creation

## Purpose

Convert the approved plan into an issue hierarchy on the tracker. After this phase, the plan and research files are deleted — the issues hold all information needed for implementation.

## Procedure

### 1. Create the Parent Issue

The parent issue represents the entire feature/initiative. Compose it from the plan:

**Title:** Concise feature description (under 70 chars, imperative form)

**Body:**

```markdown
<!-- 1-2 sentence summary of the feature and its purpose -->

## Motivation

<!-- From the design discussion: why this feature matters -->

## Background

<!-- From research: non-obvious context, constraints, past decisions -->
<!-- Do NOT include implementation details here -->

### Related Code

<!-- Key file paths from research that provide context -->

## Proposal

<!-- Desired end state from the plan's Goal section -->

## Task Overview

<!-- Ordered list of sub-issues with dependency relationships -->

| # | Task | Dependencies | Size |
|---|------|--------------|------|
| 1 | <title> | — | Small |
| 2 | <title> | #1 | Medium |
| 3 | <title> | #1 | Small |
| 4 | <title> | #2, #3 | Medium |

## Design Decisions

<!-- From the plan's Design Decisions table -->

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ... | ... | ... |

## References

<!-- Links to related issues, docs, or external resources -->
```

Create the parent issue using the platform CLI. Record the issue number.

### 2. Create Sub-Issues

For each task in the plan, create a sub-issue:

**Title:** The task title from the plan (imperative form, under 70 chars)

**Body:**

```markdown
<!-- 1-2 sentence summary of what this task accomplishes -->

Parent: #<parent-issue-number>

## Motivation

<!-- Why this task exists, in context of the parent feature -->

## Background

<!-- Task-specific context from the plan -->

### Files

<!-- Exact file paths to create or modify -->

| File | Action | Changes |
|------|--------|---------|
| `path/to/file` | Create / Modify | What changes and why |

## Implementation Approach

<!-- From the plan: concrete approach with code examples -->
<!-- This is NOT "how to implement" as imperative instructions -->
<!-- It IS "what the implementation looks like" as reference code -->

## Acceptance Criteria

- [ ] <criterion 1>
- [ ] <criterion 2>

## Dependencies

<!-- Link to blocking issues -->
Blocked by: #<issue-number> <!-- if any -->
```

Create each sub-issue using the platform CLI.

### 3. Link Sub-Issues to Parent

After all sub-issues are created, establish the hierarchy:

- **GitHub**: Use sub-issue linking (see platform guide)
- **GitLab**: Use parent-child relationship or related issues
- **Backlog**: Use parent issue field

Also establish dependency links between sub-issues where specified.

### 4. Clean Up Local Files

Delete the temporary plan and research files:

```bash
rm <plan-dir>/YYYY-MM-DD-<topic-slug>.md
rm <plan-dir>/research-<topic-slug>.md
```

If the plan directory is now empty, delete it too (unless it's a permanent project directory like `docs/plans/`).

### 5. Return Result

Output:
- Parent issue URL
- List of sub-issue URLs with their titles and dependency relationships
- The dependency graph (ASCII)

```
Created issue hierarchy:
  Parent: #100 — Add user search feature
  ├─ #101 — Add pg_trgm index to users table
  ├─ #102 — Create search endpoint (blocked by #101)
  ├─ #103 — Add search UI component (blocked by #101)
  └─ #104 — Add search integration tests (blocked by #102, #103)
```
