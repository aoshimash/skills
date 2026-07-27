# Annotation Cycle

## Purpose

Refine the plan through iterative inline annotation, and close the Design Flow
with its single approval. This is the round-trip batching mechanism of the
flow: one annotated file carries dozens of corrections and every answer to the
plan's open questions in one exchange, where chat-based steering would need
one exchange per correction.

## How It Works

The plan file acts as **shared mutable state** between the user and the agent:

```
Agent writes plan.md (research + design + open questions + split proposal)
    ↓
User opens it, answers the open questions inline, adds notes
    ↓
Agent reads plan.md, addresses every note and every answer
    ↓
User reviews the updated plan
    ↓
Repeat until no notes remain → single final approval → issue creation
```

## Annotation Format

**Open questions** are answered in place, on the `**Answer:**` line the plan
file provides:

```markdown
1. **Should search cover archived users?**
   - Option A: active only — simpler index, matches the current list view
   - Option B: include archived behind a filter — more useful for support
   - Recommendation: A, archived search has no requested use case yet
   - **Answer:** B, support asks for this weekly. Filter defaults to off.
```

**Everything else** is annotated with HTML comments anywhere in the file:

```markdown
### Task 3: Add search endpoint

**Scope:**
Users can be searched by name and email via a new API endpoint.
<!-- NOTE: search by name only for now — email search has privacy implications, keep it out of scope. -->

**Acceptance Criteria:**
- [ ] Search results return within 500ms
<!-- NOTE: 500ms is unrealistic for the current dataset; make it 1s -->
```

Annotations may also appear as `<!-- TODO: ... -->`, `<!-- REMOVE: ... -->`,
`<!-- QUESTION: ... -->`, or any text inside `<!-- ... -->` that was not in the
previous version.

## Procedure

### 1. Prompt the User

After the plan file is presented (see [plan-file.md](plan-file.md) step 5),
wait for the user to signal that the notes are ready. Do not poll and do not
ask intermediate questions in chat — anything you would ask belongs in the
file as an open question.

### 2. Address Everything

When the user signals readiness:

1. Read the plan file.
2. Collect (a) every answered open question and (b) every annotation not
   present in the previous version.
3. Resolve each one:
   - **Answered open question**: apply the answer to the design — update
     `## Design Decisions` with the decision and its rationale, rewrite the
     affected task scopes and dependencies, then remove the question from
     `## Open Questions`.
   - **NOTE / correction**: incorporate the change directly. Remove the
     annotation.
   - **REMOVE**: delete the indicated section. Remove the annotation.
   - **TODO**: flesh out the indicated section. Remove the annotation.
   - **QUESTION**: answer inline, briefly. If it cannot be answered without
     the user, convert it into a new numbered open question. Remove the
     annotation.
4. Re-run the task quality checks from [plan-file.md](plan-file.md) step 3 on
   every affected task; re-derive the dependency graph and the Split Proposal
   if the shape of the work changed.
5. Write the updated plan file.

### 3. Present Changes

Summarize what changed, grouped by cause:

> "Addressed 4 notes and 1 answered question:
> - Open Q1 → archived users are searchable behind a filter; recorded as a
>   design decision, Task 3 scope and Task 5 AC updated
> - Task 3: narrowed to name-only search per your note
> - Task 3: relaxed the response-time criterion to 1s
> - Task 5: removed the caching section
>
> Updated plan is at `<path>`."

### 4. Final Approval

Before presenting the approval, verify:

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | All annotations resolved | No `<!-- ... -->` notes remain in the file |
| 2 | All open questions answered | `## Open Questions` is empty or absent — an unanswered question blocks approval |
| 3 | Task quality | Every task passes all 7 checks from plan-file.md step 3 |
| 4 | Dependency graph consistent | Referenced dependencies exist and form a DAG |
| 5 | No scope creep | Tasks match the agreed design decisions and the stated goal |
| 6 | Design Decisions up to date | Every annotation or answer that changed an approach or constraint is reflected in the table and in the affected task scopes |
| 7 | Split Proposal current | The tree matches the current task list, sizes, and dependencies |

Then ask the user to choose (see Environment Adaptation in SKILL.md) — one
approval covering the plan **and** the split:

- **Approve and create issues** — proceed to
  [issue-creation.md](issue-creation.md) with the Split Proposal as written.
- **Another annotation round** — return to step 1.
- **Abort** — stop; leave the plan file in place.

**Do NOT create issues until the user explicitly approves.** If the user wants
a different split, that is an annotation on the `## Split Proposal` section,
not a separate gate.
