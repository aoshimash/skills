# Evaluation Test Cases

Cases 1–12 evaluate the Lightweight Flow (batched question round + draft
approval), cases 13–21 the Design Flow (one plan file + annotation cycle +
single final approval), and cases 22–23 external-fact verification.

## How to Run

1. Start a new conversation and trigger the create-issue skill.
2. Provide the case's initial input; answer follow-ups as the persona would.
3. Score the run against the Flow Criteria below, and the resulting issue
   body/bodies against the 11 issue-quality criteria in SKILL.md L3.
4. Record the run in the Evaluation Log at the bottom.

## Flow Criteria

| # | Criterion | Pass condition |
|---|---|---|
| 1 | Zero questions on complete input | Lightweight Flow with complete initial input asks nothing before the draft approval |
| 2 | One batched round | With incomplete input, every missing item arrives in a **single** round — never a one-question-at-a-time interview |
| 3 | Analysis before asking | Codebase analysis runs before the question round; anything the codebase answers is not asked |
| 4 | Stores checked first | Conventions recorded in the project's agent instructions or user-level config (labels, assignee, language, priority defaults) are applied, not asked |
| 5 | Approval before creation | No issue is created in either flow without an explicit approval of the exact content |
| 6 | Issue quality | Every created body passes the 11 criteria in SKILL.md L3 |
| 7 | Two-layer decisions | Structural decisions are recorded in the issue; local reversible ones are deliberately left to implementation time; no implementation steps, file lists, or code examples appear |
| 8 | One plan file | The Design Flow presents research findings, design decisions, open questions, tasks, and the split proposal as **one** file — no separate research file and no research-approval gate |
| 9 | Open questions embedded | Structural unknowns become numbered in-file questions with options, trade-offs, and a recommendation — not chat interruptions |
| 10 | Annotation cycle closes cleanly | Every note and every answered question is addressed; an unanswered open question blocks approval; one final approval covers plan and split together |
| 11 | Research persisted | After creation, the research findings exist as a comment on the parent (or single) issue, collapsed where the tracker renders HTML |
| 12 | Working tree clean | The plan file is deleted after creation; `git status` shows no plan or research artifacts |
| 13 | Template adoption | Where the repository defines issue templates/forms, they are the skeleton: sections filled, skill content mapped in, unmatched content appended as delimited sections |
| 14 | Split proposed, never automatic | A hierarchy is created only per the approved Split Proposal; when declined, exactly one issue is created with the task breakdown as a section |
| 15 | Real issue numbers | Task Overview tables carry real issue numbers after creation, and links are read back to confirm they registered |
| 16 | External facts verified | Precise external-software claims are verified against a primary source fetched this session, or explicitly marked as assumptions |
| 17 | No obsolete ceremony | The skill text contains no boring-scope test; task quality is judged by the 7 checks in plan-file.md |

## Lightweight Flow Cases

### Case 1: Complete input, zero questions

- **Persona**: Engineer who writes a full request in one message
- **Initial input**: "Create an issue: the `/health` endpoint returns 200 even
  when the database connection is down, so our uptime monitor never pages us.
  It should return 503 when the DB ping fails. Repo conventions already set
  labels and assignee."
- **Expected behavior**: codebase analysis runs, no question is asked, the
  draft is presented once, and the only interaction is the approval choice.
- **Criteria**: 1, 3, 4, 5, 6, 7

### Case 2: Vague bug report from a non-engineer

- **Persona**: Business user, no technical knowledge
- **Initial input**: "The app is slow"
- **Expected behavior**: analysis first, then **one** round carrying every
  unknown (which screen, when, how slow, what "slow" means concretely,
  labels/assignee if unconfigured). Does not draft an issue from "the app is
  slow", and does not ask the questions one at a time.
- **Criteria**: 2, 3, 6

### Case 3: Detailed feature request from an engineer

- **Persona**: Backend engineer familiar with the codebase
- **Initial input**: "We need rate limiting on the API endpoints. Currently
  there's no protection against abuse and we've seen spikes from single IPs."
- **Expected behavior**: analysis identifies the API layer; the batched round
  asks only what is genuinely open (which endpoints, what limits — structural)
  and never asks about storage or library choice (local, reversible). The
  Proposal prescribes no implementation.
- **Criteria**: 2, 6, 7

### Case 4: Ambiguous scope

- **Persona**: Product manager
- **Initial input**: "We need to improve the user onboarding"
- **Expected behavior**: the scope question and the flow choice arrive in the
  same round; the result is either a focused single issue or the Design Flow.
  A vague catch-all issue is a failure regardless of flow.
- **Criteria**: 2, 6

### Case 5: Technical task with implicit How

- **Persona**: Frontend engineer
- **Initial input**: "We should migrate from REST to GraphQL for the dashboard
  API"
- **Expected behavior**: Motivation (why) separated from Proposal (end state);
  no client-library choice or migration steps in the body; Background records
  why REST is used today.
- **Criteria**: 6, 7

### Case 6: Bug report with insufficient reproduction info

- **Persona**: QA tester
- **Initial input**: "The checkout button doesn't work sometimes"
- **Expected behavior**: one round asking browser, what "sometimes" means, and
  the observed failure; "sometimes" is never accepted as a repro step. The
  final issue reproduces reliably.
- **Criteria**: 2, 6

### Case 7: Non-technical request in Japanese

- **Persona**: Japanese-speaking business stakeholder
- **Initial input**: "お客様からの問い合わせをもっと早く対応できるようにしたい"
- **Expected behavior**: interaction and issue in Japanese; "もっと早く" is
  pinned to something measurable; operational goals are separated from
  implementation criteria.
- **Criteria**: 2, 6

### Case 8: Backlog Operation type with priority

- **Persona**: DevOps engineer using Backlog
- **Initial input**: "本番環境のDBマイグレーション手順をissueにしたい"
- **Expected behavior**: Backlog detected; issue type (Operation) and priority
  travel in the **same** round as any other unknown, not as separate gates;
  the Operation skeleton with its Procedure section is used; creation via
  `bee issue create`.
- **Criteria**: 2, 4, 5, 6

### Case 9: Cross-platform setup (Backlog issues + GitHub code)

- **Persona**: Engineer whose team tracks issues on Backlog and code on GitHub
- **Initial input**: "Create a feature request for adding user notifications"
- **Expected behavior**: the issue is created on Backlog, not GitHub;
  Backlog-specific fields (type, priority) are resolved from configuration or
  the single round.
- **Criteria**: 2, 4, 5

### Case 10: Repository issue form present

- **Persona**: Contributor to a repo with `.github/ISSUE_TEMPLATE/bug.yml`
  requiring "What happened?", "Steps", "Version"
- **Initial input**: a bug description that also yields background,
  acceptance criteria, and one structural constraint
- **Expected behavior**: the form is detected in Step 1 and becomes the
  skeleton — every required field filled, skill content mapped into the
  matching fields, and Acceptance Criteria / Design Decisions appended as
  clearly delimited sections rather than dropped.
- **Criteria**: 5, 6, 13

### Case 11: Conventions already recorded

- **Persona**: Engineer in a repo whose agent instructions state "issues in
  English", "always self-assign", "default label: enhancement"
- **Initial input**: a complete feature request in Japanese
- **Expected behavior**: language, assignee, and label are applied from the
  stores without a question; the issue body is in English.
- **Criteria**: 1, 4, 5

### Case 12: An answer opens a new question

- **Persona**: Support lead
- **Initial input**: "Customers can't export their data"
- **Setup**: the batched round's answers reveal that export exists for CSV but
  not for the newly added workspace type — a scope question that could not
  have been asked earlier
- **Expected behavior**: a second **batched** round is acceptable and its
  questions are grouped; a drift back into one-question-at-a-time is a
  failure.
- **Criteria**: 2, 6

## Design Flow Cases

### Case 13: Simple feature design

- **Persona**: Engineer describing a new feature
- **Initial input**: "ユーザー検索機能を設計してissueに分解して"
- **Expected behavior**: D1 researches and writes **one** plan file (goal,
  research findings, design decisions, open questions, tasks, dependency
  graph, split proposal); no research gate; D2 annotation cycle; one final
  approval; D3 creates parent + sub-issues, posts the research comment,
  deletes the plan file.
- **Verification**:
  - [ ] Exactly one plan file is written; no separate research file exists
  - [ ] Tasks have unambiguous scope, binding decisions, and binary AC
  - [ ] No issue body contains implementation steps, file lists, or code
  - [ ] Research comment present on the parent; plan file gone from the tree
- **Criteria**: 5, 6, 7, 8, 10, 11, 12, 14, 15

### Case 14: Complex multi-component feature

- **Persona**: Engineer planning a large migration
- **Initial input**: "認証システムをOAuth2に移行したい"
- **Expected behavior**: multi-area signal escalates to the Design Flow;
  migration strategy alternatives appear as an **embedded open question** with
  a recommendation rather than a chat prompt; dependencies order the tasks
  (infra → migration → cleanup).
- **Verification**:
  - [ ] Research covers every file touching authentication
  - [ ] The strategy choice is an in-file open question, answered inline
  - [ ] Dependencies form a DAG with no cycles
  - [ ] Rollback constraints appear where relevant
- **Criteria**: 8, 9, 10, 14

### Case 15: Bug-driven design

- **Persona**: Engineer investigating a performance problem
- **Initial input**: "ログインが遅い。調査して改善計画を立てて"
- **Expected behavior**: research profiles the login path; each improvement
  becomes a task with a measurable criterion; the findings survive as the
  research comment.
- **Criteria**: 8, 11, 6

### Case 16: Cross-platform Design Flow (Backlog)

- **Persona**: Engineer designing a feature in a Backlog-managed project
- **Initial input**: "Backlogで管理しているプロジェクトで新機能を設計したい"
- **Expected behavior**: `bee` used throughout; parent-child via
  `--parent-issue`; dependencies stated in the body since Backlog has no
  blocking relation; the research comment posted as a **plain** comment titled
  `Research findings (create-issue, YYYY-MM-DD)` because Backlog does not
  render HTML.
- **Criteria**: 11, 14, 15

### Case 17: Annotation changes the approach

- **Persona**: Engineer refining a design after the first plan
- **Setup**: the user annotates `<!-- NOTE: completely different approach, use
  X instead of Y -->`
- **Expected behavior**: affected tasks rewritten, Design Decisions updated,
  dependency graph and Split Proposal re-derived, task quality checks re-run,
  no stale references to the old approach.
- **Criteria**: 10, 17

### Case 18: Open question answered inline

- **Persona**: Engineer answering on the `**Answer:**` line
- **Setup**: the plan asks whether archived users are searchable; the user
  answers "B, with the filter defaulting to off"
- **Expected behavior**: the answer becomes a row in Design Decisions with its
  rationale, the affected task scopes and AC change, and the question is
  removed from `## Open Questions` — the user is not asked again in chat or in
  the created issues.
- **Criteria**: 9, 10, 7

### Case 19: Unanswered open question at the gate

- **Persona**: Engineer who annotates everything except one question
- **Expected behavior**: the final approval is not presented; the outstanding
  question is named and another annotation round is requested. Guessing an
  answer, or creating issues with the question unresolved, is a failure.
- **Criteria**: 10, 5

### Case 20: Split declined

- **Persona**: Engineer who wants one ticket for everything
- **Setup**: the plan yields 4 tasks; the user annotates the Split Proposal to
  ask for a single issue, then approves
- **Expected behavior**: exactly ONE issue is created, carrying the breakdown
  as a `## Task Breakdown` section; no sub-issue calls are made; the research
  comment lands on that single issue; the plan file is deleted.
- **Criteria**: 11, 12, 14

### Case 21: Nested split (grandchild)

- **Persona**: Engineer on GitHub with one unusually large task
- **Setup**: after refinement one task remains Large and is proposed for a
  nested split in the plan's Split Proposal
- **Expected behavior**: the nested level appears in the approved tree; the
  child is created as a sub-issue that also carries its own Task Overview;
  grandchildren are linked to the child; both Task Overview tables are updated
  with real numbers; depth never exceeds 3.
- **Criteria**: 14, 15

## External Fact Verification Cases

### Case 22: Plausible-but-wrong external default (Lightweight)

- **Persona**: DevOps engineer describing a Helm chart deployment
- **Initial input**: "We want to enable the built-in cache that ships with the
  `example-chart` Helm chart — it should already be running by default, we just
  need to configure it."
- **Setup**: the chart's actual `values.yaml` has `cache.enabled: false`
- **Expected behavior**: the default-enabled claim is checked against the
  chart's own values file before the draft is presented, corrected if wrong,
  or marked "unverified" — criterion 11 in SKILL.md L3 blocks a draft that
  states the wrong default as fact.
- **Criteria**: 16, 6

### Case 23: Plan carries unverified facts into issue creation

- **Persona**: Platform engineer designing a self-hosted deployment (mirrors
  aoshimash/homelab-k8s#258–#260)
- **Setup**: the approved plan states three external claims taken from memory
  or search snippets: a chart bundling a dependency "by default" (actually
  false), an AC requiring a component removed in the current version, and a
  required-extensions list missing one entry
- **Expected behavior**: D3 step 1 catches all three before any issue is
  created — each is corrected against a primary source fetched this session or
  explicitly marked as an assumption. Codebase facts grounded by direct file
  reads are not re-verified.
- **Criteria**: 16, 5

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
| 2026-07-05 | — | — | — | Merged design-sprint into create-issue: adaptive Lightweight/Design routing, Split Proposal gate, cases 9-17. | — |
| 2026-07-08 | — | — | — | Added external-fact criterion and the D4 fact-check gate per issue #54. | — |
| 2026-07-16 | — | — | — | Unified design philosophy: reader-agnostic issues, no perishable implementation detail; Sub-Issue template rewritten; pitfall recording made mandatory. | — |
| 2026-07-26 | — | — | — | Platform reference corrections verified against `gh` 2.96.0 and the Backlog/GitLab CLI docs (no behavior change). | — |
| 2026-07-26 | — | — | — | Documented the shapes of the `gh` relationship JSON fields and demoted the REST calls to fallbacks. | — |

The rows above evaluate the **pre-rewrite**, one-question-at-a-time skill and
are historical. Case numbers in them refer to the old case list.

### 2026-07-27 — Batched-interaction rewrite (Refs #96)

Wholesale rewrite per the settled decisions in #91/#96. The criteria table and
cases 1–23 above were written for the new flows.

Structural changes:

- `SKILL.md`: rewritten. Lightweight Flow is now analyze → **one batched
  question round** (skipped entirely on complete input) → draft →
  self-evaluate → single approval. The old L1 type-confirmation step and the
  "ask exactly one question at a time" instruction are gone; codebase analysis
  moved **before** the question round so it can decide what is actually open.
  Design Flow is D0 setup → D1 one plan file → D2 annotation cycle with a
  single final approval → D3 creation. The "Tasks must be boringly scoped"
  principle and both boring-scope test invocations are removed; the
  self-evaluation table gains criterion 9 (structural decisions recorded) and
  a reworded criterion 10 (self-contained, with local decisions deliberately
  open) — 11 criteria in total. New sections: "Repository Issue Templates" and
  an interaction-budget table.
- `references/plan-file.md` (new, replaces `research.md` + `design.md`):
  research procedure, design procedure, the 7 task quality checks, and the
  consolidated plan file format including `## Research Findings`,
  `## Open Questions` (numbered, with options, a recommendation, and an
  `**Answer:**` line), and `## Split Proposal`.
- `references/annotation-cycle.md`: rewritten to resolve answered open
  questions alongside annotations, and to carry the flow's **single** final
  approval covering plan and split together. Unanswered questions block it.
- `references/issue-creation.md`: the separate split gate is gone (approved in
  D2); a template-selection step and a research-comment step were added; the
  cleanup step deletes only the plan file, since there is no research file.
- `references/templates.md`: repository templates declared to take precedence;
  a `## Design Decisions` section documented for structural decisions and
  added to the Sub-Issue template.
- Platform guides: template detection (`.github/ISSUE_TEMPLATE/`,
  `.gitlab/issue_templates/`, none for Backlog) and comment commands
  (`gh issue comment --body-file`, `glab issue note -m`,
  `bee issue comment -b`) added. `gh` flags verified against local `gh`
  2.96.0; `glab` flags against the official CLI command docs; `bee issue
  comment` against nulab.github.io/bee; template paths against GitHub's and
  GitLab's own documentation, all fetched 2026-07-27.

Desk-check of the rewritten cases against the new texts (static inspection):

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass | L2 opens with "if nothing is unresolved, skip this step entirely"; L4 is the only interaction |
| 2 | Pass | L1 analysis precedes L2; the L2 table batches every unknown in one round |
| 3 | Pass | L2 table restricts questions to structural decisions; L3 criterion 4 blocks technology prescription |
| 4 | Pass | Step 2 folds a weak-signal flow choice into the same round |
| 5 | Pass | L3 criteria 3 and 4 |
| 6 | Pass | L2 row "Reproduction details" |
| 7 | Pass | L3 step 3 (language) and criterion 8 (operational vs implementation) |
| 8 | Pass | L2 rows for issue type and priority sit in the same round; Backlog guide unchanged for Operation |
| 9 | Pass | Step 1 detects the tracker independently of the code host |
| 10 | Pass | Step 1 item 3 + "Repository Issue Templates" mapping rules + GitHub guide's form handling |
| 11 | Pass | "Ask once, in one round" principle and L2's store check |
| 12 | Pass | "Never settle for vague" principle explicitly allows a batched follow-up round |
| 13 | Pass | D1 writes one file; D3 posts the comment and deletes the plan |
| 14 | Pass | plan-file.md step 2 item 2 routes approach choices to `## Open Questions` |
| 15 | Pass | plan-file.md research section; issue-creation.md step 7 |
| 16 | Pass | Backlog guide's plain-comment fallback; parent-child and body-level dependencies unchanged |
| 17 | Pass | annotation-cycle.md step 2 item 4 re-derives graph and split, re-runs the checks |
| 18 | Pass | annotation-cycle.md step 2 item 3, first bullet |
| 19 | Pass | annotation-cycle.md step 4, check 2 |
| 20 | Pass | issue-creation.md step 3 single-issue case; step 7 posts to that issue |
| 21 | Pass | issue-creation.md step 4 grandchild paragraph + step 5 |
| 22 | Pass | L3 criterion 11 blocks presentation |
| 23 | Pass | issue-creation.md step 1 |

All 23 cases pass the desk-check. This entry records a static evaluation
(instructions inspected against expected behavior); no live conversational run
was performed for this rewrite. Case 10 (repository issue forms) and case 19
(unanswered open question) exercise behavior that has never been run live and
are the first candidates for a live run.
