# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation
2. Trigger the create-issue skill
3. Provide the user input described in the test case
4. Respond to follow-up questions as described in the persona
5. Evaluate the generated issue draft against the 10 quality criteria in Step L5 (Lightweight Flow) or the Split Proposal criteria (Design Flow)
6. Record which flow (Lightweight/Design) was chosen and whether it matched the expectation
7. Record results in the Evaluation Log section at the bottom

## Lightweight Flow Cases

### Case 1: Vague bug report from non-engineer

- **Persona**: Business user, no technical knowledge
- **Initial input**: "The app is slow"
- **Expected behavior**:
  - Skill asks follow-up questions to clarify (which page? when? how slow?)
  - Does NOT proceed to draft with only "the app is slow"
  - Final issue has concrete reproduction steps
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: #7 (Proposal unambiguous), #9 (Self-contained)

### Case 2: Detailed feature request from engineer

- **Persona**: Backend engineer, familiar with codebase
- **Initial input**: "We need rate limiting on the API endpoints. Currently there's no protection against abuse and we've seen spikes from single IPs."
- **Expected behavior**:
  - Skill still asks clarifying questions (which endpoints? what limits?)
  - Codebase analysis identifies relevant API files
  - Proposal does NOT prescribe specific implementation (e.g., "use Redis")
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: #4 (No How), #5 (Non-obvious context)

### Case 3: Ambiguous scope

- **Persona**: Product manager
- **Initial input**: "We need to improve the user onboarding"
- **Expected behavior**:
  - Skill identifies that scope is too broad and either narrows it down to a focused single issue OR proposes the Design Flow
  - Does NOT create a vague catch-all issue
  - A vague catch-all issue with no clear boundaries is a failure regardless of which flow was chosen
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
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: #7 (Proposal unambiguous), #9 (Self-contained)

### Case 6: Non-technical feature request in Japanese

- **Persona**: Japanese-speaking business stakeholder
- **Initial input**: "お客様からの問い合わせをもっと早く対応できるようにしたい"
- **Expected behavior**:
  - All interaction and the final issue are in Japanese
  - Skill clarifies what "もっと早く" means concretely
  - Acceptance criteria are measurable
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: #8 (Criteria independently verifiable), language matching

### Case 7: Backlog issue creation with Operation type

- **Persona**: DevOps engineer using Backlog
- **Initial input**: "本番環境のDBマイグレーション手順をissueにしたい"
- **Expected behavior**:
  - Detects Backlog platform from CLAUDE.md config
  - Presents issue type options including Operation
  - Asks for priority confirmation (High / Normal / Low)
  - Uses Operation template with Procedure section
  - Creates issue via `bee issue create`
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: Issue type confirmation, priority confirmation, Operation template usage

### Case 8: Cross-platform setup (Backlog issues + GitHub PRs)

- **Persona**: Engineer in a team using Backlog for task management and GitHub for code
- **Initial input**: "Create a feature request for adding user notifications"
- **Expected behavior**:
  - Detects Backlog as issue tracker from CLAUDE.md
  - Creates the issue on Backlog (not GitHub)
  - Issue type confirmation step is shown
  - Priority confirmation step is shown (Backlog-specific)
  - Expected: stays in Lightweight flow (no escalation)
- **Key criteria to watch**: Correct platform detection, Backlog-specific fields

## Design Flow Cases

### Case 9: Simple feature design

- **Persona**: Engineer describing a new feature
- **Initial input**: "ユーザー検索機能を設計してissueに分解して"
- **Expected behavior**:
  - Explicit request triggers escalation to Design Flow (Step 2 criterion 1)
  - D1 Research: investigates existing user model, API patterns, search infrastructure. Writes research file.
  - D2 Design: asks clarifying questions (search fields, pagination, performance). Proposes approaches. Writes plan with task breakdown and Split Proposal.
  - D3 Annotation: prompts user to annotate plan. Addresses annotations. Each task passes boring implementation test.
  - D4 Issue Creation: confirms the Split Proposal via `AskUserQuestion` BEFORE creating anything, then creates parent issue + sub-issues with dependencies. Cleans up local files.
- **Verification**:
  - [ ] Research file contains relevant file paths and architecture analysis
  - [ ] Plan has concrete code examples, not placeholders
  - [ ] Each sub-issue is independently implementable
  - [ ] Dependencies form a valid DAG
  - [ ] Split proposed via `AskUserQuestion` before any parent/sub-issue is created — never automatic
  - [ ] Local plan/research files are deleted after issue creation

### Case 10: Complex multi-component feature

- **Persona**: Engineer planning a large migration
- **Initial input**: "認証システムをOAuth2に移行したい"
- **Expected behavior**:
  - Multi-area change (auth + session + middleware + routes) triggers escalation to Design Flow (Step 2 criterion 2)
  - D1 Research: investigates current auth, session management, middleware, all auth-dependent routes.
  - D2 Design: multiple approach options (gradual migration vs big bang, library choices). Task breakdown includes migration steps, backward compatibility.
  - D3 Annotation: multiple rounds expected for a complex feature.
  - D4 Issue Creation: split confirmed via `AskUserQuestion`, then parent + sub-issues with careful dependency ordering (infra first, then migration, then cleanup).
- **Verification**:
  - [ ] Research identifies ALL files touching authentication
  - [ ] Design presents migration strategy options with trade-offs
  - [ ] Tasks have correct dependency ordering (no circular deps)
  - [ ] Sub-issues include rollback considerations where appropriate
  - [ ] No sub-issue requires design judgment to implement
  - [ ] Split proposed via `AskUserQuestion` before any parent/sub-issue is created — never automatic

### Case 11: Bug-driven design

- **Persona**: Engineer investigating a performance issue
- **Initial input**: "ログインが遅い。調査して改善計画を立てて"
- **Expected behavior**:
  - Explicit request for investigation + planning triggers escalation to Design Flow
  - D1 Research: profiles login flow, identifies bottlenecks, checks monitoring/logging.
  - D2 Design: based on findings, proposes performance improvements as tasks.
  - D4 Issue Creation: each improvement is a separate sub-issue with measurable acceptance criteria.
- **Verification**:
  - [ ] Research includes profiling data or file-level analysis of the login flow
  - [ ] Acceptance criteria include measurable performance targets
  - [ ] Tasks are ordered by impact (highest impact first, lowest dependency first)

### Case 12: Cross-platform Design Flow (Backlog + GitHub)

- **Persona**: Engineer designing a feature in a Backlog-managed project
- **Initial input**: "Backlogで管理しているプロジェクトで新機能を設計したい"
- **Expected behavior**:
  - Detects Backlog as issue tracker from CLAUDE.md or user input.
  - Uses `bee` CLI for issue creation.
  - Handles Backlog's parent-child issue structure.
  - Mentions dependencies in issue body (Backlog lacks built-in blocking).
- **Verification**:
  - [ ] Correct platform detection
  - [ ] Uses `bee issue create` with `--parent` flag
  - [ ] Dependencies noted in issue body since Backlog lacks blocking feature
  - [ ] Priority is confirmed with user (Backlog has built-in priority levels)

### Case 13: Annotation cycle depth

- **Persona**: Engineer refining a design after seeing the first draft
- **Setup**: After plan is written, user annotates with `<!-- NOTE: completely different approach, use X instead of Y -->`
- **Expected behavior**:
  - Claude reads the annotation and rewrites the affected tasks.
  - Code examples are updated to reflect the new approach.
  - Dependencies are rechecked (approach change may alter dependency graph).
  - Boring implementation test is re-run on all affected tasks.
- **Verification**:
  - [ ] Annotation is fully addressed (not partially)
  - [ ] Code examples match the new approach
  - [ ] Dependency graph is updated if needed
  - [ ] No stale references to the old approach remain

## Flow-Selection and Split-Proposal Cases (new)

### Case 14: Borderline escalation

- **Persona**: Backend engineer
- **Initial input**: "Add rate limiting to the API and an admin toggle for it"
- **Expected behavior**:
  - Signals are weak/mixed (2 areas: API + admin UI, but modest scope) — the skill either justifies staying in the Lightweight Flow, justifies escalating with a clear reason, or asks the user directly via `AskUserQuestion`
  - Silently guessing on weak signals without any justification or question is a failure
- **Verification**:
  - [ ] A flow decision is made with an explicit, stated reason, OR the user is asked
  - [ ] No silent, unexplained flow choice on ambiguous input

### Case 15: Mid-flight escalation

- **Persona**: Engineer with a request that looks simple at first
- **Initial input**: "Add validation to the signup form"
- **Setup**: Codebase analysis (Step L3) reveals the change actually requires touching the frontend form, a new backend validation service, and a schema migration (3+ areas)
- **Expected behavior**:
  - Skill announces the findings from codebase analysis
  - Proposes switching to the Design Flow via `AskUserQuestion` rather than continuing to draft an oversized single issue
  - Does NOT silently continue in the Lightweight Flow once the escalation criteria are clearly met
- **Verification**:
  - [ ] Findings are stated before proposing escalation
  - [ ] Escalation is proposed, not forced
  - [ ] If the user declines, the skill continues in Lightweight Flow with the now-broader scope acknowledged

### Case 16: Split declined

- **Persona**: Engineer who wants one ticket to track everything
- **Setup**: Design Flow (D1-D3) completes and yields 4 tasks; at the Step D4 Split Proposal gate, the user picks "Create a single issue"
- **Expected behavior**:
  - Skill creates ONE comprehensive issue containing the task breakdown as a `## Task Breakdown` section (not a parent/sub-issue hierarchy)
  - No sub-issues or grandchild issues are created
  - Plan and research files are still cleaned up
- **Verification**:
  - [ ] Exactly one issue is created on the tracker
  - [ ] The issue body includes all 4 tasks as clearly delimited subsections
  - [ ] No sub-issue API/CLI calls are made
  - [ ] Local plan/research files are deleted

### Case 17: Nested split (grandchild)

- **Persona**: Engineer designing a feature on GitHub where one task is unusually large
- **Setup**: Design Flow decomposition yields 3 tasks; after refinement, one task remains Large (~2+ hours) and cannot be shrunk further without becoming multiple deliverables
- **Expected behavior**:
  - Skill proposes a nested split for that task specifically (grandchild issues under it) as part of the Step D4 Split Proposal, shown in the ASCII tree with a 3rd level
  - User confirms via `AskUserQuestion`
  - GitHub nested sub-issue links are created (child issue linked to parent; grandchild issues linked to the child)
  - Output hierarchy tree shows all 3 levels
- **Verification**:
  - [ ] Grandchild split is proposed only for the task that stayed Large, not applied to all tasks
  - [ ] Maximum depth of 3 levels is respected
  - [ ] `gh issue edit <child> --add-sub-issue <grandchild>` (or platform equivalent) is used to link grandchildren
  - [ ] Final output tree correctly shows parent → child → grandchild

## External Fact Verification Cases (new)

### Case 18: Plausible-but-wrong external default (Lightweight Flow)

- **Persona**: DevOps engineer describing a Helm chart deployment
- **Initial input**: "We want to enable the built-in cache that ships with the `example-chart` Helm chart — it should already be running by default, we just need to configure it."
- **Setup**: The chart's actual `values.yaml` (available for the tester to check, e.g. a local `values.yaml` with `cache.enabled: false`) shows the cache is disabled by default — the opposite of what the user's phrasing implies.
- **Expected behavior**:
  - Skill does not restate "enabled by default" as fact in the Background/Proposal without checking a primary source
  - Skill fetches/reads the actual `values.yaml` (or equivalent primary source) before finalizing the draft, or — if no primary source is reachable in the test — marks the default-enabled claim as "unverified" instead of asserting it
  - Step L5 criterion 10 blocks presentation of a draft that states the wrong default as fact
- **Key criteria to watch**: #10 (External facts verified), #5 (Non-obvious context — must be correct, not just present)

### Case 19: Plan carries unverified facts into Design Flow issue creation

- **Persona**: Platform engineer designing a self-hosted app deployment (mirrors a real incident: aoshimash/homelab-k8s#258–#260)
- **Setup**: D1 Research and D2 Design produce a plan whose task Background/Approach sections state three external-software claims from memory/search snippets, not from a primary source read this session:
  1. "The Helm chart bundles the cache dependency by default" (actually `false` in the chart's `values.yaml`)
  2. An acceptance criterion requiring a component that no longer exists in the current version of the target software
  3. A "required Postgres extensions" list that is missing one required extension
- **Expected behavior**:
  - At D4 Step 0 (Fact-Check External Claims), before any issue is created, the skill identifies these three claims as precise/actionable external-software facts
  - For each, it fetches a primary source (official docs, actual chart `values.yaml`/source) this session and corrects the claim, or — if unable to verify — marks it explicitly as an assumption ("TBD"/"unverified") rather than stating it as fact
  - No issue is created until the gate is resolved (verified or explicitly marked)
- **Verification**:
  - [ ] All three claims are either corrected against a primary source or marked as assumptions before `gh issue create` (or platform equivalent) runs
  - [ ] The gate does not re-verify unrelated codebase facts already grounded via direct file reads in D1 Research
  - [ ] No issue is created with a stated-as-fact external claim that wasn't verified this session

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
| 2026-07-05 | — | — | — | Merged design-sprint into create-issue: added adaptive Lightweight/Design flow routing, Split Proposal gate, and cases 9-17 (9-13 renumbered from design-sprint, 14-17 new). Case numbering for 1-8 preserved from the original create-issue log above. | — |
| 2026-07-08 | — | — | — | Added criterion 10 (External facts verified) to Lightweight Flow L5 and a Fact-Check External Claims gate (D4 Step 0) to Design Flow, per issue #54 (real-world incident: aoshimash/homelab-k8s#258–#260). Added Cases 18-19. | — |
