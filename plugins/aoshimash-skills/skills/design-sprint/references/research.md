# Research Phase

## Purpose

Deeply understand the codebase before any design work begins. The research artifact ensures:
- Design decisions are grounded in reality (not assumptions)
- Existing patterns, caching layers, and conventions are respected
- No logic is duplicated unknowingly

## Procedure

### 1. Investigate the Codebase

Explore broadly, then deeply. Use multiple rounds of Grep/Glob/Read:

1. **Related files** — Search for keywords, class names, routes, components related to the feature. Follow imports and dependencies.
2. **Architecture patterns** — Identify directory structure conventions, naming patterns, abstraction layers, framework usage.
3. **Existing similar features** — Find the closest existing feature to what is being designed. Understand how it was built and why.
4. **Dependencies** — Check involved packages/modules, version constraints, compatibility.
5. **Test patterns** — Find existing tests to understand testing conventions (framework, location, naming, mocking strategy).
6. **CLAUDE.md** — Read project-level CLAUDE.md for coding standards, preferred libraries, workflow rules.
7. **Recent git history** — Check recent commits and branches related to the area being designed. Look for in-progress or abandoned work.
8. **Configuration** — Check CI/CD config, build config, environment setup that may affect the feature.

### 2. Write the Research File

Write findings to `<plan-dir>/research-<topic-slug>.md` with this structure:

```markdown
# Research: <Topic>

Date: YYYY-MM-DD

## Relevant Files

| File | Role | Notes |
|------|------|-------|
| `path/to/file.ts` | Description | Key observations |

## Architecture

How the relevant part of the system is structured. Include data flow if applicable.

## Conventions

Patterns this feature must follow to be consistent:
- Naming conventions
- Directory structure
- Error handling patterns
- Logging patterns

## Dependencies

Packages, modules, and services involved. Version constraints if any.

## Test Patterns

How similar features are tested. Framework, file location, naming, mocking approach.

## Existing Similar Features

The closest existing feature and how it was implemented. What can be reused or referenced.

## Constraints & Risks

- Things that could go wrong
- Compatibility concerns
- Performance considerations
- Security considerations

## Open Questions

Questions that need to be answered during the design phase.
```

### 3. Present and Gate

Present the research file path to the user:

> "Research is written to `<path>`. Review it and let me know if it captures the relevant context, or if there are areas I should investigate further."

Use `AskUserQuestion` with options:
- **Approve** — Proceed to design.
- **Add notes** — User will annotate the research file or provide verbal feedback. Address feedback, update the file, and re-present.
- **Abort** — Stop.

Do NOT proceed to the Design phase until the user approves the research.
