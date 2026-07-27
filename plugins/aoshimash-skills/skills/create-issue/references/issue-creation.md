# Issue Creation

## Purpose

Used in the **Design Flow** (SKILL.md D3) to convert the approved plan into
issues on the tracker. Afterwards the research findings live on the tracker as
a comment and the local plan file is gone — the issues plus that comment hold
everything implementation needs.

Every issue body created here (parent, sub, grandchild, or single) must
satisfy the same quality criteria as Lightweight Flow issues (SKILL.md L3,
adapted to the skeleton in use) — a good issue is the same regardless of flow
or reader. In particular: no implementation steps, file-edit lists, or code
examples in any issue body.

The split was already approved as part of the final approval in
[annotation-cycle.md](annotation-cycle.md). Do not re-ask for it here; create
exactly the hierarchy the approved `## Split Proposal` describes.

## 1. Fact-Check External Claims

Scope: only claims about external/third-party software that will actually
appear in the issue bodies about to be created — not everything read during
research.

Scan the plan's content (research findings, design decisions, task scopes,
notes, and acceptance criteria) for precise, actionable claims about
external/third-party software: default values, version constraints, config key
names, required components/extensions, licensing. For each:

- Already verified against a primary source (official docs, or the actual
  source/config/values file) fetched this session → leave as-is.
- Otherwise → fetch the primary source and confirm or correct it before it
  goes into an issue body.
- Cannot be cheaply verified → state it explicitly as an assumption ("TBD",
  "unverified") in the issue body rather than as fact.

General codebase facts already grounded via direct file reads are out of
scope; this step targets external-software claims, which are the ones most
likely to be wrong from memory or search snippets.

## 2. Choose the Skeleton

If the repository defines issue templates or forms (detected in SKILL.md Step
1), they are the skeleton for every issue created here — fill their sections
and map this skill's content into them, per SKILL.md "Repository Issue
Templates". Otherwise use the templates in [templates.md](templates.md):
Parent Issue for the parent, Sub-Issue for each task, or a single-issue
template when the split was declined.

## 3. Create the Parent Issue

The parent represents the entire feature/initiative. Fill it from the plan:

- **Summary** — 1-2 sentences
- **Motivation** — from the plan's goal and design rationale
- **Background** — non-obvious context from the research findings (no
  implementation details)
- **Proposal** — the plan's Goal section
- **Task Overview** — the task table with dependencies and sizes
- **Design Decisions** — the plan's Design Decisions table, including every
  decision that came out of an answered open question

Create it with the platform CLI and record the issue number.

**Single-issue case** (split declined): compose ONE issue from the
Feature Request or Technical Task skeleton, with the plan's Goal as
Motivation/Proposal and the task breakdown as a `## Task Breakdown` section
(title, purpose, scope, and AC per task, as subsections). Then skip to step 6.

## 4. Create Sub-Issues

For each task in the plan:

- **Title** — the task title (imperative, under 70 chars)
- `Parent: #<parent-issue-number>`
- **Motivation** — why this task exists, in context of the parent feature
- **Background** — task-specific context from the plan's Notes: non-obvious
  constraints, the design decisions that bind this task, useful research
  findings; Related Code as factual current state
- **Proposal** — the task's desired end state and boundaries, from its Scope
- **Acceptance Criteria** — from the task
- **Dependencies** — `Blocked by: #<issue-number>` for blocking siblings

As each sub-issue is created, record the mapping from its plan-local index
(the `#` column in the Task Overview table) to the real issue number assigned
by the platform. Step 5 needs it.

**Grandchild issues**: if the approved split nests a task, treat that task as
a **child that is also a parent** — create it with the Sub-Issue skeleton plus
its own `## Task Overview` table, then create each grandchild with
`Parent: #<child-issue-number>`. Maximum depth is 3 levels; if a grandchild
would still be Large, the decomposition should have been redesigned during the
annotation cycle. Keep a separate local-to-real mapping per child-parent.

## 5. Update Task Overview Tables

Plan-local placeholders must be replaced with real issue numbers before they
mislead readers — platforms like GitHub auto-link any `#N`, so a leftover `#1`
links to whatever unrelated issue holds that number.

1. Fetch the current parent issue body (e.g.
   `gh issue view <number> --json body -q '.body'`).
2. In the `## Task Overview` table only:
   - **Task column**: prepend the real reference — `<title>` becomes
     `#<real-number> — <title>`
   - **Dependencies column**: replace each plan-local reference (`#1`, `#2`)
     with the corresponding real issue number
   - Change nothing outside the table rows.
3. Write the body back with the platform CLI (e.g.
   `gh issue edit <parent-number> --body-file <file>`).

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

Apply the same update to any child issue that has its own Task Overview table,
once its grandchildren exist.

## 6. Link the Hierarchy

- **GitHub**: sub-issue links — each child to its parent, each grandchild to
  its child (see platform guide).
- **GitLab**: parent-child relationship or related issues.
- **Backlog**: the parent issue field.

Also establish dependency links between siblings where specified, and read the
relationships back to confirm the links registered (see the platform guide's
inspection section) rather than assuming the edit took.

## 7. Post the Research Comment

The research findings are durable; the plan file is not. Post the plan's
`## Research Findings` section as a comment on the **parent issue** — or on
the single issue, when the split was declined — before deleting anything. This
is what implement-issue reads at implementation time so it can re-verify only
the delta instead of researching from scratch.

Format (collapsed, so it does not crowd the issue thread):

```markdown
<details>
<summary>Research findings (create-issue, YYYY-MM-DD)</summary>

<the plan's ## Research Findings section, headings demoted one level>

</details>
```

Keep the blank lines around the body — without them the Markdown inside the
`<details>` block does not render. On trackers that do not render HTML in
comments (e.g. Backlog), post the same content as a plain comment titled
`Research findings (create-issue, YYYY-MM-DD)` instead. See the platform
guide's comment section for the command.

Sub-issues do not get their own copy: implement-issue reads the parent's
comment as part of parent context.

## 8. Clean Up

Delete the plan file:

```bash
rm <plan-dir>/YYYY-MM-DD-<topic-slug>.md
```

If the plan directory was created by this run and is now empty, remove it too
(leave permanent project directories such as `docs/plans/` in place). Verify
nothing this flow wrote remains in the working tree — `git status` should show
no plan or research artifacts.

## 9. Return the Result

Output the parent issue URL (or the single issue URL), the sub-issue and
grandchild URLs with titles and dependencies, and the hierarchy as an ASCII
tree. Mention where the research comment was posted.

```
Created issue hierarchy:
  Parent: #100 — Add user search feature   (research findings attached as a comment)
  ├─ #101 — Add pg_trgm index to users table
  ├─ #102 — Create search endpoint (blocked by #101)
  ├─ #103 — Add search UI component (blocked by #101)
  │   ├─ #106 — Add search input component
  │   └─ #107 — Add results list component
  └─ #104 — Add search integration tests (blocked by #102, #103)
```
