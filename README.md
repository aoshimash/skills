# aoshimash/skills

Personal [Agent Skills](https://agentskills.io) collection for **development workflow** — issues, pull requests, dependency updates, and the shared conventions behind them. Distributed as a Claude Code plugin, but each skill under `plugins/aoshimash-skills/skills/` is a plain Agent Skills directory usable by any compliant agent.

## Installation

1. Add the marketplace:

```
/plugin marketplace add aoshimash/skills
```

2. Install the plugin:

```
/plugin install aoshimash-skills@aoshimash-skills
```

### Using with other agents

The plugin is only one distribution channel. Each skill under `plugins/aoshimash-skills/skills/` is a plain [Agent Skills](https://agentskills.io) directory (a `SKILL.md` plus optional `references/`, `scripts/`, `assets/`), so any agent implementing the Agent Skills spec can use one directly — point your agent at, or copy, the skill directory.

## Issue Workflow

`create-issue`, `implement-issue`, and `merge-issue-prs` cover the full issue lifecycle. Each adapts to scale: `create-issue` goes from a quick single issue to a researched, user-annotated design decomposed into an issue hierarchy; `implement-issue` goes from one autonomous implementation to a dependency-ordered parallel batch; `merge-issue-prs` merges a batch's own PRs into a per-milestone integration branch, so the issues it merged cost one human review per milestone rather than one apiece — a PR it defers still goes to a human individually, and holds up the integration branch's cleanup until it is closed. The issue tracker is the interface between them — each skill also works standalone, since a hand-written issue works with `implement-issue`, a `create-issue` issue can be implemented manually, and the merge gate runs on a parent issue's ready PRs without the batch.

```
create-issue                               implement-issue
┌─────────────────────────────┐            ┌──────────────────────────────┐
│ Lightweight Flow (default)  │            │ Single Mode (default)        │
│  Analyze → One batched      │            │  Understand & decide         │
│  question round → Draft     │            │  → Implement & verify        │
│  → Self-eval → Approve      │            │  → Draft PR → review gates   │
│                             │            │  → CI → automated reviewers  │
│ Design Flow (escalated)     │  Issues    │  → Ready → Harvest decisions │
│  One plan file (research +  │ ────────→  │                              │
│  design + open questions +  │  (tracker) │ Batch Mode (parent/milestone │
│  split) → Annotation cycle  │            │  /label/list)                │
│  → Approve → Issues         │            │  Dependency graph            │
│                             │            │  → Parallel worktrees        │
│                             │            │  → Review gates + pattern    │
│                             │            │    propagation               │
│                             │            │  → Merge gate (integration   │
│                             │            │    mode) → Summary           │
│                             │            │  → Harvest (once per batch)  │
└─────────────────────────────┘            └──────────────────────────────┘
```

Batch mode picks one of two **merge modes** inside the execution-plan approval, and that choice decides where a ready PR goes next:

```
                    ready PR (draft → ready = "machines done")
                                     │
             standard mode ──────────┴────────── integration mode
                   │                                     │
                   ▼                                     ▼
      a human reviews and merges         merge-issue-prs (the merge gate)
      each PR — N issues cost            eligibility, fail closed
      N human reviews                    → serial merge, one in flight
                                         → verify on integration-branch CI
                                         → revert + stop the line on failure
                                                         │
                                                         ▼
                                         integration/issue-<parent>
                                                         │
                                                         ▼
                                         one integration→main PR per
                                         milestone: a live dashboard while
                                         the batch runs, flipped to ready
                                         when it is terminal, green,
                                         unescalated, and fully disclosed
                                                         │
                                                         ▼
                                         one human review per milestone
                                         → merge to main
```

**Typical usage:**

```
> /create-issue
# Simple request → analyze codebase → one batched question round → draft → approve → create
# Complex request → one plan file (research + design + open questions + split) → annotate → approve → create issue(s)

> /implement-issue
# Single issue → understand & decide (no routine questions) → implement & verify
#   → security review → draft PR → two-stage review gates → CI
#   → automated reviewers → flip to ready → harvest decisions → recap
# Parent issue / milestone / label / list → confirm batch (standard or
#   integration mode) → dependency graph → parallel worktrees → review gates
#   → merge gate (integration mode) → summary → harvest once

> /merge-issue-prs
# Parent issue / integration branch → eligibility triage (fail closed)
#   → serial merge → verify on integration-branch CI → revert on failure
#   → milestone PR (integration→main): draft while the batch runs, ready
#     once all four flip conditions hold → a human reviews and merges it
```

**Key properties:**

- **Issue tracker is the interface** — The skills connect through the issue tracker (GitHub, GitLab, Backlog) and, for the merge gate, the repository's git state. No skill-specific files persist after completion; every run re-derives what it needs.
- **Works with humans and AI** — Issues created by `create-issue` are readable and implementable by anyone. Issues written by hand work with `implement-issue`. A good issue is the same for both readers: it explains why and what — never how.
- **Splitting is always proposed, never automatic** — `create-issue` defaults to a single issue; a parent + sub-issue (or nested grandchild) hierarchy is only created after the user confirms a Split Proposal.
- **Annotation cycle** — in the Design Flow, plans are refined through inline notes in a local markdown file. The file is deleted after issues are created.
- **Autonomous implementation, decisions logged not asked** — `implement-issue` runs from invocation to PR without routine questions. There is no plan-approval gate: decisions come from the issue, its parent, the repository's agent instructions, or user-level configuration, and land in the PR body instead of in chat. Only genuinely undecidable decisions stop the run, as one batched question whose answers are written back to the issue.
- **Parallel execution** — in Batch mode, `implement-issue` resolves issue dependencies as a DAG and dispatches independent issues in parallel using git worktrees. Where the environment supports per-instance model selection, each runs on the capability tier its issue's content calls for: mechanical work runs cheaply, judgment-heavy work does not, and uncertainty resolves upward.
- **Two merge modes in Batch mode** — **standard** bases every worktree and PR on the default branch, and each PR waits for its own human reviewer. **Integration** bases them on one integration branch and hands each ready PR to `merge-issue-prs`, so a dependency counts as satisfied only once its PR merged and was not reverted — dependents finally build on their dependencies' code rather than on a base that lacks it. The mode is chosen inside the execution-plan approval, never as a separate gate; Single mode never offers it, and integration mode is offered only where `merge-issue-prs` is installed and the repository is on GitHub.
- **Machine merges land only on the integration branch** — `merge-issue-prs` never merges into the default branch, and it decides each PR under a fail-closed eligibility policy (pipeline-created PR, source issue authored by a user with repository write access, machine gates passed, CI green, no human comment). Merges run one at a time, each verified after it lands against the integration branch's own CI, with auto-revert and stop-the-line when verification does not hold and immediate escalation when a revert itself fails. Anything unknown, ambiguous, or possibly truncated is deferred to a human rather than merged.
- **One human review per milestone** — the integration→main PR is the batch's single human checkpoint: a live dashboard while the batch runs, flipped to ready only once the batch is terminal, the branch is green at the head a human would merge, no escalation is outstanding, and the body is final — with every deferred, blocked, or reverted issue listed alongside the human action it needs. A human comment on any per-issue PR removes it from the autonomous path permanently and sends it to `respond-to-pr-review`.
- **A batch survives its session** — an integration-mode batch re-derives where an earlier session stopped from the issue tracker and git alone; no state file persists between sessions. The one thing it cannot re-derive is which issues a human approved into the batch, so the approving session records that on the parent issue — the issues considered and the subset approved, written once and never updated. A later unattended session dispatches the issues that record enumerates and no others, which is how a scheduled run advances past the group it inherited. The record is trusted only when its author holds repository write access, and absent or untrusted it falls back to advancing the PRs an approved plan already produced. Either way scheduling extends a batch's reach without widening its scope: an issue linked in after the approval is outside the record, and the milestone PR remains a human's to review and merge.
- **Two-stage review, always** — every PR (single or batch) is reviewed for spec compliance (does it match the issue?) then code quality (is it well-written?). Pattern propagation across in-flight PRs only applies in Batch mode.
- **Nothing unsafe leaves the machine** — a security review of the pending changes runs after checks and self-review pass and before the branch is pushed. Unresolved Critical/High findings block the push.
- **Machines finish before humans start** — every PR opens as a **draft** and flips to ready-for-review only once the review gates pass, CI is green, and the repository's own automated reviewers have been responded to. A PR that can't clear them stays a draft with the unresolved state recorded. Human review comments are never auto-addressed — those go through `respond-to-pr-review`. The flip means the same thing in both merge modes — *machines done* — and only its reader changes: a human by default, the merge gate in integration mode.
- **Decisions are harvested after delivery** — once the PR is ready, decisions that generalize past the issue are offered for promotion into a durable store: the repository's agent instructions (as a separate PR) or user-level configuration. One batched confirmation, nothing written without it, and most runs produce no candidates at all.

### Design Philosophy

The issue workflow draws from two sources, combines them with an issue-centric approach, has since been revised for an autonomy-first workflow built on 2026-era models, and was then extended to close the merge loop:

**From [superpowers](https://github.com/obra/superpowers):**
- Brainstorming quality — deep clarifying questions, multiple approaches with trade-offs
- Subagent-driven parallel execution with git worktree isolation
- Two-stage review — spec compliance before code quality, because they catch different classes of problems

**From [Boris Tane's workflow](https://boristane.com/blog/how-i-use-claude-code/):**
- Dedicated research phase before design — prevents implementations that ignore existing patterns, caching layers, or conventions
- Plan as shared mutable state — a local markdown file the user annotates inline, not chat-based steering. Document-based iteration is more precise than conversational back-and-forth
- Annotation cycle — the user adds `<!-- NOTE: ... -->` comments directly in the plan file, Claude addresses each one, repeat until clean. This is where the highest-value human input happens

superpowers also contributed a staged workflow with hard approval gates, and both sources shared a "boring implementation" ideal — every creative decision settled during planning so that implementing is mechanical. Both ideas have been deliberately retired; see the autonomy-first revision below.

**Issue-centric design (original):**
- superpowers stores specs and plans in `docs/superpowers/` files. This works for solo use but creates friction in team settings — not everyone uses the same tools, and tool-specific files clutter the repo
- Instead, the issue tracker is the single shared artifact. `create-issue`'s Design Flow uses one local plan file only during the annotation cycle, then converts everything to issues — the research findings stay as a comment on the parent issue, and the file is deleted
- This means a team member who doesn't use these skills can still read the issues, pick one up, and implement it — the workflow degrades gracefully

**Reader-agnostic issues (original):**
- An issue is read by humans and AI agents alike, and a good issue is the same for both: motivation (why), desired end state with binary acceptance criteria (what), and the structural design decisions and constraints behind them — never implementation steps, file-edit lists, or code examples (how)
- Time passes between issue creation and implementation. Implementation detail rots in that gap — other changes land, files move, approaches get invalidated; design decisions and constraints do not. Issues record decisions, never steps
- The quality bar for an issue is tight scope, recorded structural decisions and constraints, and binary acceptance criteria. The implementer (human or `implement-issue`) plans the how at implementation time, against the codebase as it exists then
- Findings from research that will help at implementation time (current state, gotchas, related code) still belong in the issue as supplementary background — they help humans and AI alike

**Autonomy-first revision (2026, original):**
- Earlier versions gated implementation behind plan approvals and required every design decision to be settled at issue-creation time. Current models plan natively and follow intent-level instructions reliably, while user round trips became the scarce resource — so pre-approval gates are replaced by autonomous execution reviewed post-hoc at the PR
- Two-layer decision timing — structural decisions (shape of a split, cross-issue consistency, high reversal cost) are recorded in issues at creation time; local, reversible decisions are delegated to implementation time, guided by the decision principles in the [shared rules corpus](plugins/aoshimash-skills/rules/agent-rules.md), and logged in the PR. When in doubt, a decision belongs on the issue side
- Never ask twice — before asking, check the decision stores (issue body, repository agent instructions, user-level configuration); every answer is written back to the store matching its scope. The loop closes from the write side too: decisions the implementer made on its own are harvested once the PR is delivered, and the ones that generalize are offered for promotion into a durable store in one batched confirmation — a rule that binds every later run is the user's to approve, not the run's
- Review-first PRs — removing mid-run gates concentrates human judgment at the PR, so the PR body is ordered for the reviewer: decisions and risk areas first, acceptance criteria mapped to verification evidence, mechanical changes last. Machines finish before humans start: PRs stay draft until CI, the internal review gates, and repository-configured automated reviewers are done; human review comments are never auto-addressed
- This revision is the design contract both skills were rewritten against — `implement-issue` in [#93](https://github.com/aoshimash/skills/issues/93), [#94](https://github.com/aoshimash/skills/issues/94), [#95](https://github.com/aoshimash/skills/issues/95), and `create-issue` in [#96](https://github.com/aoshimash/skills/issues/96) — and the diagram above describes them as they are today. All tracked under [#91](https://github.com/aoshimash/skills/issues/91)
- Informed by Anthropic's published guidance at the time of this revision — [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5), [Claude Code best practices](https://code.claude.com/docs/en/best-practices), and [harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) — and the Claude Code team's published workflow ([How Boris uses Claude Code](https://howborisusesclaudecode.com/)). Full rationale and decision log: [#91](https://github.com/aoshimash/skills/issues/91)

**Closing the loop — machine merges, one human checkpoint (2026, original):**
- The autonomy-first revision moved human judgment to the PR, and per-PR review then became the pipeline's throughput cap. `implement-issue` ended at ready-for-review and contained no merge step at all, so N issues meant N human reviews — and because every batch worktree branched from the default branch, a dependent issue could not build on its dependency's code until a human merged it. Batch mode parallelized implementation but not review
- The model this follows puts human judgment at spec/design approval upstream and at risk-tiered review downstream, with machine gates in between. The upstream checkpoint already existed (`create-issue`'s Design Flow), so what was missing was the downstream half — the part the 2025–2026 write-ups referenced below address
- **Stage B is what exists today** — machine merges confined to a per-milestone integration branch, and human review relocated rather than removed: one integration→main PR per milestone, which nothing in the pipeline merges, approves, or reviews. Reaching the default branch therefore still costs a human reviewing and merging a PR; what changes is that it costs one per milestone instead of one per issue. The safety model is not new either: it is ported from `merge-renovate-prs`, this repository's existing precedent for merging without sign-off — machine-checkable preconditions instead of a sign-off, strictly serial merges, post-merge verification, fail-closed auto-revert, stop-the-line on the first failure, and escalation when the revert itself fails
- **Stage A is deferred on purpose** — risk-tiered auto-merge straight to the default branch under a low-risk policy. A risk policy has to be calibrated on observed history rather than invented upfront, and integration mode is what produces that history. It is recorded here so the follow-up arrives with provenance instead of as a fresh idea; AGENTS.md's design axis is explicit that introducing it changes the axis rather than applies it
- What autonomy here does *not* buy: the plan is still approved by a person. Recording that approval in the tracker ([#128](https://github.com/aoshimash/skills/issues/128)) lets a scheduled session implement the issues it covers, so a batch can now run past the group it inherited — but never past the plan: an issue nobody approved is never started, and the milestone PR is still merged by a human. Scheduling makes a batch outlive its session; it does not remove the checkpoint
- Tracked under [#109](https://github.com/aoshimash/skills/issues/109) — the merge gate in [#110](https://github.com/aoshimash/skills/issues/110), [#114](https://github.com/aoshimash/skills/issues/114), [#111](https://github.com/aoshimash/skills/issues/111); integration mode, cross-session re-entry, and model tiers in [#115](https://github.com/aoshimash/skills/issues/115), [#112](https://github.com/aoshimash/skills/issues/112), [#113](https://github.com/aoshimash/skills/issues/113); this documentation in [#116](https://github.com/aoshimash/skills/issues/116). Informed by Anthropic's [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — externalized state, fresh context per work unit, independent verification — and by [Ona](https://ona.com/stories/auto-approving-low-risk-prs) and [Rewind](https://rewind.com/blog/ai-approve-pull-requests-safely/) on risk-tiered auto-approval, which inform Stage A rather than Stage B

## Skills

| Skill | Description |
|-------|-------------|
| [create-issue](plugins/aoshimash-skills/skills/create-issue/) | Create well-structured issues on any platform (GitHub, GitLab, Backlog) with codebase analysis — from a quick single issue (one batched question round, one approval) to a designed issue hierarchy (one annotated plan file → parent + sub-issues, research kept as an issue comment) |
| [implement-issue](plugins/aoshimash-skills/skills/implement-issue/) | Read issues, implement autonomously, and open review-first draft PRs — two-stage review, pre-push security review, automated-reviewer response, flip to ready, then post-PR decision harvesting; batch mode (dependency graph, worktrees, parallel agents on content-based model tiers) for parent issues / milestones / labels / lists, with an optional integration mode that bases every PR on one integration branch, hands the ready ones to `merge-issue-prs`, and resumes across sessions from the tracker and git |
| [go](plugins/aoshimash-skills/skills/go/) | Finish a change at a consistent verification bar — derive what the change claims to make true, exercise those claims end to end in the project's own environment, run only the checks no project automation already covers, remove verification residue, and end with an explicit `VERIFIED` / `PARTIALLY VERIFIED` / `NOT VERIFIED` report; never silent success |
| [analyze-sessions](plugins/aoshimash-skills/skills/analyze-sessions/) | Analyze Claude Code session history to detect recurring patterns and propose improvements to skills and settings.json |
| [respond-to-pr-review](plugins/aoshimash-skills/skills/respond-to-pr-review/) | Process PR review comments one by one — explain, confirm actions, implement fixes, and post reply comments |
| [merge-issue-prs](plugins/aoshimash-skills/skills/merge-issue-prs/) | Merge the pipeline's own per-issue implementation PRs into a per-milestone integration branch without per-PR human review — a fail-closed eligibility policy (pipeline-created PR, write-access issue author, gates passed, CI green, no human comment) rules each PR eligible or deferred, merges run strictly serially with post-merge verification and auto-revert, and one integration→main PR carries the human review |
| [merge-renovate-prs](plugins/aoshimash-skills/skills/merge-renovate-prs/) | Merge Renovate PRs one at a time, autonomously by default — verify monitoring/revert preconditions, LLM pre-check, merge, post-merge verification, and auto-revert on failure; interactive per-PR-approval mode available |
| [sync-agent-rules](plugins/aoshimash-skills/skills/sync-agent-rules/) | Write the shared conventions from [the rule corpus](plugins/aoshimash-skills/rules/agent-rules.md) into the current repository's `AGENTS.md` — detect which rules apply from the files actually present, write only those into a delimited managed block, and open a PR; additive, so nothing is removed without confirmation |
| [collect-agent-rules](plugins/aoshimash-skills/skills/collect-agent-rules/) | Promote hand-written conventions from your own repositories into [the rule corpus](plugins/aoshimash-skills/rules/agent-rules.md) — confirm which repositories to scan, read their `AGENTS.md` over the API without cloning, ignore managed blocks, propose the conventions that recur across repositories, and open a PR for the ones approved one at a time |

## Structure

```
plugins/aoshimash-skills/
├── .claude-plugin/plugin.json    # Plugin manifest
├── rules/
│   └── agent-rules.md            # Shared conventions corpus (read by sync-agent-rules,
│                                 #   appended to by collect-agent-rules)
└── skills/
    └── <skill-name>/
        ├── SKILL.md              # Skill definition (required)
        ├── scripts/              # Helper scripts (optional)
        ├── assets/               # Templates and static files (optional)
        └── references/           # Reference docs (optional)
```

`rules/agent-rules.md` sits outside every skill on purpose: a running skill
resolves to a version-pinned copy rather than the git checkout, so the corpus is
addressed as a repository path and fetched over the GitHub API at runtime. That
also means a rule added there is distributable immediately, without waiting for
an installed plugin to update.

## License

MIT
