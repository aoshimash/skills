# Evaluation Test Cases

Human-readable index of the eval scenarios. The runnable source of truth is
[../evals/evals.json](../evals/evals.json); this file explains each case in
prose. Two kinds: **trigger evals** (does the skill fire on the right
phrasing?) and **behavioral evals** (does it do the right thing?).

## Trigger Evals

Phrases that **should** invoke `collect-agent-rules` (promote hand-written
conventions from owned repositories into the shared corpus), and
genuinely-tricky near-misses that should **not**. Full set in `evals.json` under
`trigger_evals`.

### Should trigger (EN + JA)

- "collect the hand-written rules from my other repos and add the good ones to the shared corpus"
- "scan my repositories for conventions worth centralizing and promote them"
- "find conventions I've repeated across my projects and promote them into the shared rule corpus"
- "harvest the conventions from my own GitHub repos into the shared agent rules"
- "look through my repos' AGENTS.md files, tell me which rules should be shared, and add the ones I pick"
- "自分のリポジトリから共通化できる規約を集めて共通ルールに追加して"
- "他のリポジトリの AGENTS.md からルールを収集して"
- "エージェントルールを収集して、良さそうなものは共通ルールに昇格させて"
- "共通ルールに昇格させたいルールを探して PR 作って"

### Should NOT trigger (near-misses)

- **Distributing** the corpus into the current repository ("sync the shared
  agent rules into this repo's AGENTS.md", "AGENTS.md に共通の規約を反映して")
  → `sync-agent-rules`. Same vocabulary, opposite data flow; this is the
  sharpest near-miss in both directions.
- **Editing the corpus directly** ("add a rule saying we always use go-task
  instead of Make") → an ordinary edit to `aoshimash/skills`. It changes the
  same file this skill changes, but there is nothing to scan and nothing to
  propose.
- **Session analysis** ("analyze my recent sessions and propose improvements to
  my skills", "セッションを分析して", "スキルを改善して", "ログを分析して") →
  `analyze-sessions`. Both skills observe → propose → approve → emit a PR, and
  both use the verb "collect"/"分析" loosely in conversation, so the boundary is
  the **data source**: session JSONL on this machine versus `AGENTS.md` in
  remote repositories. The mirror cases live in `analyze-sessions`'s own eval
  file.
- **Authoring an `AGENTS.md`** for the current repository → project
  documentation, not promotion.
- A **conceptual question** ("what conventions do I usually use across my
  projects?") → informational, no corpus change.
- **Cloning and grepping repositories** for something unrelated (TODOs, license
  headers) → a different task that happens to span repositories.
- **Dependency PRs** / **PR review comments** / **issue creation** → other
  skills.

## Behavioral Evals

Each maps to an entry in `evals/evals.json` with objective expectations. All are
paper exercises — they judge the discipline of the described approach, so they
need no live repositories.

**Cases 1–2 and 8–9 are success paths**; **cases 3–7, 12 and 13 are
guard/refusal paths** (the skill must decline, skip, or stop and leave the
checkout untouched); **case 10** covers re-running against an open promotion PR;
**case 11** covers fence-aware parsing, which the corpus itself exercises on
every run.

### Case 1: Recurrence proposes, one repository does not (`recurrence-across-repos`)

**Setup**: Six owned repositories. Three state a "use go-task, never a
Makefile" convention in hand-written text; one states a project-specific
"integration tests need the staging VPN" note.

**Expected behavior**:
- The repository set is confirmed **before** anything is read.
- The go-task convention is grouped across the three repositories despite
  differing wording, and proposed with a drafted id, title, `Detect` patterns
  (`**/Taskfile.yaml` and friends) and a body.
- The single-repository VPN note is **listed as an observation, not proposed**,
  and the project-specific framing is why.
- Each proposed candidate is put to its own decision; there is no "add all".
- The approved rule lands as a pull request against `aoshimash/skills`.

### Case 2: Managed blocks are invisible (`managed-block-excluded`)

**Setup**: Five repositories that already received the corpus via
`sync-agent-rules`, so each carries the shared rules inside a managed block. One
of them also has a hand-written commit-message convention outside the block,
matched by one other repository.

**Expected behavior**:
- Everything between `<!-- BEGIN aoshimash-agent-rules -->` and
  `<!-- END aoshimash-agent-rules -->` is removed before candidate derivation,
  so the distributed rules are **not** rediscovered — not proposed, not
  counted as five-repository recurrence, not reported as candidates.
- Content inside the block is excluded even where it carries no `<!-- rule: -->`
  marker.
- The hand-written convention outside the block is the only candidate.
- Cross-checking against the corpus is a second, independent guard: a rule
  already in the corpus is dropped as "already covered", naming the covering id.

### Case 3: Wrong repository refusal (`wrong-repository-refusal`)

**Setup**: The session is inside a checkout of an unrelated project.

**Expected behavior**:
- Preconditions detect that this is not a checkout of `aoshimash/skills` (the
  corpus path is absent and the remote does not resolve to it) — and distinguish
  that from an identity check that could not run at all, since a logged-out or
  offline `gh` must be reported as itself, not as a wrong-repository verdict.
- **Stops and explains**: the corpus must be edited as a real file, and the
  skill's own bundled copy is a version-pinned cache that is replaced on update,
  so there is nothing here to edit.
- Does **not** clone `aoshimash/skills` to work around it, does not scan
  anything, does not create a branch, and does not open a pull request.
- Tells the user to re-run from a checkout of `aoshimash/skills`.

### Case 4: The set is confirmed before scanning (`repository-set-confirmed`)

**Setup**: The user says "collect rules from my repos" with no list. The account
owns 40 repositories, including forks and archived ones. The prompt asks what
happens on cancellation.

**Expected behavior**:
- Enumerates owned repositories as **metadata only**, excluding forks and
  archived repositories, and presents the resolved set.
- **Reads no repository content until an explicit selection is made** — an
  unanswered question is not consent.
- Offers scan-all, a named subset, and cancel.
- On cancel: no API content reads, no branch, no commit, no file touched.
- Does not silently scan all 40, and does not scan repositories the user does
  not own.

### Case 5: Malformed managed block in a scanned repository (`malformed-block-skipped`)

**Setup**: One scanned `AGENTS.md` has a `BEGIN` delimiter with no matching
`END` after a botched merge, followed by 150 lines of hand-written
documentation. Another has two `BEGIN`/`END` pairs.

**Expected behavior**:
- Counts whole-line delimiters, fence-aware, and accepts only 0/0 or exactly 1/1
  in order.
- **Both repositories are skipped and reported**, with the counts observed.
- Critically, the unterminated `BEGIN` is **not** treated as running to end of
  file — that reading would classify the 150 hand-written lines as distributed
  rules and drop them from the scan.
- No attempt to repair the file, and no edit to the scanned repository at all.
- The remaining repositories are still scanned; recurrence counts state that two
  repositories were skipped.

### Case 6: API failures (`api-failure-boundaries`)

**Setup**: Of eight selected repositories, two have no `AGENTS.md` (404), one
returns a Git LFS pointer instead of markdown, and the seventh call hits a
secondary rate limit.

**Expected behavior**:
- A 404 is ordinary: recorded as "no `AGENTS.md`" and the scan continues.
- Non-markdown content: that repository is skipped with a reason, and the scan
  continues.
- The rate limit **stops the scan and reports**, naming which repositories were
  read and which were not — because recurrence counted over a partial set
  understates the signal and the user cannot see that from the report.
- Nothing is written on any of these paths: no branch, no commit, no pull
  request.
- No silent swallowing — every skipped repository appears in the report.

### Case 7: Every candidate rejected (`all-candidates-rejected`)

**Setup**: Three candidates are proposed; the user skips all three.

**Expected behavior**:
- Each candidate is presented individually and skipped on an explicit decision;
  Skip is the default and silence never means Add.
- The approval queue is empty, so the write phase never runs: **no branch, no
  commit, no push, no pull request, no edit to the corpus.**
- The starting branch (or detached-HEAD SHA) is restored and any temporary file
  outside the checkout is deleted.
- Skipped candidates are not recorded anywhere, so a later run may propose them
  again — and the report says so rather than implying they were suppressed
  permanently.

### Case 8: Append format and determinism (`corpus-append-format`)

**Setup**: One approved candidate; the corpus currently ends with the last
`## rule:` section and a single trailing newline.

**Expected behavior**:
- The new section is written in the corpus format: `## rule: <id>`, then
  `**Title:**`, `**Detect:**` as a comma-separated list of backticked globs, and
  `**Rule:**` followed by the body — the `Detect` patterns naming files that
  indicate the tool is in use, not files that prove compliance.
- Appended **after the last `## rule:` section** — before any following
  `##`-level heading, not blindly at end of file.
- Exactly one blank line before the new section; no trailing blank line; exactly
  one trailing newline; the corpus's recorded line ending used throughout.
- The proposed id does not collide with an existing corpus id, and no existing
  rule is modified, reordered, or reformatted.
- Only the corpus file is staged, by name — never `git add -A`.
- The pull request targets `aoshimash/skills` and is not merged by the skill.

### Case 9: No clone, nothing left behind (`no-clone-read-only`)

**Setup**: Twelve repositories to scan; the session starts on a feature branch
with unrelated commits. The prompt asks for every file and every git command.

**Expected behavior**:
- **No `git clone`** of any scanned repository; contents come from the GitHub
  API.
- Fetched content is held in memory or under the system temp directory — never
  inside the checkout, where it would land in the commit.
- The promotion branch is created from `origin/<default-branch>`, never from the
  session's feature branch, so unrelated commits stay out of the pull request.
- The only file created or modified in the checkout is the corpus file.
- The starting branch is restored at the end; a branch this run created with no
  commit on it is deleted.

### Case 10: Re-run against an open promotion PR (`rerun-does-not-duplicate`)

**Setup**: A previous run promoted a `commit-message-format` rule and its pull
request is still open on `chore/collect-agent-rules`. The user re-runs against
the same repository set.

**Expected behavior**:
- The open pull request is detected, and the corpus is read from **that
  branch's** ref, so the already-promoted rule is part of the known corpus.
- It is therefore **not proposed again and not appended a second time**; it is
  reported as already covered.
- The new commit goes on top of that branch and the push **updates the open pull
  request** rather than opening a second one.
- A stale local branch with no open pull request is **not** reused; it is
  recreated from the freshly fetched default branch, after checking it holds no
  unpushed commits.
- No force-push: a non-fast-forward rejection stops the run and reports.

### Case 11: Fenced examples are not delimiters (`fenced-regions-skipped`)

**Setup**: One scanned `AGENTS.md` documents this mechanism, showing the
`BEGIN`/`END` delimiters and a `## rule:` template inside fenced code blocks,
and also carries one real managed block.

**Expected behavior**:
- Fenced regions are skipped when counting delimiters, so the file counts 1/1
  (the real block) rather than 2/2 — a naive count would refuse a legitimate
  file as malformed.
- Fenced regions are skipped when segmenting sections, so a heading inside a
  code sample does not start a section.
- The same rule applies to the corpus: the `## rule: <id>` line inside the
  corpus's own Format fence is **not** parsed as a rule, so no phantom `<id>`
  rule exists to collide with a proposed id or to mark a candidate "already
  covered".
- Only the real rule sections the corpus currently holds are parsed, named by
  id. The expectation is deliberately not a fixed count — this skill's own first
  successful run adds a fifth.
- Prose that merely mentions a delimiter inline is not counted either — only
  whole lines count.

Case 11 needs no special fixture on the corpus side: the corpus ships the fenced
template, so **every** run exercises that half.

### Case 12: The corpus moved mid-run (`corpus-moved-mid-run`)

**Setup**: One candidate approved. While the run was scanning and asking, a
teammate merged a pull request that added a rule to the corpus, so the file on
the branch about to be committed to is not the file Phase 2 read.

**Expected behavior**:
- After checking out the promotion branch and **before appending**, the corpus
  file on disk is re-read and compared byte-for-byte against the Phase 2 read.
- The difference **stops the run**; nothing is written.
- The reasoning is stated: the recorded insertion point describes the file that
  was read, not the file on disk, so appending at a stale index could land the
  new section inside another rule's body — and deduplication was done against
  the older rule set, so the approved candidate may now be a duplicate.
- No silent recompute-and-continue, no merge, rebase, reset, or force.
- Re-running is named as the recovery.

This is the check standing between a stale insertion index and a corrupted
corpus, and it is the one path that neither the append-format case nor the
re-run case exercises.

### Case 13: Precondition guards (`precondition-guards`)

**Setup**: The corpus file has uncommitted edits, an unrelated file is already
staged, and the checkout has no `origin` remote.

**Expected behavior**:
- Preconditions run in an order where each failure is diagnosed as itself: git
  repository root, then `origin`, then `gh` auth and network, then repository
  identity, then the clean-corpus check.
- The missing `origin` is named as blocking, with the reason (the base-ref fetch
  and the push both need it; a local-only repository has nowhere to open a pull
  request).
- The modified corpus file and the pre-staged change are both named as blocking,
  so the promotion commit contains only the promotion.
- **Nothing is stashed, committed, or discarded** on the user's behalf, and the
  in-progress corpus edits are not overwritten.
- Nothing is scanned, no branch is created, no pull request is opened.
- The report also makes clear that a logged-out `gh` would be reported as a
  login problem rather than as a wrong-repository error, since the auth check
  precedes the identity check.

## Evaluation Log

### 2026-07-26 — Mechanism verification (issue #83)

**What was run.** Not a skill-behavior benchmark. The eval harness used for
`merge-renovate-prs` (repeated executor runs per case × with-skill/baseline ×
independent graders) was not available in this environment, so instead the
*mechanical claims* the skill's instructions depend on were executed directly
against the real corpus file in this branch, synthetic `AGENTS.md` fixtures, and
a reference implementation of the parse/splice recipe. This checks that the
procedure is executable and produces the asserted result; it does **not** measure
whether an agent reading `SKILL.md` follows it.

| # | Claim under test | Result |
|---|---|---|
| C1 | Fence-aware `## rule:` enumeration of the corpus (Phase 2) | **Pass** — against the real corpus in this branch, a naive line match finds 5 sections, the fence-aware enumerator finds 4; the suppressed line is the Format section's `## rule: <id>` template. |
| C2 | Insertion point = after the last `## rule:` section, not blind EOF (Phase 2 step 5) | **Pass** — on the real corpus (which ends with a rule) the point is EOF; on a fixture with a trailing non-rule `## Notes` section the point is that heading's line, so the appended rule does not land inside the notes and the notes are not absorbed into the last rule's body. |
| C3 | Splice recipe is byte-deterministic and idempotent (Phase 8-4) | **Pass** — appending the same rendered rule from two independent runs produced identical bytes; re-parsing the result and re-appending nothing produced a byte-identical file; exactly one blank line between sections and exactly one trailing newline in every case. |
| C4 | Fence-aware whole-line delimiter counting on scanned files (Phase 5-1) | **Pass** — real block 1/1; a file documenting the mechanism inside fences 0/0; that file plus one real block 1/1 fence-aware but **2/2 counted naively**; unterminated 1/0; doubled 2/2; inline prose mention 0/0. All states distinguishable, so case 5 and case 11 are both implementable. |
| C5 | Managed-block removal leaves the hand-written text intact (Phase 5-2) | **Pass** — removing `BEGIN`…`END` inclusive from a fixture with hand-written sections above and below left both intact and dropped all four distributed rules, including a marker-less foreign paragraph inside the block. |
| C6 | `evals.json` valid and schema-identical to `merge-renovate-prs` | **Pass** — parses as JSON; same top-level keys (`skill_name`, `trigger_evals`, `evals`); every eval carries exactly `id`/`name`/`prompt`/`expected_output`/`files`/`expectations`; every trigger eval exactly `query`/`should_trigger`; ids sequential 1–11. |
| C7 | `gh` invocations used by the skill exist as described | **Pass** — verified against the installed CLI (`gh` 2.96.0): `gh repo list` supports `--source`, `--no-archived`, `--limit`, `--json nameWithOwner,…` and defaults to a limit of 30; `gh api repos/<o>/<r>/contents/<path> -H "Accept: application/vnd.github.raw"` returns raw file text and reports `HTTP 404` for a missing path. |

### 2026-07-26 — Mechanism verification (issue #83, review fix round 1)

**What was run.** Same method and same limits as the round above: the mechanical
claims *added or changed* in the fix round were executed directly. Still not a
skill-behavior benchmark.

| # | Claim under test | Result |
|---|---|---|
| F1 | The optional file-list read exists and reports truncation (Phase 4-2) | **Pass** — `gh api "repos/aoshimash/skills/git/trees/main?recursive=1"` returns a `tree` array of blob/tree entries plus a `truncated` boolean (`false`, 85 entries for this repository), so the `Detect` sanity check has a real data source and a defined "incomplete" signal. |
| F2 | A directory path is not a 404 (scanning.md error table) | **Confirmed** — `gh api repos/aoshimash/skills/contents/plugins -H "Accept: application/vnd.github.raw"` returns HTTP 200 with a JSON array, not 404. The reviewed revision's parenthetical was wrong; the "not markdown text" row now names this case explicitly. |
| F3 | `deleteBranchOnMerge` on the corpus repository (Phase 1 stale-branch stop) | **Pass** — `gh repo view aoshimash/skills --json deleteBranchOnMerge` reports `true`, so a merged promotion cleans its branch up and the leftover-remote-branch case is specifically the closed-unmerged one, as the instruction now states. |
| F4 | The commands the fork path prescribes exist | **Pass** — `gh repo sync` exists and syncs a destination from its parent by default; `gh pr list` accepts `--repo` and the `headRepositoryOwner` JSON field, and its help states `--head` does not support `<owner>:<branch>` syntax — which is why the fork path checks the head owner rather than relying on that filter. |
| F5 | `evals.json` still valid and schema-identical after the fix round | **Pass** — parses as JSON; same top-level keys as `merge-renovate-prs`; every eval carries exactly `id`/`name`/`prompt`/`expected_output`/`files`/`expectations`; every trigger eval exactly `query`/`should_trigger`; ids sequential 1–13; names unique. |
| F6 | The corpus parse and splice still behave after the corpus Contract edit | **Pass** — re-ran the round-1 C1–C5 checks against the edited corpus: fence-aware enumeration still yields the real rules where a naive match yields one more, the insertion point still resolves to end of file, and two independent splices remain byte-identical and idempotent. |

Not re-verified because nothing changed there: the round-1 findings on delimiter
counting and managed-block removal stand as recorded.

### Accepted deviation

The 13 behavioral cases and 20 trigger cases in `evals.json` have **not** been
benchmarked. Both need the eval harness (skill registration, repeated executor
runs, independent grading) plus a with-skill vs baseline comparison to be
meaningful, and neither is available here. They are authored and reviewed but
unmeasured — treat the table above as evidence that the mechanisms work, not
that the skill triggers or is followed reliably. Run the full benchmark before
relying on any pass-rate claim, as `merge-renovate-prs` did on 2026-06-21.

The trigger-collision claim against `analyze-sessions` is part of that
unmeasured set: the should-NOT-trigger cases exist in both skills' eval files
(this file and `analyze-sessions`'s `references/eval-cases.md`), but whether the
two descriptions actually separate in practice is exactly what the unrun
benchmark would measure.

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-07-26 | C1–C7 mechanism checks | 7/7 pass | Executed against the real corpus file, synthetic `AGENTS.md` fixtures, and the installed `gh`. |
| 2026-07-26 | F1–F6 mechanism checks (fix round 1) | 6/6 pass | Executed against the live GitHub API for `aoshimash/skills`, the installed `gh` 2.96.0, and the edited corpus. |
| 2026-07-26 | Trigger evals (20) | not run | Accepted deviation — harness unavailable. |
| 2026-07-26 | Behavioral cases 1–13 | not run | Accepted deviation — harness unavailable. |
