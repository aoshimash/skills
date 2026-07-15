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
2. Ask the user to choose (see Environment Adaptation in SKILL.md) with numbered options.
3. Wait for the user's choice.
4. If the user selects "Other" and provides free text, incorporate it directly — do NOT re-present new options.

### 3. Task Decomposition

Break the design into tasks where each task = one potential sub-issue. For each task:

| Field | Requirement |
|-------|-------------|
| **Title** | Imperative form, concise (e.g., "Add user search endpoint") |
| **Purpose** | Why this task exists, in context of the whole feature |
| **Scope** | The desired end state and explicit boundaries (what is NOT included). Two engineers reading it would agree on what to build |
| **Notes** | Optional: non-obvious constraints, relevant design decisions, useful findings from research (current state, gotchas). No implementation steps, file-edit lists, or code examples |
| **Acceptance Criteria** | Binary pass/fail conditions |
| **Dependencies** | Which other tasks must complete first |
| **Estimated size** | Small (< 30 min) / Medium (30-60 min) / Large (1-2 hours). If Large, consider splitting further |

**Notes is optional in form but mandatory in substance**: any pitfall discovered during research that an implementer could plausibly fall into (hidden coupling, caching behavior, ordering requirements, API quirks) MUST be recorded there — as a constraint, never as implementation code. With implementation detail excluded from issues, recorded constraints are the channel that carries design-time knowledge to implementation time; an unrecorded pitfall is a trap left armed for whoever implements the task.

If decomposition yields **exactly one task** at Small or Medium size, do not force a hierarchy — note this to the user and fall back to a single issue: skip to the Split Proposal step, which will recommend a single issue in this case, then finish via the Lightweight Flow's draft/self-eval/create steps (SKILL.md Steps L4–L6) using that one task as the issue content.

### 4. The "Boring Scope" Test

Implementation must be boring — but the boringness comes from tight scope and recorded decisions, not from prescribing the implementation. Before writing the plan, verify each task against:

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | No open design decisions | Every choice the task depends on is recorded in Design Decisions — nothing is left to the implementer's judgment |
| 2 | Scope is unambiguous | Two engineers reading the task would agree on what to build and what not to build |
| 3 | No implementation prescription | The task contains no implementation steps, file-edit lists, or code examples — the implementer plans those at implementation time |
| 4 | AC is testable | Each criterion has a clear binary outcome |
| 5 | Dependencies are explicit | Blocking relationships are stated, not implied |
| 6 | Size is appropriate | No task is larger than ~2 hours of work |

If any task fails, split it, tighten its scope, or record the missing decision until it passes.

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

**Scope:**
<desired end state and explicit boundaries — what is included and what is not>

**Notes:** (optional)
<non-obvious constraints, relevant design decisions, useful findings from research>

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
