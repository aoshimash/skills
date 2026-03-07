# Workflow Detail

## Phase 1: Plan

### 1-1. Parse the Issue

Extract and organize the following from the issue body:

| Field | What to look for |
|---|---|
| **Summary** | 1–2 sentence overview at the top |
| **Motivation** | Why this matters (user need, business goal, pain point) |
| **Background** | Current state, constraints, business rules, related code paths |
| **Proposal** | Desired end state (what, not how) |
| **Acceptance Criteria** | Binary pass/fail conditions for completion |
| **References** | Links, screenshots, related issues |

If any critical field is missing or ambiguous:
- **Missing**: Ask the user to provide it.
- **Vague** (e.g., "it should work well"): Propose 2–3 concrete, binary-testable criteria and ask the user to confirm or adjust. Do not proceed until acceptance criteria are specific enough to verify.

### 1-2. Analyze the Codebase

Based on issue context, investigate:

1. **Related files** — Grep/Glob for keywords, class names, routes, or components mentioned in the issue.
2. **Architecture patterns** — Identify the project's conventions (directory structure, naming, frameworks, abstraction layers).
3. **Dependencies** — Check what modules/packages are involved; note version constraints.
4. **Test patterns** — Find existing tests to understand testing conventions (framework, location, naming).
5. **CLAUDE.md** — Read project-level CLAUDE.md for coding standards, preferred libraries, and workflow rules.
6. **Existing branches** — Check for branches that reference the issue number (e.g., `git branch -a | grep <issue-number>`). If a partial implementation exists, note what is already done and ask the user whether to continue from it or start fresh.

Record findings as structured notes for use in the plan.

### 1-3. Resolve Design Decisions

Before drafting the plan, identify any decisions that require human judgment. Examples:

- Multiple valid architectural approaches (e.g., REST vs GraphQL, new table vs extend existing)
- Trade-offs between simplicity and extensibility
- Ambiguous requirements that could be interpreted differently
- Technology or library choices not dictated by CLAUDE.md
- Scope boundaries (what's "good enough" for this issue)

For each decision point, use `AskUserQuestion` with numbered options:

1. **Present options** (2–4 choices) with:
   - A short label for each option
   - Pros and cons or key trade-offs in the description
   - Mark the recommended option with "(Recommended)" in its label
2. **Wait for the user's choice** before proceeding.

If no design decisions require human input, skip this step and proceed to 1-4.

### 1-4. Draft Implementation Plan

Create a plan with this structure:

```
## Implementation Plan for #<issue-number>

### Summary
1-2 sentence description of the approach.

### Files to Change
For each file, describe:
- **Path**: `path/to/file`
- **Action**: Create / Modify / Delete
- **Changes**: What will be added, changed, or removed and why

### New Dependencies (if any)
- Package name, version, why needed

### Edge Cases & Risks
- List potential issues and how to handle them

### Verification
How each acceptance criterion will be verified:
- Criterion 1 → verification method
- Criterion 2 → verification method

### Out of Scope
Explicitly list things NOT included to prevent scope creep.
```

### 1-5. Self-Evaluate the Plan

Before presenting, verify:

| # | Check | Pass condition |
|---|---|---|
| 1 | Covers all acceptance criteria | Every criterion has a verification method |
| 2 | Stays in scope | No changes unrelated to the issue |
| 3 | Follows project conventions | Consistent with CLAUDE.md and existing patterns |
| 4 | Files list is complete | No missing files needed for the change |
| 5 | Risks identified | Non-obvious edge cases documented |

If any check fails, revise the plan before presenting.

### 1-6. Present and Get Approval

Present the plan to the user. Clearly state:

- What will change and why
- Any assumptions or decisions made
- Questions or trade-offs requiring user input

Wait for explicit approval. If the user requests changes, revise the plan and re-present.

## Phase 2: Implement

### 2-1. Prepare Working Environment

Use the implementation location chosen in Phase 0 Setup.

Branch naming convention (for new branch and worktree):

```
<type>/<issue-number>-<short-description>
```

Examples:
- `feat/42-add-user-search`
- `fix/108-login-timeout`
- `refactor/55-extract-auth-module`

Type is inferred from issue labels or content:
- Bug → `fix/`
- Feature → `feat/`
- Technical task / refactor → `refactor/` or `chore/`

**If "Worktree"** (default): Fetch latest, then create a worktree from the default branch:
```bash
git fetch origin
git worktree add .claude/worktrees/<branch-name> -b <branch-name> origin/<default-branch>
cd .claude/worktrees/<branch-name>
```

**If "New branch"**: Fetch latest and create a branch from the default branch:
```bash
git fetch origin
git checkout origin/<default-branch>
git checkout -b <branch-name>
```

**If "Current branch"**: Verify the branch is clean (`git status`). Continue on the current branch.

### 2-1b. Update Issue Status

If the issue tracker supports status updates (e.g., Backlog), update the issue status to "In Progress" after preparing the working environment and before starting implementation. See the platform-specific guide for the command.

This step is placed here (after plan approval) rather than in Phase 0, so the issue is not marked "In Progress" if the plan is rejected or abandoned.

### 2-2. Implement Changes

Follow the approved plan file by file. For each file:

1. Read the file first to understand current state.
2. Make the planned changes.
3. Keep changes minimal — only what the plan specifies.

Guidelines:

- **Follow existing patterns** — Match the style of surrounding code (naming, indentation, abstractions).
- **No unrelated changes** — Do not refactor, clean up, or "improve" code outside the plan scope.
- **No over-engineering** — Implement the simplest solution that satisfies the acceptance criteria.
- **Secure by default** — Validate user input, avoid injection vulnerabilities, handle errors at system boundaries.

### 2-3. Run Project Checks (loop until all pass)

Check CLAUDE.md for project-specific commands. Common checks:

| Check | Typical command |
|---|---|
| Tests | `npm test`, `pytest`, `go test ./...`, etc. |
| Lint | `npm run lint`, `ruff check`, `golangci-lint run`, etc. |
| Type check | `tsc --noEmit`, `mypy .`, etc. |
| Build | `npm run build`, `go build ./...`, etc. |
| Format | `prettier --write`, `ruff format`, `gofmt`, etc. |

Run whatever the project defines. **Loop (max 3 attempts):**

1. Run all checks.
2. If any fail, fix the issue and re-run all checks.
3. Repeat until all checks pass or 3 attempts are reached.

If a fix requires a design decision (e.g., how to handle an unexpected edge case), use `AskUserQuestion` to present numbered options with a recommendation and wait for the user's choice.

**If checks still fail after 3 attempts**: Stop and escalate to the user. Use `AskUserQuestion` to present:
- Which checks are still failing and what was tried
- Options: continue trying, skip the failing check, or abandon the implementation

If the project has no defined checks, skip this step but note it when creating the PR.

### 2-4. AI Self-Review (loop until clean)

After all project checks pass, review the full diff of changes:

```bash
git diff
```

Check for:
- Logic errors, off-by-one, null/undefined risks
- Security issues (injection, auth bypass, data exposure)
- Missing error handling at system boundaries
- Inconsistency with the approved plan
- Code that doesn't follow project conventions

**Loop (max 3 rounds):**

1. Review the diff.
2. If issues found:
   - Fix issues that have a clear correct solution.
   - If a fix requires human judgment (e.g., ambiguous requirements, UX trade-offs, business logic), use `AskUserQuestion` to present the issue with numbered options and a recommendation. Wait for the user's choice.
3. After fixes, re-run project checks (Step 2-3) to ensure fixes don't break anything.
4. Re-review the diff.
5. Repeat until no issues remain or 3 review rounds are reached.

**If issues remain after 3 rounds**: Stop and use `AskUserQuestion` to present remaining issues. Let the user decide whether to:
- Proceed with known issues
- Fix manually
- Abandon the implementation

**After self-review completes**, output a visible summary to the user before proceeding to commit:

```
Self-review complete: N round(s), N issue(s) found, N fixed, N remaining
```

This ensures the user can verify that self-review was performed and see the result at a glance.

### 2-5. Commit

Write a Conventional Commit message referencing the issue:

```
<type>: <description>

<body explaining what and why>

Refs #<issue-number>
```

Example:
```
feat: add user search endpoint

Implement full-text search for users by name and email.
Search uses existing pg_trgm index for performance.

Refs #42
```

Guidelines:
- Subject line under 72 characters.
- Body explains **what** changed and **why**, not the obvious **how**.
- Reference the issue with `Refs #N`. Use `Closes #N` only in the PR body, not the commit.

## Phase 3: Pull/Merge Request

### 3-0. Detect Code Hosting Platform

The code hosting platform (for PRs) is independent of the issue tracker. Detect from the git remote URL:

- `github.com` → GitHub (use `gh` CLI)
- `gitlab.com` or known GitLab instance → GitLab (use `glab` CLI)

This allows cross-platform setups (e.g., Backlog for issue tracking + GitHub for code hosting).

### 3-1. Push and Create PR/MR

Push and create the PR/MR using the **code hosting** platform's CLI. See the platform-specific guide for exact commands.

PR/MR body format:

```markdown
## Summary
<1-3 bullet points describing what changed>

Closes #<issue-number>

## Changes
- <file-level description of changes>

## Test Plan
- [ ] <how each acceptance criterion was verified>
- [ ] <any manual testing steps>
```

### 3-2. Comment on Issue

If the issue tracker supports comments (e.g., Backlog), post a comment on the issue with the PR/MR link. This is especially useful for cross-platform setups where the PR is not automatically linked to the issue.

### 3-3. Return Result

Return the PR/MR URL to the user.
