# GitHub

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)

## Detect Platform

Check in order:
1. The project's agent instructions (e.g. CLAUDE.md, AGENTS.md): an `## Issue Tracker` section with `platform: github`
2. Git remote URL contains `github.com`

## Check for Issue Templates

Used in SKILL.md Step 1. A repository template, when present, is the skeleton
for every issue this run creates.

```bash
ls .github/ISSUE_TEMPLATE/ 2>/dev/null
```

GitHub's documented location is the `.github/ISSUE_TEMPLATE/` directory: `.md`
Markdown templates, `.yml` issue forms, and an optional `config.yml` (which is
configuration, not a template). Older repositories may still carry a single
`.github/ISSUE_TEMPLATE.md` — honor it if present.

Read the chosen template file and fill it yourself, then pass the composed
body with `--body-file`. `gh issue create --template <name>` only pre-populates
body text for interactive creation and is not used here.

For a `.yml` issue form, treat each `body` element with an `id`/`label` as a
required section (respect `validations.required`) and compose the equivalent
Markdown headings in the same order.

## Create Issue

```bash
gh issue create --title "<title>" --body "<body>" [--label "<label>"] [--assignee "<user>"]
```

For bodies longer than a shell line, write the body to a file and use
`--body-file <path>` (`-` reads standard input).

`gh issue create` prints the issue URL to stdout. To capture the issue number for later use (e.g., linking sub-issues):

```bash
number=$(gh issue create --title "<title>" --body "<body>" | grep -oE '[0-9]+$')
```

Parent and dependency relationships can also be set at creation time, avoiding a
follow-up `gh issue edit`:

```bash
gh issue create --title "<title>" --body "<body>" --parent <parent-number> --blocked-by <blocking-number>
```

Both flags accept a comma-separated list of issue numbers or URLs.

## Add Sub-Issue to Parent

After creating a sub-issue, link it to the parent:

```bash
gh issue edit <parent-number> --add-sub-issue <sub-issue-number>
```

Equivalently, from the child's side: `gh issue edit <sub-issue-number> --parent <parent-number>`.

Counterparts: `--remove-sub-issue <number>`, `--remove-parent`.

## Add Dependency Between Issues

Mark that one issue blocks another:

```bash
gh issue edit <blocked-issue-number> --add-blocked-by <blocking-issue-number>
```

Counterparts: `--remove-blocked-by <number>`, `--add-blocking <number>`, `--remove-blocking <number>`.

Note: issue dependencies (`blocked by` / `blocking`) are a separate GitHub feature
from sub-issues — neither requires the other, and GitHub's docs describe no
repository setting to enable either. Dependencies went generally available in
August 2025; the `gh` flags above were added in `gh` v2.94.0. Up to 50 issues can
be linked per relationship type.

If the flags are rejected as unknown (older `gh` version), fall back to mentioning dependencies in the issue body:

```markdown
Blocked by: #<issue-number>
```

## List Issues

```bash
gh issue list [--label "<label>"] [--milestone "<milestone>"] [--state open]
```

## Inspect Hierarchy and Dependency Links

Use this to verify what was created — after linking a parent or a dependency, read the
relationships back rather than assuming the edit took. `gh issue view --json` and
`gh issue list --json` both accept these relationship fields:

| Field | Shape | Holds |
|---|---|---|
| `parent` | object, or `null` | The parent issue, when this issue is a sub-issue |
| `subIssues` | `{nodes: [...], totalCount}` | This issue's sub-issues |
| `subIssuesSummary` | `{total, completed, percentCompleted}` | Sub-issue completion counts |
| `blockedBy` | `{nodes: [...], totalCount}` | Issues that must close before this one |
| `blocking` | `{nodes: [...], totalCount}` | Issues this one blocks |

`subIssues`, `blockedBy`, and `blocking` wrap their contents in `.nodes` — a `.subIssues[]`
expression finds nothing. Each node carries `number`, `title`, `state`, `url`, and `id`;
`state` is upper-case (`OPEN` / `CLOSED`).

```bash
# One issue's links
gh issue view <number> --json number,parent,subIssues,blockedBy,blocking

# Verify a created hierarchy in one call
gh issue view <parent-number> --json subIssuesSummary,subIssues \
  --jq '{total: .subIssuesSummary.total, sub: [.subIssues.nodes[] | {number, title, state}]}'

# Confirm a dependency actually registered
gh issue view <blocked-number> --json blockedBy --jq '[.blockedBy.nodes[].number]'
```

**Availability.** These fields need `gh` v2.94.0 or newer; the `JSON FIELDS` list in
`gh issue view --help` names every field the installed version accepts, and an unsupported
name makes the command fail rather than return empty. Sub-issues work on GitHub.com and
GHES 3.17+; `blockedBy` / `blocking` require GHES 3.19+.

**Fallback.** Where the fields are unavailable, read the same relationships from REST:

```bash
gh api repos/{owner}/{repo}/issues/<number>/sub_issues --jq '.[] | {number, title, state}'
gh api repos/{owner}/{repo}/issues/<number>/dependencies/blocked_by --jq '.[] | {number, state}'
gh api repos/{owner}/{repo}/issues/<number>/dependencies/blocking --jq '.[] | {number, state}'
```

REST returns `state` lower-case (`open` / `closed`), unlike the JSON fields above — do not
compare the two forms directly. Where REST is unavailable too, dependencies live in the
issue body as `Blocked by: #N` (see [Add Dependency Between Issues](#add-dependency-between-issues)).

## Comment on an Issue (research comment)

Used in [issue-creation.md](issue-creation.md) step 7 to attach the Design
Flow's research findings to the parent issue. GitHub renders HTML in comments,
so the collapsed `<details>` form applies here.

```bash
gh issue comment <number> --body-file <path>
```

`--body "<text>"` works for short comments; research findings are long enough
that a file is the safer route.

## Agent-Instructions Config Example

```markdown
## Issue Tracker
- platform: github
```

No additional config needed. `gh` CLI auto-detects the repo from git remote.
