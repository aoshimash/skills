---
name: create-issue
description: >
  Create well-structured issues on any platform (GitHub, GitLab, Backlog) with
  codebase analysis — from a single quick issue to a fully designed issue
  hierarchy (parent + sub-issues with dependencies). Everything unknown is
  gathered in one batched question round; design work is carried by a single
  consolidated plan file refined through inline annotation; nothing is
  published without an explicit approval. Use when the user wants to create an
  issue, file a bug report, request a feature, create a technical task, or
  design a feature and break it down into implementable issues. Triggers on
  phrases like "create an issue", "file a bug", "open an issue", "issueを作って",
  "issue作成", "バグ報告", "機能要望", "課題を作成", "design sprint", "スプリント設計",
  "機能を設計して issue に分解", "plan and create issues", "design and decompose",
  "この機能を設計して".
---

# Create Issue

Create issues on any issue tracking platform, always grounded in codebase
analysis. Two flows: a **Lightweight Flow** for a single, well-scoped issue,
and a **Design Flow** for research-driven decomposition into an issue
hierarchy. Every issue is written to be solvable by both humans and AI agents
with zero prior context — a good issue is the same regardless of who
implements it: it explains why and what, records the decisions that bind the
work, and leaves how to implementation time.

Interaction is batched, not incremental:

| Flow | Interaction |
|---|---|
| Lightweight | At most **one batched question round** (skipped entirely when nothing is unresolved), then **one draft approval** |
| Design | **One plan file** (research + design + open questions + split proposal) iterated through the annotation cycle, then **one final approval** covering plan and split together |

## Principles

- **Motivation & Proposal, never How**: Describe why it matters and what the
  desired outcome is. Never prescribe implementation — no implementation
  steps, no lists of files to edit, no code examples. Whoever picks up the
  issue plans the implementation at implementation time.
- **No perishable detail**: Time passes between issue creation and
  implementation. File lists, code snippets, and step-by-step approaches rot
  in that gap; decisions and constraints do not. Record decisions, never
  steps.
- **Structural decisions now, local decisions later**: Settle and record what
  has high reversal cost or must stay consistent across sibling issues — the
  shape of a split, cross-cutting conventions, externally visible contracts.
  Leave naming, choices among roughly equivalent designs, and tactical detail
  to implementation time; they are guided by the repository's decision
  principles and logged in the PR. When in doubt, record it in the issue.
- **Background from code**: Always analyze the codebase to ground the issue in
  reality. Include file paths and current state as background, not as
  implementation guidance. Background should capture what is NOT obvious from
  reading the code: decisions, constraints, business rules. Known pitfalls are
  not optional context: if analysis reveals a trap an implementer could
  plausibly fall into (hidden coupling, caching, ordering requirements, API
  quirks), record it as a constraint — never as code.
- **Ask once, in one round**: Before asking anything, check the decision
  stores — this conversation, the repository's agent instructions, user-level
  configuration, and (in the Design Flow) the plan file itself. Ask everything
  still unresolved in a single round; never run a one-question-at-a-time
  interview. Record each answer in the store matching its scope so it is never
  asked again.
- **Never settle for vague**: Ambiguity is resolved before an issue is
  created, not after. A follow-up round is legitimate when an answer opens a
  genuinely new question — batch that round too.
- **Nothing is published without approval**: Issues are outward-facing. Both
  flows end with an explicit approval of the exact content that will be
  created. This is the one gate that is never removed.
- **Plan as shared mutable state** (Design Flow): The plan lives in a local
  markdown file the user can annotate inline. Chat-based steering is
  imprecise; document-based iteration is not.
- **Findings are durable, plans are perishable** (Design Flow): The research
  findings are posted to the tracker as a collapsed comment so implementation
  starts from them; the local plan file is deleted once the issues exist.
- **Repository templates take precedence**: When the repository defines issue
  templates or forms, the template is the skeleton (see [Repository Issue
  Templates](#repository-issue-templates)).
- **Splitting is a proposal, never automatic**: Whether to create a parent +
  sub-issues (or nested grandchild issues) is always confirmed with the user.
  Default to a single issue when in doubt.
- **Accessible to everyone**: Use plain language in all interactions. Avoid
  jargon. The skill should be equally usable by engineers and non-engineers.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`, which can carry several questions in one round) | Numbered options as plain text, all questions in one message; wait for the user's reply |

## Step 1: Detect Platform and Templates

1. Determine the issue tracking platform in this order:
   1. **Project agent instructions** (e.g. `AGENTS.md` / `CLAUDE.md`): an
      `## Issue Tracker` section with `platform`, `project`, `base_url` fields
   2. **Git remote URL**: infer from origin (github.com → GitHub, gitlab.com →
      GitLab)
   3. **Ask**: if undetectable, include the question in the batched round and
      suggest recording the answer in the project's agent instructions
2. Load the corresponding platform guide from `references/`:
   - GitHub → [references/platform-github.md](references/platform-github.md)
   - GitLab → [references/platform-gitlab.md](references/platform-gitlab.md)
   - Backlog → [references/platform-backlog.md](references/platform-backlog.md)
   - Other → output Markdown for the user to paste manually
3. Check whether the repository defines its own issue templates or forms (see
   the platform guide's template-detection section). If it does, they become
   the skeleton for every issue this run creates — see [Repository Issue
   Templates](#repository-issue-templates).

## Step 2: Choose the Flow

Default to the **Lightweight Flow**. Escalate to the **Design Flow** when ANY
of the following signals fire:

1. **Explicit request** — the user asks for design, planning, or decomposition
   (e.g. "design this feature", "break it into issues", "design sprint",
   "設計して issue に分解").
2. **Multi-area change** — the request touches 3+ distinct areas of the
   codebase (e.g. schema + API + UI).
3. **Unresolved architecture** — 2+ valid architectural approaches exist and
   the choice changes the shape of the work.
4. **Not one-PR-sized** — the work clearly cannot land as a single reviewable
   PR (heuristic: multiple deliverables that could ship independently, or more
   than roughly 1-2 days of work).

If the signals are weak or conflicting, fold the flow choice into the batched
question round (see Environment Adaptation):
- "Quick single issue" → Lightweight Flow
- "Full design flow (plan file → annotation cycle → issue hierarchy)" →
  Design Flow

**Mid-flight escalation**: if the Lightweight Flow's codebase analysis (Step
L1) reveals criteria 2-4, state what was found and propose switching to the
Design Flow as part of the batched round. If the round's answers instead show
the scope expanding rather than converging, propose the switch in the
follow-up round. Never escalate silently.

**De-escalation**: if the Design Flow's research shows the work fits
comfortably in one issue, say so and finish through the Lightweight Flow's
draft/approve steps (L3-L4) instead of forcing a hierarchy.

## Lightweight Flow

### L1: Analyze the Codebase First

Analysis comes before questions: it decides which questions are actually
unresolved, and a question the codebase can answer is never asked.

- `git status` / `git diff` / recent history for in-flight work
- Grep/Glob for related files, functions, and patterns
- Affected areas, dependencies, and pitfalls an implementer could fall into
- Project conventions: agent instructions, existing issue conventions,
  configured labels/assignees/language

Use the findings to populate **Background** and **Related Code**, as factual
current state rather than implementation guidance. Then check for escalation
signals 2-4 (Step 2) before continuing.

### L2: One Batched Question Round

Assemble everything still unresolved into a **single** round (see Environment
Adaptation), then ask it once. If nothing is unresolved, skip this step
entirely and go to L3 — with complete initial input the draft approval is the
only interaction.

Check the decision stores before adding anything to the round: the
conversation so far, the repository's agent instructions, and user-level
configuration. Anything already recorded there is applied, not asked.

Candidate contents of the round — include only what is genuinely open:

| Item | Include when |
|---|---|
| **Issue type** (Bug Report / Feature Request / Technical Task / Operation) | Genuinely ambiguous. Clearly inferable types ("something is broken" → Bug Report) are never asked. Include platform-specific types where the platform has them |
| **Motivation** | The user's message does not explain why this matters or what the impact is |
| **Desired outcome** | The end state is missing, or stated so vaguely that two people would build different things. Watch for vague verbs — "improve", "simplify", "optimize" — and ask what specifically changes and for what |
| **Scope boundaries** | It is unclear what is explicitly not included, or whether the root cause may sit in an external system (clarify ownership; when unknown, propose scoping the issue to investigation only) |
| **Reproduction details** | Bug Reports whose repro steps are not specific enough to reproduce reliably |
| **Structural decisions** | A choice with high reversal cost or cross-issue consequence is open and the codebase does not settle it. Local, reversible choices are never asked — they belong to implementation time |
| **Priority** | The platform has built-in priority levels (e.g. Backlog) and no default is configured |
| **Labels** | No default labels are configured; fetch existing labels (e.g. `gh label list`) and present a recommendation to confirm |
| **Assignee** | No default assignee rule is configured |
| **Flow choice** | Escalation signals are weak or conflicting (Step 2), or analysis revealed mid-flight escalation |

Acceptance criteria are generated from the motivation, proposal, and analysis
— not asked. They are presented for the first time in the L3 draft.

**Write answers back.** Answers about this issue are carried into the issue
body (Design Decisions / Background) by construction. When an answer states a
durable convention instead — "always self-assign", "issues in English",
"default labels are X" — say so in the completion message and offer to record
it in the repository's agent instructions or user-level configuration, so the
next run does not ask again. The offer rides along with the result; it is not
a separate gate.

### L3: Draft and Self-Evaluate

1. Compose the issue body. Use the repository's template when one exists,
   otherwise the matching template from
   [references/templates.md](references/templates.md).
2. Start with a **1-2 sentence summary** before any section, so the issue
   scans well in lists.
3. **Language**: if the project's agent instructions or conventions specify a
   language for issues, use it. Otherwise match the user's language.
4. Evaluate the draft against the criteria below before showing it:
   - Fails on **missing information from the user** → the round in L2 was
     incomplete; ask the remaining questions in one follow-up round. Do not
     guess.
   - Fails on **wording or structure** → revise silently and re-evaluate.
   - Fails on an **unverified external-software claim** → fetch the primary
     source and verify or correct it; if it cannot be cheaply verified, mark
     it as an assumption ("TBD", "unverified") rather than stating it as fact.

| # | Criterion | Pass condition |
|---|---|---|
| 1 | **Summary present** | The issue opens with a 1-2 sentence summary conveying the core problem/request without reading further |
| 2 | **Sections complete** | Every section the chosen skeleton requires is present and non-empty |
| 3 | **Motivation stands alone** | Reading Motivation alone — without Proposal — fully explains why this issue matters and what the impact is |
| 4 | **No How** | No section contains implementation steps, file-edit lists, code examples, or technology choices ("should use X library") that the issue does not genuinely constrain |
| 5 | **Background has non-obvious context** | Background includes at least one thing that cannot be learned by reading the code (a past decision, a business rule, a constraint), and every pitfall found during analysis is recorded as a constraint |
| 6 | **Background has code refs** | Related Code lists specific file paths from the analysis |
| 7 | **Proposal is unambiguous** | Two engineers reading the Proposal would agree on the desired end state |
| 8 | **Criteria are binary** | Each acceptance criterion passes or fails on inspection; none needs subjective judgment. Operational goals ("response within 24h") are separated from implementation criteria ("a notification is sent on form submit") |
| 9 | **Structural decisions recorded** | Every decision with high reversal cost or cross-issue consequence is stated in the issue; nothing structural is left implicit. Local, reversible decisions are deliberately absent |
| 10 | **Self-contained** | Someone with zero prior context can start implementing without asking a clarifying question; the decisions left open are answerable from repository convention |
| 11 | **External facts verified** | Every precise claim about external/third-party software (default value, version constraint, config key name, required component, licensing) is verified against a primary source fetched this session or explicitly marked as an assumption. Claims already verified this session need no re-verification |

### L4: Approve and Create

1. Present the full draft — title, labels/assignee/priority, and the exact body
   that will be created.
2. Ask the user to choose (see Environment Adaptation): **Create** / **Revise**
   (collect the changes, apply them, re-present) / **Abort**. Never create an
   issue without this approval.
3. On approval, create the issue with the platform-specific method from the
   loaded platform guide, applying labels, assignee, and priority.
4. Report the issue URL, plus any durable-convention offer from L2.

## Design Flow

### D0: Setup

1. Identify the **feature or initiative** to design. If the goal itself is
   unstated, ask for it in 1-2 sentences — this is the only question asked
   before the plan file exists; everything else becomes an embedded open
   question.
2. Determine the **plan directory**: a directory configured in the project's
   agent instructions (e.g. `docs/plans/`), otherwise `docs/plans/`, created
   if needed. Plan files are named `YYYY-MM-DD-<topic-slug>.md`.

### D1: Research, Design, and the Plan File

See [references/plan-file.md](references/plan-file.md) for the detailed
procedure and the file format.

**Summary:**

1. Research the codebase deeply — related files, architecture, conventions,
   dependencies, test patterns, agent instructions, recent history, risks.
2. Design against those findings: settle the structural decisions, decompose
   the work into tasks, and derive dependencies.
3. Where a structural choice genuinely needs the user, do **not** stop — write
   it into the plan's `## Open Questions` as a numbered question with options,
   trade-offs, and a recommendation, for the user to answer inline.
4. Write everything into **one** plan file: goal, research findings, design
   decisions, open questions, tasks, dependency graph, split proposal, out of
   scope. There is no separate research file and no research-approval gate.
5. Present the plan file path and go straight to the annotation cycle.

If research shows the work fits comfortably in one issue, apply the
de-escalation rule from Step 2 instead of forcing a hierarchy.

### D2: Annotation Cycle

See [references/annotation-cycle.md](references/annotation-cycle.md) for the
detailed procedure.

**Summary:**

1. Tell the user to open the plan file, answer the open questions inline, and
   annotate anything to correct, reject, or refine — including the Split
   Proposal — then say when the notes are ready.
2. Read the file, address every annotation and every answered open question,
   re-run the task quality checks, rewrite the plan, and summarize what
   changed.
3. Repeat until no notes remain.
4. **Final approval** (see Environment Adaptation), covering the plan and the
   split together: **Approve and create issues** / **Another annotation
   round** / **Abort**. Unanswered open questions block this approval.

### D3: Issue Creation

See [references/issue-creation.md](references/issue-creation.md) for the
detailed procedure.

**Summary:**

1. Fact-check the external-software claims that will appear in the issue
   bodies against primary sources, or mark them as assumptions.
2. Create the **parent issue** (or a single issue, if the split was declined)
   and the **sub-issues**, using the repository's templates when present and
   [references/templates.md](references/templates.md) otherwise. Every body
   must pass the L3 criteria.
3. Replace plan-local task numbers with real issue numbers, then link children
   to parents and dependencies between siblings.
4. Post the **research comment**: the plan's research findings as a comment on
   the parent issue (or on the single issue) — collapsed where the tracker
   renders HTML — so implementation starts from them and re-verifies only the
   delta.
5. Delete the plan file — nothing this flow wrote stays in the working tree.
6. Return the hierarchy as an ASCII tree with URLs.

## Split Proposal

Splitting is always a user-confirmed proposal, never automatic.

- **Propose a parent + sub-issues** when the plan yields 2+ tasks that are
  independently implementable and reviewable.
- **Propose a nested split (grandchild issues)** when a single task remains
  Large (roughly 2+ hours) after refinement — on platforms with nested
  sub-issues (GitHub), its parts become sub-issues of that child. Maximum
  depth is 3 levels; if a grandchild would still be Large, redesign the
  decomposition instead of nesting deeper.
- The proposal lives in the plan's `## Split Proposal` section as an ASCII
  tree with sizes and dependencies, and is approved as part of the single
  final approval in D2 — it is not a second gate. To take a different shape,
  the user annotates the section like any other part of the plan.
- If the user declines the split, create ONE issue containing the full task
  breakdown as a section, instead of a hierarchy.

## Repository Issue Templates

When the repository defines issue templates or forms (see the platform
guide's template-detection section), the template is the skeleton:

- Fill the template's sections; map this skill's content into the sections
  that match semantically (e.g. skill Motivation → template "Why"), keeping
  the template's own wording and order.
- Append content that has no matching section as clearly delimited sections
  after the template body — never drop it.
- Structure yields to the template; quality does not. The L3 criteria still
  apply, and the required content (summary, motivation, background,
  desired end state, binary acceptance criteria, structural decisions) must
  land somewhere in the body.
- Issue forms with required fields: fill every required field. Where a form
  cannot express a needed section, put it in the form's free-text body field.
- When several templates exist, pick the one matching the issue type; if none
  matches (e.g. a parent issue in a repo with only a bug form), use this
  skill's own template from
  [references/templates.md](references/templates.md) and say which was used.

## Evaluation

To improve this skill, run the test cases in
[references/eval-cases.md](references/eval-cases.md) and iterate on this
SKILL.md based on the results.

## References

- [references/templates.md](references/templates.md) — Issue templates (single-issue types + Parent Issue / Sub-Issue) and how repository templates supersede them
- [references/plan-file.md](references/plan-file.md) — Design Flow research, design, and the consolidated plan file format
- [references/annotation-cycle.md](references/annotation-cycle.md) — Design Flow annotation cycle and final approval
- [references/issue-creation.md](references/issue-creation.md) — Design Flow issue creation, research comment, and cleanup
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands (issues, sub-issues, dependencies, comments, templates)
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands (issues, links, comments, templates)
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog CLI commands (bee) (issues, parent-child, comments)
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
