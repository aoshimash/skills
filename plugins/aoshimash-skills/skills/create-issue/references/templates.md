# Issue Templates

## Table of Contents

- [Bug Report](#bug-report)
- [Feature Request](#feature-request)
- [Technical Task](#technical-task)
- [Operation](#operation)
- [Parent Issue](#parent-issue)
- [Sub-Issue](#sub-issue)

---

## Bug Report

```markdown
<!-- 1-2 sentence summary of the bug and its impact -->

## Motivation

<!-- Why this bug matters: user impact, business impact, severity -->

## Background

<!-- Background information not obvious from the code -->
<!-- Constraints, prior decisions, related discussions -->

### Steps to Reproduce

1.
2.
3.

### Expected Behavior

### Actual Behavior

### Related Code

<!-- File paths and brief description of relevant areas -->

## Proposal

<!-- What needs to be fixed: the desired end state -->

## Acceptance Criteria

- [ ]
- [ ]

## References

<!-- Related issues, PRs, docs, error logs -->
```

---

## Feature Request

```markdown
<!-- 1-2 sentence summary of what is being requested and why -->

## Motivation

<!-- User need, business goal, pain point being solved -->

## Background

<!-- Current state, constraints, business rules -->
<!-- Information not obvious from the code -->

### Current Behavior

<!-- How things work today (if applicable) -->

### Related Code

<!-- File paths and brief description of relevant areas -->

## Proposal

<!-- What should be achieved: the desired outcome -->
<!-- Not HOW to implement it, but WHAT the result should be -->

## Acceptance Criteria

- [ ]
- [ ]

## References

<!-- Related issues, PRs, specs, designs, user feedback -->
```

---

## Technical Task

```markdown
<!-- 1-2 sentence summary of the task and its purpose -->

## Motivation

<!-- Technical motivation: tech debt, performance, maintainability, security -->

## Background

<!-- Current architecture/design and why it exists -->
<!-- Constraints, dependencies, past decisions -->

### Current State

<!-- Code analysis: relevant files, current implementation, metrics -->

### Related Code

<!-- File paths with brief descriptions -->

## Proposal

<!-- What should be achieved technically -->
<!-- Define the end state, not the implementation steps -->

## Acceptance Criteria

- [ ]
- [ ]

## References

<!-- Related issues, PRs, ADRs, benchmarks, monitoring dashboards -->
```

---

## Operation

```markdown
<!-- 1-2 sentence summary of the operation and its purpose -->

## Motivation

<!-- Why this operation is needed: business need, operational requirement -->

## Background

<!-- Context about the current operational process -->
<!-- Constraints, dependencies, timing requirements -->

### Related Code

<!-- File paths and brief description of relevant areas -->

## Proposal

<!-- What should be achieved operationally -->

## Procedure

<!-- Step-by-step procedure to complete the operation -->
<!-- Include pre-conditions, execution steps, and post-conditions -->

1. **Pre-conditions**:
   -

2. **Steps**:
   1.
   2.
   3.

3. **Post-conditions / Verification**:
   -

## Acceptance Criteria

- [ ]
- [ ]

## References

<!-- Related issues, runbooks, operational docs -->
```

---

## Parent Issue

Used in the Design Flow to represent an entire feature/initiative that has been decomposed into sub-issues.

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

> **Note**: The Task Overview table is written with plan-local numbers at creation time (`#1`, `#2`, etc. in the Dependencies column). Step 3.5 of [issue-creation.md](issue-creation.md) updates the table with real issue numbers after sub-issues are created.

---

## Sub-Issue

Used in the Design Flow for each task in the plan. Sub-issues follow the same reader-agnostic structure as every other issue this skill creates: motivation, background, proposal, acceptance criteria — never implementation steps, file-edit lists, or code examples. A sub-issue may itself be a **parent** when a task was further split into grandchild issues (nested sub-issues) — in that case its body also includes a Task Overview table for its own children, following the Parent Issue template above.

```markdown
<!-- 1-2 sentence summary of what this task accomplishes -->

Parent: #<parent-issue-number>

## Motivation

<!-- Why this task exists, in context of the parent feature -->

## Background

<!-- Task-specific context from the plan: non-obvious constraints, -->
<!-- relevant design decisions, useful findings from research -->

### Related Code

<!-- File paths as factual current state, not a list of files to edit -->

## Proposal

<!-- The task's desired end state and explicit scope boundaries -->
<!-- WHAT the result should be, never HOW to implement it -->

## Acceptance Criteria

- [ ] <criterion 1>
- [ ] <criterion 2>

## Dependencies

<!-- Link to blocking issues -->
Blocked by: #<issue-number> <!-- if any -->
```
