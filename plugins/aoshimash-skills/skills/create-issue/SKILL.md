---
name: create-issue
description: Create well-structured issues on any platform (GitHub, GitLab, etc.) with codebase analysis. Use when the user wants to create an issue, file a bug report, request a feature, or create a technical task. Triggers on phrases like "create an issue", "file a bug", "open an issue", "issueを作って", "issue作成", "バグ報告", "機能要望", "課題を作成".
---

# Create Issue

Create issues structured around **Summary / Motivation / Background / Proposal / Acceptance Criteria / References** on any issue tracking platform. Always include codebase analysis for accurate context. Ensure issues are solvable by both humans and AI agents.

## Principles

- **Motivation & Proposal, never How**: Describe why it matters and what the desired outcome is. Never prescribe implementation.
- **Background from code**: Always analyze the codebase to ground the issue in reality. Include file paths and current state as background, not as implementation guidance. Background should capture what is NOT obvious from reading the code: decisions, constraints, business rules.
- **Actionable by anyone**: Include enough information for a human or AI agent with no prior context to understand and resolve the issue. An incomplete issue creates back-and-forth communication that costs more than asking thorough questions upfront.
- **Accessible to everyone**: Use plain language in all interactions. Avoid jargon. The skill should be equally usable by engineers and non-engineers.
- **Never settle for vague**: If the user's response is ambiguous, incomplete, or leaves room for multiple interpretations, ask follow-up questions until the intent is clear. It is better to ask too many questions than to create an issue that requires clarification later.

## Workflow

### 1. Detect Platform

Determine the issue tracking platform in this order:

1. **CLAUDE.md**: Check for `## Issue Tracker` section with `platform`, `project`, `base_url` fields
2. **Git remote URL**: Infer from origin (github.com → GitHub, gitlab.com → GitLab)
3. **Ask once**: If undetectable, ask the user and suggest adding the config to CLAUDE.md

Load the corresponding platform guide from `references/`:
- GitHub → [references/platform-github.md](references/platform-github.md)
- GitLab → [references/platform-gitlab.md](references/platform-gitlab.md)
- Backlog → [references/platform-backlog.md](references/platform-backlog.md)
- Other → Output Markdown for the user to paste manually

### 2. Determine Issue Type

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

### 3. Gather Information

Collect information through conversation using natural, plain-language questions. Use AskUserQuestion when presenting choices.

**Fast path**: If the user's initial message already provides clear motivation, desired outcome, and enough detail to generate verifiable acceptance criteria, skip the step-by-step questions below and proceed directly to generating AC (without confirming it yet — see Step 4).

**Step-by-step** (when more information is needed):

Do not ask for all fields at once — build on each response. Ask exactly one question at a time. Never combine multiple questions or sub-questions into a single message.

1. Ask: "Why is this needed?" or "What problem are you experiencing?"
2. Based on the response, ask: "What would you like the result to look like?" or "How should it work when it's fixed/done?"
3. Generate verifiable acceptance criteria from the Motivation and Proposal. Do NOT ask the user to confirm AC yet — it will be cross-checked against codebase analysis in Step 4 and presented in the draft.

**Ensure completeness through follow-up questions.** After each response, check:
- Is the scope clear? Could two different people interpret this differently?
- Is the problem within the scope of this project? If the root cause may be in an external system, clarify ownership. If unknown, suggest scoping the issue to investigation only.
- Are there edge cases or boundary conditions left unaddressed?
- For Bug Reports: Are reproduction steps specific enough to reproduce reliably?
- For Feature Requests: Is the desired behavior described concretely, not just abstractly? Watch for vague verbs like "improve", "simplify", "reduce", "optimize" — always ask what specifically changes and for what.
- Are the completion criteria things that can be verified at implementation time? Separate operational goals (e.g., "response time under 24h") from implementation criteria (e.g., "notification is sent on form submit").

If any answer is no, ask a targeted follow-up question. Repeat until the information is sufficient for someone with zero context to implement correctly. Do not proceed to Step 4 until the information is complete.

**Priority**: For platforms with built-in priority levels (e.g., Backlog: High / Normal / Low), ask the user to confirm the priority. Skip this for platforms without built-in priorities (e.g., GitHub, GitLab — use labels instead if needed).

**Labels**: Check CLAUDE.md for default labels configuration. If defaults are configured, apply them without asking. If not, fetch the existing labels from the project (e.g., `gh label list`), recommend appropriate labels based on the issue type and content, and present the recommendation to the user for confirmation.

**Assignees**: Check CLAUDE.md for default assignee configuration (e.g., "always self-assign"). If defaults are configured, apply them without asking. If not, ask the user: assign to yourself, someone else, or no one. If someone else, fetch the available assignees (e.g., `gh api repos/{owner}/{repo}/assignees`) and let the user choose.

When both labels and assignees need user input (no defaults configured for either), combine them into a single AskUserQuestion call instead of asking separately.

### 4. Analyze Codebase

Always run codebase analysis to enrich the issue with accurate background:

- `git status` and `git diff` for recent changes
- Grep/Glob for related files, functions, and patterns
- Identify affected areas and dependencies

Use findings to populate the **Background** and **Related Code** sections. Present current state as factual background, not implementation suggestions.

**Cross-check AC**: After codebase analysis, review the acceptance criteria generated in Step 3 against analysis results. If the codebase reveals information that would improve or correct AC items (e.g., existing config files, related modules, edge cases), revise the AC before including it in the draft. The user sees the finalized AC in the Step 5 draft, not as a separate confirmation.

### 5. Draft the Issue

Load the appropriate template from [references/templates.md](references/templates.md) and fill it in.

Every issue starts with a **1-2 sentence summary** at the top before any sections. This summary enables quick scanning in issue lists.

**Language**: If CLAUDE.md or project conventions specify a language for issues (e.g., "Write issue titles/bodies in English"), use that language. Otherwise, match the user's language.

### 6. Self-Evaluate Before Presenting

Before showing the draft to the user, evaluate it against all criteria below.

- If a criterion fails due to **missing information from the user** → return to Step 3 and ask a targeted follow-up question. Do not guess or fill in gaps.
- If a criterion fails due to **draft wording or structure** → revise the draft silently and re-evaluate.
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

### 7. Create the Issue

After user approval, create the issue using the platform-specific method from the loaded platform guide. Apply labels if determined in Step 3. Confirm creation and share the issue URL.

## Evaluation

To improve this skill, run the test cases in [references/eval-cases.md](references/eval-cases.md) and iterate on this SKILL.md based on the results.

## References

- [references/templates.md](references/templates.md) — Issue templates
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/platform-backlog.md](references/platform-backlog.md) — Backlog MCP tools
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
