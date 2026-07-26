# Shared Agent Rules

The canonical set of the author's personal project conventions. This file is the
single source: the rules are copied *from* here into individual repositories'
`AGENTS.md`.

- `sync-agent-rules` **reads** this file (over the GitHub API, from
  `aoshimash/skills`) and writes the relevant rules into a target repository.
- A future `collect-agent-rules` skill (issue #83, not yet implemented) will
  **edit** this file in a local checkout to add rules promoted from hand-written
  `AGENTS.md` files in owned repositories.

This file is data, not instructions to an agent. Nothing here changes how a
skill behaves; a rule body is text to be copied verbatim into another
repository's instruction file.

## Contract

These are fixed. `sync-agent-rules` depends on them today and
`collect-agent-rules` will depend on them, so do not change them without
updating every skill that reads or writes this format.

| Thing | Value |
|---|---|
| This file's path | `plugins/aoshimash-skills/rules/agent-rules.md`, relative to the repository root of `aoshimash/skills` |
| Managed-block delimiters | `<!-- BEGIN aoshimash-agent-rules -->` … `<!-- END aoshimash-agent-rules -->`, each alone on its own line |
| Block preamble | Immediately inside `BEGIN`: the heading `## Shared Conventions`, then an HTML comment beginning `<!-- Managed by the sync-agent-rules skill`. Both are generated, not content — a reader strips them, a writer re-emits them |
| Per-rule marker inside a block | `<!-- rule: <id> -->`, on the line after the rule's `###` heading |

The delimiters are HTML comments, so they are invisible in rendered markdown and
greppable in source. They serve two purposes: they tell `sync-agent-rules` what
it owns and may refresh, and they will tell `collect-agent-rules` what to
**ignore** when scanning a repository for rules worth promoting — without that
boundary, already-distributed rules would be rediscovered as candidates on every
scan. That second purpose is why the format is fixed here even though the
collection skill does not exist yet.

## Format

Every rule is one `## rule: <id>` section appearing under the "Rules" heading
below. The id is stable, lowercase, hyphen-separated, and is what a managed block
references — never rename an id without accepting that repositories carrying it
will treat the old one as orphaned.

A `## rule:` line **inside a fenced code block is not a rule** — the template
immediately below is an example, and a rule body may legitimately contain fenced
markdown. Skip fenced regions when enumerating rules.

```markdown
## rule: <id>

**Title:** <heading text used in the target repository>

**Detect:** `<glob>`, `<glob>`, …

**Rule:**

<body — copied verbatim into the target repository>
```

- **Detect** is a comma-separated list of backticked glob patterns. Each is
  matched against the target repository's file list; **any** match makes the
  rule relevant. Prefix a pattern with `**/` so it matches at the repository root
  and at any depth — unless the tool only ever works at a fixed path, in which
  case anchor the pattern there instead (as `github-actions-pinning` does with
  `.github/workflows/*.yaml`). Patterns name the *files that indicate the tool is
  in use*, not files that prove compliance — a repository that violates a rule
  still needs to carry it.
- **Rule** body starts on the line **after** the `**Rule:**` line and runs to the
  next `##`-level heading or end of file, with leading and trailing blank lines
  trimmed. The `**Rule:**` marker line itself is never part of the body. Stopping
  at any `##` heading — not only at the next `## rule:` — keeps a non-rule section
  appended after the last rule from being swallowed into that rule's body. It is
  copied byte-for-byte, so it must read correctly standing alone in someone
  else's `AGENTS.md`.
- A body may use bullets, tables, code fences, and links, but **no markdown
  headings** — it is emitted under a `###` heading and any heading inside it
  would break the target file's outline.
- Bodies are written in English, matching this repository and the author's newer
  `AGENTS.md` files.
- Avoid version numbers and image tags that rot, except where naming one is the
  point of the rule.

**Adding a rule requires no change to any `SKILL.md`.** Append a new
`## rule:` section below and it is distributable immediately — the skills
enumerate these sections generically and nothing about a rule (id, title,
pattern, or body) is hard-coded in a skill. Keep sections in a stable order;
that order determines the order rules are appended in a target repository.

## Rules

## rule: container-base-image

**Title:** Container image policy

**Detect:** `**/Dockerfile`, `**/Dockerfile.*`, `**/*.Dockerfile`, `**/Containerfile`, `**/compose.yaml`, `**/compose.yml`, `**/docker-compose.yaml`, `**/docker-compose.yml`

**Rule:**

| Purpose | Base image | Why |
|---|---|---|
| Build stage | Debian/Ubuntu-based (e.g. `golang:1.25-bookworm`) | glibc compatibility, full toolchain, debuggable |
| Production stage | distroless (e.g. `gcr.io/distroless/static-debian12`) | minimal attack surface, no shell, no package manager |
| Development and tooling | Debian/Ubuntu-based | rich debug tooling, glibc-based compatibility |

- **Do not use Alpine.** musl-vs-glibc incompatibilities, missing debug tooling,
  and differing DNS behaviour. Exception: when upstream publishes only an
  Alpine-based image (e.g. `migrate/migrate`), using it is acceptable.
- Build Go binaries with `CGO_ENABLED=0` so they are static and pair cleanly
  with distroless.
- To debug a distroless image, use its `:debug` tag (which includes busybox) or
  an ephemeral container (`kubectl debug`).

## rule: python-package-management

**Title:** Python package management

**Detect:** `**/pyproject.toml`, `**/uv.lock`, `**/requirements*.txt`, `**/setup.py`, `**/setup.cfg`, `**/Pipfile`, `**/*.py`

**Rule:**

- Manage every Python project with [uv](https://docs.astral.sh/uv/).
  Dependencies are declared in `pyproject.toml` and locked in `uv.lock`; both
  are committed.
- **Never invoke `pip`, `pip install`, `python`, or `python3` directly.** Every
  Python operation goes through uv — `uv add`, `uv sync`, `uv run`.
- Give each independently-versioned component its own uv project (its own
  `pyproject.toml` and virtual environment) and run uv commands from that
  project's directory rather than from the repository root.

## rule: cli-version-management

**Title:** CLI tool version management

**Detect:** `**/aqua.yaml`, `**/aqua.yml`, `**/.aqua.yaml`, `**/.aqua.yml`, `**/aqua/aqua.yaml`, `**/.aqua/aqua.yaml`, `**/.tool-versions`, `**/.nvmrc`, `**/.node-version`, `**/.terraform-version`, `**/mise.toml`, `**/.mise.toml`

**Rule:**

- Pin every CLI tool the repository needs with [aqua](https://aquaproj.github.io/),
  configured in `aqua.yaml` at the repository root and committed.
- **aqua is the single source of tool versions.** Do not add a second version
  manager (asdf, mise, nvm, pyenv, tfenv), and do not keep parallel version
  files such as `.nvmrc` or `.terraform-version`.
  - Exception: when a build host discovers a version only from its own file
    (for example a hosting platform reading `.node-version`), keep that file,
    record why, and keep it in sync with `aqua.yaml`. Renovate raises a pull
    request for both, so following it is enough.
- Install tools through aqua in CI as well, so local and CI run the same
  versions.

## rule: github-actions-pinning

**Title:** GitHub Actions pinning

**Detect:** `.github/workflows/*.yaml`, `.github/workflows/*.yml`, `**/action.yaml`, `**/action.yml`

**Rule:**

- Pin every third-party GitHub Action to a full commit SHA, with the
  human-readable version in a trailing comment:

  ```yaml
  - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
  ```

  A tag or branch reference is mutable and can be repointed at different code
  after review.
- Do not maintain the pins by hand. Enable Renovate's
  [`helpers:pinGitHubActionDigests`](https://docs.renovatebot.com/presets-helpers/)
  preset so pinning and updating are automatic.
