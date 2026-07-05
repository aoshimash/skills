# Design Phase

## Purpose

This procedure is used in the **Design Flow** (see SKILL.md Step 2) to transform research into a concrete, implementable design through structured brainstorming with the user. The output is a plan file with a task breakdown, and — if the user approves — a proposal to split the work into a parent + sub-issues.

## Procedure

### 1. Brainstorming

Ask clarifying questions **one at a time**. Build on each answer. Use research findings to ask informed, specific questions rather than generic ones.

Topics to cover (skip what is already clear):
- What is the desired user-facing behavior?
- What are the boundaries of scope? (What is explicitly NOT included?)
- Are there performance requirements?
- Are there backward-compatibility constraints?
- How should errors be handled?
- What is the migration/rollout strategy (if applicable)?

### 2. Approach Selection

When multiple valid approaches exist:

1. Propose 2-3 approaches, each with:
   - A short label
   - How it works (1-2 sentences)
   - Pros and cons
   - Mark the recommended approach with "(Recommended)"
2. Use `AskUserQuestion` with numbered options.
3. Wait for the user's choice.
4. If the user selects "Other" and provides free text, incorporate it directly — do NOT re-present new options.

### 3. Task Decomposition

Break the design into tasks where each task = one potential sub-issue. For each task:

| Field | Requirement |
|-------|-------------|
| **Title** | Imperative form, concise (e.g., "Add user search endpoint") |
| **Purpose** | Why this task exists, in context of the whole feature |
| **Files** | Exact file paths to create or modify |
| **Approach** | Concrete implementation with code examples. No placeholders, no "add validation here" |
| **Acceptance Criteria** | Binary pass/fail conditions |
| **Dependencies** | Which other tasks must complete first |
| **Estimated size** | Small (< 30 min) / Medium (30-60 min) / Large (1-2 hours). If Large, consider splitting further |

If decomposition yields **exactly one task** at Small or Medium size, do not force a hierarchy — note this to the user and fall back to a single issue: skip to the Split Proposal step, which will recommend a single issue in this case, then finish via the Lightweight Flow's draft/self-eval/create steps (SKILL.md Steps L4–L6) using that one task as the issue content.

### 4. The "Boring Implementation" Test

Before writing the plan, verify each task against:

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | No design decisions | Someone can implement by following instructions mechanically |
| 2 | Code examples present | Key implementation shown with actual code, not descriptions |
| 3 | Files are specific | Exact paths listed, not "relevant files" |
| 4 | AC is testable | Each criterion has a clear binary outcome |
| 5 | Dependencies are explicit | Blocking relationships are stated, not implied |
| 6 | Size is appropriate | No task is larger than ~2 hours of work |

If any task fails, split or refine it until it passes.

### 5. Write the Plan File

Write to `<plan-dir>/YYYY-MM-DD-<topic-slug>.md`:

```markdown
# Plan: <Feature Name>

Date: YYYY-MM-DD
Status: Draft

## Goal

<1-2 sentence description of what this feature achieves>

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| <decision point> | <what was chosen> | <why> |

## Tasks

### Task 1: <Title>

**Purpose:** <why this task>
**Dependencies:** None | Task N
**Size:** Small / Medium / Large

**Files:**
- `path/to/file.ts` — Create / Modify: <what changes>

**Approach:**
<concrete implementation with code examples>

**Acceptance Criteria:**
- [ ] <criterion 1>
- [ ] <criterion 2>

---

### Task 2: <Title>
...

## Dependency Graph

<ASCII visualization of task dependencies>

## Split Proposal

<See Split Proposal section below — filled in after task decomposition>

## Out of Scope

- <explicitly excluded items>
```

### 6. Split Proposal

See the **Split Proposal** section in SKILL.md for the full decision criteria. Summary:

1. Evaluate the task breakdown against the split criteria (independent tasks → parent + sub-issues; a task still Large after refinement → nested grandchild issues on platforms that support it).
2. Fill in the plan's `## Split Proposal` section with the proposed hierarchy as an ASCII tree, sizes, and dependencies.
3. Do NOT ask for approval yet — the proposal is presented to the user together with the rest of the plan in Step 7, and confirmed later at the Split Proposal gate (after the Annotation Cycle, before Issue Creation).

### 7. Present the Plan

Present the plan file path to the user:

> "Plan is written to `<path>`. Please review it before we start the annotation cycle. You can open it in your editor and add inline notes (HTML comments like `<!-- NOTE: ... -->`) to any part you want to change, including the Split Proposal."

Proceed to the Annotation Cycle phase.
