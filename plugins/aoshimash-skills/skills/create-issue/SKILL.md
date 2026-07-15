---
name: create-issue
description: >
  Create well-structured issues on any platform (GitHub, GitLab, Backlog) with
  codebase analysis — from a single quick issue to a fully designed issue
  hierarchy (parent + sub-issues with dependencies) built through research,
  brainstorming, and annotation cycles. Use when the user wants to create an
  issue, file a bug report, request a feature, create a technical task, or
  design a feature and break it down into implementable issues. Triggers on
  phrases like "create an issue", "file a bug", "open an issue", "issueを作って",
  "issue作成", "バグ報告", "機能要望", "課題を作成", "design sprint", "スプリント設計",
  "機能を設計して issue に分解", "plan and create issues", "design and decompose",
  "この機能を設計して".
---

# Create Issue

Create issues on any issue tracking platform, always grounded in codebase analysis. This skill has two flows: a **Lightweight Flow** for a single, well-scoped issue, and a **Design Flow** for research-driven decomposition into an issue hierarchy. Every issue is structured to be solvable by both humans and AI agents with zero prior context. A good issue is the same regardless of who implements it — it explains why and what, and leaves how to implementation time.

## Principles

- **Motivation & Proposal, never How**: Describe why it matters and what the desired outcome is. Never prescribe implementation — no implementation steps, no lists of files to edit, no code examples. Whoever picks up the issue (human or AI) plans the implementation at implementation time.
- **No perishable detail**: Time passes between issue creation and implementation. File lists, code snippets, and step-by-step approaches rot in that gap; design decisions and constraints do not. Record decisions, never steps.
- **Background from code**: Always analyze the codebase to ground the issue in reality. Include file paths and current state as background, not as implementation guidance. Background should capture what is NOT obvious from reading the code: decisions, constraints, business rules. Findings from analysis that will help at implementation time (current state, gotchas, related modules) are welcome as supplementary background — they help humans and AI alike. Known pitfalls are not optional context: if analysis reveals a trap an implementer could plausibly fall into (hidden coupling, caching, ordering requirements, API quirks), record it as a constraint — never as code.
- **Actionable by anyone**: Include enough information for a human or AI agent with no prior context to understand and resolve the issue. An incomplete issue creates back-and-forth communication that costs more than asking thorough questions upfront.
- **Accessible to everyone**: Use plain language in all interactions. Avoid jargon. The skill should be equally usable by engineers and non-engineers.
- **Never settle for vague**: If the user's response is ambiguous, incomplete, or leaves room for multiple interpretations, ask follow-up questions until the intent is clear. It is better to ask too many questions than to create an issue that requires clarification later.
- **Research before design** (Design Flow): Never design without deeply understanding the codebase first. Produce a written research artifact, not a verbal summary.
- **Plan as shared mutable state** (Design Flow): The plan lives in a local markdown file that the user can annotate inline. Chat-based steering is imprecise; document-based iteration is not.
- **Tasks must be boringly scoped** (Design Flow): Each task must be scoped so narrowly and unambiguously that the implementer — human or AI — faces no open design decisions. Achieve this through precise scope, recorded design decisions, and binary acceptance criteria, not by prescribing the implementation. If a task requires design judgment, decompose further or record the decision.
- **Hard gates** (Design Flow): Do not proceed to the next phase without explicit user approval.
- **Splitting is a proposal, never automatic**: Whether to create a parent + sub-issues (or nested grandchild issues) is always confirmed with the user. Default to a single issue when in doubt.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |

## Step 1: Detect Platform

Determine the issue tracking platform in this order:

1. **CLAUDE.md**: Check for `## Issue Tracker` section with `platform`, `project`, `base_url` fields
2. **Git remote URL**: Infer from origin (github.com → GitHub, gitlab.com → GitLab)
3. **Ask once**: If undetectable, ask the user and suggest adding the config to CLAUDE.md

Load the corresponding platform guide from `references/`:
- GitHub → [references/platform-github.md](references/platform-github.md)
- GitLab → [references/platform-gitlab.md](references/platform-gitlab.md)
- Backlog → [references/platform-backlog.md](references/platform-backlog.md)
- Other → Output Markdown for the user to paste manually

## Step 2: Choose the Flow

Default to the **Lightweight Flow**. Escalate to the **Design Flow** when ANY of the following signals fire:

1. **Explicit request** — the user asks for design, planning, or decomposition (e.g., "design this feature", "break it into issues", "design sprint", "設計して issue に分解").
2. **Multi-area change** — the request touches 3+ distinct areas of the codebase (e.g., schema + API + UI).
3. **Unresolved architecture** — 2+ valid architectural approaches exist and the choice changes the shape of the work.
4. **Not one-PR-sized** — the work clearly cannot land as a single reviewable PR (heuristic: multiple deliverables that could ship independently, or more than roughly 1-2 days of work).
5. **Diverging scope** — during information gathering (Lightweight Step L2), scope questions keep multiplying instead of converging.

If the signals are weak or conflicting, ask the user to choose (see Environment Adaptation):
- "Quick single issue" → Lightweight Flow
- "Full design flow (research → design → annotation cycle → issue hierarchy)" → Design Flow

**Mid-flight escalation**: if Lightweight Flow's codebase analysis (Step L3) reveals criteria 2-4, stop and state what was found, then propose switching to the Design Flow as a user choice (see Environment Adaptation). Never escalate silently.

**De-escalation**: if the Design Flow's research (Step D1) shows the work fits comfortably in one issue, say so and finish via the Lightweight Flow's draft/self-eval/create steps (L4-L6) instead of forcing a hierarchy. Never force a hierarchy the work doesn't need.

## Lightweight Flow

### L1: Determine Issue Type

Infer the issue type from conversation context. Available types:

- **Bug Report** — Something is broken or not working as expected
- **Feature Request** — New functionality or an improvement
- **Technical Task** — Refactoring, performance, tech debt (present only when clearly technical)
- **Operation** — Operational/procedural tasks with step-by-step procedures (available on platforms that support it, e.g., Backlog)

If the type is **clearly inferable** from the user's message (e.g., "something is broken" → Bug Report, "I want to add..." → Feature Request), proceed without confirmation.

If the type is **genuinely ambiguous** or could be multiple types, ask using plain language:
- "Is something broken or not working as expected?" → Bug Report
- "Are you requesting something new or an improvement?" → Feature Request

Include platform-specific types (e.g., Operation for Backlog) in the options when applicable.

### L2: Gather Information

Collect information through conversation using natural, plain-language questions. When presenting choices, ask the user to choose (see Environment Adaptation).

**Fast path**: If the user's initial message already provides clear motivation, desired outcome, and enough detail to generate verifiable acceptance criteria, skip the step-by-step questions below and proceed directly to generating AC (without confirming it yet — see Step L3).

**Step-by-step** (when more information is needed):

Do not ask for all fields at once — build on each response. Ask exactly one question at a time. Never combine multiple questions or sub-questions into a single message.

1. Ask: "Why is this needed?" or "What problem are you experiencing?"
2. Based on the response, ask: "What would you like the result to look like?" or "How should it work when it's fixed/done?"
3. Generate verifiable acceptance criteria from the Motivation and Proposal. Do NOT ask the user to confirm AC yet — it will be cross-checked against codebase analysis in Step L3 and presented in the draft.

**Ensure completeness through follow-up questions.** After each response, check:
- Is the scope clear? Could two different people interpret this differently?
- Is the problem within the scope of this project? If the root cause may be in an external system, clarify ownership. If unknown, suggest scoping the issue to investigation only.
- Are there edge cases or boundary conditions left unaddressed?
- For Bug Reports: Are reproduction steps specific enough to reproduce reliably?
- For Feature Requests: Is the desired behavior described concretely, not just abstractly? Watch for vague verbs like "improve", "simplify", "reduce", "optimize" — always ask what specifically changes and for what.
- Are the completion criteria things that can be verified at implementation time? Separate operational goals (e.g., "response time under 24h") from implementation criteria (e.g., "notification is sent on form submit").

If any answer is no, ask a targeted follow-up question. Repeat until the information is sufficient for someone with zero context to implement correctly. Do not proceed to Step L3 until the information is complete.

If, during this step, the scope keeps expanding rather than converging (criterion 5 in Step 2), pause and propose the Design Flow instead of continuing to gather information for an ever-growing single issue.

**Priority**: For platforms with built-in priority levels (e.g., Backlog: High / Normal / Low), ask the user to confirm the priority. Skip this for platforms without built-in priorities (e.g., GitHub, GitLab — use labels instead if needed).

**Labels**: Check CLAUDE.md for default labels configuration. If defaults are configured, apply them without asking. If not, fetch the existing labels from the project (e.g., `gh label list`), recommend appropriate labels based on the issue type and content, and present the recommendation to the user for confirmation.

**Assignees**: Check CLAUDE.md for default assignee configuration (e.g., "always self-assign"). If defaults are configured, apply them without asking. If not, ask the user: assign to yourself, someone else, or no one. If someone else, fetch the available assignees (e.g., `gh api repos/{owner}/{repo}/assignees`) and let the user choose.

When both labels and assignees need user input, present them as a single combined choice instead of asking separately.

### L3: Analyze Codebase

Always run codebase analysis to enrich the issue with accurate background:

- `git status` and `git diff` for recent changes
- Grep/Glob for related files, functions, and patterns
- Identify affected areas and dependencies

Use findings to populate the **Background** and **Related Code** sections. Present current state as factual background, not implementation suggestions.

**Cross-check AC**: After codebase analysis, review the acceptance criteria generated in Step L2 against analysis results. If the codebase reveals information that would improve or correct AC items (e.g., existing config files, related modules, edge cases), revise the AC before including it in the draft. The user sees the finalized AC in the Step L4 draft, not as a separate confirmation.

**Check for escalation signals**: if this analysis reveals the change spans 3+ distinct areas, or that 2+ architectural approaches are viable, stop and follow the "Mid-flight escalation" rule in Step 2 before continuing.

### L4: Draft the Issue

Load the appropriate template from [references/templates.md](references/templates.md) and fill it in.

Every issue starts with a **1-2 sentence summary** at the top before any sections. This summary enables quick scanning in issue lists.

**Language**: If CLAUDE.md or project conventions specify a language for issues (e.g., "Write issue titles/bodies in English"), use that language. Otherwise, match the user's language.

### L5: Self-Evaluate Before Presenting

Before showing the draft to the user, evaluate it against all criteria below.

- If a criterion fails due to **missing information from the user** → return to Step L2 and ask a targeted follow-up question. Do not guess or fill in gaps.
- If a criterion fails due to **draft wording or structure** → revise the draft silently and re-evaluate.
- If a criterion fails due to an **unverified external-software claim** → fetch the primary source (official docs, or the actual source/config/values file) to verify or correct the claim; if it cannot be cheaply verified, mark it as an assumption (e.g., "TBD", "unverified") instead of stating it as fact. Then re-evaluate.
- Only present the draft after all checks pass.

| # | Criterion | Pass condition |
|---|---|---|
| 1 | **Summary present** | Issue starts with a 1-2 sentence summary that conveys the core problem/request without reading further |
| 2 | **Sections complete** | Motivation, Background, Proposal, Acceptance Criteria, References are all present and non-empty |
| 3 | **Motivation stands alone** | Reading Motivation alone — without Proposal — fully explains why this issue matters and what the impact is |
| 4 | **No How** | Neither Proposal nor Background contains implementation steps, code suggestions, or technology choices (e.g., "should use X library") |
| 5 | **Background has non-obvious context** | Background includes at least one piece of information that cannot be learned by reading the code alone (e.g., a past decision, a business rule, a constraint) |
| 6 | **Background has code refs** | Related Code section includes specific file paths from codebase analysis |
| 7 | **Proposal is unambiguous** | Two different engineers reading the Proposal would agree on what the desired end state is. If multiple interpretations are possible, the information is insufficient |
| 8 | **Criteria are independently verifiable** | Each acceptance criterion has a clear binary outcome: it either passes or fails. No criterion requires subjective judgment |
| 9 | **Self-contained** | A person or AI with zero prior context can read the issue and begin implementation without asking any clarifying questions |
| 10 | **External facts verified** | Every precise, actionable claim about external/third-party software in the draft (default value, version constraint, config key name, required component/extension, licensing) is either verified against a primary source fetched this session, or explicitly marked as an assumption. Claims already verified against a primary source fetched during this session (e.g., in codebase/dependency research) don't need re-verification |

### L6: Create the Issue

After user approval, create the issue using the platform-specific method from the loaded platform guide. Apply labels if determined in Step L2. Confirm creation and share the issue URL.

## Design Flow

### D0: Setup

1. Identify the **feature or initiative** to design. If unclear, ask the user to describe the goal in 1-2 sentences.
2. Determine the **plan directory**. Check in order:
   1. CLAUDE.md for a configured plan directory (e.g., `docs/plans/`)
   2. If not configured, use `docs/plans/` and create it if needed
   3. Plan files are named: `YYYY-MM-DD-<topic-slug>.md` (e.g., `2026-04-07-user-search.md`)

### D1: Research

See [references/research.md](references/research.md) for the detailed procedure.

**Summary:**

1. Investigate the codebase deeply — related files, architecture patterns, conventions, dependencies, test patterns, CLAUDE.md rules, recent git history.
2. Write findings to `<plan-dir>/research-<topic-slug>.md`. Include: relevant file paths, current architecture, conventions, constraints, dependencies, and potential risks.
3. Present the research file to the user.
4. **Hard Gate:** Ask the user to choose (see Environment Adaptation): "Review the research file and confirm it captures the relevant context" — Approve / Add notes / Abort. If the user adds notes, update the research file and re-present.

If research reveals the work fits comfortably in one issue, apply the "De-escalation" rule from Step 2 and finish via the Lightweight Flow instead of continuing to D2.

### D2: Design

See [references/design.md](references/design.md) for the detailed procedure.

**Summary:**

1. Ask clarifying questions **one at a time** to understand the feature's goals, constraints, and scope. Use the research findings to ask informed questions.
2. When 2+ valid approaches exist, propose each with trade-offs and a recommendation. Ask the user to choose (see Environment Adaptation) with numbered options. Wait for the user's choice.
3. Break the work into tasks (title, purpose, scope, acceptance criteria, dependencies, estimated size).
4. Each task must pass the **"boring scope" test**: is the task scoped so tightly — with every design decision recorded — that implementing it requires zero design judgment?
5. Draft the Split Proposal (see below) into the plan's `## Split Proposal` section, and write the plan to `<plan-dir>/YYYY-MM-DD-<topic-slug>.md`.

### D3: Annotation Cycle

See [references/annotation-cycle.md](references/annotation-cycle.md) for the detailed procedure.

**Summary:**

1. Tell the user: "Open `<plan-file>` in your editor and add inline notes (e.g., `<!-- NOTE: ... -->`) to correct, reject, or refine any part — including the Split Proposal. When done, tell me to address the notes."
2. When the user signals readiness, read the plan file and address every annotation:
   - If a note rejects an approach → replace with the user's direction
   - If a note adds a constraint → incorporate it
   - If a note asks a question → answer inline or ask a clarifying question
3. After addressing all notes, re-run the "boring scope" test on each task.
4. Write the updated plan and present changes.
5. **Repeat** until the user approves with no remaining notes.
6. **Hard Gate:** Ask the user to choose (see Environment Adaptation): "Is the plan ready to be converted to issues?" — Approve / Another annotation round / Abort.

### D4: Issue Creation

See [references/issue-creation.md](references/issue-creation.md) for the detailed procedure.

**Summary:**

1. Fact-check external-software claims that will appear in the issue bodies against primary sources (or mark unverifiable ones as assumptions) before creating anything.
2. Confirm the Split Proposal (see below) — this is a separate, explicit gate even after the plan itself is approved.
3. Create the **parent issue** from the plan's goal and design decisions section (or a single issue, if the user declined the split).
4. Create **sub-issues** (and grandchild issues, if a nested split was approved) from each task in the plan.
5. Link issues to their parent and establish dependency links between siblings.
6. Clean up: delete the plan file and research file. The issues now hold all information.
7. Return the parent issue URL and the list of sub-issue (and grandchild) URLs, as an ASCII tree.

## Split Proposal

Splitting is always a user-confirmed proposal, never automatic. After task decomposition in Step D2:

- **Propose a parent + sub-issues** when the plan yields 2+ tasks that are independently implementable and reviewable.
- **Propose a nested split (grandchild issues)** when a single task remains Large (roughly 2+ hours) after refinement — on platforms with nested sub-issues (GitHub), its parts become sub-issues of that child. Maximum depth is 3 levels (parent → child → grandchild); if a grandchild would still be Large, redesign the decomposition instead of nesting deeper.
- Present the proposed hierarchy as an ASCII tree with sizes and dependencies, then ask the user to choose (see Environment Adaptation):
  - "Create parent + sub-issues" (mark "(Recommended)" when the criteria above are met)
  - "Create a single issue"
  - "Adjust the breakdown"
- If the user declines the split, create ONE issue containing the full task breakdown as a section, instead of a hierarchy.

This gate is presented once, in Step D4 (Issue Creation), after the plan itself has been approved through the annotation cycle — not repeated per task.

## Evaluation

To improve this skill, run the test cases in [references/eval-cases.md](references/eval-cases.md) and iterate on this SKILL.md based on the results.

## References

- [references/templates.md](references/templates.md) — Issue templates (single-issue types + Parent Issue / Sub-Issue)
- [references/research.md](references/research.md) — Design Flow research phase procedure
- [references/design.md](references/design.md) — Design Flow design phase procedure
- [references/annotation-cycle.md](references/annotation-cycle.md) — Design Flow annotation cycle procedure
- [references/issue-creation.md](references/issue-creation.md) — Design Flow issue hierarchy creation procedure
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands (issues, sub-issues, dependencies)
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands (issues, sub-issues, dependencies)
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog CLI commands (bee) (issues, parent-child)
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
