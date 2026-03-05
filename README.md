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

## Skills

| Skill | Description |
|-------|-------------|
| [create-issue](plugins/aoshimash-skills/skills/create-issue/) | Create well-structured issues on any platform (GitHub, GitLab, etc.) with codebase analysis and self-evaluation |
| [implement-issue](plugins/aoshimash-skills/skills/implement-issue/) | Read a platform issue, plan implementation, get approval, implement changes, and open a PR/MR |

## Agents

| Agent | Description |
|-------|-------------|
| [skill-analyzer](plugins/aoshimash-skills/agents/skill-analyzer.md) | Record skill usage session logs and analyze accumulated logs for recurring issues (spawned automatically by skills) |

## Structure

```
plugins/aoshimash-skills/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/
│   └── skill-analyzer.md        # Session log analyzer agent
└── skills/
    └── <skill-name>/
        ├── SKILL.md              # Skill definition (required)
        ├── scripts/              # Helper scripts (optional)
        └── references/           # Reference docs (optional)
```

## License

MIT
