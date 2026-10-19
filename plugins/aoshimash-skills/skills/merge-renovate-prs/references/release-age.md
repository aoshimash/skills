# Release-Age Gate: Enforcing the Configured Cooldown

Detailed procedure for the release-age gate (workflow.md 1-3, re-run at 2-6). It makes the cooldown the repo configured in Renovate hold for every update this skill merges — including the ones Renovate itself could not age.

## Table of Contents

- [Why this gate exists](#why-this-gate-exists)
- [Scope](#scope)
- [The cooldown value](#the-cooldown-value)
- [Determining a member's age](#determining-a-members-age)
- [The PR's age and the decision](#the-prs-age-and-the-decision)
- [Repeated lower-bound waits](#repeated-lower-bound-waits)
- [Known limits](#known-limits)

## Why this gate exists

Renovate's `minimumReleaseAge` holds an update until the release is old enough, so a short-lived broken release is pulled upstream before it reaches this repo. It needs a release timestamp from the datasource, and several datasources do not supply one — GHCR, Quay, ECR and other non-Docker-Hub registries, Git tags, and digest updates on those registries among them. Since Renovate 42 the default `minimumReleaseAgeBehaviour: timestamp-required` holds such an update forever, so repos set `timestamp-optional` for them — which raises the update with **no** age check at all.

The timestamp is missing from the datasource, not from the world. In aoshimash/homelab-k8s, three GHCR updates were merged under the 3-day cooldown in one month (#313 paperless-ngx 3.2.1 at ~32h, #366 home-assistant 2026.10 at ~2.3 days, #374 paperless-ngx 3.3.2 at ~21h); each had an upstream GitHub Release whose `published_at` showed it. This gate looks up that date, and when none can be found it falls back to a bound that is always available and always conservative.

## Scope

Check **every member of every candidate PR** (a grouped PR has several — read them from the update table in the PR body), not only the ones Renovate could not age. Deciding which members Renovate aged would mean re-implementing `packageRules` resolution or keeping a list of timestamp-less datasources, and that list goes stale in the unsafe direction as Renovate's support changes. Re-checking an update Renovate already aged costs an API call and at worst holds it a little longer.

Exempt:

- **Security updates** — Renovate raises vulnerability fixes immediately by design (and configs commonly set `vulnerabilityAlerts.minimumReleaseAge: null`). Renovate's default `vulnerabilityAlerts` config marks them with a `[SECURITY]` commit-message (and so PR-title) suffix; it adds no label by default, so honor any `labels` or suffix the repo's `vulnerabilityAlerts` override sets.
- **`pin` / `pinDigest`** — these freeze what the repo already runs; nothing new is introduced.
- Any member whose effective `minimumReleaseAge` resolves to `null` / `0` in the Renovate config (see below) for a reason the config states.

## The cooldown value

Use the repo's own `minimumReleaseAge`, never a constant: read it in Phase 0 (workflow.md 0-2), and resolve it per member by applying the top-level value and then each matching `packageRules` entry in order (later rules win). `minimumReleaseAgeBehaviour: timestamp-optional` does **not** change the value — it only says what Renovate does when it cannot measure; this gate measures.

No `minimumReleaseAge` configured anywhere → the repo has no cooldown; skip the gate.

## Determining a member's age

Collect up to two numbers per member and take the **larger** (see [The PR's age and the decision](#the-prs-age-and-the-decision) for why the larger is safe).

### 1. Upstream release date (version updates only)

For a version update (major / minor / patch), find the upstream release for the **target** version and read its `published_at`. The source repository comes from the PR body's update table (the `source` link) or release-notes section. Try the exact tag forms the repo is known to use (`v{version}`, `{version}`, `{chart}-{version}`):

```bash
gh api repos/{upstream_owner}/{upstream_repo}/releases/tags/{tag} --jq '.published_at'
```

**Accept the date only if it passes a sanity check:** the release for the **from** version, looked up the same way, must also be found and must be **older** than the target's. A tag name can resolve to an unrelated release — in actions/actions-runner-controller, the tag `actions-runner-controller-0.15.0` is the legacy controller's 2021 release, not the 2026 `gha-runner-scale-set-0.15.0`, and Renovate's own PR body linked the wrong one (#345). A mismatched date can only make a release look *older* than it is, which is the unsafe direction, so a date that fails the check — or whose from-version counterpart cannot be found — is discarded, not trusted.

Do not use a lightweight tag's commit date: the commit can be arbitrarily older than the tag. Do not list every release with `--paginate` to search for a match on repos with long release histories; exact-tag lookups or the release URL in the PR body are enough, and a miss falls through to the lower bound.

**Digest updates** take no release date: a new digest for the same tag is a rebuild or a floating tag moving, and the version's release date says nothing about when that digest was pushed. Use the lower bound alone.

### 2. The lower bound from Renovate's commit (always available)

Renovate can only write a commit that references a release which already exists, so for the newest commit **Renovate authored** on the PR branch:

> true age of every member ≥ now − that commit's `committedDate`

```bash
gh pr view {pr} --json commits \
  --jq '[.commits[] | select(any(.authors[]; .login == "{renovate_login}"))] | last | .committedDate'
```

`{renovate_login}` is the bot identity detection established (e.g. `renovate[bot]`). Filtering by author is required: a `gh pr update-branch` adds a merge commit authored by whoever ran it, and that commit's date bounds nothing (in homelab-k8s#374 the newest commit was such a merge, one minute before the merge).

Renovate re-commits when it rebases or picks up a newer version; each re-commit resets the bound to later, which only makes the gate wait longer.

## The PR's age and the decision

- **Member age** = the larger of the accepted release-date age and the lower bound. Taking the larger is sound because the lower bound is a hard floor on the true age; a release-date age below it means the release record was edited or re-published later, and the floor still holds.
- **PR age** = the **smallest** member age among non-exempt members: a grouped PR is only as old as its newest member.
- **PR age ≥ the cooldown** → the PR passes the gate and enters the order (workflow.md 1-4).
- **PR age < the cooldown** → **cooldown wait**: in autonomous mode do not merge and do not send to the human queue — waiting resolves it. Remove it from this run's order and record, for the report, the member that set the age, which source set it (release date or lower bound), and the **eligible date** (the age source + the cooldown). For a lower-bound wait, word the date as "earliest", since a Renovate re-commit would move it. In interactive mode, list waiting PRs in the plan the same way; the user may explicitly include one, which is their call to make.

The gate runs at triage on every candidate, and again at 2-6 for a PR whose Renovate-authored head commit changed since triage (Renovate pushed while the run was in progress).

## Repeated lower-bound waits

A member whose age only the lower bound can establish — typically a GHCR digest on a floating tag — gets re-committed by Renovate on every scheduled run. On a weekly schedule with a same-day merge session, its bound never reaches a multi-day cooldown, and it holds back every other member of its group with it. That is the same failure Renovate's `timestamp-required` default has, so it must surface rather than repeat silently.

- On the **first** lower-bound wait for a PR, post one comment on it (English, repo convention) carrying the marker `<!-- merge-renovate-prs:cooldown-wait -->`, the member that set the age, and the earliest eligible date. This is the cross-run record; the next run has no other memory.
- When a later run finds the PR **again** waiting on the lower bound and a marker comment from the same account (`gh api user --jq .login`) already exists, it is the second consecutive wait: do not comment again, and raise a **configuration proposal** in Phase 3-2 (workflow.md) — for example removing that member from the group, pinning a floating tag to a full version so updates carry release dates, or `minimumReleaseAge: null` for that package with the reason recorded in the config.

```bash
gh pr view {pr} --json comments \
  --jq '[.comments[] | select(.author.login == "{me}" and (.body | contains("<!-- merge-renovate-prs:cooldown-wait -->")))] | length'
```

The marker only ever leads to a proposal, which the user approves or declines, so a marker another account posted, or a run in between that waited on a release date instead, can at most cause an early proposal — never a merge.

## Known limits

- **Upstream release time is not registry push time.** Renovate measures when the artifact appeared in the registry; this gate measures when the upstream release was published, which usually precedes the image or chart push by the build's duration (minutes to hours). The age is overestimated by that much. Accepted: it is small against a cooldown measured in days, and it applies only where Renovate had no timestamp at all.
- **Registry push time is not used.** GHCR's package-versions API would give the push time of a digest, but it requires the `read:packages` token scope (a token without it gets HTTP 403, confirmed 2026-10-19). Reading an image's own `created` field was not adopted: reproducible builds commonly set it to a fixed epoch, which would make any image look years old.
- **The sanity check needs both releases.** An upstream that publishes no GitHub Releases, or names them in a way the exact-tag lookup misses, gets no release date; such members are aged by the lower bound alone.
