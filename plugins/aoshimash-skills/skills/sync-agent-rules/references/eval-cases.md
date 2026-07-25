# Evaluation Test Cases

Human-readable index of the eval scenarios. The runnable source of truth is
[../evals/evals.json](../evals/evals.json); this file explains each case in
prose. Two kinds: **trigger evals** (does the skill fire on the right
phrasing?) and **behavioral evals** (does it do the right thing?).

## Trigger Evals

Phrases that **should** invoke `sync-agent-rules` (write the shared conventions
into the current repository's `AGENTS.md`), and genuinely-tricky near-misses
that should **not**. Full set in `evals.json` under `trigger_evals`.

### Should trigger (EN + JA)

- "sync the shared agent rules into this repo's AGENTS.md"
- "apply my standard conventions to this repository — only the ones that actually apply here"
- "共通ルールをこのリポジトリに同期して"
- "AGENTS.md に共通の規約を反映して。使ってないツールのルールは入れなくていい"
- "add my usual project rules to AGENTS.md and open a PR"
- "この新しいリポジトリに標準のルールを入れたい"
- "distribute the shared conventions from aoshimash/skills into this repo"
- "エージェントルールを同期して、PR 作って"
- "pull down my shared rule set and write the relevant ones into AGENTS.md"

### Should NOT trigger (near-misses)

- **Collecting** rules from other repos into the corpus → the opposite direction
  (the future `collect-agent-rules` skill, issue #83, not yet implemented). This
  is the sharpest near-miss: same vocabulary, opposite data flow.
- **Editing the corpus** ("add a rule saying we use go-task not Make") → a
  normal edit to `aoshimash/skills`, not a distribution run.
- **Authoring an `AGENTS.md`** describing this repo's architecture and test
  commands → writing project documentation, not syncing shared rules.
- **Applying a rule to code** ("this Dockerfile uses alpine — switch it to
  debian slim") → the skill writes rule *text*; it does not enforce rules.
- **"sync my fork with upstream main"** → git branch sync; a trap on the word
  "sync".
- A **conceptual question** ("what conventions do I usually use for Python?") →
  informational, no repository change.
- **Creating an issue** about centralizing conventions → issue creation.
- **Dependency PRs** / **session analysis** / **PR review comments** → other
  skills.
- **Pinning the actions in `.github/workflows` to SHAs** → doing the work a rule
  describes, not distributing the rule.

## Behavioral Evals

Each maps to an entry in `evals/evals.json` with objective expectations. All are
paper exercises — they judge the discipline of the described approach, so they
need no live repository.

**Cases 1–7 are success paths**; **cases 8–10 are guard/refusal paths** (the
skill must decline and leave the repository untouched); **case 11** covers the
re-run-against-an-open-PR path; **case 12** covers corpus parsing, where the
corpus itself guarantees the tricky input is present on every run.

### Case 1: Detected subset, silent skip (`detect-subset-silently`)

**Setup**: A Go service repo — `Dockerfile`, `go.mod`, `.github/workflows/ci.yml`
— with no Python files and no `aqua.yaml`. `AGENTS.md` exists with
repo-specific sections and no managed block.

**Expected behavior**:
- Corpus fetched from `aoshimash/skills` over the API, not from the skill's own
  directory.
- Container image rule and GitHub Actions pinning rule detected and written.
- Python and CLI-version rules **not written and not mentioned** — no prompt, no
  option list, no question about future tooling.
- Written inside the `BEGIN`/`END aoshimash-agent-rules` delimiters with a
  per-rule id marker each; bodies copied verbatim, **excluding** the `**Rule:**`
  marker line.
- Existing `AGENTS.md` content untouched; result is a pull request on a branch
  based on the freshly fetched default branch.

### Case 2: Idempotent second run (`idempotent-second-run`)

**Setup**: The same sync ran yesterday and merged. Neither the repository nor the
corpus has changed.

**Expected behavior**:
- Renders the expected block and **compares before writing**.
- **Strips the generated preamble** (the `## Shared Conventions` heading and the
  managed-by comment) when parsing, instead of capturing it as content — see the
  evaluation log below for why this specific step is load-bearing.
- Compares in the **file's own line ending**, not assuming LF.
- No edit, no commit, **no pull request**; reports "already in sync".
- No reordering or re-wrapping that would manufacture a diff.

### Case 3: Additive, confirm before removal (`additive-preserve-and-confirm-removal`)

**Setup**: The block holds three entries — the Python rule the user added
explicitly when the repo was empty (repo still has no Python), an entry with id
`legacy-changelog-policy` that no longer exists in the corpus, and a
hand-written paragraph inside the block, **above the first rule heading**, with
no id marker. Detection matches only the container image rule.

**Expected behavior**:
- The undetected Python rule is **kept**, and **not** prompted about.
- The unmarked hand-written paragraph is kept **verbatim, in place** — and
  specifically is **not** swallowed by the preamble strip from case 2, even
  though it precedes the first `###`. Only the two known generated items are
  stripped.
- `legacy-changelog-policy` is recognized as orphaned and **presented for
  explicit confirmation**, Keep as default.
- Nothing is ever removed automatically.
- The container image rule is appended; the foreign entry is reported in the PR
  body.

### Case 4: Empty-repo bootstrap (`empty-repo-bootstrap`)

**Setup**: A repository created ten minutes ago — `README.md` and `LICENSE`
only. The prompt also asks what happens on cancellation.

**Expected behavior**:
- Nothing detected and no existing block → the bootstrap case.
- **The full catalog is offered for explicit selection** (id, title, one-line
  gist), multi-select, with select-all and cancel — not an empty run, not an
  empty block, not "nothing to do". This is the documented **exception** to the
  silent-skip principle, not a violation of it.
- **On cancellation, nothing is left behind** — no stray `AGENTS.md`, no partial
  edit, no leftover sync branch — because all writes are deferred to the final
  phase.
- No fabricated detection matches.

### Case 5: `CLAUDE.md`-only target (`claude-md-only-target`)

**Setup**: No `AGENTS.md`; a hand-written 200-line `CLAUDE.md` that does **not**
import `AGENTS.md`. Two rules detected.

**Expected behavior**:
- Recognizes that a fresh `AGENTS.md` here would not be loaded by anything.
- **Asks** rather than guessing: target `AGENTS.md` + add the `@AGENTS.md`
  import to `CLAUDE.md` (recommended) / write into `CLAUDE.md` / `AGENTS.md`
  only with an explicit warning / abort.
- The answer **only decides the target** — the file is created in the write
  phase, so aborting leaves the repository untouched.
- `CLAUDE.md` is touched only on an explicit selection, and only by one line.
- No other file created; the existing `CLAUDE.md` content is not reformatted.
- A newly created `AGENTS.md` starts with `<!-- BEGIN … -->` on line 1.

This case is the one that exercises the documented no-`AGENTS.md` behavior.

### Case 6: The corpus is authoritative (`corpus-is-authoritative`)

**Setup**: The corpus was edited an hour ago (one rule's wording corrected, one
rule added); the installed copy of the skill predates both. The repo already
carries the older container image rule.

**Expected behavior**:
- Reads the corpus over the network from `aoshimash/skills`, **not** from its own
  installed directory — freshness is independent of plugin-update timing.
- The existing entry is **refreshed in place** with the corrected text, matched
  **by rule id**, never by comparing body text. This is the mechanism that
  pushes a corrected rule out to repositories already carrying it.
- The newly added rule is written only if its patterns match.
- A failed fetch **stops the run** — no bundled fallback, no rule text written
  from memory.

### Case 7: No clone, no extra files (`no-clone-no-extra-files`)

**Setup**: A Python service with `pyproject.toml`, a `Dockerfile`, and
workflows. **The session is on a feature branch with two unrelated commits**, and
**one of them is the commit that added the `Dockerfile`** — that file does not
exist on the default branch yet. The prompt asks for every file touched, every
git command run, and which branch is inspected to decide relevance.

**Expected behavior**:
- **No `git clone`** — operates on the current working tree.
- `git fetch origin`, then the sync branch is based on
  **`origin/<default-branch>`**, never on the current feature-branch HEAD, so the
  user's two commits stay out of the PR and the base is not stale.
- **Detection runs *after* that checkout**, so relevance reflects the PR's base
  rather than the session's branch: the `Dockerfile` that exists only on
  `feat/checkout-flow` is **not** detected, and the container image rule is
  neither written nor cited as relevant.
- The only repository file created or modified is `AGENTS.md`.
- **No per-repository state/config/cache file** — the managed block is the state.
- Fetched corpus kept outside the working tree.
- Staging is explicit (`git add AGENTS.md`), never `git add -A` / `git add .`.
- Own branch + pull request; never a direct commit to the default branch; never
  self-merged; the starting branch is restored at the end.

### Case 8: Self-sync guard (`self-sync-guard`)

**Setup**: The working directory is a checkout of `aoshimash/skills` itself — the
repository that holds the corpus. It has workflows, so a rule *would* match.

**Expected behavior**:
- Identifies the target as the corpus repository during preconditions.
- **Does not proceed silently** on the strength of the matching files.
- Explains the problem (rules there are authored, not distributed; the block
  would duplicate the corpus the repository ships).
- Asks whether to continue or stop, **defaulting to stopping**.
- Absent an explicit "continue": nothing written, no branch, no PR.

### Case 9: Malformed block refusal (`malformed-block-refusal`)

**Setup**: `AGENTS.md` has a `BEGIN` delimiter with **no matching `END`** after a
botched merge, followed by ~150 lines of hand-written documentation. Two rules
detected.

**Expected behavior**:
- **Validates the delimiters before merging or writing** — counts `BEGIN` and
  `END`, requiring the delimiter to be the entire line so a prose mention is not
  miscounted, and accepting only 0/0 or exactly 1/1 in order.
- **Stops and reports, writing nothing.**
- Critically, does **not** treat the unterminated block as extending to end of
  file — that reading would destroy the 150 lines below it.
- Does not auto-repair by inserting a guessed `END`.
- Refuses equivalently on duplicated `BEGIN`/`END` pairs.

### Case 10: Dirty worktree refusal (`dirty-worktree-refusal`)

**Setup**: The user has uncommitted edits to `AGENTS.md` and an unrelated staged
change.

**Expected behavior**:
- Checks the working tree in preconditions; identifies **both** the modified
  `AGENTS.md` and the pre-staged change as blocking.
- Refuses and names the failed precondition.
- **Does not stash, commit, or discard** the user's work, and does not overwrite
  the in-progress `AGENTS.md` with the rendered block.
- No branch, no PR; tells the user to commit or stash and re-run.

### Case 11: Re-run against an open sync PR (`reuse-existing-sync-pr`)

**Setup**: An open PR already exists on `chore/sync-agent-rules`, where a
reviewer hand-edited the managed block. The default branch has no block at all.
A newly added `Dockerfile` makes one more rule match.

**Expected behavior**:
- **Fetches and checks out the existing sync branch first**, then reads, renders,
  compares and writes against *that* branch's file — reading the default branch
  would see no block, treat every entry as new, and clobber the reviewer's work.
- Honest about the consequence: a reviewer's typo fix **inside a managed rule
  body is overwritten** by the corpus text, because the corpus is authoritative
  — corrections belong in the corpus.
- Appends the newly detected rule; the push **updates the open PR** rather than
  opening a second one.
- **No force-push**: stops and reports on a non-fast-forward rejection, and stops
  in branch setup if the local branch diverged.

### Case 12: The fenced template is not a rule (`fenced-template-is-not-a-rule`)

**Setup**: A repository created this morning — `README.md` and `LICENSE` only, so
nothing is detected and the bootstrap catalog is what gets shown. The prompt asks
for every parsed rule id, the exact catalog, and which `## rule:` lines in the
corpus are rules and which are not.

**Expected behavior**:
- **Fenced regions are skipped when enumerating rules.** The corpus's "Format"
  section shows the rule template inside a fence whose first line is literally
  `## rule: <id>`; matching `## rule:` line by line parses a fifth, phantom rule
  with the placeholder id `<id>` and the placeholder detect pattern `<glob>`.
- Exactly the four real rules are parsed, by id.
- The corpus's own non-rule sections (Contract, Format, Rules) are skipped too.
- **The catalog offers exactly those four rules** — no `<id>` entry. This is where
  a missed fence stops being harmless: on the detected path the phantom matches
  nothing, but a bootstrap catalog makes it *selectable*, and selecting it would
  write the template's placeholder text into the repository as a convention.

Unlike every other case, this one needs no special fixture: the corpus ships the
fenced template, so **every** run of the skill exercises this path.

## Evaluation Log

### 2026-07-26 — Mechanism verification (issue #82, review fix round 1)

**What was run.** Not a skill-behavior benchmark. The eval harness used for
`merge-renovate-prs` (repeated executor runs per case × with-skill/baseline ×
independent graders) was not available in this environment, so instead the
*mechanical claims* the skill's instructions depend on were executed directly
against a throwaway git repository and a reference implementation of the
render/parse recipe. This checks that the procedure in `SKILL.md` is executable
and produces the asserted result; it does **not** measure whether an agent
reading `SKILL.md` follows it.

| # | Claim under test | Result |
|---|---|---|
| T1 | Per-pattern `git ls-files --cached --others --exclude-standard -- ':(glob)<p>'` detection (Phase 3) | **Pass** — on a Go+Docker fixture, `container-base-image` matched via `**/Dockerfile` and `github-actions-pinning` via `.github/workflows/*.yml`, while the Python and CLI-version rules matched nothing. Exactly case 1's expectation, and one invocation per pattern does reveal *which* pattern matched. |
| T2 | `.gitignore`d paths excluded | **Pass** — a planted `node_modules/Dockerfile` did not appear; only the root `Dockerfile` matched. |
| T3 | Malformed-block validation by whole-line delimiter count (Phase 4 step 1) | **Pass** — well-formed 1/1; unterminated 1/0; doubled 2/2; a file mentioning both delimiters inline in prose counted 0/0, i.e. not miscounted. All four states are distinguishable, so case 9's refusal is implementable. |
| T4 | Preamble strip → re-emit is idempotent (Phase 4 step 3) | **Pass** — three successive render→parse→render rounds were byte-identical, with the `## Shared Conventions` heading and the managed-by comment each appearing exactly once. |
| T5 | The reviewed revision's preamble defect was real | **Confirmed** — with the strip disabled and a parser that (as case 3 requires) preserves content above the first `###` as a foreign entry, the run was **not** idempotent and the preamble accumulated to **3 copies after two runs**. The defect is invisible to a parser that discards pre-`###` content — but such a parser fails case 3, so the strip is load-bearing either way. |
| T6 | Case 3 survives the preamble strip | **Pass** — a hand-written paragraph above the first `###` was preserved verbatim while the preamble was still emitted exactly once. The strip is narrow (two known items only), not "everything before the first heading". |
| T7 | Line-ending normalization (Phase 9) | **Pass** — an LF render compared byte-wise against a CRLF file differs, which would have produced a pull request on every run; comparing after normalizing to the file's own ending matches. |

### 2026-07-26 — Mechanism verification (issue #82, review fix round 2)

**What was run.** Same method and same limits as round 1: the *mechanical claims*
added or changed in round 2 were executed directly — the fence-aware enumerator
and delimiter counter, and the entry trim — against the real corpus file in this
branch and against synthetic target files. Still not a skill-behavior benchmark.

| # | Claim under test | Result |
|---|---|---|
| M1 | A `## rule:` line inside a fence is not a rule (Phase 1) | **Pass** — run against the actual corpus in this branch: a naive line-by-line match finds **5** `## rule:` lines, a fence-aware enumerator finds **4**. The one suppressed line is the Format section's template (`## rule: <id>`), and it is the corpus's only fenced `##` line. This is the input case 12 asserts, and it is present on **every** run. |
| M2 | Trimming each parsed entry's blank lines reaches a fixed point (Phase 4 step 4) | **Pass** — with a foreign entry supplied carrying a trailing blank line, the untrimmed parser grew the block by exactly one line per render (17→18→19→20, no fixed point). With the trim, render 1 normalizes (17→16) and renders 2 and 3 are byte-identical at 16. Confirms the round-2 claim and that the failure it fixes was real. |
| M3 | A body terminated at the next `##`-level heading, not just the next `## rule:` (Phase 1) | **Pass** — parsing the real corpus this way yields 4 bodies (13/8/11/12 lines) and **no body contains a markdown heading**, which is what the corpus format requires of a body copied into a target repository. |
| M4 | Fence-aware whole-line delimiter counting (Phase 4 step 1) | **Pass** — real block 1/1; a target file that documents the mechanism inside a fence 0/0; that same file plus one real block 1/1 fence-aware but **2/2 counted naively**, i.e. naive counting would refuse a legitimate file as malformed. Round 1's four states still distinguishable: unterminated 1/0, doubled 2/2, prose mention 0/0. |
| M5 | `evals.json` valid and schema-identical to `merge-renovate-prs` | **Pass** — parses as JSON; same top-level keys (`skill_name`, `trigger_evals`, `evals`); every eval carries exactly `id`/`name`/`prompt`/`expected_output`/`files`/`expectations`; every trigger eval exactly `query`/`should_trigger`; ids sequential 1–12. |

### Accepted deviation (both rounds)

The 12 behavioral cases and 20 trigger cases in `evals.json` have **not** been
benchmarked. Both need the eval harness (skill registration, repeated executor
runs, independent grading) plus a with-skill vs baseline comparison to be
meaningful, and neither is available here. They are authored and reviewed but
unmeasured — treat the tables above as evidence that the mechanisms work, not
that the skill triggers or is followed reliably. Run the full benchmark before
relying on any pass-rate claim, as `merge-renovate-prs` did on 2026-06-21.

This applies to case 12 as well: the fence-skipping *mechanism* is verified
against the real corpus (M1), but whether an agent reading `SKILL.md` actually
skips the fence is exactly the unmeasured part.

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-07-26 | T1–T7 mechanism checks (round 1) | 7/7 pass | Executed against a scratch repo; the preamble defect was reproduced and the fix verified. |
| 2026-07-26 | M1–M5 mechanism checks (round 2) | 5/5 pass | Executed against the real corpus file and synthetic target files; the untrimmed-entry growth defect was reproduced and the fix verified. |
| 2026-07-26 | Trigger evals (20) | not run | Accepted deviation — harness unavailable. |
| 2026-07-26 | Behavioral cases 1–12 | not run | Accepted deviation — harness unavailable. |
