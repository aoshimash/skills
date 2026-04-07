# Annotation Cycle

## Purpose

Refine the plan through iterative inline annotation. This is the highest-value phase: the user injects domain knowledge, corrects assumptions, and sharpens scope directly in the document. Chat-based steering is imprecise; document-based iteration allows indexed, precise corrections.

## How It Works

The plan file acts as **shared mutable state** between the user and Claude:

```
Claude writes plan.md
    ↓
User opens in editor, adds inline notes
    ↓
Claude reads plan.md, addresses every note
    ↓
User reviews updated plan
    ↓
Repeat until no notes remain
```

## Annotation Format

The user adds HTML comments anywhere in the plan file:

```markdown
### Task 3: Add search endpoint

**Approach:**
Use a full-text search query against the users table.
<!-- NOTE: use pg_trgm index, not full-text search. We already have it set up. -->

**Files:**
- `src/api/users.ts` — Modify: add search handler
<!-- NOTE: this should be in src/api/routes/users.ts, not src/api/users.ts -->
```

Annotations may also appear as:
- `<!-- TODO: ... -->`
- `<!-- REMOVE: ... -->`
- `<!-- QUESTION: ... -->`
- Any text inside `<!-- ... -->` that was not in the previous version

## Procedure

### 1. Prompt the User

After presenting the plan:

> "Open `<plan-file>` in your editor and add inline notes (`<!-- NOTE: ... -->`) to correct, reject, or refine any part. Tell me when you're ready for me to address them."

### 2. Address Annotations

When the user signals readiness:

1. Read the plan file.
2. Find all annotations (HTML comments not present in the original plan).
3. For each annotation:
   - **NOTE / correction**: Incorporate the change directly. Remove the annotation.
   - **REMOVE**: Delete the indicated section. Remove the annotation.
   - **TODO**: Flesh out the indicated section. Remove the annotation.
   - **QUESTION**: Answer inline (briefly) or ask a clarifying question via `AskUserQuestion`. Remove the annotation after resolution.
4. After addressing all annotations, re-run the "boring implementation" test on all tasks.
5. Update the plan file with changes.

### 3. Present Changes

Summarize what changed:

> "Addressed N annotations:
> - Task 3: switched to pg_trgm index per your note
> - Task 3: corrected file path to src/api/routes/users.ts
> - Task 5: removed caching section as requested
>
> Updated plan is at `<path>`. Review and add more notes if needed, or approve to proceed."

### 4. Gate

Use `AskUserQuestion` with options:
- **Approve** — Plan is ready to convert to issues.
- **Another round** — User will add more annotations.
- **Abort** — Stop.

If "Another round", return to step 1.

**Do NOT create issues until the user explicitly approves.**

## Quality Checks Before Approval

Before presenting the final gate, verify:

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | All annotations resolved | No `<!-- ... -->` notes remain in the file |
| 2 | Boring implementation test | Every task passes all 6 criteria from the design phase |
| 3 | Dependency graph consistent | All referenced task dependencies exist and form a DAG |
| 4 | No scope creep | Tasks match the agreed design decisions |
| 5 | Code examples up to date | Annotations that changed approach are reflected in code examples |

If any check fails, fix it before presenting the gate.
