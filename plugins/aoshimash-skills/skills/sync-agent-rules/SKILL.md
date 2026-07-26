---
name: sync-agent-rules
description: >
  Write the shared personal conventions from the aoshimash/skills rule corpus
  into the current repository's AGENTS.md — fetch the corpus over the GitHub
  API, decide which rules are relevant from the files actually present in the
  repository, write only those into a delimited managed block, and open a pull
  request. Additive: entries already inside the block are never removed
  without confirmation, and a repository where nothing is detected gets the
  full catalog offered for explicit selection. Use when the user says
  "sync agent rules", "apply my shared conventions to this repo",
  "add the standard rules to AGENTS.md", "distribute the shared rules here",
  "共通ルールを同期して", "AGENTS.md に共通の規約を反映して",
  "このリポジトリに標準ルールを入れて", "エージェントルールを同期",
  "共通の規約をこのリポジトリに配布して", or otherwise wants this
  repository's AGENTS.md brought in line with the shared rule set.
compatibility: Requires git, network access, and the GitHub CLI (gh) authenticated with read access to aoshimash/skills and write access to the target repository
---

# Sync Agent Rules

Distribute the author's shared conventions into the repository the session is
running in. The rules live in one corpus file in `aoshimash/skills`; this skill
reads it, keeps only the rules whose tooling is actually present here, and
writes them into a delimited managed block in this repository's `AGENTS.md`.
The result is a pull request.

This skill is the **transport, not the rulebook**. It never invents a rule and
never edits the corpus — adding or correcting a rule is an edit to the corpus
file in `aoshimash/skills`.

## Core Principles

1. **The corpus is addressed as a repository path, never relative to this
   skill.** A running skill may resolve to a read-only, version-pinned copy that
   is replaced on update and is not the git checkout. Always fetch the corpus
   from `aoshimash/skills` over the network (Phase 1). This also means a rule
   added to the corpus today is distributable today, without waiting for an
   installed copy of this skill to catch up.
2. **Relevance is decided from the repository's files, not from the user.**
   Every rule declares the file patterns that indicate its tool is in use.
   Detection is re-evaluated on every run, so a rule appears by itself once its
   tool appears here. **Rules whose patterns do not match are skipped
   silently** — not written, not offered, not asked about — *except* in the
   bootstrap case (Phase 5), where nothing at all is detected and the full
   catalog is deliberately offered for selection. Never ask the user whether
   they might use a tool later.
3. **Writes are additive.** The managed block may hold rules that detection
   would not produce, because a user selected them explicitly. A later run must
   preserve them. Removal is only ever presented for confirmation and is never
   applied automatically.
4. **Idempotent.** A second run against an unchanged repository must produce a
   byte-identical file, therefore no commit and no pull request. Render the
   block by the exact recipe in Phase 8 and compare before writing.
5. **No clone, and no new files.** The skill runs inside the target repository,
   so the change is an ordinary edit plus a pull request. Never `git clone`.
   Never create a per-repository state file, config file, cache, or scratch file
   inside the repository — the managed block *is* the state.
6. **The rule text is copied verbatim.** Do not reword, re-wrap, summarize, or
   "improve" a rule body while writing it. Byte-for-byte copying is what makes
   the block idempotent and what makes a corrected rule propagate cleanly.
7. **Nothing is written until the decision to write is made.** No edit to the
   repository's tracked content happens outside git's own branch operations until
   Phase 10 — Phase 2 does create/check out a branch, which moves git refs and can
   swap tracked files, and the wrap-up restores both. Phases 0–9 otherwise read,
   decide, and ask; a run that ends in "already in sync", a cancelled bootstrap,
   or a refusal leaves the repository exactly as it was found.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |

User choice is used in four places only, and never as an approval gate on the
sync itself: Phase 0's confirmation when the target *is* the corpus repository,
Phase 5's catalog selection when nothing is detected, Phase 6's decision when
the repository has a `CLAUDE.md` but no `AGENTS.md`, and Phase 7's confirmation
before removing anything from an existing managed block.

## The Contract

These are fixed, and other skills depend on them. Do not vary them per run.

| Thing | Value |
|---|---|
| Corpus path | `plugins/aoshimash-skills/rules/agent-rules.md` in `aoshimash/skills` |
| Rule format | One `## rule: <id>` section per rule, containing a `**Title:**` line, a `**Detect:**` line of backticked glob patterns, and a `**Rule:**` line followed by the verbatim rule body. Specified in full in the corpus file's own "Format" section |
| Block delimiters | `<!-- BEGIN aoshimash-agent-rules -->` … `<!-- END aoshimash-agent-rules -->`, each alone on its own line |
| Block preamble | Immediately inside `BEGIN`: the heading `## Shared Conventions`, then an HTML comment beginning `<!-- Managed by the sync-agent-rules skill`. Both are **generated**, not content — this skill strips them when reading (Phase 4) and re-emits them when writing (Phase 8) |
| Per-rule marker | `<!-- rule: <id> -->`, on the line after the rule's `###` heading inside the block |

Because a rule is just a section in one file and this skill enumerates the
sections generically, **adding a rule to the corpus requires no edit to this
`SKILL.md`** — no rule id, title, pattern, or body is hard-coded here.

## Workflow

### Phase 0: Preconditions

Verify all of the following before touching anything. Stop and say which one
failed if any does not hold.

1. **Inside a git repository, at its root.** `git rev-parse --show-toplevel`
   succeeds; run everything from that directory. This repository is the target —
   there is nothing to clone.
2. **The target instruction files are unmodified.** `git status --porcelain`
   must not list `AGENTS.md` or `CLAUDE.md`, and nothing may be already staged.
   Refuse to proceed otherwise, so the commit contains only the sync and no
   in-progress work is swept into it.
3. **`gh` is authenticated** (`gh auth status`) and the network is reachable.
4. **An `origin` remote exists and points at GitHub** (`git remote get-url
   origin`). Without it, Phase 2's `git fetch origin` and `gh repo view` fail
   mid-run; a local-only repository has nowhere to open a pull request.
5. **Record the starting position** so the wrap-up can restore it:
   `git symbolic-ref --quiet --short HEAD` for a branch, or — when that fails
   because HEAD is detached — `git rev-parse HEAD` for the commit. Restoring by
   SHA is correct for a detached HEAD; do not assume a branch name exists.
6. **If the remote is `aoshimash/skills` itself**, the target is the corpus
   repository. Rules there are authored, not distributed, and a managed block in
   its `AGENTS.md` would duplicate the corpus it ships. Say so and ask the user
   to choose (see Environment Adaptation) whether to continue or stop; default
   to stopping.

### Phase 1: Fetch the corpus

Read the corpus from `aoshimash/skills` over the API. **Do not read it from this
skill's own directory** — that copy may be stale or read-only.

```bash
gh api repos/aoshimash/skills/contents/plugins/aoshimash-skills/rules/agent-rules.md \
  -H "Accept: application/vnd.github.raw"
```

Fallback if that read fails (rate limit, transient error):

```bash
curl -fsSL https://raw.githubusercontent.com/aoshimash/skills/main/plugins/aoshimash-skills/rules/agent-rules.md
```

Hold the fetched text in memory, or write it to a temporary location **outside
the repository** (e.g. the system temp directory) — never into the working tree.
Parse every `## rule: <id>` section into `(id, title, detect patterns, body)`.
The body starts on the line **after** the `**Rule:**` line and runs to the next
`##`-level heading or end of file, with surrounding blank lines trimmed — the
`**Rule:**` marker line itself is never part of the body. Stopping at any `##`
heading, not only at the next `## rule:`, is what keeps a non-rule section
appended after the last rule from being absorbed into that rule's body and
copied into every target repository — which would inject a `##` heading that the
corpus format forbids in bodies. Preserve the corpus order, which determines the
order of newly appended rules.

Two things are **not** rules and must be skipped: sections that are not
`## rule:` headings (the corpus's own "Contract" and "Format" documentation),
and any `## rule:` line **inside a fenced code block** — the Format section
shows the template inside a fence, and a rule body may itself contain fenced
markdown.

If both reads fail, stop and report it. Never fall back to a copy bundled with
the skill, and never reconstruct rule text from memory.

### Phase 2: Establish the working branch

Do this **before** detecting anything and before reading the target file, so
every step that follows — detection, read, render, compare, write — sees one
single branch's copy of the repository.

```bash
git fetch origin
```

Determine the default branch (e.g.
`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`), then check
whether a sync pull request is actually open:

```bash
gh pr list --head chore/sync-agent-rules --state open
```

- **An open pull request exists for `chore/sync-agent-rules`** → reuse that
  branch. Its target file already carries the block and may carry hand edits a
  reviewer made on the pull request; reading and writing there is what preserves
  them.

  ```bash
  git switch chore/sync-agent-rules
  git merge --ff-only origin/chore/sync-agent-rules
  ```

  If the fast-forward fails, stop and report — **never** `git reset --hard`,
  merge, rebase, or force. A local branch that is merely *ahead* of the remote is
  the expected state after Phase 10 step 4 preserved an unpushed commit, and a
  hard reset would silently destroy it.
- **No open pull request** → do not reuse the branch even if a local
  `chore/sync-agent-rules` exists. Nothing deletes local branches when a pull
  request merges, so a leftover branch is behind the default branch; after a
  squash merge its merge base is the pre-sync commit, and the next pull request
  would re-add the whole block and conflict with the already-merged version.
  Recreate it from the freshly fetched default branch:

  ```bash
  git switch -c chore/sync-agent-rules origin/<default-branch>   # -C to replace a leftover branch
  ```

  **Never base it on the session's current branch** — a feature branch would drag
  unrelated commits into the pull request, and a stale local default branch would
  give a stale base. Before replacing a leftover local branch, check it holds no
  commits absent from `origin/<default-branch>`; if it does (an unpushed commit
  from an earlier rejected push), stop and report rather than discarding work.

If the branch operation fails for any other reason — most commonly
`git switch` aborting because unrelated uncommitted files would be overwritten —
stop and report it. Do not stash or discard the user's work to get past it.

Remember whether this run created the branch. If the run later ends without a
commit, the wrap-up deletes it.

### Phase 3: Detect which rules are relevant

Detection runs **after** the checkout above, so it reflects the branch the pull
request will actually be based on. Detecting against the session's own branch
would be wrong in both directions: a `Dockerfile` that exists only on a feature
branch would be reported as the reason for a rule the pull request's base does
not contain, and a file deleted on that feature branch but present on the default
branch would be missed.

For each rule, test its `Detect` patterns against the files present in the
repository. Use git's own file list, so `.gitignore` is honoured and files added
but not yet committed still count. Run **one invocation per pattern**, so you
know which pattern matched and not merely that something did:

```bash
git ls-files --cached --others --exclude-standard -- ':(glob)<pattern>'
```

Non-empty output means the rule's tool is in use → the rule is **detected**; you
may stop at its first matching pattern. Empty output across all of its patterns
→ not detected, and Principle 2 applies: skip it silently.

Notes:

- `--others --exclude-standard` includes untracked-but-not-ignored files, so a
  `Dockerfile` created moments ago is seen, while ignored paths such as
  `node_modules/` and `.venv/` are excluded automatically.
- `':(glob)**/x'` matches `x` at the repository root as well as at any depth. A
  pathspec that matches nothing exits 0 with empty output, so "non-empty output"
  is the correct test — do not rely on the exit status.
- Detection is about the *presence of the tool*, not about compliance. A
  repository that violates a rule still gets the rule.

Record, per detected rule, the pattern that matched and one example file, so the
pull request can explain why every rule is there.

### Phase 4: Read the target file

Pick the target file, in this order:

| Situation | Target |
|---|---|
| `AGENTS.md` exists | `AGENTS.md` |
| `AGENTS.md` absent, but `CLAUDE.md` contains a `BEGIN` delimiter line | `CLAUDE.md`. A previous run wrote there on the user's instruction; the block's location *is* that recorded decision, so do not ask again. Test for the `BEGIN` line alone, not for a well-formed pair — a stray unmatched `BEGIN` must reach step 1 below and be refused, not be treated as "no block" and get a second one appended |
| Otherwise | **Undecided** — resolved in Phase 6, after Phase 5 can still cancel the run |

Then validate and parse the chosen file in four steps, specified in full in
[references/block-format.md](references/block-format.md):

1. **Validate the block** — count whole-line `BEGIN` and `END` delimiters,
   skipping fenced regions as Phase 1 does. Accept only zero of each, or exactly
   one of each with `BEGIN` first. Anything else is malformed: **stop and report,
   write nothing.**
2. **Record the file's line ending** (LF or CRLF, by majority) and whether it
   ends with a newline. Phase 9 compares and Phase 10 writes in that ending.
3. **Strip the generated preamble** — the `## Shared Conventions` heading and
   the managed-by comment — with the blank lines around them. Phase 8 re-emits
   both.
4. **Parse the remainder into an ordered entry list, trimming each entry's
   surrounding blank lines.** An entry carrying a `<!-- rule: <id> -->` marker is
   a **managed entry**; anything else between the delimiters is a **foreign
   entry**, including a hand-written paragraph above the first `###` heading.

Follow the reference rather than improvising: it records the failure each step
prevents. Step 1 is what stops a malformed block from swallowing hand-written
content below it, and steps 3 and 4 are each independently what keeps a second
run from manufacturing a diff (Principle 4).

### Phase 5: Bootstrap when nothing is detected

If the detected set is empty **and** the block has no managed entries — a
repository with no tooling yet, e.g. one created moments ago — do not finish with
an empty run and do not write an empty block. Present the full corpus catalog
(each rule's id, title, and a one-line gist) and ask the user to choose (see
Environment Adaptation) which rules to write. Multiple selections are expected;
offer an option to select all and an option to cancel without changes.

If the user cancels, go straight to the wrap-up: nothing has been written yet
(Principle 7), so there is nothing to undo beyond restoring the branch.

Otherwise treat the selections exactly as detected rules for the rest of the
workflow. They are the reason Principle 3 exists: a later run detects nothing and
must still leave them alone.

If the detected set is empty but the block already carries managed entries, this
is **not** a bootstrap — the repository is either in sync (Phase 9) or needs only
the refresh from Phase 7 step 2. Do not present the catalog.

### Phase 6: Resolve an undecided target file

Only reached when Phase 4 left the target undecided and Phase 5 did not cancel —
that is, only once something is actually going to be written.

| Situation | Action |
|---|---|
| Neither `AGENTS.md` nor `CLAUDE.md` exists | Target `AGENTS.md`, to be created in Phase 10 with the block as its entire contents. Mention in the pull request that a `CLAUDE.md` importing it (`@AGENTS.md`) is the convention, but do not create one. |
| `CLAUDE.md` exists and already imports `AGENTS.md` (contains `@AGENTS.md`) | Target `AGENTS.md`, to be created in Phase 10. `CLAUDE.md` needs no change — the import already picks it up. |
| `CLAUDE.md` exists and does **not** import `AGENTS.md` | Writing a fresh `AGENTS.md` here would land the rules in a file no agent reads. Do not guess — ask the user to choose (see Environment Adaptation): **(1) Target `AGENTS.md` and add an `@AGENTS.md` import line to `CLAUDE.md`** (recommended; matches the convention) / **(2) Target `CLAUDE.md` instead** / **(3) Target `AGENTS.md` only, no import** — warn that nothing will load it until something imports it / **(4) Abort**. |

Option 1 is the only case where a second file is touched; it is a one-line
addition to a file that already exists, it happens only on the user's explicit
selection, and like everything else it is applied in Phase 10. No other file in
the repository is ever created or modified.

**Then apply Phase 4 steps 1–4 to the resolved file before continuing.** Phase 4
routed this file to "Undecided" and so never validated or measured it. If the
target resolved to an existing file — option 2's `CLAUDE.md` — it still needs its
block validated, its line ending recorded, its preamble stripped and its entries
parsed. Skipping that appends an LF block to a CRLF `CLAUDE.md` (whose mismatch
the *next* run would "fix" with a purely cosmetic second pull request), and
appends a second block to a `CLAUDE.md` holding a stray unmatched `BEGIN` instead
of refusing it. For a file that does not exist yet, the steps are trivially
satisfied: no block, no entries, and LF as the line ending.

### Phase 7: Merge into the managed block

Build the new entry list from the parsed entries and the detected set, by the
merge rules in [references/block-format.md](references/block-format.md):

1. **Keep every existing entry, in its existing order** (Principle 3).
2. **Refresh each managed entry whose id is still in the corpus** — title and
   body replaced with the corpus version, in place. This is how a corrected rule
   reaches repositories that already carry it.
3. **A managed entry whose id is gone from the corpus is orphaned** — ask the
   user to choose (see Environment Adaptation) per orphan, **Keep** (default) or
   **Remove**. Never remove without an explicit selection.
4. **Keep foreign entries verbatim, in place**, and list them in the pull
   request body.
5. **Append detected rules that are not already present**, in corpus order.

Match entries on the id, never on the title or body text; a detected rule that
is already present is refreshed by step 2, not duplicated.

### Phase 8: Render the block

Render the block by the byte-level recipe in
[references/block-format.md](references/block-format.md), with no variation: the
delimiters, the regenerated preamble, one `### <title>` plus
`<!-- rule: <id> -->` marker per entry, bodies copied verbatim, the fixed
blank-line separators, and the target file's recorded line ending (Phase 4
step 2). The reference also gives placement for the three cases — creating the
file, appending to an existing file that has no block, and replacing an existing
block in place.

The recipe being fixed is what makes Phase 9's comparison meaningful; any drift
in spacing, ordering, or wrapping manufactures a diff on every run.

### Phase 9: Compare, and stop if in sync

Compare the rendered file content against the file on disk, both in the file's
recorded line ending so the comparison reflects real content and not encoding.

- **Identical** → nothing to do. Make no edit and open no pull request. Report
  which rules are present, which were detected, and that the repository is
  already in sync, then go to the wrap-up. This is the second-run case and it
  must be a true no-op.
- **Different** → continue to Phase 10.

### Phase 10: Write, commit, and open a pull request

This is the only phase that modifies anything. The branch is already checked out
and up to date from Phase 2.

1. Write the target file, and `CLAUDE.md` too if the user chose Phase 6 option 1.
2. Stage **only** those files by name. Never `git add -A` / `git add .` — that is
   the guard that keeps stray files out of the change.
3. Commit:

   ```
   chore: sync shared agent rules into AGENTS.md

   <one line per rule added / refreshed / removed>

   Source: aoshimash/skills plugins/aoshimash-skills/rules/agent-rules.md
   ```

4. Push (`git push -u origin chore/sync-agent-rules`). If the push is rejected as
   non-fast-forward, someone pushed to the sync branch during this run: **stop and
   report, and do not force-push** — the local commit is preserved, and re-running
   the skill picks the new remote state up in Phase 2.
5. Open the pull request, or, when one is already open for this branch
   (`gh pr list --head chore/sync-agent-rules`), let the push update it instead of
   opening a second one. The body states, per rule, whether it was **added**,
   **refreshed** (text changed upstream), **kept** (present but not detected), or
   **removed** (confirmed by the user), plus the pattern and example file that
   matched for each detected rule. List any foreign entries found inside the
   block.
6. Return the pull request URL.

Never commit directly to the default branch, and never merge the pull request as
part of this skill.

### Wrap-up

Reached by every exit path — success, "already in sync", a cancelled bootstrap, or
a refusal.

1. Restore the starting position recorded in Phase 0 step 5 (branch name, or
   commit SHA for a detached HEAD).
2. If this run created the sync branch and made no commit on it, delete it
   (`git branch -d chore/sync-agent-rules`) so a cancelled run leaves nothing
   behind. Never delete a branch that existed before this run.

## What This Skill Does Not Do

- Does not edit the corpus. New or corrected rules are changes to
  `aoshimash/skills`.
- Does not enforce the rules. It writes text into an instruction file; making CI
  check compliance is a separate concern.
- Does not touch other repositories, and does not clone anything.
- Does not remove anything from the managed block without explicit confirmation.
- Does not repair a malformed managed block, force-push, or resolve a diverged
  sync branch. Each of those stops the run for a human.

## References

- [references/block-format.md](references/block-format.md) — the managed-block
  machinery in full: Phase 4's validate-and-parse steps, Phase 7's merge rules,
  and Phase 8's render and placement recipe. Required reading for those three
  phases; the summaries above are not sufficient on their own.
- [../../rules/agent-rules.md](../../rules/agent-rules.md) — the corpus, in this
  repository. At runtime it is read from `aoshimash/skills` over the API
  (Phase 1), not from this path.
- [references/eval-cases.md](references/eval-cases.md) — human-readable index of
  the eval scenarios; runnable source is [evals/evals.json](evals/evals.json).
