# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation
2. Trigger the create-issue skill
3. Provide the user input described in the test case
4. Respond to follow-up questions as described in the persona
5. Evaluate the generated issue draft against the 9 quality criteria in Step 6
6. Record results in the Evaluation Log section at the bottom

## Test Cases

### Case 1: Vague bug report from non-engineer

- **Persona**: Business user, no technical knowledge
- **Initial input**: "The app is slow"
- **Expected behavior**:
  - Skill asks follow-up questions to clarify (which page? when? how slow?)
  - Does NOT proceed to draft with only "the app is slow"
  - Final issue has concrete reproduction steps
- **Key criteria to watch**: #7 (Proposal unambiguous), #9 (Self-contained)

### Case 2: Detailed feature request from engineer

- **Persona**: Backend engineer, familiar with codebase
- **Initial input**: "We need rate limiting on the API endpoints. Currently there's no protection against abuse and we've seen spikes from single IPs."
- **Expected behavior**:
  - Skill still asks clarifying questions (which endpoints? what limits?)
  - Codebase analysis identifies relevant API files
  - Proposal does NOT prescribe specific implementation (e.g., "use Redis")
- **Key criteria to watch**: #4 (No How), #5 (Non-obvious context)

### Case 3: Ambiguous scope

- **Persona**: Product manager
- **Initial input**: "We need to improve the user onboarding"
- **Expected behavior**:
  - Skill identifies that scope is too broad and asks to narrow down
  - Does NOT create a vague catch-all issue
  - Results in a focused issue with clear boundaries
- **Key criteria to watch**: #7 (Proposal unambiguous), #8 (Criteria independently verifiable)

### Case 4: Technical task with implicit How

- **Persona**: Frontend engineer
- **Initial input**: "We should migrate from REST to GraphQL for the dashboard API"
- **Expected behavior**:
  - Skill separates the Motivation (why migrate?) from the Proposal (what should the end state be?)
  - Proposal does NOT say "use Apollo Client" or prescribe migration steps
  - Background captures why REST is currently used
- **Key criteria to watch**: #3 (Motivation stands alone), #4 (No How)

### Case 5: Bug report with insufficient reproduction info

- **Persona**: QA tester
- **Initial input**: "The checkout button doesn't work sometimes"
- **Expected behavior**:
  - Skill asks: which browser? what does "sometimes" mean? what happens when it fails?
  - Does NOT accept "sometimes" as a valid reproduction step
  - Final issue has specific, reproducible conditions
- **Key criteria to watch**: #7 (Proposal unambiguous), #9 (Self-contained)

### Case 6: Non-technical feature request in Japanese

- **Persona**: Japanese-speaking business stakeholder
- **Initial input**: "お客様からの問い合わせをもっと早く対応できるようにしたい"
- **Expected behavior**:
  - All interaction and the final issue are in Japanese
  - Skill clarifies what "もっと早く" means concretely
  - Acceptance criteria are measurable
- **Key criteria to watch**: #8 (Criteria independently verifiable), language matching

### Case 7: Backlog issue creation with Operation type

- **Persona**: DevOps engineer using Backlog
- **Initial input**: "本番環境のDBマイグレーション手順をissueにしたい"
- **Expected behavior**:
  - Detects Backlog platform from CLAUDE.md config
  - Presents issue type options including Operation
  - Asks for priority confirmation (High / Normal / Low)
  - Uses Operation template with Procedure section
  - Creates issue via Backlog MCP tool
- **Key criteria to watch**: Issue type confirmation, priority confirmation, Operation template usage

### Case 8: Cross-platform setup (Backlog issues + GitHub PRs)

- **Persona**: Engineer in a team using Backlog for task management and GitHub for code
- **Initial input**: "Create a feature request for adding user notifications"
- **Expected behavior**:
  - Detects Backlog as issue tracker from CLAUDE.md
  - Creates the issue on Backlog (not GitHub)
  - Issue type confirmation step is shown
  - Priority confirmation step is shown (Backlog-specific)
- **Key criteria to watch**: Correct platform detection, Backlog-specific fields

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Criteria passed | Criteria failed | Notes | SKILL.md revision needed? |
|------|--------|-----------------|-----------------|-------|---------------------------|
| 2026-03-05 | 1 | 1,2,3,4,5,6,8 | 7,9 | Proposal too broad ("identify root cause and address"). Scope unclear when problem may be external. | Yes — added scope ownership check to Step 3 |
| 2026-03-05 | 2 | 1,2,3,4,5,6,7,8,9 | — | Clean pass. How (GraphQL) successfully excluded from Proposal. | No |
| 2026-03-05 | 3 | 1,2,3,4,5,6,8 | 7,9 | "Simplify" and "essential fields" left undefined. Need to ask which specific fields to keep/defer. | Yes — added vague verb detection to Step 3 |
| 2026-03-05 | 4 | 1,2,3,4,5,6,7,8,9 | — | Clean pass. "Migrate to GraphQL" correctly reframed as "consolidate to single request". | No |
| 2026-03-05 | 5 | 1,2,3,4,5,6,7,8,9 | — | Clean pass. "Sometimes" narrowed to "6+ items on Chrome" through 5 follow-up questions. | No |
| 2026-03-05 | 6 | 1,2,3,4,5,6,7,9 | 8 | "Response within 24h" is an operational goal, not an implementation criterion. | Yes — added operational vs implementation criteria separation to Step 3 |
