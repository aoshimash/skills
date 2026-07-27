# Research, Design, and the Plan File

## Purpose

Used in the **Design Flow** (SKILL.md D1) to turn a stated goal into one
consolidated plan file. Research grounds the design in reality; the design
settles the structural decisions and cuts the work into tasks; whatever
genuinely needs the user becomes an embedded open question instead of a stop.

Everything lands in a single file — there is no separate research file, and no
research-approval gate. The user's first look at this work is the plan file
itself, refined through the annotation cycle.

## 1. Research the Codebase

Explore broadly, then deeply, over multiple rounds of Grep/Glob/Read:

1. **Related files** — keywords, class names, routes, components related to
   the feature. Follow imports and dependencies.
2. **Architecture patterns** — directory conventions, naming, abstraction
   layers, framework usage.
3. **Existing similar features** — the closest existing feature to what is
   being designed, how it was built, and why.
4. **Dependencies** — packages/modules involved, version constraints,
   compatibility.
5. **Test patterns** — framework, location, naming, mocking strategy.
6. **Project agent instructions** (e.g. `AGENTS.md` / `CLAUDE.md`) — coding
   standards, preferred libraries, workflow rules, decision principles.
7. **Recent git history** — commits and branches in the area, including
   in-progress or abandoned work.
8. **Configuration** — CI/CD, build, and environment setup that affects the
   feature.

Record what an implementer could not learn by reading the code: past
decisions, business rules, constraints, and traps (hidden coupling, caching,
ordering requirements, API quirks). These findings are the durable half of
this flow — they are posted to the tracker as the research comment in
[issue-creation.md](issue-creation.md).

## 2. Design Against the Findings

1. **Settle the structural decisions.** Anything with high reversal cost, or
   that must stay consistent across sibling tasks — the shape of the split,
   externally visible contracts, cross-cutting conventions — is decided here
   and recorded in `## Design Decisions` with its rationale. Local, reversible
   decisions (naming, tactical choices among equivalent designs) are
   deliberately left to implementation time; do not record them and do not ask
   about them.
2. **Turn genuine unknowns into open questions.** When a structural choice
   depends on information only the user has, or 2+ approaches are valid and
   the choice changes the shape of the work, write it into `## Open Questions`
   with options, trade-offs, and a recommendation — do not stop to ask. The
   user answers inline during the annotation cycle.
3. **Decompose into tasks**, one task per potential sub-issue:

| Field | Requirement |
|-------|-------------|
| **Title** | Imperative form, concise (e.g. "Add user search endpoint") |
| **Purpose** | Why this task exists, in context of the whole feature |
| **Scope** | The desired end state and explicit boundaries (what is NOT included). Two engineers reading it would agree on what to build |
| **Notes** | Non-obvious constraints, the design decisions that bind this task, useful research findings (current state, gotchas). No implementation steps, file-edit lists, or code examples |
| **Acceptance Criteria** | Binary pass/fail conditions |
| **Dependencies** | Which other tasks must complete first |
| **Estimated size** | Small (< 30 min) / Medium (30-60 min) / Large (1-2 hours). If Large, consider splitting further |

**Notes is optional in form but mandatory in substance**: any pitfall
discovered during research that an implementer could plausibly fall into MUST
be recorded there as a constraint, never as implementation code. With
implementation detail excluded from issues, recorded constraints are the
channel that carries design-time knowledge to implementation time; an
unrecorded pitfall is a trap left armed for whoever implements the task.

If decomposition yields **exactly one task** at Small or Medium size, do not
force a hierarchy: note it, and finish through the Lightweight Flow's
draft/approve steps (SKILL.md L3-L4) using that task as the issue content.

## 3. Task Quality Checks

Before writing the plan — and again after every annotation round — verify each
task against:

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | Structural decisions recorded | Every choice with high reversal cost or cross-task consequence that this task depends on is stated in Design Decisions or the task's Notes — nothing structural is left implicit |
| 2 | Scope is unambiguous | Two engineers reading the task would agree on what to build and what not to build |
| 3 | No implementation prescription | No implementation steps, file-edit lists, or code examples — and no local, reversible decision pre-made on the implementer's behalf |
| 4 | AC is testable | Each criterion has a clear binary outcome |
| 5 | Dependencies are explicit | Blocking relationships are stated, not implied |
| 6 | Size is appropriate | No task is larger than ~2 hours of work |
| 7 | Constraints carried | Every pitfall from research that touches this task appears in its Notes |

If a task fails, split it, tighten its scope, or record the missing decision
until it passes. A task that still needs an answer from the user is not fixed
by guessing — add an open question.

## 4. Write the Plan File

Write to `<plan-dir>/YYYY-MM-DD-<topic-slug>.md`:

```markdown
# Plan: <Feature Name>

Date: YYYY-MM-DD
Status: Draft

## Goal

<1-2 sentence description of what this feature achieves>

## Research Findings

<!-- Posted to the tracker as the research comment after issue creation. -->

### Relevant Files

| File | Role | Notes |
|------|------|-------|
| `path/to/file.ts` | Description | Key observations |

### Architecture

<How the relevant part of the system is structured; data flow if applicable>

### Conventions

<Naming, directory structure, error handling, logging — what this work must follow>

### Dependencies

<Packages, modules, services involved; version constraints>

### Test Patterns

<Framework, file location, naming, mocking approach>

### Existing Similar Features

<The closest existing feature, how it was implemented, what can be referenced>

### Constraints & Risks

<Traps, compatibility concerns, performance and security considerations>

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| <decision point> | <what was chosen> | <why> |

## Open Questions

<!-- Answer inline, directly under each question. Delete the section if empty. -->

1. **<question>**
   - Option A: <how it works> — <trade-offs>
   - Option B: <how it works> — <trade-offs>
   - Recommendation: <A or B> because <reason>
   - **Answer:**

## Tasks

### Task 1: <Title>

**Purpose:** <why this task>
**Dependencies:** None | Task N
**Size:** Small / Medium / Large

**Scope:**
<desired end state and explicit boundaries — what is included and what is not>

**Notes:**
<non-obvious constraints, binding design decisions, useful research findings>

**Acceptance Criteria:**
- [ ] <criterion 1>
- [ ] <criterion 2>

---

### Task 2: <Title>
...

## Dependency Graph

<ASCII visualization of task dependencies>

## Split Proposal

<ASCII tree of the proposed hierarchy with sizes and dependencies — see the
Split Proposal section in SKILL.md. Approved as part of the final approval in
the annotation cycle, not as a separate gate.>

## Out of Scope

- <explicitly excluded items>
```

## 5. Present the Plan

Present the path and hand straight over to the annotation cycle:

> "The plan is at `<path>`. It carries the research findings, the design
> decisions, the task breakdown, and the proposed split. Open it, answer the
> open questions inline under each one, and add inline notes
> (`<!-- NOTE: ... -->`) anywhere you want something changed — including the
> Split Proposal. Tell me when the notes are ready."

Do not ask for approval here — the single approval comes at the end of the
annotation cycle.
