# AGENTS.md

This is the canonical, agent-neutral guide for this repository. It provides
guidance to coding agents (and humans) working with code here.

## Overview

This is a Claude Code Plugin Marketplace repository. It contains a plugin (`aoshimash-skills`) that bundles Agent Skills, distributed as a Claude Code plugin.

## Architecture

- `.claude-plugin/marketplace.json` — Marketplace manifest (lists available plugins)
- `plugins/aoshimash-skills/.claude-plugin/plugin.json` — Plugin manifest
- `plugins/aoshimash-skills/skills/<skill-name>/` — Individual skills, each with a `SKILL.md` and optional `references/`, `scripts/`, `assets/`

## Skill Development

Skills follow the [skill-creator](https://github.com/anthropics/skills) best practices:

- `SKILL.md` is the required entry point. Frontmatter requires `name` and `description`; `compatibility` is allowed to declare a genuine environment requirement — an intended product, required CLIs/system packages, or network access (e.g. `Requires git, docker, jq, and access to the internet`). Add it only when truly needed: per the [Agent Skills spec](https://agentskills.io/specification), most skills do not need it.
- Use imperative/infinitive form in SKILL.md body.
- Keep SKILL.md under 500 lines. Split detailed content into `references/` files.
- Each skill should have eval test cases in `references/eval-cases.md`. Run them after changes and record results in the evaluation log.

## Agent Portability

Skills in this repository target any agent implementing the [Agent Skills spec](https://agentskills.io/specification), not only Claude Code.

**Guiding principle: agent-agnostic baseline, tool-native maximum.** Every skill must be fully usable by any compliant agent using only baseline capabilities, while still taking advantage of a specific agent's native tools where they exist.

**Exemption for product-bound skills.** A skill that declares a product in its `compatibility` frontmatter is exempt from the baseline-usability requirement above and MAY omit the Environment Adaptation section. The remaining rules still apply to it wherever they are meaningful.

Rules:

- Never prescribe a product-specific tool name as the only way to do something. Describe the capability the step needs, then map it to a native tool as an example.
- No `.claude/` paths (or other product-specific paths) inside skill instructions, except (a) inside "On Claude Code, …" conditional notes, or (b) in a skill that declares that product in its `compatibility` frontmatter.
- Product-specific advice goes in "On Claude Code, …" conditional notes, so other agents can skip it.
- Every capability a skill uses appears in that skill's Environment Adaptation section.

Canonical Environment Adaptation template — place it in each `SKILL.md` immediately after the intro/principles and before the workflow sections, instantiated with only the capabilities that skill actually uses:

```markdown
## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |
| **Separate agent instance** — run a task in a fresh context that has not seen this conversation | Subagent dispatch (e.g. Claude Code's Task tool) | Run sequentially in the current context; for verification, mark the result `SELF-REVIEWED` in the artifact it lands in (e.g. the PR body or reply comment the step produces) |
| **Background execution** — run long commands without blocking | Background shell (e.g. Claude Code's background Bash) | Run commands sequentially |
```

Neutral vocabulary — use the capability term in skill instructions; reserve product-specific names for the example column above and for "On Claude Code, …" notes:

| Product-specific term | Neutral capability term |
|---|---|
| subagent / Task tool | separate agent instance (fresh context) |
| `AskUserQuestion` | user choice |
| background Bash | background execution |
| plan mode | (no neutral equivalent — use only inside "On Claude Code, …" notes) |

## Git Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `chore:`)
