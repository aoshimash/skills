# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Claude Code Plugin Marketplace repository. It contains a plugin (`aoshimash-skills`) that bundles skills for Claude Code.

## Architecture

- `.claude-plugin/marketplace.json` — Marketplace manifest (lists available plugins)
- `plugins/aoshimash-skills/.claude-plugin/plugin.json` — Plugin manifest
- `plugins/aoshimash-skills/skills/<skill-name>/` — Individual skills, each with a `SKILL.md` and optional `references/`, `scripts/`, `assets/`

## Skill Development

Skills follow the [skill-creator](https://github.com/anthropics/skills) best practices:

- `SKILL.md` is the required entry point. Frontmatter has `name` and `description` only.
- Use imperative/infinitive form in SKILL.md body.
- Keep SKILL.md under 500 lines. Split detailed content into `references/` files.
- Each skill should have eval test cases in `references/eval-cases.md`. Run them after changes and record results in the evaluation log.

## Git Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `chore:`)
