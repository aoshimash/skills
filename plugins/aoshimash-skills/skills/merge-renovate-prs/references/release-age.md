# Release-Age Gate: Enforcing the Configured Cooldown

Detailed procedure for the release-age gate (workflow.md 1-3, re-run at 2-6). It makes the cooldown the repo configured in Renovate hold for every update this skill merges — including the ones Renovate itself could not age — at the moment it merges; a floating value's later releases are outside it (see [Known limits](#known-limits)).

## Table of Contents

- [Why this gate exists](#why-this-gate-exists)
- [Scope](#scope)
- [The cooldown value](#the-cooldown-value)
- [Determining a member's age](#determining-a-members-age)
- [Floating values](#floating-values)
- [The PR's age and the decision](#the-prs-age-and-the-decision)
- [Repeated lower-bound waits](#repeated-lower-bound-waits)
- [Known limits](#known-limits)

## Why this gate exists

Renovate's `minimumReleaseAge` holds an update until the release is old enough, so a short-lived broken release is pulled upstream before it reaches this repo. It needs a release timestamp from the datasource, and several datasources do not supply one — GHCR, Quay, ECR and other non-Docker-Hub registries, Git tags, and digest updates on those registries among them. Since Renovate 42 the default `minimumReleaseAgeBehaviour: timestamp-required` holds such an update forever, so repos set `timestamp-optional` for them — which raises the update with **no** age check at all.

The timestamp is missing from the datasource, not from the world. In aoshimash/homelab-k8s, three GHCR updates were merged under the 3-day cooldown in one month (#313 paperless-ngx 3.2.1 at ~32h, #366 home-assistant 2026.10 at ~2.3 days, #374 paperless-ngx 3.3.2 at ~21h); each had an upstream GitHub Release whose `published_at` showed it. This gate reads the registry's own publish time where the registry records one, the upstream release date where it does not, and when neither can be found falls back to a bound that is always available and always conservative.

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

The commands in this file are the CLI form of each read; platform-github.md "Access Method" decides whether another method covers the GitHub reads. The registry reads are not GitHub operations and run as written (SKILL.md "Environment Adaptation", package registry read).

First decide whether the member's value is **floating** — resolved by the consuming tool at run time to the newest release matching it — as [Floating values](#floating-values) defines. A floating member is aged only as that section says; everything else in this section is for the rest.

Collect two numbers per member — a **source age** and the **lower bound** — and take the **larger** (see [The PR's age and the decision](#the-prs-age-and-the-decision) for why the larger is safe). The source age is the first of these that yields an accepted date; a member with neither is aged by the lower bound alone:

1. the **registry publish time** of the exact target version;
2. only when the registry gives none, the **upstream release date**.

The order follows what the cooldown is for: a broken release pulled soon after publication must never reach this repo, so what counts is when the artifact the repo installs became available. Where the registry records that, it is the measurement; the upstream release date is a proxy for it, and the lower bound a floor. When step 1 yields an accepted time, step 2 is not read: an upstream release published before the registry upload would only make the member look older.

### 1. Registry publish time (version updates only)

Applies when the member's package is installed from a registry this file has a reference read for — the public npm registry or PyPI — and the update has an exact target version. That version is the one the lockfile change resolves, or the pinned version the diff writes (Renovate's diff link carries it as `…/{from}/{to}`), never a range from the update table (`^24.0.0` → `^26.0.0`).

Take the registry from the lockfile's tarball URL where the lockfile records one (`resolved` in `package-lock.json` or `yarn.lock`), otherwise from the repo's registry or index configuration (`.npmrc` `registry` / `@scope:registry`, a pip or uv index setting), otherwise the public default. A package resolved from any other registry — a private registry or a mirror — gets no registry time here: the public record under the same name may not be the artifact the repo installs.

- **npm.** The full package document's `time` object maps each version to the time it was published. The abbreviated install document (`Accept: application/vnd.npm.install-v1+json`) has no `time`, so read the full one (`npm view {package} time --json` returns the same object):

  ```bash
  curl -fsS "https://registry.npmjs.org/{package}" | jq -r --arg v "{version}" '.time[$v] // empty'
  ```

- **PyPI.** A version is one or more distribution files, each uploaded on its own. The per-version JSON API lists them under `urls`, each with `upload_time_iso_8601`; take the **newest**, because a file added later (a wheel for another platform) became installable only then:

  ```bash
  curl -fsS "https://pypi.org/pypi/{package}/{version}/json" | jq -r '[.urls[].upload_time_iso_8601] | max // empty'
  ```

  PyPI's JSON API documentation shows this field only in its examples. The Simple Repository API specification defines the per-file `upload-time` as the time the file was uploaded to the index, and the two values were observed equal for every file of requests 2.32.3 (2026-10-30).

Empty output (no record for that version) or a failed read (a 404, a network error) → no registry time; go to step 2.

**Accept the time only if it passes the same sanity check as the release date in step 2:** the **from** version's registry time, read the same way, must exist and be **older** than the target's; otherwise discard the target's time and go to step 2. A version key cannot resolve to an unrelated record the way a tag name can, but the read can still hit the wrong package — an npm alias (`"x": "npm:typescript@^7"`), or a name the public registry also holds while the repo installs from elsewhere — and the check catches that wherever the from version is missing there or out of order.

Do not take Renovate's `renovate/stability-days` status as the age or as a pass. Under `minimumReleaseAgeBehaviour: timestamp-optional`, Renovate treats a release without a timestamp as stable, so the check can be green for an update it never aged, and it is one status for the whole branch, which does not say which members it measured. It is the check this gate exists to back up.

### 2. Upstream release date (version updates only, when the registry gives none)

For a version update (major / minor / patch) with no accepted registry time — container images on registries without timestamps, GitHub Actions, Git-tag datasources, or a registry read that came back empty — find the upstream release for the **target** version and read its `published_at`. The source repository comes from the PR body's update table (the `source` link) or release-notes section. Try the exact tag forms the repo is known to use (`v{version}`, `{version}`, `{chart}-{version}`):

```bash
gh api repos/{upstream_owner}/{upstream_repo}/releases/tags/{tag} --jq '.published_at'
```

**Accept the date only if it passes a sanity check:** the release for the **from** version, looked up the same way, must also be found and must be **older** than the target's. A tag name can resolve to an unrelated release — in actions/actions-runner-controller, the tag `actions-runner-controller-0.15.0` is the legacy controller's 2021 release, not the 2026 `gha-runner-scale-set-0.15.0`, and Renovate's own PR body linked the wrong one (#345). A mismatched date can only make a release look *older* than it is, which is the unsafe direction, so a date that fails the check — or whose from-version counterpart cannot be found — is discarded, not trusted.

Do not use a lightweight tag's commit date: the commit can be arbitrarily older than the tag. Do not list every release with `--paginate` to search for a match on repos with long release histories; exact-tag lookups or the release URL in the PR body are enough, and a miss falls through to the lower bound.

**Digest updates** take no registry time and no release date: a new digest for the same tag is a rebuild or a floating tag moving, and the version's publish or release date says nothing about when that digest was pushed. Use the lower bound alone.

### The lower bound from Renovate's commit (always available)

Renovate can only write a commit that references a release which already exists, so for the newest commit **Renovate authored** on the PR branch:

> true age of every non-floating member ≥ now − that commit's `committedDate`

It bounds the version the commit names, so it says nothing about a floating member: the release such a value resolves to can be published after the commit.

```bash
gh pr view {pr} --json commits \
  --jq '[.commits[] | select(any(.authors[]; .login == "{renovate_login}"))] | last | .committedDate'
```

`{renovate_login}` is the bot identity detection established (e.g. `renovate[bot]`). Filtering by author is required: a branch update (`gh pr update-branch`) adds a merge commit authored by whoever ran it, and that commit's date bounds nothing (in homelab-k8s#374 the newest commit was such a merge, one minute before the merge).

Renovate re-commits when it rebases or picks up a newer version; each re-commit resets the bound to later, which only makes the gate wait longer.

## Floating values

Every read above ages the version Renovate picked, and CI installs that version only when the value the diff writes names it exactly. A **floating** value is resolved by the consuming tool at run time to the newest release matching it: `node-version: "26"` under `actions/setup-node`, a major-only image tag (`node:26`), an action ref on a moving major tag (`@v5`), a range that no lockfile fixes. For such a member the source age measures a build CI may not install, and the lower bound is no floor. In the PR behind [eval Case 22](eval-cases.md#case-22-a-floating-value-cooldown-floating-value--autonomous), Renovate committed `node-version: "26"` at 2026-10-28T22:28:35Z, having picked 26.12.1. actions/node-versions then published 26.13.0 at 2026-10-29T02:33:28Z and listed it in its manifest at 15:48:30Z, and from then on setup-node would install 26.13.0 for `"26"` on a runner without a 26.x cached — a build younger than the commit.

### Recognising one

Treat a member's value as **exact** only when one of these holds; otherwise it is floating:

- a lockfile the diff changes records the exact version (step 1's case);
- the value carries a digest or a commit SHA;
- the value is the full version Renovate resolved the update to — the string its release notes, badges or diff link name for the target, ignoring a leading `v` — with no range operator, wildcard or alias.

An update table showing `24` → `26` while its badges name 26.12.1 is floating. When the value cannot be compared with Renovate's resolved version, treat it as floating.

### Aging one

A floating member's age is the age of the **newest release its value can resolve to now**, read from the source the consuming tool resolves from. Do not take the larger of that and the lower bound, and do not read the release Renovate picked. This file has that read for one tool; any other floating member — another tool, another input, a value form not listed below — has an **unknown** age (see [The PR's age and the decision](#the-prs-age-and-the-decision)).

**`actions/setup-node`**, when its step sets `node-version` to a major (`26`) or a major and minor (`26.12`), and sets neither `node-version-file`, `mirror` nor `stable: false`. setup-node v7.1.0 (`src/distributions/official_builds/official_builds.ts`, with `@actions/tool-cache`'s `find` and `findFromManifest`; read 2026-10-30) resolves such a value in this order. With `check-latest: true` it first takes the manifest's match. Then it checks the runner's tool cache, which yields its highest matching version. Then it takes the first stable entry of the actions/node-versions `versions-manifest.json` on `main` that matches and has a file for the runner. `@actions/tool-cache` requires the manifest sorted newest first and stops at the first match. If the manifest has no match, or fetching it or the build fails, setup-node takes the highest matching version in the Node.js release index (`https://nodejs.org/dist/index.json`). Leaving aside versions placed in the tool cache by something other than setup-node (see Known limits), the youngest build the value can resolve to is the newer of the manifest's first match and the release index's highest.

```bash
# 1. The manifest's first stable match, with its release tag
gh api -H "Accept: application/vnd.github.raw" \
  "repos/actions/node-versions/contents/versions-manifest.json?ref=main" \
  | jq -r --arg spec "{spec}" 'first(.[] | select(.stable and ((.version + ".") | startswith($spec + ".")))) | "\(.version) \(.release_url | sub(".*/tag/"; ""))"'

# 2. That release's publish time
gh api "repos/actions/node-versions/releases/tags/{tag}" --jq '.published_at'

# 3. The release index's highest match
curl -fsS "https://nodejs.org/dist/index.json" \
  | jq -r --arg spec "{spec}" '[.[].version | ltrimstr("v") | select(test("^[0-9]+\\.[0-9]+\\.[0-9]+$")) | select((. + ".") | startswith($spec + "."))] | max_by(split(".") | map(tonumber)) // empty'
```

`{spec}` is the `node-version` value the diff writes, unquoted. Read 1 ignores the runner's platform. A newer entry without a file for it would be skipped by setup-node, so ignoring the platform can only pick a younger build.

- **The index's version is newer than the manifest's** → the newest build is not in the manifest yet, and setup-node installs it whenever the manifest cannot be fetched. The member is too young. Its eligible date is not computed, because the time the manifest will list it is unknown; the next run re-reads it.
- **Otherwise** → the member's age is now − read 2's `published_at`. That release is the actions/node-versions build of a Node.js release Node.js had already published (v26.13.0: nodejs/node's GitHub Release at 2026-10-28T16:57:41Z, the build at 2026-10-29T02:33:28Z). So this age is never more than the time since Node.js published that version. It is more than the time since the manifest listed the build (26.13.0 was listed at 2026-10-29T15:48:30Z, 13 h after its release). That time is not used: it measures when setup-node could first fetch this build, not how long the release has been public.
- **Any read fails or returns nothing** → the age is unknown.

### After the merge

The gate measures a floating member once, when it merges. From then on CI installs each newer matching release as soon as its source lists it, with no PR and no cooldown — as the value the PR replaces already did. When a run finds a floating member whose newest resolution is younger than the cooldown, it raises a **configuration proposal** in Phase 3-2 (workflow.md): pin the value to a full version, so that the version the diff writes is the build CI installs, and each later release reaches the repo only as a change to that value, which this gate ages. Name the member, its value, the build it resolves to and that build's age. The cost is a change for every release in that line instead of none.

## The PR's age and the decision

- **Member age** = the larger of the source age (the accepted registry time or, failing that, the accepted release date) and the lower bound. Taking the larger is sound because the lower bound is a hard floor on the true age; a source age below it means the record was edited or re-published later, and the floor still holds. A **floating** member's age is its newest resolution's age alone ([Floating values](#floating-values)), or unknown.
- **Any non-exempt member's age unknown** → the gate cannot pass the PR, and waiting does not resolve it: in autonomous mode defer it to the **human queue**, naming the member, its value, and why its resolution could not be aged; in interactive mode surface it the same way.
- **PR age** = the **smallest** member age among non-exempt members: a grouped PR is only as old as its newest member.
- **PR age ≥ the cooldown** → the PR passes the gate and enters the order (workflow.md 1-4).
- **PR age < the cooldown** → **cooldown wait**: in autonomous mode do not merge and do not send to the human queue — waiting resolves it. Remove it from this run's order and record, for the report, the member that set the age, which source set it (registry time, release date, lower bound, or a floating value's newest resolution), and the **eligible date** (the age source + the cooldown). For a lower-bound or floating wait, word the date as "earliest", since a Renovate re-commit or a newer matching release would move it; a floating wait on a build not yet in its manifest has no date, and is reported as re-checked next run. In interactive mode, list waiting PRs in the plan the same way; the user may explicitly include one, which is their call to make.

The gate runs at triage on every candidate, and again at 2-6 for a PR whose Renovate-authored head commit changed since triage (Renovate pushed while the run was in progress). A PR with a floating member has that member re-read at 2-6 whether or not Renovate pushed, since a new matching release changes its age without a commit.

## Repeated lower-bound waits

A member whose age only the lower bound can establish — typically a GHCR digest on a floating tag — gets re-committed by Renovate on every scheduled run. On a weekly schedule with a same-day merge session, its bound never reaches a multi-day cooldown, and it holds back every other member of its group with it. That is the same failure Renovate's `timestamp-required` default has, so it must surface rather than repeat silently.

- On the **first** lower-bound wait for a PR, post one comment on it (English, repo convention) carrying the marker `<!-- merge-renovate-prs:cooldown-wait -->`, the member that set the age, and the earliest eligible date. This is the cross-run record; the next run has no other memory.
- When a later run finds the PR **again** waiting on the lower bound and a marker comment from the same account (the account the run is authenticated as — with the CLI, `gh api user --jq .login`) already exists, it is the second consecutive wait: do not comment again, and raise a **configuration proposal** in Phase 3-2 (workflow.md) — for example removing that member from the group, pinning a floating tag to a full version so updates carry release dates, or `minimumReleaseAge: null` for that package with the reason recorded in the config.

```bash
gh pr view {pr} --json comments \
  --jq '[.comments[] | select(.author.login == "{me}" and (.body | contains("<!-- merge-renovate-prs:cooldown-wait -->")))] | length'
```

The marker only ever leads to a proposal, which the user approves or declines, so a marker another account posted, or a run in between that waited on a registry time or release date instead, can at most cause an early proposal — never a merge.

A floating wait posts no marker: its proposal ([After the merge](#after-the-merge)) is raised in the run that observes it, without waiting for a second one.

## Known limits

- **Registry time covers two registries.** The gate reads the publish time on the public npm registry and PyPI. Every other registry falls through to the upstream release date, even one that records a publish time; adding one means a reference read in step 1, with its field confirmed from that registry's own documentation, and a row in SKILL.md's capability table. A package installed from a private registry or a mirror gets no registry time either.
- **Upstream release time is not registry push time.** Where step 2 applies, the gate measures when the upstream release was published, which usually precedes the image or chart push by the build's duration (minutes to hours). The age is overestimated by that much. Accepted: it is small against a cooldown measured in days, and it applies only where no registry time was found.
- **Container registry push time is not used.** GHCR's package-versions API would give the push time of a digest, but it requires the `read:packages` token scope (a token without it gets HTTP 403, confirmed 2026-10-19). Reading an image's own `created` field was not adopted: reproducible builds commonly set it to a fixed epoch, which would make any image look years old.
- **The sanity check needs both records.** An upstream that publishes no GitHub Releases, or names them in a way the exact-tag lookup misses, gets no release date; such members are aged by the lower bound alone.
- **The sanity check rejects parallel release lines.** A package that ships several major lines side by side can publish the from version after the target: `@types/node` 24.19.2 went to npm only two minutes before 26.6.5, so a from version published a few minutes later would have failed, and actions/node-versions released 24.22.2 a week after 26.12.1. Then a correct time is discarded and the member falls to the next source, often the lower bound. It costs a longer wait, never an early merge.
- **A floating value's resolution is read for one tool.** Only setup-node's `node-version` major or major.minor form has a read. Every other floating member — an action ref on a moving major tag, a major-only image tag, `node-version-file`, a mirror — has an unknown age and defers the PR to the human queue. Before this rule such members were aged by the version Renovate picked or by the lower bound, neither of which bounds them. Adding a tool means a read here, confirmed from that tool's own source or documentation.
- **The setup-node read bounds the builds setup-node itself fetches.** A version placed in the runner's tool cache by something other than setup-node — a runner image's preinstalled versions or a manual install — that is newer than both the manifest's and the release index's match is not seen. The read also assumes setup-node v7.1.0's order; a step pinned to another major is not checked against it.
- **The gate cannot hold a floating value's later releases.** It ages the value once, at the merge. Every later matching release reaches CI with no cooldown until the value is pinned, which is why a floating member younger than the cooldown is always proposed for pinning ([After the merge](#after-the-merge)).
