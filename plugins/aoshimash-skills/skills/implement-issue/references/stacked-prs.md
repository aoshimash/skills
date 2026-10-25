# Stacked PRs in Standard Mode

In standard mode every PR used to be based on the default branch, so a dependent issue was
implemented on a base that did not contain its dependency's code. A **stacked PR** fixes that
without giving up per-PR human review: the dependent's worktree is cut from its dependency's
head branch, and its PR targets that branch, so its diff shows only its own change and its code
builds on the code it depends on.

This file is called from [batch.md](batch.md) Merge Modes, B1-3 (the plan), B2-1 (the base,
and restacking at each group boundary), B2-2 (the dispatch), B2-5/B2-6 (the `HELD` status), and
B0 (restacking a re-invoked batch). [review-gates.md](review-gates.md) diffs every PR against its
own base, which is what lets a stacked PR be reviewed as its own change.
Kept out of batch.md because that file is already past the size at which new policy is split
rather than grown.

**Scope.** Standard mode only. Integration mode never stacks — it already cuts each dependent
from an integration branch its dependencies have merged into. Single mode never stacks.

**Plain stacks only.** A stack here is a PR whose base is another PR's head branch, made with
git and `gh pr create --base`. GitHub's native stacked-PR feature (the `gh stack` extension and
the stacks API) is not used; see Known limits.

## S1. Which dependents are stacked

Decide per issue, at B1-3 for the plan and again at B2-1 just before its worktree is cut. Count
the issue's **unmerged dependencies** — dependencies whose PR has not merged into the default
branch (a dependency outside the batch is handled by B1-1 as before and is not counted here):

| Unmerged dependencies | Base |
|---|---|
| None | The default branch, as before |
| Exactly one | **Stacked** on that dependency's head branch, if S2's depth limit and S4's CI precondition allow |
| Two or more | A **merge point**: not dispatched this run — status `HELD` (S5) |

**Why a merge point is held rather than stacked.** A PR can target only one branch. Basing it
on a merge of two unreviewed branches would make its diff carry one dependency's code under the
other's base — a change nobody could review as its own. It is dispatched by a later run, once
all but at most one of its dependencies have merged.

A dependency still has to be **satisfied** exactly as before (B2-5): its PR reached ready for
review. Stacking changes the base the dependent is cut from, never when it may start.

**An unsatisfied dependency outranks a merge point.** Where one dependency failed and another is
merely unmerged, the issue is `SKIPPED` for the failure (B2-5), not `HELD`: no later merge can
release it.

## S2. Depth

Number the PRs from the bottom: a PR based on the default branch is level 1, a PR stacked on it
is level 2, and so on. **The limit is level 3.** An issue that would land at level 4 is `HELD`
until a PR beneath it merges. The deeper a stack, the further one review change at the bottom
ripples, and the longer the chain a reviewer must merge in order.

A tree is allowed: two dependents may stack on the same dependency, each at the same level.

## S3. Making a stacked PR

1. **Cut from the dependency's head branch**, fetched immediately before:
   `git worktree add … origin/<dependency-head-branch>` (platform guide, "Stacked PRs").
2. **Target that branch**: the implementer's dispatch (B2-2) names it as the base, and the PR is
   created with `--base <dependency-head-branch>`.
3. **Write a `## Stack` section** at the top of the PR body, before Decisions & Deviations:

   ```markdown
   ## Stack
   Stacked on #<dependency-PR> (`<dependency-head-branch>`), level <n>.
   Merge #<dependency-PR> first. Once it has merged, this PR must target `<default-branch>`
   before it is merged — GitHub retargets it if the base branch is deleted after that merge,
   and the next run of implement-issue retargets it otherwise; if neither has happened,
   retarget it by hand.
   ```

4. **Keep `Closes #<issue>`.** It does not fire while the PR targets another PR's branch; it
   fires once the PR is retargeted at the default branch and merged there.

Review gates, CI, the automated review response, and the ready flip run exactly as for any
other PR. The gates diff the PR against its own base (review-gates.md), so they see only this
PR's change — not its dependency's code, which a default-branch diff would show as scope creep.

## S4. Precondition: CI must run on a stacked PR

Before the plan offers stacking, establish that the repository's pull-request CI runs on a PR
whose base is **not** the default branch. A workflow that filters its `pull_request` trigger
by base branch — `branches: [main]`, or a `branches-ignore` that excludes other names — never
runs on a stacked PR. The PR then reports no checks, which workflow.md 3-3 cannot tell apart
from a repository with no CI at all, and it would be flipped to ready on checks that never ran.

Read the workflow files on the default branch (platform guide, "Stacked PRs"). For every
workflow that runs checks on a pull request — a `pull_request` or `pull_request_target` trigger
whose event types include opening or updating a PR (no `types:` means the defaults, which do) —
check whether its branch filter admits an arbitrary branch name.

- **Every such workflow admits it**, or the repository has no pull-request CI at all → stacking
  is available.
- **Any such workflow excludes it** → stacking is unavailable for this batch. Base every PR on
  the default branch, as before, and say why in one line of the plan, naming the workflow.
- **It cannot be established** — CI configured outside `.github/workflows`, a trigger built
  from something other than a literal filter, or a file that does not parse → treat stacking
  as unavailable, and say so. The cost is today's behaviour, not a PR flipped on missing CI.

A workflow that only runs after a merge (`types: [closed]`) runs no checks on an open PR and
is not counted.

## S5. `HELD`

| Status | Set by | Meaning | Terminal? |
|---|---|---|---|
| `HELD` | orchestrator | Not dispatched this run: its base would be a merge point (S1) or past the depth limit (S2) | For this batch — a later run dispatches it once enough of its dependencies have merged |

`HELD` is **not** a failure and does not cascade `SKIPPED`. An issue that depends on a `HELD`
issue is itself `HELD`, with the cause traced to the first one. The summary lists every `HELD`
issue with what it waits for — `HELD (waiting for #103 or #104 to merge)` — so a human knows
which merges release it. Dispatching it later is new work, so it needs a plan approved in that
session (batch-reentry.md R8 §1): an unattended run reports it and starts nothing.

## S6. Keeping a stack straight

A base can move after a dependent was cut from it — inside the run, when a Stage 2.5
propagation fix or a later fix round pushes to a dependency that is already ready, and after
it, through human review and human merges. So restacking runs at two points:

- **At every group boundary**, as part of B2-1's light position read, for the stacked PRs the
  batch has already delivered — never for a PR whose implementer or gate is still running —
  and **once more after the last group**, before B3's summary, so a push during the final group
  is not left for the next invocation.
- **When the batch is re-invoked**, at B0's light position read. That is advancing PRs an
  approved plan already produced, so it runs in an unattended session too
  (batch-reentry.md R8 §1).

**Which PRs, and in what order.** Every PR of this batch whose body carries a `## Stack`
section — including one GitHub has already retargeted, which still needs its new base merged
in. Work **bottom-up**, lowest level first, so a PR is checked against a base that has itself
just been restacked.

**The base comes from the platform, never from the body.** The `## Stack` section is text, so
it only selects the PR. Its base is the PR's `baseRefName`. Where that is the default branch,
merge the default branch in if it is not already contained, and stop. Where it is a branch that
is the head of another PR **of this batch**, act on that PR's state below. Any other base —
a branch no batch PR heads — is reported, not merged.

For a base that is a batch PR's head:

| Base PR | Action |
|---|---|
| Open, and its head is already an ancestor of this PR's head | Nothing |
| Open, and its head has moved on | Merge `origin/<base-branch>` into this PR's branch and push |
| Merged | Retarget this PR at the **base PR's own base** (`baseRefName` — the default branch when the stack was merged bottom-up, another PR's branch when it was not) unless that is already its base, then merge that branch in and push. On the default branch this also clears the duplicate commits a squash merge leaves behind |
| Closed without merging | Touch nothing. The stack's foundation is gone; report the PR as needing a human |

**Where the merge runs.** The issue's own worktree is gone by then (B2-7), and
batch-reentry.md R7 forbids reusing a leftover one. Cut a fresh, detached worktree at a fresh
path from `origin/<this PR's branch>`, merge there, push `HEAD` to the PR's branch, and remove
the worktree (platform guide, "Stacked PRs").

**Guards, all fail-closed:**

- **Never rebase, reset, or force-push.** A restack is a merge commit on top; review history on
  the PR stays intact.
- **A merge that conflicts is aborted** and nothing is pushed. Report the PR and the conflicting
  paths; a human resolves it.
- **A PR with any human review or comment is reported, not restacked.** Human review comments
  are never auto-addressed, and a push under a reviewer's feet is not this run's to make.
  Authorship is judged as in automated-review.md: ambiguous counts as human.
- **A read that may be incomplete restacks nothing** — the same rule as context-budget.md C3.

Restacking does not re-run the review gates. It brings in code that was reviewed on its own PR,
and the PR's CI runs again on the push. It is not a move toward any eligibility, which is why
batch-reentry.md's "never retargets" rule for the merge gate's candidates does not cover it.

## Known limits

- **Restacking needs a re-run.** Between runs, a stack is only as straight as GitHub keeps it.
  GitHub's documentation says that deleting a merged PR's head branch retargets the open PRs
  based on it to that PR's base; it does not say whether the repository's automatic head-branch
  deletion triggers the same. In the one real stack found in the owner's repositories
  (`Tech-Residence/isucon-template`, which deletes head branches on merge), the retarget never
  got the chance: #6 merged into `main`, its head branch was never deleted — it still exists —
  so #7, stacked on it, was never retargeted and was later merged into that already-merged
  branch; its code reached `main` only by some later route. Without a retarget and without a re-run, that is what happens, which is
  why S3's `## Stack` section tells the human.
- **Merge order is the human's.** The `## Stack` section says to merge bottom-up. A human who
  merges a stacked PR into its base branch first makes the base PR carry both changes; the
  base PR's diff then shows them, and both still reach the default branch only through a
  human-merged PR.
- **Merge points wait for humans.** A batch with many merge points holds much of its work until
  humans merge; integration mode handles them in one run, because its merge gate merges.
- **GitHub's native stacks are not used.** They would add stack-aware CI and server-side
  rebasing, but need the `gh stack` extension and are not yet verified with this skill. The
  plain stack works without them.
- **The CI precondition reads workflow files only.** Required checks configured as rulesets or
  external CI are not inspected beyond S4's "cannot be established" rule.
