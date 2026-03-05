# Default Review Perspectives

These are language-agnostic review perspectives applied to all agents by default. Projects can override or extend these via `.claude/aoshimash-skills.local.md`.

## Perspectives

### Correctness
- Logic errors, off-by-one, null/undefined safety
- Edge cases and boundary conditions
- Race conditions and state consistency
- Error propagation — catch blocks that swallow errors, fallbacks that hide problems

### Security
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization bypass
- Secrets or credentials exposure
- Input validation at system boundaries

### Architecture
- Code organization and separation of concerns
- Coupling and cohesion
- Unnecessary complexity or premature abstraction
- Dead code

### Error Handling
- Proper error boundaries and meaningful error messages
- Recovery strategies
- Silent failures — `console.log` instead of proper error handling, missing error propagation

### Maintainability
- Naming clarity and consistency
- Code duplication that should be extracted
- Comments that are stale, inaccurate, or will rot as code evolves
- Project convention violations (naming, file structure, patterns)

## Custom Perspectives

Projects can define custom perspectives in `.claude/aoshimash-skills.local.md`:

```yaml
multi-agent-review:
  perspectives:
    - name: performance
      description: "Performance-critical review"
      prompt: >
        Analyze for performance issues: unnecessary allocations,
        N+1 queries, missing indexes, unbounded loops, large payload
        serialization.
    - name: accessibility
      description: "Web accessibility review"
      prompt: >
        Check for accessibility issues: missing ARIA labels,
        insufficient color contrast, keyboard navigation gaps,
        missing alt text on images.
```

Custom perspectives are **merged** with the defaults. To disable a default perspective, set it explicitly with `enabled: false`:

```yaml
multi-agent-review:
  perspectives:
    - name: architecture
      enabled: false
```

## Per-Agent Perspective Override

To assign specific perspectives to a single agent instead of the defaults:

```yaml
multi-agent-review:
  agents:
    - name: claude
      enabled: true
      perspectives:
        - correctness
        - security
    - name: codex
      enabled: true
      perspectives:
        - architecture
        - error-handling
```

When `perspectives` is set on an agent, that agent uses **only** those perspectives (no merging with defaults).
