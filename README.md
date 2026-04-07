# aoshimash/skills

Personal Claude Code skills collection, packaged as a Plugin for easy installation.

## Installation

1. Add the marketplace:

```
/plugin marketplace add aoshimash/skills
```

2. Install the plugin:

```
/plugin install aoshimash-skills@aoshimash-skills
```

## Sprint Workflow

`design-sprint` and `run-sprint` work together for issue-driven development. Design produces issues; sprint consumes them. Either skill also works standalone — you can hand-write issues and run-sprint them, or design-sprint issues and implement them manually.

```
design-sprint                              run-sprint
┌────────────────────────────┐            ┌──────────────────────────────┐
│ 1. Research                │            │ 1. Fetch issues              │
│    Deep codebase analysis  │            │    Parent / milestone / label│
│    → research.md           │            │                              │
│                            │            │ 2. Dependency graph          │
│ 2. Design                  │            │    Build DAG, detect cycles  │
│    Brainstorm with user    │            │    Visualize execution order  │
│    → plan.md               │            │                              │
│                            │  Issues    │ 3. Parallel execution        │
│ 3. Annotation cycle        │ ────────→  │    Worktree per issue        │
│    User annotates plan.md  │  (tracker) │    Subagent per issue        │
│    Claude addresses notes  │            │                              │
│    Repeat 1-N rounds       │            │ 4. Two-stage review          │
│                            │            │    Spec compliance → Quality │
│ 4. Issue creation          │            │                              │
│    Parent + sub-issues     │            │ 5. Summary                   │
│    Dependencies linked     │            │    Status table + PR links   │
│    Local files cleaned up  │            │                              │
└────────────────────────────┘            └──────────────────────────────┘
```

**Typical usage:**

```
> /design-sprint
# → Research → Design → Annotate plan → Create issue hierarchy

> /run-sprint
# → Pick up those issues → Build dependency graph → Implement in parallel → Review → Done
```

**Key properties:**

- **Issue tracker is the interface** — Both skills connect only through the issue tracker (GitHub, GitLab, Backlog). No skill-specific files persist after completion.
- **Works with humans and AI** — Issues created by design-sprint are readable and implementable by anyone. Issues written by hand work with run-sprint.
- **Annotation cycle** — Plans are refined through inline notes in a local markdown file (inspired by [Boris Tane's workflow](https://boristane.com/blog/how-i-use-claude-code/)). The file is deleted after issues are created.
- **Parallel execution** — run-sprint resolves issue dependencies as a DAG and dispatches independent issues in parallel using git worktrees.
- **Two-stage review** — Each issue's PR is reviewed for spec compliance (does it match the issue?) then code quality (is it well-written?).

## Skills

| Skill | Description |
|-------|-------------|
| [design-sprint](plugins/aoshimash-skills/skills/design-sprint/) | Research codebase, design a feature via brainstorming and annotation cycles, and create an issue hierarchy (parent + sub-issues with dependencies) |
| [run-sprint](plugins/aoshimash-skills/skills/run-sprint/) | Fetch a set of issues, build a dependency graph, implement them in parallel (worktrees + subagents) with two-stage review per issue |
| [create-issue](plugins/aoshimash-skills/skills/create-issue/) | Create well-structured issues on any platform (GitHub, GitLab, etc.) with codebase analysis and self-evaluation |
| [implement-issue](plugins/aoshimash-skills/skills/implement-issue/) | Read a platform issue, plan implementation, get approval, implement changes, and open a PR/MR |
| [analyze-sessions](plugins/aoshimash-skills/skills/analyze-sessions/) | Analyze Claude Code session history to detect recurring patterns and propose improvements to skills and settings.json |
| [multi-agent-review](plugins/aoshimash-skills/skills/multi-agent-review/) | Run multiple AI CLIs (Claude, Codex, Gemini) in parallel for code review and produce a unified review output |
| [respond-to-pr-review](plugins/aoshimash-skills/skills/respond-to-pr-review/) | Process PR review comments one by one — explain, confirm actions, implement fixes, and post reply comments |

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
