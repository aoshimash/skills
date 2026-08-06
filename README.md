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

`create-issue` and `implement-issue` cover the full issue lifecycle. Each adapts to scale: `create-issue` goes from a quick single issue to a researched, user-annotated design decomposed into an issue hierarchy; `implement-issue` goes from one autonomous implementation to a dependency-ordered parallel batch. The issue tracker is the interface between them — either skill also works standalone, since a hand-written issue works with `implement-issue` and a `create-issue` issue can be implemented manually.

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
│                             │            │    propagation → Summary     │
│                             │            │  → Harvest (once per batch)  │
└─────────────────────────────┘            └──────────────────────────────┘
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
# Parent issue / milestone / label / list → confirm batch → dependency graph
#   → parallel worktrees → review gates → summary → harvest once
```

**Key properties:**

- **Issue tracker is the interface** — Both skills connect only through the issue tracker (GitHub, GitLab, Backlog). No skill-specific files persist after completion.
- **Works with humans and AI** — Issues created by `create-issue` are readable and implementable by anyone. Issues written by hand work with `implement-issue`. A good issue is the same for both readers: it explains why and what — never how.
- **Splitting is always proposed, never automatic** — `create-issue` defaults to a single issue; a parent + sub-issue (or nested grandchild) hierarchy is only created after the user confirms a Split Proposal.
- **Annotation cycle** — in the Design Flow, plans are refined through inline notes in a local markdown file. The file is deleted after issues are created.
- **Autonomous implementation, decisions logged not asked** — `implement-issue` runs from invocation to PR without routine questions. There is no plan-approval gate: decisions come from the issue, its parent, the repository's agent instructions, or user-level configuration, and land in the PR body instead of in chat. Only genuinely undecidable decisions stop the run, as one batched question whose answers are written back to the issue.
- **Parallel execution** — in Batch mode, `implement-issue` resolves issue dependencies as a DAG and dispatches independent issues in parallel using git worktrees.
- **Two-stage review, always** — every PR (single or batch) is reviewed for spec compliance (does it match the issue?) then code quality (is it well-written?). Pattern propagation across in-flight PRs only applies in Batch mode.
- **Nothing unsafe leaves the machine** — a security review of the pending changes runs after checks and self-review pass and before the branch is pushed. Unresolved Critical/High findings block the push.
- **Machines finish before humans start** — every PR opens as a **draft** and flips to ready-for-review only once the review gates pass, CI is green, and the repository's own automated reviewers have been responded to. A PR that can't clear them stays a draft with the unresolved state recorded. Human review comments are never auto-addressed — those go through `respond-to-pr-review`.
- **Decisions are harvested after delivery** — once the PR is ready, decisions that generalize past the issue are offered for promotion into a durable store: the repository's agent instructions (as a separate PR) or user-level configuration. One batched confirmation, nothing written without it, and most runs produce no candidates at all.

### Design Philosophy

The issue workflow draws from two sources, combines them with an issue-centric approach, and has since been revised for an autonomy-first workflow built on 2026-era models:

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

## Skills

| Skill | Description |
|-------|-------------|
| [create-issue](plugins/aoshimash-skills/skills/create-issue/) | Create well-structured issues on any platform (GitHub, GitLab, Backlog) with codebase analysis — from a quick single issue (one batched question round, one approval) to a designed issue hierarchy (one annotated plan file → parent + sub-issues, research kept as an issue comment) |
| [implement-issue](plugins/aoshimash-skills/skills/implement-issue/) | Read issues, implement autonomously, and open review-first draft PRs — two-stage review, pre-push security review, automated-reviewer response, flip to ready, then post-PR decision harvesting; batch mode (dependency graph, worktrees, parallel agents) for parent issues / milestones / labels / lists |
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
