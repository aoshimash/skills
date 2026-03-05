---
name: create-issue
description: Create well-structured issues on any platform (GitHub, GitLab, etc.) with codebase analysis. Use when the user wants to create an issue, file a bug report, request a feature, or create a technical task. Triggers on phrases like "create an issue", "file a bug", "open an issue", "issueを作って", "issue作成", "バグ報告", "機能要望", "課題を作成".
---

# Create Issue

Create issues structured around **Summary / Motivation / Background / Proposal / Acceptance Criteria / References** on any issue tracking platform. Always include codebase analysis for accurate context. Ensure issues are solvable by both humans and AI agents.

## Step Tracking

Throughout the workflow, maintain an internal checklist of completed steps. This ensures no step is skipped and provides data for the session log.

Steps: `detect-platform` → `determine-type` → `gather-info` → `analyze-codebase` → `draft` → `self-evaluate` → `create-issue` → `log-and-improve`

Mark each step as completed when it finishes. If a step is skipped (with reason) or abandoned, record that too. The final `log-and-improve` step is **mandatory** — always execute it, even if the workflow is abandoned partway through.

### Signals to track during execution

Observe and record these 3 signal types throughout Steps 1–7:

1. **Draft rejection**: The user requests changes to the draft after it is presented. Record each occurrence with the reason.
2. **Question round-trips**: Count the number of back-and-forth exchanges during information gathering (Step 3). A round-trip is one question from the skill followed by one answer from the user.
3. **Self-evaluation miss**: The draft passed Step 6 self-evaluation but the user still identified a problem. Record what was missed.

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
- Other → Output Markdown for the user to paste manually

### 2. Determine Issue Type

Infer the issue type from conversation context. If unclear, ask using plain language:

- "Is something broken or not working as expected?" → **Bug Report**
- "Are you requesting something new or an improvement?" → **Feature Request**
- Only present **Technical Task** when the user's description is clearly technical (e.g., mentions refactoring, performance, tech debt)

### 3. Gather Information

Collect information through conversation using natural, plain-language questions. Do not ask for all fields at once — build on each response.

**Step-by-step:**

1. Ask: "Why is this needed?" or "What problem are you experiencing?"
2. Based on the response, ask: "What would you like the result to look like?" or "How should it work when it's fixed/done?"
3. Do NOT ask the user for Acceptance Criteria. Instead, generate verifiable criteria from the Motivation and Proposal, then confirm: "I've drafted the following completion criteria — do these look right?"

**Ensure completeness through follow-up questions.** After each response, check:
- Is the scope clear? Could two different people interpret this differently?
- Is the problem within the scope of this project? If the root cause may be in an external system, clarify ownership. If unknown, suggest scoping the issue to investigation only.
- Are there edge cases or boundary conditions left unaddressed?
- For Bug Reports: Are reproduction steps specific enough to reproduce reliably?
- For Feature Requests: Is the desired behavior described concretely, not just abstractly? Watch for vague verbs like "improve", "simplify", "reduce", "optimize" — always ask what specifically changes and for what.
- Are the completion criteria things that can be verified at implementation time? Separate operational goals (e.g., "response time under 24h") from implementation criteria (e.g., "notification is sent on form submit").

If any answer is no, ask a targeted follow-up question. Repeat until the information is sufficient for someone with zero context to implement correctly. Do not proceed to Step 4 until the information is complete.

**Labels**: Fetch the existing labels from the project (e.g., `gh label list`). Based on the issue type and content, recommend appropriate labels from the available list. Present the recommendation to the user for confirmation.

**Assignees**: Ask the user: assign to yourself, someone else, or no one. If someone else, fetch the available assignees (e.g., `gh api repos/{owner}/{repo}/assignees`) and let the user choose.

### 4. Analyze Codebase

Always run codebase analysis to enrich the issue with accurate background:

- `git status` and `git diff` for recent changes
- Grep/Glob for related files, functions, and patterns
- Identify affected areas and dependencies

Use findings to populate the **Background** and **Related Code** sections. Present current state as factual background, not implementation suggestions.

### 5. Draft the Issue

Load the appropriate template from [references/templates.md](references/templates.md) and fill it in.

Every issue starts with a **1-2 sentence summary** at the top before any sections. This summary enables quick scanning in issue lists.

**Language**: Match the user's language. If the user writes in Japanese, write the issue in Japanese. If in English, write in English.

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

### 8. Log & Improve (mandatory)

**Always execute this step**, even if the workflow was abandoned or partially completed.

#### Spawn skill-analyzer agent

Pass a session summary containing:
- `skill`: "create-issue"
- `project`: repository name
- `issue`: issue identifier (if created) or "not created"
- `steps_completed`: list from step tracking checklist
- `steps_skipped`: list with reasons
- `rejections`: list of {step, reason} — primarily from draft rejections
- `retries`: list of {step, reason} — e.g., returning to Step 3 for missing information
- `user_friction`: list of observations — include question round-trip count and any self-evaluation misses
- `outcome`: "success", "partial", or "abandoned"
- `notes`: any additional observations

The agent writes the log and analyzes accumulated entries for patterns.

See [references/log-analysis.md](references/log-analysis.md) for how to handle the agent's results. If the agent reports improvement suggestions, present them to the user and offer to create a PR.

## Evaluation

To improve this skill, run the test cases in [references/eval-cases.md](references/eval-cases.md) and iterate on this SKILL.md based on the results.

## References

- [references/templates.md](references/templates.md) — Issue templates
- [references/platform-github.md](references/platform-github.md) — GitHub CLI commands
- [references/platform-gitlab.md](references/platform-gitlab.md) — GitLab CLI commands
- [references/log-analysis.md](references/log-analysis.md) — How to handle skill-analyzer agent results
- [references/eval-cases.md](references/eval-cases.md) — Evaluation test cases
