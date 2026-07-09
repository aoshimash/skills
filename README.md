# aoshimash/skills

Personal [Agent Skills](https://agentskills.io) collection. Distributed as a Claude Code plugin, but each skill under `plugins/aoshimash-skills/skills/` is a plain Agent Skills directory usable by any compliant agent.

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

`create-issue` and `implement-issue` cover the full issue lifecycle. Each adapts to scale: `create-issue` goes from a quick single issue to a researched, user-annotated design decomposed into an issue hierarchy; `implement-issue` goes from one interactive implementation to a dependency-ordered parallel batch. The issue tracker is the interface between them — either skill also works standalone, since a hand-written issue works with `implement-issue` and a `create-issue` issue can be implemented manually.

```
create-issue                               implement-issue
┌─────────────────────────────┐            ┌──────────────────────────────┐
│ Lightweight Flow (default)  │            │ Single Mode (default)        │
│  Gather → Analyze → Draft   │            │  Plan → Approve → Implement  │
│  → Self-eval → Create       │            │  → PR → Review gates         │
│                             │            │                              │
│ Design Flow (escalated)     │  Issues    │ Batch Mode (parent/milestone │
│  Research → Design          │ ────────→  │  /label/list)                │
│  → Annotation cycle         │  (tracker) │  Dependency graph            │
│  → Split Proposal (asks)    │            │  → Parallel worktrees        │
│  → Issue hierarchy          │            │  → Review gates + pattern    │
│                             │            │    propagation → Summary     │
└─────────────────────────────┘            └──────────────────────────────┘
```

**Typical usage:**

```
> /create-issue
# Simple request → gather info → analyze codebase → draft → self-eval → create
# Complex request → research → design → annotate plan → propose a split → create issue(s)

> /implement-issue
# Single issue → plan → approve → implement → PR → two-stage review
# Parent issue / milestone / label / list → confirm batch → dependency graph
#   → parallel worktrees → review gates → summary
```

**Key properties:**

- **Issue tracker is the interface** — Both skills connect only through the issue tracker (GitHub, GitLab, Backlog). No skill-specific files persist after completion.
- **Works with humans and AI** — Issues created by `create-issue` are readable and implementable by anyone. Issues written by hand work with `implement-issue`.
- **Splitting is always proposed, never automatic** — `create-issue` defaults to a single issue; a parent + sub-issue (or nested grandchild) hierarchy is only created after the user confirms a Split Proposal.
- **Annotation cycle** — in the Design Flow, plans are refined through inline notes in a local markdown file. The file is deleted after issues are created.
- **Parallel execution** — in Batch mode, `implement-issue` resolves issue dependencies as a DAG and dispatches independent issues in parallel using git worktrees.
- **Two-stage review, always** — every PR (single or batch) is reviewed for spec compliance (does it match the issue?) then code quality (is it well-written?). Pattern propagation across in-flight PRs only applies in Batch mode.

### Design Philosophy

The issue workflow draws from two sources and combines them with an issue-centric approach:

**From [superpowers](https://github.com/obra/superpowers):**
- Staged workflow with hard gates (no implementation before design approval)
- Brainstorming quality — deep clarifying questions, multiple approaches with trade-offs
- Subagent-driven parallel execution with git worktree isolation
- Two-stage review — spec compliance before code quality, because they catch different classes of problems
- "Boring implementation" test — if a task requires design judgment, it's not decomposed enough

**From [Boris Tane's workflow](https://boristane.com/blog/how-i-use-claude-code/):**
- Dedicated research phase before design — prevents implementations that ignore existing patterns, caching layers, or conventions
- Plan as shared mutable state — a local markdown file the user annotates inline, not chat-based steering. Document-based iteration is more precise than conversational back-and-forth
- Annotation cycle — the user adds `<!-- NOTE: ... -->` comments directly in the plan file, Claude addresses each one, repeat until clean. This is where the highest-value human input happens
- "Implementation should be boring" — all creative decisions are resolved during planning, not during coding

**Issue-centric design (original):**
- superpowers stores specs and plans in `docs/superpowers/` files. This works for solo use but creates friction in team settings — not everyone uses the same tools, and tool-specific files clutter the repo
- Instead, the issue tracker is the single shared artifact. `create-issue`'s Design Flow uses local files only temporarily during the annotation cycle, then converts everything to issues and deletes the files
- This means a team member who doesn't use these skills can still read the issues, pick one up, and implement it — the workflow degrades gracefully

## Skills

| Skill | Description |
|-------|-------------|
| [create-issue](plugins/aoshimash-skills/skills/create-issue/) | Create well-structured issues on any platform (GitHub, GitLab, Backlog) with codebase analysis — from a quick single issue to a designed issue hierarchy (research → design → annotation cycle → parent + sub-issues) |
| [implement-issue](plugins/aoshimash-skills/skills/implement-issue/) | Read issues, plan, implement, and open PRs with two-stage review — single-issue interactive by default, with batch mode (dependency graph, worktrees, parallel subagents) for parent issues / milestones / labels / lists |
| [analyze-sessions](plugins/aoshimash-skills/skills/analyze-sessions/) | Analyze Claude Code session history to detect recurring patterns and propose improvements to skills and settings.json |
| [multi-agent-review](plugins/aoshimash-skills/skills/multi-agent-review/) | Run multiple AI CLIs (Claude, Codex, Gemini) in parallel for code review and produce a unified review output |
| [respond-to-pr-review](plugins/aoshimash-skills/skills/respond-to-pr-review/) | Process PR review comments one by one — explain, confirm actions, implement fixes, and post reply comments |
| [review-dependency-prs](plugins/aoshimash-skills/skills/review-dependency-prs/) | Review and merge dependency-bot PRs (Renovate, Dependabot) one at a time — triage, read release notes, summarize risk, gate on user approval, and verify changes are working |

## Structure

```
plugins/aoshimash-skills/
├── .claude-plugin/plugin.json    # Plugin manifest
└── skills/
    └── <skill-name>/
        ├── SKILL.md              # Skill definition (required)
        ├── scripts/              # Helper scripts (optional)
        └── references/           # Reference docs (optional)
```

## License

MIT
