---
name: design-sprint
description: >
  Research a codebase deeply, design a feature through brainstorming, refine the
  plan via annotation cycles, and create an issue hierarchy (parent + sub-issues
  with dependencies). Use when the user says "design sprint", "スプリント設計",
  "機能を設計して issue に分解", "plan and create issues", "design and decompose",
  "この機能を設計して", or describes a feature that needs to be broken down into
  implementable issues.
---

# Design Sprint

Research the codebase, design a feature through iterative refinement, and create an issue hierarchy ready for implementation by humans or AI.

## Core Principles

1. **Research before design** — Never design without deeply understanding the codebase first. Produce a written research artifact, not a verbal summary.
2. **Plan as shared mutable state** — The plan lives in a local markdown file that the user can annotate inline. Chat-based steering is imprecise; document-based iteration is not.
3. **Implementation must be boring** — Each sub-issue must be implementable without creative decisions. If a sub-issue requires design judgment, it is not decomposed enough.
4. **Issues are the deliverable** — The final output is an issue hierarchy on the tracker, not a local document. Local files are temporary working artifacts.
5. **Hard gates** — Do not proceed to the next phase without explicit user approval.

## Workflow

### Phase 0: Setup

1. Detect the **issue tracker** platform (check CLAUDE.md `## Issue Tracker` → git remote → ask user). Load the platform guide:
   - GitHub: [references/platform-github.md](references/platform-github.md)
   - GitLab: [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog: [references/platform-backlog.md](references/platform-backlog.md)
2. Identify the **feature or initiative** to design. If unclear, ask the user to describe the goal in 1-2 sentences.
3. Determine the **plan directory**. Check in order:
   1. CLAUDE.md for a configured plan directory (e.g., `docs/plans/`)
   2. If not configured, use `docs/plans/` and create it if needed
   3. Plan files are named: `YYYY-MM-DD-<topic-slug>.md` (e.g., `2026-04-07-user-search.md`)

### Phase 1: Research

See [references/research.md](references/research.md) for the detailed procedure.

**Summary:**

1. Investigate the codebase deeply — related files, architecture patterns, conventions, dependencies, test patterns, CLAUDE.md rules, recent git history.
2. Write findings to `<plan-dir>/research-<topic-slug>.md`. Include: relevant file paths, current architecture, conventions, constraints, dependencies, and potential risks.
3. Present the research file to the user.
4. **Hard Gate:** Use `AskUserQuestion` — "Review the research file and confirm it captures the relevant context" with options: Approve / Add notes / Abort. If the user adds notes, update the research file and re-present.

### Phase 2: Design

See [references/design.md](references/design.md) for the detailed procedure.

**Summary:**

1. Ask clarifying questions **one at a time** to understand the feature's goals, constraints, and scope. Use the research findings to ask informed questions.
2. When 2+ valid approaches exist, propose each with trade-offs and a recommendation. Use `AskUserQuestion` with numbered options. Wait for the user's choice.
3. After design decisions are resolved, write the plan to `<plan-dir>/YYYY-MM-DD-<topic-slug>.md` with this structure:
   - Goal (1-2 sentences)
   - Design decisions (what was chosen and why)
   - Task breakdown (each task = one sub-issue, with: purpose, files to change, approach with code examples, acceptance criteria, dependencies)
4. Each task must pass the **"boring implementation" test**: can someone implement it by following the instructions mechanically, with zero design judgment?

### Phase 3: Annotation Cycle

See [references/annotation-cycle.md](references/annotation-cycle.md) for the detailed procedure.

**Summary:**

1. Tell the user: "Open `<plan-file>` in your editor and add inline notes (e.g., `<!-- NOTE: ... -->`) to correct, reject, or refine any part. When done, tell me to address the notes."
2. When the user signals readiness, read the plan file and address every annotation:
   - If a note rejects an approach → replace with the user's direction
   - If a note adds a constraint → incorporate it
   - If a note asks a question → answer inline or ask a clarifying question
3. After addressing all notes, re-run the "boring implementation" test on each task.
4. Write the updated plan and present changes.
5. **Repeat** until the user approves with no remaining notes.
6. **Hard Gate:** Use `AskUserQuestion` — "Is the plan ready to be converted to issues?" with options: Approve / Another annotation round / Abort.

### Phase 4: Issue Creation

See [references/issue-creation.md](references/issue-creation.md) for the detailed procedure.

**Summary:**

1. Create the **parent issue** from the plan's goal and design decisions section. Include:
   - Summary (1-2 sentences)
   - Motivation (from the design discussion)
   - Background (from research, non-obvious context only)
   - Proposal (desired end state)
   - Task overview (list of sub-issues with dependency order)
2. Create **sub-issues** from each task in the plan. Each sub-issue includes:
   - Summary
   - Motivation (why this task, in context of the parent)
   - Implementation approach (from the plan, with code examples — not "how to implement" but "what the implementation looks like")
   - Acceptance criteria (verifiable, binary)
   - Dependencies (link to blocking sub-issues using platform syntax)
3. Link sub-issues to the parent issue.
4. Clean up: delete the plan file and research file. The issues now hold all information.
5. Return the parent issue URL and list of sub-issue URLs.

## References

- [references/research.md](references/research.md) — Research phase procedure
- [references/design.md](references/design.md) — Design phase procedure
- [references/annotation-cycle.md](references/annotation-cycle.md) — Annotation cycle procedure
- [references/issue-creation.md](references/issue-creation.md) — Issue hierarchy creation procedure
- [references/platform-github.md](references/platform-github.md) — GitHub sub-issue and dependency commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab sub-issue and dependency commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog sub-issue and dependency commands
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
