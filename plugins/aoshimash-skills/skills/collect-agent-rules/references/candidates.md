# Candidates

Detailed procedure for Phases 6–7 of [../SKILL.md](../SKILL.md): turning the
hand-written sections from Phase 5 into ranked candidates, drafting each in the
corpus format, and deciding on them one at a time.

Still nothing is written in these phases. A run where every candidate is skipped
ends at the wrap-up with the checkout untouched.

## Phase 6: Derive and rank candidates

### 6-1. Group equivalent sections across repositories

Compare the sections from Phase 5 across repositories and group the ones that
state the **same convention**, even when the wording differs. "Use uv for
Python, never pip" and "All Python dependency management goes through uv" are
one candidate, not two. Matching is on the stated constraint, not on heading
text — repositories rarely agree on headings.

Record, per group, every repository it appeared in and the heading path it
appeared under. The report and the pull request body both cite these.

### 6-2. Drop what is not promotable

Exclude a group when any of the following holds. Each exclusion is recorded so
the report can say why a section the user expected to see is absent.

| Exclusion | Why |
|---|---|
| **Already covered by a corpus rule** (from Phase 2), by id or by stating the same constraint | The corpus already carries it; a second copy under a new id would be distributed twice. Name the covering rule id in the report. |
| **Repository-specific** — architecture, directory layout, build/test/run commands, deployment targets, domain rules, anything naming this project's own modules | The corpus is personal conventions that travel; project documentation does not. |
| **Not a constraint** — an overview paragraph, a link list, a changelog, a description of what the repository is | There is no rule to state. |
| **Secrets, credentials, private hostnames, internal URLs** | The corpus is a public file in `aoshimash/skills`. Never promote text containing them, and do not "sanitize and promote" — say why it was dropped and let the author decide. |
| **Contradicts an existing corpus rule** | Two rules that disagree would both be distributed into the same `AGENTS.md`. Report the conflict, naming the existing rule id, and let the author resolve it as a corpus edit rather than proposing an addition. |
| **Text that came from inside a managed block** | Already removed in Phase 5; listed here because it is the failure this skill exists to avoid. |

### 6-3. Rank

The primary signal is **recurrence**: the number of scanned repositories whose
hand-written text states the convention.

- **2 or more repositories → proposed.** Rank by repository count, then by how
  general the convention is (a tool choice that applies to any project outranks
  one that applies to a narrow stack).
- **Exactly 1 repository → listed, not proposed.** Show these in the report
  under a separate "single-repository observations" heading so the author can
  see them, but do not put them to a decision. Recurrence is the evidence this
  skill has; a lone convention may be genuinely local, and asking about every
  one of them turns a scan of twenty repositories into an interrogation.
  - Exception: if the user explicitly asked for a specific convention to be
    promoted, or asks about one of the listed observations, treat it as a
    candidate and put it to the same per-candidate decision. That is a human
    supplying the judgment recurrence would otherwise have to supply.

If no group reaches two repositories, report the single-repository observations
and the exclusions, then go to the wrap-up. **No branch, no commit, no pull
request** — an empty result is a normal outcome, not a failure.

### 6-4. Draft each candidate in corpus format

Before presenting a candidate, draft it as the `## rule:` section it would
become. The corpus's own "Format" section is authoritative; the essentials:

- **Id** — stable, lowercase, hyphen-separated, describing the convention
  (`container-base-image`, not `rule-5`). It **must not collide** with an
  existing corpus id from Phase 2, or with another candidate approved in this
  run. A collision would make two rules indistinguishable to the per-rule marker
  that distribution writes into target repositories; pick a different id rather
  than reusing one, and never repurpose an existing id.
- **Title** — the `###` heading text the rule will get in a target repository.
- **Detect** — a comma-separated list of backticked glob patterns naming the
  files that indicate **the tool is in use**, not files that prove compliance: a
  repository that violates a rule still needs to carry it. Prefix each pattern
  with `**/` so it matches at the root and at any depth, unless the tool only
  ever works at a fixed path, in which case anchor it there. Derive the patterns
  from the convention itself (a uv rule detects `**/pyproject.toml`,
  `**/uv.lock`, `**/*.py`), then **sanity-check them against the file lists read
  in Phase 4-2**: at least one pattern should match at least one path in at
  least one repository the convention was found in. A pattern set matching
  nothing there is almost certainly wrong, and a rule whose patterns match
  nothing is undistributable — `sync-agent-rules` would never write it into any
  repository. Report a failed check alongside the candidate and let the user
  correct it through **Add with edits**; do not drop the candidate silently, and
  do not block on it. Phase 4-2 is best-effort, so when no file list is
  available say the check was **skipped** rather than implying it passed.
- **Body** — English, no markdown headings (it is emitted under a `###` heading
  in the target file), written to read correctly standing alone in a stranger's
  `AGENTS.md`. Merge the wording from the repositories it was found in rather
  than copying one verbatim; drop project-specific references. Avoid version
  numbers and image tags that rot, except where naming one is the point of the
  rule. Bullets, tables, code fences, and links are all fine.

## Phase 7: Decide one candidate at a time

### 7-1. Present the findings report

Present the whole picture once, before any decision, so the user is choosing
with the full set in view:

```
## Scan

Repositories scanned: N (M skipped — <reason per repository>)

## Candidates (proposed)

### 1. <title>  —  seen in <k> repositories
- **Proposed id**: `<id>`
- **Seen in**: `<owner>/<repo>` (heading “<path>”), `<owner>/<repo>` (heading “<path>”), …
- **Detect**: `<glob>`, `<glob>` — matches `<path>` in `<owner>/<repo>` (or: matched nothing / check skipped, no file list)
- **Proposed rule body**:
  <the drafted body>

### 2. …

## Single-repository observations (not proposed)

- <convention> — `<owner>/<repo>`, heading “<path>”

## Excluded

- <convention> — <reason> (e.g. already covered by `python-package-management`)
```

### 7-2. Decide

Then take the proposed candidates in rank order, **one at a time**, and ask the
user to choose (see the skill's Environment Adaptation):

| Option | Effect |
|---|---|
| **Add** | The drafted rule is queued for Phase 8, exactly as shown. |
| **Add with edits** | The user supplies changes (title, id, detect patterns, wording). Apply them, re-run the id-collision check from 6-4 if the id changed, show the revised draft, and confirm before queueing. Treat free-text as the instruction it is — do not re-present a fresh menu. |
| **Skip** (default) | The candidate is dropped from this run. It will be proposed again on a future run, since nothing about it was recorded. |
| **Abort** | End the run immediately. Go to the wrap-up; nothing has been written. |

Rules for this gate:

- **No bulk approval.** There is no "add all" option. The whole point of the
  skill is that only the author can tell a general convention from a local one,
  and that judgment is per candidate.
- **No candidate is queued without an explicit Add.** Silence, an ambiguous
  answer, or an unanswered question means Skip — never an implicit yes.
- Answering does not write anything. Every approval accumulates in memory, and
  Phase 8 runs once, at the end, only if the queue is non-empty.
- If every candidate is skipped, the queue is empty: report that and go to the
  wrap-up. No branch, no commit, no pull request.
