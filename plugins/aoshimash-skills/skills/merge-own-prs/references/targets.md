# Targets, Selection, and the Local Checkout

How a run decides which repositories it works in and which PRs in them it may act on. Everything after selection — ordering and the per-PR loop — lives in [workflow.md](workflow.md).

## Table of Contents

- [Target forms](#target-forms)
- [Candidates](#candidates)
- [The selected set](#the-selected-set)
  - [Review requested from the account](#review-requested-from-the-account)
  - [Mergeable without another person's approval](#mergeable-without-another-persons-approval)
  - [Not an integration-branch PR](#not-an-integration-branch-pr)
- [Rules that follow from the set](#rules-that-follow-from-the-set)
- [A local checkout per repository](#a-local-checkout-per-repository)
- [Known limits](#known-limits)

## Target forms

Resolve the target once, from the user's request, before the first GitHub read:

| The user names | The run covers | Review-request condition |
|---|---|---|
| nothing | the repository in the current directory | applies |
| a repository (`owner/repo`, or its URL) | that repository | applies |
| one or more PRs (a PR URL, `owner/repo#N`, or `#N` in the repository the conversation or the current directory names) | the repository of each PR | skipped for the named PRs |
| an owner — an organization or a user account (`my-org`, `github.com/my-org`) | every repository of that owner where the account has an open PR | applies |

A name with a `/` is a repository; a bare name is an owner. A bare name that is also a repository of the current directory's owner, or a PR reference whose repository cannot be told, is not guessed: ask (user choice). Several repositories form **one serial queue** — they are never processed in parallel.

## Candidates

The candidates are the open, non-draft PRs authored by the account the platform access method authenticates as, in the target ([platform-github.md](platform-github.md) "List candidate PRs"). For named PRs, the candidates are the named PRs; one that is closed, a draft, or authored by someone else is reported and dropped.

The search is complete only when the number of rows fetched is below the limit passed; a count equal to the limit is re-read with a higher limit, up to the search API's 1,000-result ceiling. An enumeration that may be short only misses PRs — the safe direction — so the run proceeds and the report says the enumeration may be incomplete and why.

## The selected set

The **selected set** is the set of PRs the run may act on: reply, resolve, push to, review, merge, revert. A candidate is selected only when **all three** conditions below hold. Read them per PR with one GraphQL query ([platform-github.md](platform-github.md) "Read the selection fields of a PR"); a read that fails leaves the PR unselected, with the failure as its reason.

### Review requested from the account

The PR's current review requests include the account itself, or a team the account belongs to ([platform-github.md](platform-github.md) "List the account's teams"). This is how the user marks a PR as ready for this skill: CODEOWNERS, a teammate, or the user requested review from them or from their team.

- GitHub's `review-requested:@me` search does **not** return PRs the account authored, even when one of its teams is requested (observed 2026-11-12: a PR with a team request for the author's team was absent from that search). So the condition is read from each candidate's own `reviewRequests`, never from that search.
- A request for a team counts when the team appears in the account's team list. A team list that cannot be read completely means team requests cannot be judged: only direct requests select, and the report says so.
- **Named PRs skip this condition.** Naming a PR is itself the delegation. The other two conditions still apply.

### Mergeable without another person's approval

The account can merge the PR without anyone else approving it — the user's precondition for this skill. It holds when either is true:

- `reviewDecision` is empty: no rule on the base branch requires an approving review, so the author can merge once the other requirements hold; or
- `viewerCanMergeAsAdmin` is true: the account may bypass the base branch's protections — a ruleset bypass-list entry, or repository-admin rights over classic branch protection.

Anything else — `REVIEW_REQUIRED` or `CHANGES_REQUESTED` with `viewerCanMergeAsAdmin` false — excludes the PR: it needs another person's review, which is not this skill's job. Observed 2026-11-12 across four repositories: `viewerCanMergeAsAdmin` was true exactly where the base branch's ruleset reported `current_user_can_bypass: always`, and false where it reported `never`.

Being mergeable without approval is about the review requirement only. Every other requirement — CI, threads, conflicts, rules the bypass would skip — is checked in the pre-merge gate ([workflow.md](workflow.md) "2-4") and shown to the human.

### Not an integration-branch PR

A PR whose base branch matches `integration/**` belongs to the issue pipeline's merge gate (`merge-issue-prs`), which owns those branches and their milestone PRs. Exclude it and say which skill handles it. A PR from an `integration/**` branch into the default branch — a milestone PR — is not excluded by this rule: it is a human-reviewed PR like any other, and this skill's per-PR human decision is that review.

## Rules that follow from the set

- **Never act on a PR outside it.** A base PR of a stacked selected PR that is not itself selected blocks the stacked one: report the pair, process neither.
- **An empty set is a result, not a failure.** Report how many candidates there were and why each was excluded. Do not widen the set to find work.
- **The set is fixed at Phase 0.** GitHub's search docs say a requested reviewer stops being listed once they review; for the author's own replies the docs say nothing. Observed 2026-11-12 on one PR: the author's in-thread reply, which GitHub recorded as an empty COMMENTED review six minutes after a request to the author's team, left that team request in place. One observation is not a rule, so the run keeps a PR it selected whatever happens to the request. The report names every PR the run handled but did not merge, because a later run may no longer select it by request — name it explicitly to pick it up.

## A local checkout per repository

Fix-ups need a working tree on the PR's head branch. Never use the user's own working tree: it may hold unrelated uncommitted work.

- The current directory is a clone of the target repository → add a worktree for the PR's head branch in a new, empty temporary directory.
- Otherwise → clone the repository into a new, empty temporary directory and check out the PR there.

One worktree or clone per repository, reused across that repository's PRs, never shared between repositories. Report each path, so a human can pick up a stopped line from it. Remove a worktree only when the run ends with nothing stopped in it.

## Known limits

- **The candidate search is GitHub's search index.** A PR opened moments ago can be missing from it. That only shrinks the candidates.
- **Team membership is the account's own view.** A secret team the account belongs to is listed; membership granted after the list was read is not.
- **A team request is shared.** Another member of the requested team can review or merge the PR while the run handles it. The loop re-reads the PR before each step that writes ([workflow.md](workflow.md) "2-1"), and a PR someone else merged is verified, not merged again.
