# Managed Block Format

The byte-level machinery behind Phases 4, 7, and 8 of [../SKILL.md](../SKILL.md):
how an existing managed block is read and parsed, how its entries are merged with
the detected rules, and exactly how the result is rendered and placed.

This file specifies the *procedures*. The fixed values they operate on — the
corpus path, the rule format, the block delimiters, the block preamble, and the
per-rule marker — are "The Contract" in `SKILL.md`, restated in the corpus file's
own "Contract" section (`plugins/aoshimash-skills/rules/agent-rules.md`). Those
values are a cross-skill contract; do not vary them here.

Phase and step numbers below match `SKILL.md`'s workflow, and the summaries there
link to the corresponding section here.

## Phase 4 (detail): Validate and parse the target file

Applied to the target file chosen by Phase 4's selection table — or, when that
table left the target undecided, to the file Phase 6 resolves it to.

1. **Validate the block.** Count the lines whose entire content, ignoring
   surrounding whitespace, is exactly the `BEGIN` delimiter, and likewise for
   `END`, **skipping fenced code regions** as Phase 1 does. Requiring the
   delimiter to be the whole line stops a prose mention of it from being
   miscounted; skipping fences stops a target file that *documents* this
   mechanism with a fenced example from being treated as the real block — which
   would replace the fence's contents and leave stray fence lines behind. Accept
   only **zero** of each (no block yet) or **exactly one of each, `BEGIN` before
   `END`**. Anything else — a `BEGIN` with no `END` (truncated file, deleted
   marker) or two pairs (bad merge) — is a malformed block: **stop and report,
   write nothing.** Never guess the missing boundary; treating an unterminated
   block as running to end of file would destroy every hand-written section
   below it.
2. **Record the file's line ending** (LF or CRLF, by majority) and whether the
   file ends with a newline. Phase 9 compares and Phase 10 writes in the file's
   own line ending, so a CRLF checkout does not diff against an LF render on
   every run.
3. **Strip the generated preamble** from the top of the block: the
   `## Shared Conventions` heading line if present, and the HTML comment
   beginning `<!-- Managed by the sync-agent-rules skill` if present, together
   with the blank lines around them. Phase 8 re-emits both verbatim. **Skipping
   this step is what makes a second run produce a spurious diff**, because the
   preamble would otherwise be captured as content and then duplicated.
4. **Parse the remainder into an ordered list of entries, trimming each entry's
   surrounding blank lines** exactly as Phase 1 trims a corpus body. An entry
   carrying a `<!-- rule: <id> -->` marker is a **managed entry**; anything else
   between the delimiters is a **foreign entry** — including a hand-written
   paragraph that sits before the first `###` heading. A file with no delimiters
   yields an empty list.

   The trim is not cosmetic. Phase 8 supplies the separator blank lines on emit,
   so an entry parsed *with* its trailing blank line gains another one on every
   render — the gap grows by one line per run and the block never reaches a fixed
   point, breaking Principle 4. Managed entries escape this only because step 2 of
   Phase 7 replaces their bodies wholesale; foreign entries are preserved as
   parsed, so untrimmed input persists.

## Phase 7 (detail): Merge into the managed block

Build the new entry list from the parsed entries and the detected set:

1. **Keep every existing entry, in its existing order.** This is Principle 3.
2. For each managed entry whose id exists in the corpus: **replace its title and
   body with the corpus version, in place.** This is how a corrected rule reaches
   repositories that already carry it.
3. A managed entry whose id is **no longer in the corpus** is orphaned. Ask the
   user to choose (see `SKILL.md`'s Environment Adaptation) per orphan: **Keep**
   (default) / **Remove**. Never remove without an explicit selection.
4. **Foreign entries are kept verbatim, in place.** Do not reformat or relocate
   them. List them in the pull request body so the user can see what is inside
   the block but not managed.
5. **Append detected rules that are not already present**, in corpus order,
   after the existing entries.

A detected rule that is already present is simply refreshed by step 2 — it is
not duplicated. Match entries on the id, never on the title or body text.

## Phase 8 (detail): Render and place the block

Render exactly this, with no variation — the byte-level recipe is what makes
Phase 9's comparison meaningful:

```markdown
<!-- BEGIN aoshimash-agent-rules -->
## Shared Conventions

<!-- Managed by the sync-agent-rules skill (aoshimash/skills).
     Source: plugins/aoshimash-skills/rules/agent-rules.md
     Managed entries below are refreshed on every sync. Keep
     repository-specific rules outside this block. -->

### <title>
<!-- rule: <id> -->

<body>

### <next title>
<!-- rule: <next id> -->

<body>

<!-- END aoshimash-agent-rules -->
```

- The heading and the managed-by comment are the generated preamble from "The
  Contract". Emit them exactly as above on every run — Phase 4 step 3 already
  removed the previous copy, so they are never duplicated.
- One blank line after each `<!-- rule: ... -->` marker, one blank line between a
  body and the next `###` heading, one blank line before `<!-- END ... -->`.
- Rule bodies are copied verbatim from the corpus, including their own
  formatting. Do not re-wrap lines.
- Foreign entries are emitted verbatim at their recorded position, separated from
  their neighbours by a single blank line.
- Use the target file's recorded line ending (Phase 4 step 2) throughout; LF for
  a file being created.

Placement:

- **Creating the file** (Phase 6 rows 1–2, and row 3 options 1 and 3): the file
  *is* the block — `<!-- BEGIN … -->` is line 1, with no leading blank line, and
  the file ends with a single newline after `<!-- END … -->`.
- **Appending to an existing file with no block**: if the file does not already
  end with a newline, add one; then one blank line, then the block; then a
  single trailing newline.
- **Updating an existing block**: replace only the text between and including
  the delimiters — which Phase 4 step 1 has already proven to be exactly one
  well-formed pair. Everything outside them is untouched.
