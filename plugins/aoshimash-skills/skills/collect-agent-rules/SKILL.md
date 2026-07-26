---
name: collect-agent-rules
description: >
  Promote hand-written conventions out of the author's own GitHub repositories
  and into the shared rule corpus in aoshimash/skills — confirm which
  repositories to scan, read each one's AGENTS.md over the GitHub API without
  cloning, ignore everything inside a managed rules block, propose the
  conventions that recur across repositories, decide on them one at a time, and
  open a pull request adding the approved ones to the corpus. Runs inside a
  checkout of aoshimash/skills; proposes, never promotes automatically. Use
  when the user says "collect agent rules", "promote rules into the shared
  corpus", "find rules worth sharing in my repos", "scan my repositories for
  conventions to centralize", "harvest conventions from my other projects",
  "ルールを収集して", "他のリポジトリのルールを共通ルールに取り込んで",
  "自分のリポジトリから共通化できる規約を集めて", "エージェントルールを収集",
  "共通ルールに昇格させて", or otherwise wants hand-written conventions in
  owned repositories gathered into the shared rule set.
compatibility: Requires git, network access, and the GitHub CLI (gh) authenticated with read access to the user's own repositories and write access to aoshimash/skills; runs inside a checkout of aoshimash/skills
---

# Collect Agent Rules

Promote hand-written conventions out of the author's own repositories and into
the shared rule corpus. This skill runs inside a checkout of `aoshimash/skills`,
reads the `AGENTS.md` of the repositories the user confirms, proposes the
conventions that look worth sharing, and — for the candidates the user approves
— appends them to the corpus and opens a pull request.

This is the reverse direction of `sync-agent-rules`: that skill distributes the
corpus into a repository; this one collects from repositories into the corpus.
Rewriting a source repository to drop its now-shared copy is **out of scope** —
a later `sync-agent-rules` run puts the promoted rule into that repository's
managed block, and tidying the hand-written original is left to the author.

## Core Principles

1. **The corpus is edited as a real file, addressed by repository path.** A
   running skill may resolve to a read-only, version-pinned copy that is
   replaced on update and is not the git checkout, so writing into "its own"
   directory would write into a directory that disappears. The corpus is
   `plugins/aoshimash-skills/rules/agent-rules.md` in a checkout of
   `aoshimash/skills`, and running anywhere else stops the run (Phase 0).
2. **Text inside a managed block is never a candidate.** Rules previously
   distributed by `sync-agent-rules` appear in every repository that received
   them; treating them as candidates would rediscover the entire corpus on every
   scan. Only text outside the delimiters counts (Phase 5).
3. **Scanning is read-only and never clones.** Repository contents are read
   through the GitHub API. Never `git clone`, and never create a working copy of
   a scanned repository.
4. **Scope is the author's own repositories, and the set is confirmed before
   scanning.** Harvesting conventions out of other people's projects contradicts
   the point, and scanning every owned repository unprompted is both slow and
   rarely what is wanted. Enumeration reads repository *metadata* only; no file
   is read before the user confirms the set (Phase 3).
5. **Promotion is never automatic.** Recurrence across repositories is a signal,
   not a verdict — many conventions are legitimately specific to one project,
   and only the author can tell which are general. Candidates are decided **one
   at a time**, and nothing is added without an explicit decision (Phase 7).
6. **Nothing is written until the decision to write is made.** No local branch,
   working-tree file, or commit changes before Phase 8 — Phase 1 does run
   `git fetch`, which updates remote-tracking refs, but that touches nothing the
   run could damage and nothing the wrap-up has to undo. Phases 0–7 otherwise
   read, decide, and ask. A run that finds nothing, is cancelled at the
   repository confirmation, or has every candidate rejected leaves the checkout
   exactly as it was found — no stray file, no stray branch, no stray commit.
7. **A promoted rule is never re-proposed.** Two mechanisms close the loop:
   Phase 2 reads the corpus from the branch the pull request will be based on,
   so a rule promoted by an earlier run is already known; and Phase 5 excludes
   managed blocks, so the same rule coming back through distribution is
   invisible. Re-running after an approved addition therefore neither
   re-proposes it nor duplicates it.
8. **Approved candidates are written in the corpus format, not pasted.** A
   promoted rule gets an id, a title, the file patterns that indicate its tool
   is in use, and a body that reads correctly standing alone in a stranger's
   `AGENTS.md`. The corpus's own "Format" section is authoritative.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |

User choice is used in exactly two places: Phase 3's confirmation of the
repository set, and Phase 7's per-candidate decision. Both are gates in the
strict sense — an unanswered question stops the run rather than defaulting to
"yes".

## The Contract

The corpus file's **"Contract"** and **"Format"** sections are the authoritative
specification of everything below; this table is a reading aid, not a second
source. If the two ever disagree, the corpus wins.

| Thing | Value |
|---|---|
| Corpus path | `plugins/aoshimash-skills/rules/agent-rules.md`, relative to the root of a checkout of `aoshimash/skills` |
| Rule format | One `## rule: <id>` section per rule, containing a `**Title:**` line, a `**Detect:**` line of backticked glob patterns, and a `**Rule:**` line followed by the verbatim rule body |
| Managed-block delimiters | `<!-- BEGIN aoshimash-agent-rules -->` … `<!-- END aoshimash-agent-rules -->`, each alone on its own line |
| Per-rule marker inside a block | `<!-- rule: <id> -->`, on the line after the rule's `###` heading |

**Fenced regions are skipped by every parse in this skill** — when enumerating
`## rule:` sections, when counting delimiter lines, and when segmenting a
scanned file into sections. Two inputs make this mandatory rather than
defensive: the corpus's own "Format" section shows the rule template inside a
fence whose first line is literally `## rule: <id>`, so **every** run exercises
this path; and a scanned `AGENTS.md` that documents this mechanism will contain
fenced delimiter examples that must not be mistaken for a real block.

## Workflow

### Phase 0: Preconditions

Verify all of the following before touching anything, and stop if any does not
hold.

**Evaluation order.** Step 1 comes first; if it fails nothing else can be
evaluated, so report it alone. Steps 2 and 5 are then both local: evaluate
**both** and report **every** failure together, so a user with two problems
learns about two rather than discovering them one re-run at a time. Steps 3 and
4 need the network and run only once the local checks pass, in that order,
stopping at the first failure — which is what keeps a logged-out `gh` from being
reported as a wrong repository. Step 6 runs last, only when everything passed.

1. **Inside a git repository, at its root.** `git rev-parse --show-toplevel`
   succeeds; run everything from that directory.
2. **An `origin` remote exists and points at GitHub** (`git remote get-url
   origin`). Without it Phase 1's fetch and Phase 8's push have nowhere to go,
   and a local-only repository has nowhere to open a pull request. Parse the URL
   into `<owner>/<repo>` and keep it: **every later `gh` call names its
   repository explicitly**, and this is where that name comes from.
3. **`gh` is authenticated** (`gh auth status`) and the network is reachable.
   This runs before the identity check below, which is an API call: a logged-out
   or offline `gh` must be reported as exactly that, never as "this is not a
   checkout of `aoshimash/skills`".
4. **This checkout is `aoshimash/skills`.** Two parts, in this order:
   1. The corpus file exists at the contract path. This is a local check; if it
      fails, the checkout is definitively not the corpus repository.
   2. `gh repo view <origin owner/repo> --json nameWithOwner,parent` reports
      `aoshimash/skills` as the repository itself or as its parent (a fork is
      acceptable; [references/corpus-edit.md](references/corpus-edit.md) covers
      the extra handling a fork needs). **Naming the repository is mandatory
      here** — `gh repo view` takes it as a positional argument, and the value
      is the one recorded in step 2. Left off, `gh` resolves the repository from
      the whole remote set and **prefers a remote named `upstream` over
      `origin`**, so the standard fork layout (`origin` = the fork, `upstream` =
      `aoshimash/skills`) reports `aoshimash/skills` with a null parent — the run
      would conclude it is *not* on a fork and skip every fork safeguard,
      including the staleness check that stops a duplicate rule id from being
      appended. **If the command itself fails** — network error, permission
      error, rate limit — report *that* failure and stop; do not convert a
      failed call into a wrong-repository verdict.

   When either part shows this is genuinely the wrong repository, **stop and
   explain**: this skill edits the corpus as a real file, the corpus lives in
   `aoshimash/skills`, and a running skill's own copy is a version-pinned cache
   that is replaced on update — so there is nothing here to edit. Tell the user
   to re-run from a checkout of `aoshimash/skills`. Do not clone one.
5. **The corpus file is unmodified and nothing is staged.**
   `git status --porcelain` must not list the corpus file and must show no
   staged entries, so the commit contains only the promotion. Refuse rather than
   stashing, committing, or discarding the user's work.
6. **Record the starting position** so the wrap-up can restore it:
   `git symbolic-ref --quiet --short HEAD` for a branch, or — when that fails
   because HEAD is detached — `git rev-parse HEAD` for the commit. Restoring by
   SHA is correct for a detached HEAD; do not assume a branch name exists.

### Phase 1: Resolve the base ref

Fetch, determine the default branch, and decide which ref this run reads the
corpus from and will later commit onto — **without checking anything out**
(Principle 6). An open promotion pull request means its branch is reused; a
promotion branch left on the remote with **no** open pull request stops the run,
because every subsequent push would be rejected and no re-run could clear it.
A fork needs its default branch verified current first. See
[references/corpus-edit.md](references/corpus-edit.md).

### Phase 2: Read and parse the corpus

Read the corpus from the base ref resolved in Phase 1 — `git show
<base-ref>:<corpus path>`, not the working tree, so what candidates are deduped
against is exactly what Phase 8 appends to. Parse it into `(id, title, detect
patterns, body)`, skipping fenced regions and the corpus's own non-rule
sections. Record the file's line ending and whether it ends with a newline.
See [references/corpus-edit.md](references/corpus-edit.md).

### Phase 3: Confirm the repository set

List the authenticated user's own, non-fork, non-archived repositories
(metadata only — no file is read yet) and ask the user to choose (see
Environment Adaptation) which to scan: all, a named subset, or cancel. Even when
the user named repositories in the request, show the resolved set and confirm
it. On cancel, go straight to the wrap-up. See
[references/scanning.md](references/scanning.md).

### Phase 4: Read each repository's `AGENTS.md`

For each confirmed repository, read `AGENTS.md` over the GitHub API. Then, only
for those whose `AGENTS.md` was read successfully, make a best-effort second
call for the repository's file list — that is what lets Phase 6 check a drafted
`Detect` pattern against real paths, and it never blocks the run. Never clone,
and keep anything written to disk outside the working tree. A repository with no
`AGENTS.md` is recorded and skipped; an authentication, rate-limit, or network
failure **stops the scan and reports**, because recurrence counted over a
partial set understates the signal. See
[references/scanning.md](references/scanning.md).

### Phase 5: Exclude managed blocks and segment the text

In each fetched file, validate the managed-block delimiters (fence-aware,
whole-line counting; accept only zero of each, or exactly one of each with
`BEGIN` before `END`). A malformed block — unterminated or duplicated — means
that **repository is skipped and reported**, never guessed at. Remove the block
from `BEGIN` to `END` inclusive; everything that remains is the hand-written
text. Segment it into sections by heading, skipping fenced regions. See
[references/scanning.md](references/scanning.md).

### Phase 6: Derive and rank candidates

From the hand-written sections, derive candidate rules. The primary signal is
**recurrence**: the same convention stated in 2+ scanned repositories. Drop
anything already covered by a corpus rule from Phase 2, and anything tied to one
project's domain, architecture, or build commands. Conventions seen in exactly
one repository are listed for visibility but **not proposed** — unless the user
asks for one of them specifically, which puts it to the same per-candidate
decision as any other. If nothing meets the threshold, report that and go to the
wrap-up — no branch, no pull request. See
[references/candidates.md](references/candidates.md).

### Phase 7: Decide one candidate at a time

Present the findings report, then take each candidate in rank order and ask the
user to choose (see Environment Adaptation): **Add** / **Add with edits** /
**Skip** (default) / **Abort**. Never bulk-approve, and never add a candidate
without an explicit Add. Each approved candidate is drafted into the corpus
format — id, title, detect patterns, body — before moving to the next. See
[references/candidates.md](references/candidates.md).

### Phase 8: Write, commit, and open a pull request

Reached only with at least one approved candidate. Check out the branch decided
in Phase 1, confirm the corpus file on disk still matches what Phase 2 read,
append the approved rules by the byte-level recipe, stage only the corpus file,
commit, push, and open the pull request against `aoshimash/skills`. If anything
fails between writing the file and a successful commit, **restore the corpus
file** before the wrap-up — nothing else undoes a modified tracked file. See
[references/corpus-edit.md](references/corpus-edit.md).

### Wrap-up

Reached by **every** exit path — success, a cancelled confirmation, an empty
result, a refusal, and every stop-and-report above.

1. Restore the starting position recorded in Phase 0 step 6 (branch name, or
   commit SHA for a detached HEAD). A run that stopped before that step recorded
   nothing and moved nothing — skip this step rather than guessing a branch.
2. If this run created the collect branch and made no commit on it, delete it
   (`git branch -d chore/collect-agent-rules`). Never delete a branch that
   existed before this run.
3. Delete any temporary files the run created outside the working tree.
4. Report what was scanned, what was skipped and why, what was proposed, what
   was approved, and the pull request URL if one was opened.

## What This Skill Does Not Do

- Does not promote anything automatically. Recurrence proposes; the user
  decides, one candidate at a time.
- Does not edit the repositories it scans. Removing the now-shared hand-written
  copy is the author's call, after a later `sync-agent-rules` run distributes
  the promoted rule.
- Does not clone, and does not read repository contents before the set is
  confirmed.
- Does not scan other people's repositories, forks, or archived repositories.
- Does not read `CLAUDE.md`. The corpus targets `AGENTS.md`; a second source
  file would multiply the malformed-input surface for little gain.
- Does not modify existing corpus rules, reorder them, or change the corpus's
  Contract and Format sections. It only appends new `## rule:` sections.
- Does not repair a malformed managed block in a scanned repository, force-push,
  or resolve a diverged collect branch. Each of those stops for a human.
- Does not delete a leftover promotion branch, sync a stale fork, or push to a
  remote it lacks access to. It stops and hands each back with the exact command
  that clears it.

## References

- [../../rules/agent-rules.md](../../rules/agent-rules.md) — the corpus. Its
  "Contract" and "Format" sections are authoritative for everything this skill
  reads and writes.
- [references/scanning.md](references/scanning.md) — Phases 3–5: repository
  enumeration and confirmation, API reads and their error boundaries,
  managed-block exclusion, fence-aware segmentation.
- [references/candidates.md](references/candidates.md) — Phases 6–7: signals and
  thresholds, exclusions, drafting a rule in corpus format, the findings report
  and the per-candidate decision.
- [references/corpus-edit.md](references/corpus-edit.md) — Phases 1, 2 and 8:
  base-ref resolution, corpus parsing, branch establishment, the byte-level
  append recipe, commit, push, and pull request.
- [references/eval-cases.md](references/eval-cases.md) — human-readable index of
  the eval scenarios; runnable source is [evals/evals.json](evals/evals.json).
