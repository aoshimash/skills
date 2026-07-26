# Scanning Repositories

Detailed procedure for Phases 3–5 of [../SKILL.md](../SKILL.md): choosing the
repositories, reading their `AGENTS.md` without cloning, and reducing each file
to the hand-written text that may contain candidates.

Nothing in this document writes to the checkout. Every failure path here ends in
"report and go to the wrap-up", which restores the starting position and leaves
no branch behind.

## Phase 3: Confirm the repository set

### 3-1. Enumerate

Resolve the authenticated account, then list the repositories it owns:

```bash
gh api user --jq .login
gh repo list <login> --source --no-archived --limit 200 \
  --json nameWithOwner,description,defaultBranchRef,pushedAt,isPrivate
```

- `--source` excludes forks and `--no-archived` excludes archived repositories,
  matching Principle 4: a fork carries someone else's conventions, and an
  archived repository's conventions are frozen history.
- `gh repo list` defaults to a limit of 30. Pass an explicit `--limit`; if the
  number of results equals the limit the list may be truncated, so say so rather
  than presenting a silently clipped set.
- This call returns **metadata only**. No repository content is read at this
  point, which is what makes the confirmation below meaningful.
- Both `isPrivate` and `defaultBranchRef` are used later: `isPrivate` is shown in
  the confirmation list (3-2), and `defaultBranchRef` is the ref the optional
  file-list read in Phase 4 asks for. Do not request fields nothing consumes.
- If the user named repositories in the request, intersect their names with this
  list. Names that do not resolve to an owned, non-fork, non-archived repository
  are reported and dropped — never scanned on the assumption that the user meant
  something close.

### 3-2. Confirm

Present the resolved list — name, one-line description, last push, and whether
the repository is **private** — and ask the user to choose (see the skill's
Environment Adaptation): **scan all** / **scan a named subset** / **cancel**.
Sort by last push, newest first, so the repositories whose conventions are
current are easiest to pick.

Mark private repositories in the list and say why it matters: the corpus is a
public file in `aoshimash/skills`, so a convention promoted out of a private
repository becomes public text, and the pull request will name that repository
as its source. That is usually fine for a tooling convention and never fine for
anything the repository is private *because of* — flagging it is what lets the
user make that call at selection time rather than discovering it in the diff.

- **Scanning starts only after an explicit selection.** An unanswered question
  is not consent; stop and go to the wrap-up.
- On **cancel**, nothing has been read and nothing has been written. Go to the
  wrap-up.
- `aoshimash/skills` itself may appear in the list. It can be scanned like any
  other repository — its `AGENTS.md` is hand-written and it documents this
  mechanism, which the fence-aware reading in Phase 5 handles — but its content
  is mostly repository-specific guidance, so expect few candidates from it.
- Scanning is up to two API calls per repository (see Phase 4). Say roughly how
  many calls the selection implies when the set is large, so the user can narrow
  it before waiting.

## Phase 4: Read each repository's `AGENTS.md`

### 4-1. The instruction file

For each confirmed repository, in the order presented:

```bash
gh api repos/<owner>/<repo>/contents/AGENTS.md \
  -H "Accept: application/vnd.github.raw"
```

Hold the text in memory, or write it to a temporary location **outside the
checkout** (e.g. the system temp directory) and delete it in the wrap-up. Never
write a scanned file into the working tree — it would land in the corpus commit.

**Never `git clone`.** There is no case in this skill where a scanned repository
is materialized on disk.

### 4-2. The file list (best-effort)

Only for repositories whose `AGENTS.md` was read successfully — a repository
contributing no text contributes no candidates, so its paths are of no use.

```bash
gh api "repos/<owner>/<repo>/git/trees/<default-branch>?recursive=1" \
  --jq '.truncated, (.tree[] | select(.type == "blob") | .path)'
```

`<default-branch>` is the `defaultBranchRef` from Phase 3, so no extra lookup is
needed. The paths feed one thing only: the `Detect` sanity check in
[candidates.md](candidates.md#6-4-draft-each-candidate-in-corpus-format), which
confirms that a drafted glob actually matches a file in a repository the
convention was found in. A pattern matching nothing there is almost certainly
wrong, and a rule whose patterns match nothing is undistributable — it would
never be written into any repository by `sync-agent-rules`.

This read is **best-effort and never blocks the run**:

- Any failure — 404, 409 on an empty repository, permission error, transient
  error — means the paths are simply unavailable for that repository. Record
  that, continue, and do not retry. Unlike 4-1 this cannot bias recurrence,
  because it feeds no counting.
- If the response reports `truncated: true`, the path list is incomplete;
  treat it as unavailable rather than drawing conclusions from a partial tree.
- A rate limit hit **here** still stops the scan, for the same reason as in 4-1:
  the next repository's 4-1 read would fail too, and that one does bias
  recurrence.
- When no repository's paths are available, the sanity check is skipped and the
  report says so. It is a check, not a gate.

### Error boundaries

These apply to the 4-1 read. 4-2 has its own, best-effort handling above.

Handle each outcome explicitly. Silently swallowing any of them produces a
recurrence count that is wrong in a way nobody can see.

| Outcome | Action |
|---|---|
| **200 with markdown text** | Use it. Record the repository as scanned. |
| **404** — no `AGENTS.md` | Record "no `AGENTS.md`" and continue with the next repository. This is ordinary, not an error. |
| **Empty file, or whitespace only** | Record "empty `AGENTS.md`" and continue. |
| **Content that is not markdown text** — a Git LFS pointer, binary, an HTML error page, or a JSON payload (a path that is a *directory* returns HTTP 200 with a JSON array of entries, not a 404) | Skip the repository, record why, and continue. Do not attempt to interpret it. |
| **401 / 403 authentication or permission error** | **Stop the scan and report.** Do not continue with a partial set. |
| **403 / 429 rate limit** (`gh` reports the limit; `gh api rate_limit` confirms) | **Stop the scan and report**, naming which repositories were read and which were not, and that re-running later or with a smaller set will work. |
| **Network unreachable, DNS failure, `gh` not authenticated** | Stop and report. |
| **5xx or a transient failure on one repository** | Retry that repository once. If it fails again, stop and report — the same partial-set reasoning applies. |

Stopping on a partial read is deliberate. Recurrence is counted across the
confirmed set; if three of ten repositories were unreadable, a convention
present in four of them can look like a two-repository coincidence, and the
user has no way to tell from the report that the count is understated. A
repository that legitimately has no `AGENTS.md` is different — it contributes no
conventions either way, so the count stays honest and the scan continues.

Write nothing to the corpus on any of these paths.

## Phase 5: Exclude managed blocks and segment the text

Apply to each successfully fetched file, independently.

### 5-1. Validate the managed block

Count the lines whose entire content, ignoring surrounding whitespace, is
exactly the `BEGIN` delimiter, and likewise for `END`, **skipping fenced code
regions**.

- Requiring the delimiter to be the whole line stops a prose mention of it from
  being miscounted.
- Skipping fences stops a file that *documents* this mechanism with a fenced
  example from being read as if it contained a real block.

Accept only:

- **0 `BEGIN` and 0 `END`** — the file is entirely hand-written.
- **Exactly 1 of each, `BEGIN` before `END`** — one well-formed block.

Anything else is malformed: an unterminated `BEGIN` (truncated file, deleted
marker), an `END` with no `BEGIN`, `END` before `BEGIN`, or two pairs from a bad
merge. **Skip that repository, record it as malformed with the counts observed,
and continue with the rest.**

- Never guess the missing boundary. In particular, do **not** treat an
  unterminated `BEGIN` as running to end of file: that reading would classify
  every hand-written section below it as distributed rules and silently drop
  them from the scan.
- Skipping one repository is safe here — this skill only reads them — but the
  skip must appear in the report and in the pull request body, so the user can
  fix the file and re-run.

### 5-2. Remove the block

When one well-formed block exists, remove the region from the `BEGIN` line to
the `END` line **inclusive**. What remains — above and below — is the
hand-written text and the only input to Phase 6.

This is Principle 2 in mechanical form. Without it, every repository that has
ever been synced would offer the whole corpus back as candidates, and the
recurrence signal would be dominated by the rules that are already shared.

Text between the delimiters is excluded regardless of whether it carries a
`<!-- rule: <id> -->` marker: a foreign entry someone hand-wrote *inside* the
block is still inside the boundary the block declares, and re-proposing it would
be the same rediscovery loop by another route.

### 5-3. Segment into sections

Split the remaining text into sections on markdown headings (`#` through
`######`), **skipping fenced regions** so a heading inside a code sample does not
start a section. For each section keep:

- the heading text and its level,
- the enclosing heading path (e.g. `Git Conventions › Commit messages`),
- the body text,
- the repository it came from.

Fence tracking, here and everywhere else in this skill: a line whose first
non-whitespace characters are three or more backticks or three or more tildes
toggles fenced state; a closing fence must use the same character and be at
least as long as the opening one. Everything between an opening fence and its
close is inert — no headings, no delimiters, no rule markers.

Sections are the unit Phase 6 compares across repositories. Keep short
prose-only sections too; several of the author's conventions are a single
paragraph under a heading such as "Git Conventions".
