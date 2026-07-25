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

- **Collecting** rules from other repos into the corpus → that is the opposite
  direction, `collect-agent-rules`. This is the sharpest near-miss: same
  vocabulary, opposite data flow.
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

Each maps to an entry in `evals/evals.json` with objective expectations. All
seven are paper exercises — they judge the discipline of the described approach,
so they need no live repository.

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
  per-rule id marker each; bodies copied verbatim.
- Existing `AGENTS.md` content untouched; result is a pull request on a branch.

### Case 2: Idempotent second run (`idempotent-second-run`)

**Setup**: The same sync ran yesterday. Neither the repository nor the corpus
has changed.

**Expected behavior**:
- Renders the expected block and **compares before writing**.
- No edit, no branch, no commit, **no pull request**.
- Reports "already in sync" rather than claiming additions.
- No reordering or re-wrapping that would manufacture a diff.

### Case 3: Additive, confirm before removal (`additive-preserve-and-confirm-removal`)

**Setup**: The block holds three entries — the Python rule the user added
explicitly when the repo was empty (repo still has no Python), an entry with id
`legacy-changelog-policy` that no longer exists in the corpus, and a
hand-written paragraph inside the block with no id marker. Detection matches
only the container image rule.

**Expected behavior**:
- The undetected Python rule is **kept**, and **not** prompted about.
- The unmarked hand-written paragraph is kept **verbatim, in place**, and
  reported in the pull request body.
- `legacy-changelog-policy` is recognized as orphaned and **presented for
  explicit confirmation**, Keep as default.
- Nothing is ever removed automatically.
- The container image rule is appended.

### Case 4: Empty-repo bootstrap (`empty-repo-bootstrap`)

**Setup**: A repository created ten minutes ago — `README.md` and `LICENSE`
only.

**Expected behavior**:
- Nothing detected and no existing block → the bootstrap case.
- **The full catalog is offered for explicit selection** (id, title, one-line
  gist), multi-select, with select-all and cancel — not an empty run, not an
  empty block, not "nothing to do".
- Selections are written exactly as detected rules would be.
- No fabricated detection matches.

### Case 5: `CLAUDE.md`-only target (`claude-md-only-target`)

**Setup**: No `AGENTS.md`; a hand-written 200-line `CLAUDE.md` that does **not**
import `AGENTS.md`. Two rules detected.

**Expected behavior**:
- Recognizes that a fresh `AGENTS.md` here would not be loaded by anything.
- **Asks** rather than guessing: create `AGENTS.md` + add the `@AGENTS.md`
  import to `CLAUDE.md` (recommended) / write into `CLAUDE.md` / create
  `AGENTS.md` only with an explicit warning / abort.
- `CLAUDE.md` is touched only on an explicit selection, and only by one line.
- No other file created; the existing `CLAUDE.md` content is not reformatted.

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
workflows. The prompt asks for every file touched and every git command run.

**Expected behavior**:
- **No `git clone`** — operates on the current working tree.
- The only repository file created or modified is `AGENTS.md`.
- **No per-repository state/config/cache file** — the managed block is the state.
- Fetched corpus kept outside the working tree.
- Staging is explicit (`git add AGENTS.md`), never `git add -A` / `git add .`.
- Own branch + pull request, reusing an existing sync branch/PR instead of
  duplicating; never a direct commit to the default branch; never self-merged.

## Evaluation Log

| Date | Case | Result | Notes |
|------|------|--------|-------|
| — | — | not yet run | Cases authored with the skill (issue #82); no benchmark run yet. |
