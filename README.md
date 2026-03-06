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
| [improve-skills](plugins/aoshimash-skills/skills/improve-skills/) | Analyze accumulated skill session logs to detect recurring issues and propose improvements |
| [multi-agent-review](plugins/aoshimash-skills/skills/multi-agent-review/) | Run multiple AI CLIs (Claude, Codex, Gemini) in parallel for code review and produce a unified review output |

## Agents

| Agent | Description |
|-------|-------------|
| [session-logger](plugins/aoshimash-skills/agents/session-logger.md) | Record skill usage session logs by appending entries to JSONL files (spawned automatically by skills) |

## Structure

```
plugins/aoshimash-skills/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/
│   └── session-logger.md        # Session log recorder agent
└── skills/
    └── <skill-name>/
        ├── SKILL.md              # Skill definition (required)
        ├── scripts/              # Helper scripts (optional)
        └── references/           # Reference docs (optional)
```

## License

MIT
