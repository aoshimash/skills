# Corpus Edit

Detailed procedure for Phases 1, 2 and 8 of [../SKILL.md](../SKILL.md), plus the
git specifics of the wrap-up: resolving the ref the corpus is read from and
committed onto, parsing it, and appending approved rules in bytes that two
agents would produce identically.

Phases 1 and 2 only read. **Phase 8 is the only part of this skill that changes
anything**, including git refs.

## Phase 1: Resolve the base ref

```bash
git fetch --prune origin
gh repo view --repo <origin owner/repo> --json defaultBranchRef --jq .defaultBranchRef.name
gh pr list --repo aoshimash/skills --head chore/collect-agent-rules --state open \
  --json number,url,headRepositoryOwner
git ls-remote --heads origin chore/collect-agent-rules
```

Always pass `--repo` explicitly. Without it the base repository `gh` picks
depends on the local configuration, which is the difference between reading the
fork's default branch and the corpus repository's.

| Situation | Base ref | Mode |
|---|---|---|
| An open pull request exists for `chore/collect-agent-rules` | `origin/chore/collect-agent-rules` | **reuse** |
| No open pull request, and no remote branch of that name | `origin/<default-branch>` | **create** |
| No open pull request, but `origin/chore/collect-agent-rules` still exists | — | **stop** (see below) |

- **Do not check anything out here.** The branch is established in Phase 8, once
  there is something to commit (Principle 6). Recording the decision now is what
  keeps Phase 2's read and Phase 8's write on the same ref.
- The reuse case is what stops a rule promoted by a still-open earlier run from
  being proposed a second time and appended twice: Phase 2 reads that branch's
  corpus, so the rule is already there.
- **A remote branch with no open pull request stops the run.** `aoshimash/skills`
  has `deleteBranchOnMerge` enabled, so a merged promotion cleans itself up; the
  branch that survives is one whose pull request was **closed without merging**.
  Create mode would then base on the default branch and push a history unrelated
  to that leftover branch, and every future run would repeat the same rejected
  push forever — Phase 1 makes the identical decision each time, so "re-run and
  it resolves" would be false. Stop, and say exactly how to clear it: delete the
  remote branch (`git push origin --delete chore/collect-agent-rules`) or reopen
  the closed pull request, then re-run. Query the remote directly with
  `git ls-remote` rather than trusting a remote-tracking ref, which is why the
  fetch above uses `--prune`.
- A **local** `chore/collect-agent-rules` with no open pull request is not
  reused either. Nothing deletes local branches when a pull request merges, so a
  leftover branch sits behind the default branch; after a squash merge its merge
  base is the pre-promotion commit, and the next pull request would re-add
  everything and conflict.

### When the checkout is a fork

A fork is accepted, but two things must be handled or the run silently corrupts
the corpus.

1. **The pull request must land on the corpus repository.** Pass
   `--repo aoshimash/skills` to `gh pr list` and `gh pr create`. Note that
   `gh pr list --head` does not support the `<owner>:<branch>` syntax, so when
   the branch lives on a fork, confirm the pull request it finds is the one for
   this fork's branch (check its `headRepositoryOwner`) before treating it as
   reuse.
2. **The base ref must not be a stale fork copy.** `origin/<default-branch>` on
   a fork can be behind `aoshimash/skills`. Phase 2 would then dedupe against an
   old corpus, and a rule promoted upstream since the last fork sync would be
   re-proposed and appended a second time — a duplicate `## rule: <id>` in the
   merged corpus, exactly the collision 6-4 and Principle 7 exist to prevent.
   Verify the fork is current before using its default branch as the base:

   ```bash
   git fetch https://github.com/aoshimash/skills.git <parent default branch>
   git rev-list --count origin/<fork default branch>..FETCH_HEAD
   ```

   A count of `0` means the fork carries every upstream commit and
   `origin/<fork default branch>` is a sound base. Anything else means the fork
   is behind: **stop and report**, telling the user to sync it
   (`gh repo sync <fork> --source aoshimash/skills`) and re-run. Do not sync it
   automatically — that is a write to another repository, outside what this
   skill does.

## Phase 2: Read and parse the corpus

```bash
git show <base-ref>:plugins/aoshimash-skills/rules/agent-rules.md
```

Read from the ref, **not** from the working tree. The session may be on any
branch; reading the working tree would dedupe candidates against a copy the
pull request is not based on, which is how a rule gets proposed that already
exists on the base — or gets dropped as "already covered" when it is not there.

Then:

1. **Record the line ending** (LF or CRLF, by majority) and whether the blob
   ends with a newline. Phase 8 writes in that same line ending; assuming LF
   would rewrite every line of a CRLF file.
2. **Enumerate `## rule: <id>` sections, skipping fenced regions.** The Format
   section shows the template inside a fence whose first line is literally
   `## rule: <id>`; a line-by-line match parses a phantom rule with the
   placeholder id `<id>`, which would then be "already covered" for anything and
   would collide with a real id. Fence tracking is described in
   [scanning.md](scanning.md#5-3-segment-into-sections).
3. For each real rule, capture `(id, title, detect patterns, body)`. The body
   starts on the line **after** the `**Rule:**` line and runs to the next
   `##`-level heading or end of file, with surrounding blank lines trimmed.
4. **Skip the corpus's own non-rule sections** — "Contract", "Format", "Rules".
   They are documentation, and this skill never edits them.
5. **Record the insertion point**: the index of the first `##`-level heading
   line that follows the **last** `## rule:` section (fence-aware), or end of
   file if there is none. Appending here — rather than blindly at end of file —
   is what keeps a non-rule section that someone later appends after the rules
   from being swallowed into the last rule's body.

If the corpus cannot be read, or contains no `## rule:` section at all, stop and
report. Never reconstruct corpus content from memory, and never fall back to a
copy bundled with this skill.

## Phase 8: Write, commit, and open a pull request

Reached only with a non-empty approval queue from Phase 7.

### 8-1. Establish the branch

Use the mode recorded in Phase 1.

**Reuse** — the branch already has an open pull request:

```bash
git switch chore/collect-agent-rules     # or: git switch -c chore/collect-agent-rules origin/chore/collect-agent-rules
git merge --ff-only origin/chore/collect-agent-rules
```

If the fast-forward fails the branches have genuinely diverged: **stop and
report**. Never `git reset --hard`, merge, rebase, or force — a hard reset here
would destroy whatever the local branch carries that the remote does not.

A local branch merely *ahead* of the remote — the expected state after a
rejected push — is **not** a failure: `git merge --ff-only` reports
"Already up to date." and exits 0, so the run continues. That is safe because
8-2 then compares the corpus on disk against what Phase 2 read from
`origin/chore/collect-agent-rules`; the unpushed commit makes them differ and
the run stops there, before any append lands on a base it did not read.

**Create** — no open pull request:

```bash
git switch -c chore/collect-agent-rules origin/<default-branch>   # -C to replace a leftover local branch
```

Before replacing a leftover local branch with `-C`, check it holds no commits
absent from the base (`git log --oneline origin/<default-branch>..chore/collect-agent-rules`).
If it does, stop and report rather than discarding work. **Never base the branch
on the session's current branch** — that would drag unrelated commits into the
pull request.

If `git switch` fails for any other reason — most commonly unrelated
uncommitted files that would be overwritten — stop and report. Do not stash or
discard the user's work to get past it.

Remember whether this run created the branch; the wrap-up deletes it if no
commit lands.

### 8-2. Confirm the corpus has not moved

Re-read the corpus file from the working tree and compare it byte-for-byte with
what Phase 2 read from the base ref. They must be identical. If they are not,
something changed between the two — a concurrent push, a stale fetch, a
different ref than expected — and the insertion point recorded in Phase 2 no
longer describes this file. **Stop and report**; re-running picks up the new
state cleanly.

### 8-3. Render each approved rule

Each approved candidate becomes exactly these lines, in this order, with exactly
one blank line where shown and none anywhere else:

```markdown
## rule: <id>

**Title:** <title>

**Detect:** `<glob>`, `<glob>`

**Rule:**

<body>
```

- The `Detect` list is comma-and-space separated, every pattern backticked.
- The body has no leading or trailing blank lines and contains no markdown
  heading. Do not re-wrap it.

### 8-4. Splice, byte for byte

Work in lines, using the line ending recorded in Phase 2:

1. `head` = the corpus lines before the Phase 2 insertion point, with trailing
   blank lines removed.
2. `tail` = the corpus lines from the insertion point onward, unchanged.
3. Result = `head`, then for **each approved rule in approval order**: one blank
   line followed by that rule's rendered lines. Then, if `tail` is non-empty,
   one blank line followed by `tail`.
4. Join with the recorded line ending and end the file with exactly one line
   ending after its last line.

Consequences worth stating, because they are what make two runs agree:

- Exactly one blank line separates every pair of adjacent sections, and the file
  never gains a trailing blank line.
- Approval order is the corpus order for the new rules, and existing rules are
  not reordered. Corpus order determines the order rules are appended in a
  target repository.
- No existing byte changes except the possible removal of trailing blank lines
  immediately before the insertion point, and the addition of a final newline if
  the file lacked one. Both are normalizations of whitespace the corpus should
  not have had; nothing inside an existing rule is touched.

### 8-5. Commit

Stage **only** the corpus file, by name. Never `git add -A` or `git add .` —
that is the guard that keeps stray files out of the change.

```
feat(rules): promote <n> hand-written rule(s) into the shared corpus

- <id> — seen in <owner>/<repo>, <owner>/<repo>
- <id> — seen in <owner>/<repo>, <owner>/<repo>

Scanned <n> repositories (<m> skipped: <reasons>).
```

### 8-6. Push and open the pull request

```bash
git push -u origin chore/collect-agent-rules
```

If the push is rejected as non-fast-forward, someone pushed to the branch during
this run: **stop and report, and do not force-push.** The local commit survives,
and re-running picks the new remote state up in Phase 1.

Then open the pull request against `aoshimash/skills` (`--repo aoshimash/skills`,
and `--head <fork owner>:chore/collect-agent-rules` when pushing from a fork),
or — when one is already open for this branch — let the push update it rather
than opening a second one. Use a plain title (no Conventional Commit prefix),
e.g. *Promote N hand-written rules into the shared corpus*.

**If `gh pr create` itself fails** after a successful push, the commit is safely
on the remote branch and the wrap-up will *not* delete that branch, because a
commit landed on it. Report the branch name, the error, and that the corpus edit
is pushed but unreviewed. Re-running is the recovery: Phase 1 finds no open pull
request, and — because the remote branch now exists without one — stops with the
instructions for clearing it, so the user can either open the pull request by
hand or delete the branch and start over. Do not retry blindly in a loop.

The body states, per promoted rule:

- the id, title, and detect patterns, and why those patterns indicate the tool
  is in use;
- every repository the convention was found in, with the heading it appeared
  under;
- that the source repositories are **not** modified, and that a later
  `sync-agent-rules` run is what distributes the rule back into them.

Plus, for the run as a whole: which repositories were scanned, which were
skipped and why (no `AGENTS.md`, malformed managed block, unreadable content),
which candidates were skipped by the user, and which conventions were excluded
as already covered.

Return the pull request URL.

**Never commit directly to the default branch, and never merge the pull request
as part of this skill.**

## Wrap-up: git specifics

1. `git switch <starting branch>`, or `git switch --detach <starting SHA>` when
   Phase 0 recorded a detached HEAD.
2. `git branch -d chore/collect-agent-rules` only if this run created it and no
   commit landed on it. Never delete a branch that existed before this run, and
   never `-D`.
3. Delete temporary files created outside the checkout.
