# GitHub Platform Guide — Renovate PRs

GitHub-only for v1. The commands are written for the `gh` CLI and are the reference specification of each operation (see Access Method); replace `{owner}`, `{repo}`, `{pr}` as needed.

## Table of Contents

- [Access Method](#access-method)
- [List and filter Renovate PRs](#list-and-filter-renovate-prs)
- [Read a PR: diff, files, body, branch, labels](#read-a-pr-diff-files-body-branch-labels)
- [Read an upstream file at a tag](#read-an-upstream-file-at-a-tag)
- [Compare two upstream tags](#compare-two-upstream-tags)
- [Release age (the cooldown gate)](#release-age-the-cooldown-gate)
- [CI status (the merge gate)](#ci-status-the-merge-gate)
- [Workflow files (gated-publish recognition)](#workflow-files-gated-publish-recognition)
- [CI and build configuration outside Actions (gated-publish recognition)](#ci-and-build-configuration-outside-actions-gated-publish-recognition)
- [PR changed files (gated-publish re-judgement)](#pr-changed-files-gated-publish-re-judgement)
- [Workflow runs (gated-publish V-2)](#workflow-runs-gated-publish-v-2)
- [Merge (respect the repo merge method)](#merge-respect-the-repo-merge-method)
- [Create and merge a revert PR (auto-revert)](#create-and-merge-a-revert-pr-auto-revert)
- [Resolve sibling / superseded PRs](#resolve-sibling--superseded-prs)
- [main divergence: update branch](#main-divergence-update-branch)
- [Comment on the PR](#comment-on-the-pr)
- [Read bot config](#read-bot-config)

## Access Method

Resolved once per run as SKILL.md "Platform Access" describes: a connector for GitHub only when it covers **every** operation in this file and in [release-age.md](release-age.md), otherwise the CLI.

- **CLI**: `gh` installed and authenticated (`gh auth status`); the current directory is the target repo, or pass `-R {owner}/{repo}`.
- **Connector coverage**: each command is the reference for its operation. A connector tool covers an operation only when its own description or schema shows that it returns the same fields with the same completeness the command guarantees, or performs the same write. Where that cannot be confirmed, the operation is not covered, and one uncovered operation sends the whole run to the CLI. The tests below are where a connector falls short **silently**, letting a PR through that the reference read would have held, so each is covered only on positive evidence:
  - **Complete lists.** The open-PR list and the CI entries below are covered only when the tool shows it returns every item — it reads every page itself, or exposes a signal that ends the pagination (a total, a next-page cursor or link) that the run follows to the end. A page-number parameter with no such signal is not enough: a page the tool shortened by its own filtering looks exactly like the last page.
  - **The CI gate** is covered only when the connector's tools — one or several — return every entry of the rollup the reference reads: every check run **and** every commit status on the PR's head, each with its own settled state, complete by the test above. Check runs alone, or one combined state without the individual statuses, do not cover it: a failing commit status, or a failing check hidden inside a summary, would read as green.
  - **The lower-bound read** (release-age.md) is covered only by a tool returning the PR's commits with each commit's author login and `committedDate`, newest included. A list that may stop short of the newest commits gives an older bound, which makes a release look older than it is — the unsafe direction.
  - **Upstream release lookups** are covered only by a tool that reads a release **by exact tag** from a repository other than the target, with its `published_at`. A tool confined to the target repository does not cover them.
  - **Upstream file reads** (workflow.md 2-5) are covered only by a tool that reads a file's full contents at an exact tag from a repository other than the target, including files over 1 MB. A tool that returns an empty or truncated body for a large file does not cover them.
  - **Upstream tag compares** (workflow.md 2-5) are covered only by a tool that compares two tags of a repository other than the target, in either order, and returns the changed-file list with its filenames and each renamed file's previous name, so that the 300-file cap can be checked for each direction. A commit list alone, or a summary without filenames, does not cover them.
  - **Upstream tree listings** (workflow.md 2-5, the in-repo import set) are covered only by a tool that lists every file path at an exact tag of a repository other than the target and reports whether that listing was truncated. A listing that may stop short without saying so does not cover them.
  - **The workflow-file enumeration** of gated-publish recognition (below) is covered only by tools that return every file in a directory at a given ref with a signal that the listing is complete, read each file's content at that ref, and list every workflow with its state. A listing with no completeness signal does not cover it: a publishing workflow missing from it reads as "every publishing workflow is gated". The same test applies to the whole-tree listing for CI and build configuration outside Actions: a tool must return every path in the default branch's tree, recursively, with a signal that the listing is complete.
  - **The PR changed-file read** of the gated-publish re-judgement (below) is covered only by tools that return every file a PR changes, with its status and previous name, complete by the test above, together with the PR's changed-file count and head commit, and read a file's content at that head. A list that may stop short reads as "the PR changes no workflow file".
  - **The workflow-run reads** of gated-publish V-2 (below) are covered only by tools that return, for the settle read, every run on a given commit with each run's workflow path and status, complete by the test above; and, for the publish-run read, the runs of a given workflow created at or after a given time on **every** branch and tag and for every event, with each run's creation time. A tool confined to the default branch, or to one event, does not cover the publish-run read: it would return no rows for a tag-triggered or dispatched publish on another ref, which reads as a pass.
  - **The merge** is covered only by a tool that takes the repo's merge method, and the post-approval `mergeStateStatus` read only by one that returns it — without it a `BLOCKED` PR cannot be told from a mergeable one.
  - **Writes** — approving a review, merging, updating a branch with the merge or the rebase form, creating, approving and merging the revert PR, closing with a comment, commenting — are covered by a tool that performs that write and reports whether it succeeded.
- **Outside this choice**: local git (fetch, branches, revert, push) and the deploy tooling the verification plan uses (`kubectl`, Flux/Argo CLIs, `talosctl`, …) always run as written, whatever the method. So does chart rendering (`helm show chart`, `helm template` against the chart repository; workflow.md 2-5), which is not a GitHub operation. When it is unavailable, 2-5 falls back to reading the templates, and leaves unresolved anything only a render settles.

## List and filter Renovate PRs

List open PRs with the fields needed for composite detection (author, branch, labels):

```bash
gh pr list --state open --limit 100 \
  --json number,title,author,headRefName,labels,isDraft \
  --jq '.[] | {number, title, author: .author.login, isBot: .author.is_bot, branch: .headRefName, labels: [.labels[].name]}'
```

`--limit` caps what is fetched: if the number of rows returned equals it, the list may be short — raise the limit and re-read before triaging.

Filter directly by the known bot author (fast path for the common case):

```bash
gh pr list --state open --author "app/renovate" --json number,title,headRefName
```

Filter by branch prefix or label when the author is a self-hosted/custom account
(combine with the OR-detection in detection.md):

```bash
gh pr list --state open --json number,title,headRefName,labels \
  --jq '.[] | select(.headRefName | startswith("renovate/"))'

gh pr list --state open --label dependencies --json number,title
```

Read the PR body to check for Renovate signatures (Mend footer, `<!--renovate-debug-->`):

```bash
gh pr view {pr} --json body --jq '.body'
```

## Read a PR: diff, files, body, branch, labels

```bash
# Metadata in one call
gh pr view {pr} --json number,title,author,headRefName,baseRefName,labels,body,mergeable,mergeStateStatus

# The actual diff (read this, not just the changelog)
gh pr diff {pr}

# Just the changed file list
gh pr view {pr} --json files --jq '.files[].path'
```

For release notes, the bot body often links upstream; otherwise fetch the upstream
release directly (primary source):

```bash
# Releases for an upstream repo, to read notes for the target version
gh release view vX.Y.Z -R {upstream_owner}/{upstream_repo}
gh api repos/{upstream_owner}/{upstream_repo}/releases/tags/vX.Y.Z --jq '.body'
```

## Read an upstream file at a tag

For the disruption resolution (workflow.md 2-5): a chart's `values.yaml` and templates, or an operator's source, at an exact release tag of the upstream repository.

```bash
gh api -H 'Accept: application/vnd.github.raw+json' 'repos/{upstream_owner}/{upstream_repo}/contents/{path}?ref={tag}'
```

The raw media type returns the file body itself. The default JSON form leaves `content` empty for files between 1 and 100 MB, and the endpoint does not serve files over 100 MB. A read that does not return the file — one over 100 MB, or a 404, which this command cannot tell apart from a missing repository or a denied read — is the access method failing or proving unable, so its result is an unknown under SKILL.md "Platform Access" (workflow.md 2-5 step 4), not an unresolved default. A chart's source tree can differ from the published chart: the tailscale-operator chart's source `Chart.yaml` has `appVersion: "stable"`, a placeholder set at release time. Read such values from the published chart (workflow.md 2-5).

## Compare two upstream tags

For the replaced-controller check (workflow.md 2-5): whether the code that generates a controller's workloads changed between the controller's two source tags. That code is the generating package **and every in-repo package it imports, transitively**. The tailscale operator's `cmd/k8s-operator` imports `k8s-operator/apis/v1alpha1`, `kube/kubetypes`, `kube/egressservices` and `kube/ingressservices`, among others, and a change there changes the generated spec as surely as one in the operator's own directory. So the check has two parts: list that package set at the old tag, then filter the compare to it. Run both blocks in one shell; the second uses the first's variables.

**1. The in-repo import set — Go modules only.** Start from the generating package's directory, read the import blocks of its non-test `.go` files at the old tag, keep the imports under the module path that the root `go.mod` declares, and repeat for each package found:

```bash
repo={upstream_owner}/{upstream_repo} tag={old_tag} start={path} work=$(mktemp -d)
raw() { for try in 1 2 3; do  # retry transient network errors; output only from a successful try
  out=$(gh api -H 'Accept: application/vnd.github.raw+json' "repos/$repo/contents/$1?ref=$tag" < /dev/null) \
    && { printf '%s\n' "$out"; return 0; }; done; return 1; }
gh api "repos/$repo/git/trees/$tag?recursive=1" \
  --jq '.truncated, (.tree[] | select(.type == "blob") | .path)' > "$work/tree" || touch "$work/failed"
: > "$work/go.mod"  # read only when the tree has a root go.mod; with none, $mod stays empty
grep -qx go.mod "$work/tree" && { raw go.mod > "$work/go.mod" || touch "$work/failed"; }
mod=$(awk '$1 == "module" {gsub(/["`]/, "", $2); print $2; exit}' "$work/go.mod")
{ [ -n "$mod" ] && [ "$(head -n 1 "$work/tree")" = false ] \
  && grep -qE "^$start/[^/]+\.go\$" "$work/tree"; } || touch "$work/unestablished"
echo "$start" > "$work/closure"; i=1
while d=$(sed -n "${i}p" "$work/closure"); [ -n "$d" ]; do
  if [ "$d" = . ]; then pat='^[^/]+\.go$'; else pat="^$d/[^/]+\\.go\$"; fi
  grep -E "$pat" "$work/tree" | grep -v '_test\.go$' | while read -r f; do
    raw "$f" || touch "$work/failed"
  done | awk '/^import \(/ {b = 1; next} b && /^\)/ {b = 0} b || /^import [^(]/' \
    | grep -oE "\"$mod(/[^\"]*)?\"" | tr -d '"' | sed -e "s|^$mod/||" -e "s|^$mod\$|.|" \
    | while read -r p; do grep -qxF "$p" "$work/closure" || echo "$p" >> "$work/closure"; done
  i=$((i + 1))
done
echo "work=$work packages=$(wc -l < "$work/closure") $(ls "$work" | grep -E '^(failed|unestablished)$')"
```

**2. The compare, filtered to that set — in both directions.** `compare/{a}...{b}` is a three-dot compare: it lists the changes from the merge base of `a` and `b` to `b`, not the difference between the two tags. When the old tag sits on a release branch the new one does not contain — a patch release whose fixes were backported — the commits only on that branch are missing from `{old_tag}...{new_tag}`. tailscale/tailscale `compare/v1.102.4...v1.104.1` reports `status: diverged`, `behind_by: 33`, and the reverse `v1.104.1...v1.102.4` lists 85 files changed on v1.102.4's side of the merge base, among them `cmd/k8s-operator/operator.go` and `k8s-operator/reconciler/tailscaled/statefulset.go`; a two-dot compare of the pair returns 404. So the block reads both directions and unions them: any file that differs between the tags changed on at least one side of the merge base. On a linear pair the reverse lists nothing. A renamed file counts under its old name as well as its new one, so a file moved out of the set is a hit. A changed file is a hit when it sits in a package directory of the set or below one (embedded files, cgo sources), or when it is a `go.mod` or `go.sum` anywhere, because this method does not follow modules outside the repository:

```bash
gh api "repos/$repo/compare/{old_tag}...{new_tag}" \
  --jq '(.files | length), (.files[] | .filename, (.previous_filename // empty))' > "$work/fwd" || touch "$work/failed"
gh api "repos/$repo/compare/{new_tag}...{old_tag}" \
  --jq '(.files | length), (.files[] | .filename, (.previous_filename // empty))' > "$work/rev" || touch "$work/failed"
awk -v failed="$([ -e "$work/failed" ] && echo 1)" -v unest="$([ -e "$work/unestablished" ] && echo 1)" '
  FILENAME == ARGV[1] {c[$0]; next}
  FNR == 1 {n[FILENAME] = $0; next}
  seen[$0]++ {next}
  $0 ~ /(^|\/)go\.(mod|sum)$/ {print "hit: " $0; hits++; next}
  {d = $0; if (d !~ /\//) d = "."; else sub(/\/[^\/]*$/, "", d)
   while (1) {if (d in c) {print "hit: " $0; hits++; break}; if (d !~ /\//) break; sub(/\/[^\/]*$/, "", d)}}
  END {for (i = 2; i < ARGC; i++) {print "files " (i == 2 ? "old...new" : "new...old") ": " n[ARGV[i]]
                                   if (n[ARGV[i]] == "" || n[ARGV[i]] >= 300) big = 1}
       print (failed ? "method failure" : (unest || big || hits ? "not established" : "unchanged"))}' \
  "$work/closure" "$work/fwd" "$work/rev"
```

Read the last line:

- `unchanged` — both compares are complete (fewer than 300 files each), the import set was listed completely, and no hit in either. Only this establishes the generating code unchanged.
- `not established` — a read completed but cannot show the code unchanged: either changed-file list has 300 files and may be truncated (the endpoint's documentation, "Compare two commits", *Working with large comparisons*, caps it at 300 for the whole comparison, so each direction has its own cap), the tree listing reported itself truncated, the tree has no root `go.mod` (a module in a subdirectory, or no Go module at all) or the root `go.mod` declares no module, the start path holds no `.go` file, or a hit. 2-5 counts the workloads as changing.
- `method failure` — a `gh api` call errored (an error response of any kind, a 404 included, or a network failure; a file read counts only after three tries). That is the access method failing, an **unknown** under SKILL.md "Platform Access", not a result about the code.

The set is listed at the old tag only, which is enough: an import added or removed at the new tag edits a file already in the set, or adds one to a directory in it, and the compare shows that edit as a hit. It over-approximates: every non-test `.go` file counts, whatever its build constraints, and every changed file in a package directory is a hit, not only `.go` files — so when the set includes the repository's root package, as the tailscale operator's does, any changed root-level file (`VERSION.txt`, `flake.nix`) is a hit. What it does not cover: generating code in any language other than Go has no listing method here, so its in-repo imports cannot be listed and the check is **not established** — running the blocks on a repository with no root `go.mod` prints `not established` too, since block 1 reads `go.mod` only when the tree lists one; a Go module rooted in a subdirectory is not followed either, and lands in the same place; and dependencies outside the repository are not followed, which is why any `go.mod` or `go.sum` change is a hit. It is also costly: one API call per `.go` file in the set. For the tailscale operator at `v1.104.1` that was 239 packages and about 1,000 calls, roughly 7 minutes, against the authenticated rate limit of 5,000 calls an hour.

## Release age (the cooldown gate)

The commands for the release-age gate (workflow.md 1-3) — upstream release dates with their sanity check, the lower bound from Renovate's newest authored commit, and the cooldown-wait marker lookup — live with the procedure in [release-age.md](release-age.md), because each one is only correct together with the rule around it.

## CI status (the merge gate)

CI green is a precondition for merge (workflow.md 2-3). Read the rolled-up status:

```bash
# Human-readable checks summary
gh pr checks {pr}

# Programmatic rollup — every check must be SUCCESS (or neutral/skipped) to merge.
# The rollup is a union: a CheckRun carries status/conclusion, a StatusContext only state,
# so select __typename and both shapes or a commit status reads as nulls.
gh pr view {pr} --json statusCheckRollup \
  --jq '.statusCheckRollup[] | {type: .__typename, name: (.name // .context), status, conclusion, state}'
```

Decision:

- Every `CheckRun` `COMPLETED` with conclusion `SUCCESS`/`NEUTRAL`/`SKIPPED`, and every `StatusContext` with state `SUCCESS` → CI gate passes.
- Any `FAILURE`/`TIMED_OUT`/`CANCELLED` → **do not merge**; investigate and present as a finding.
- `PENDING`/`IN_PROGRESS` → wait, then re-check.
- An **empty** rollup, or any other value (`ERROR`, `ACTION_REQUIRED`, `STARTUP_FAILURE`, `STALE`, …) → not green: **do not merge**.

## Workflow files (gated-publish recognition)

Recognition of an artifact whose publish is gated behind a separate trigger ([verification.md](verification.md) "Gated publish", condition (1)) reads **every** workflow file on the default branch, not just the release workflow. List them:

```bash
gh api "repos/{owner}/{repo}/git/trees/{default_branch}:.github/workflows" \
  --jq '{truncated, files: [.tree[] | select(.type == "blob") | .path]}'
```

`truncated: false` on a read that succeeded → the listing is complete. `truncated: true`, or a read that fails (a 404 included) → the listing may be incomplete, and the row does not apply. The listing returns names relative to the directory (`container-push.yml`), while the workflows list and the settle read below return each workflow's `path` from the repository root (`.github/workflows/container-push.yml`): prefix each listed name with `.github/workflows/` when building the expected set and matching it against those reads. Then read each listed file at the same ref:

```bash
gh api "repos/{owner}/{repo}/contents/.github/workflows/{file}?ref={default_branch}" --jq .content | base64 -d
```

A file that cannot be read is a workflow whose publishing cannot be determined: the row does not apply. Record from each file its triggers — for a `push` trigger, its branch and `paths` / `paths-ignore` filters — since the settle read below derives its expected runs from them, and each reusable workflow its jobs call (`uses:`), since recognition judges a `workflow_call` workflow by its callers. Which workflows can start runs at all — the settle read below derives its expected set from it, so take it after the merge, with the settle read:

```bash
gh api --paginate "repos/{owner}/{repo}/actions/workflows?per_page=100" \
  --jq '.workflows[] | {path, state}'
```

A read that fails is verification that cannot be completed (SKILL.md "Platform Access"), as for the settle read: without each workflow's state the expected set cannot be derived, and the publish-run reads are not taken.

## CI and build configuration outside Actions (gated-publish recognition)

Recognition's condition (3) ([verification.md](verification.md) "Gated publish") looks for CI or build configuration other than GitHub Actions in the default branch's whole tree. One recursive listing returns the root entries and every path matching a common CI or build file anywhere in the tree:

```bash
gh api "repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1" \
  --jq '{truncated, root: [.tree[] | select(.path | contains("/") | not) | .path],
         ci: [.tree[].path | select(test("(^|/)(\\.gitlab-ci\\.ya?ml|Jenkinsfile[^/]*|cloudbuild[^/]*\\.(ya?ml|json)|\\.travis\\.ya?ml|\\.drone\\.ya?ml|azure-pipelines[^/]*\\.ya?ml|bitbucket-pipelines\\.ya?ml|buildspec[^/]*\\.ya?ml|\\.?appveyor\\.ya?ml)$|(^|/)\\.(circleci|buildkite|tekton|woodpecker)(/|$)"))]}'
```

`truncated: false` on a read that succeeded → the listing is complete. `truncated: true` (GitHub caps a recursive tree read, so a very large repository returns it) or a read that fails → the listing may be incomplete, and the row does not apply. Read every path in `ci` at the same ref with the contents read above (`repos/{owner}/{repo}/contents/{path}?ref={default_branch}`); a directory entry such as `.circleci` stands for the files listed under it. Then scan `root` for configuration of any CI or build system the filter does not name — most read their configuration from the root. The filter matches common file names, not every one: below the root, a system it does not name, or a named one kept under another name or path (`build/azure-pipelines/*.yml`), is not caught (verification.md, known limit).

## PR changed files (gated-publish re-judgement)

Recognition is re-judged for a PR whose changed files include anything it read or depends on ([verification.md](verification.md) "Gated publish", "Re-judge it for a PR that changes what recognition read"). Read the PR's head commit and changed-file count, then every changed file:

```bash
gh api "repos/{owner}/{repo}/pulls/{pr}" --jq '{head: .head.sha, changed_files}'
gh api --paginate "repos/{owner}/{repo}/pulls/{pr}/files?per_page=100" \
  --jq '.[] | {filename, status, previous_filename}'
```

The list is complete only when the number of rows returned equals `changed_files` and is below 3000: GitHub's API description for this endpoint says responses include at most 3000 files, so a PR at or past that count, a row count that differs, or a read that fails is a list that may be incomplete, and the row does not apply to the PR. Match `filename` — and `previous_filename` for a rename, since a file moved out of `.github/workflows/` changes the tree too — against the paths recognition read. Read the head's version of each matching file with the contents read above at `ref={head}`; a `removed` file has no head version and leaves the tree. For the external-ref rule, also match every `filename` ending in `/action.yml` or `/action.yaml` (or equal to `action.yml` / `action.yaml`) — any local composite action, wherever it sits, whether or not recognition read it — and read its head version and its default-branch version with the contents read above (`ref={head}`, `ref={default_branch}`; an `added` file has no default-branch version, so every external ref in it is changed). Compare the `uses:` lines of each changed workflow file and each changed `action.yml` / `action.yaml` between the two versions to find a changed external ref, then find the workflows that reach that file from the workflow files already read. Take the read again if the head moves before the merge.

## Workflow runs (gated-publish V-2)

Two reads for an artifact whose publish is gated behind a separate trigger ([verification.md](verification.md) "Gated publish"), taken after the merge, in this order.

**Settle read** — every run the merge is expected to start exists on the merge commit and has completed:

```bash
gh api --paginate "repos/{owner}/{repo}/actions/runs?head_sha={merge_commit_sha}&per_page=100" \
  --jq '.workflow_runs[] | {id, path, event, status, conclusion}'
```

Settled is positive evidence, never an empty list. The **expected set** is every workflow from the enumeration above whose `push` trigger admits the default branch and whose `paths` / `paths-ignore` filters, if any, admit a file the merge changed — a filter you cannot evaluate counts as admitting — less any the workflows list shows in a state other than `active`, since those start no run. A `push` trigger with only `tags` / `tags-ignore` and no `branches` / `branches-ignore` admits no branch push, so such a workflow is never in the expected set; one with neither admits every branch. Settled means both: every workflow in the expected set has a row (matched on `path`), and every row's `status` is `completed`. An empty result is settled only when the expected set is empty. GitHub creates runs asynchronously after the merge, so before then an empty or partial result means "not yet": re-read, within the wait V-2 allows. `--paginate` with `per_page=100` returns every page, so no limit comparison applies. An expected run that has not appeared, or a run that has not completed, when that wait runs out, or a read that fails, is verification that cannot be completed (SKILL.md "Platform Access"), and the publish-run reads are not taken.

**Publish-run read** — no run of a publishing workflow started at or after the merge, on any branch or tag, from any event. Take it **once for each** workflow recognition found publishing the artifact:

```bash
gh run list --all --workflow {publishing_workflow_file} --created ">={merge_time}" \
  --json databaseId,event,status,createdAt,headBranch,url
```

`--all` keeps a disabled workflow from erroring the read. No rows from every one of them → the check passes. Any row from any of them fails it, so a short list cannot hide a failure and no limit comparison applies. A read that fails is not a pass: it is verification that cannot be completed, and the report says whether a publish ran is unknown.

## Approve before merge

Submit a GitHub review approval after the go decision (autonomous) or user approval (interactive) at step 2-5, and before calling `gh pr merge`. This satisfies branch-protection rules requiring at least one approved review:

```bash
gh pr review {pr} --approve --body "Dependency update reviewed: release notes read, CI green, risk assessed."
```

Notes:
- The `--body` is optional but leaves a human-readable audit trail on the PR.
- GitHub prevents approving your own PRs — for Renovate-authored PRs this is never an issue.
- If the repo requires CODEOWNERS or team-based required reviewers, an agent approval may not satisfy the requirement. Check `mergeStateStatus` after approving; if it still shows `BLOCKED`, never bypass it — autonomous: defer the PR; interactive: surface the gap and ask the user to approve manually.

## Merge (respect the repo merge method)

Phase 0 determined the merge method. Use the matching flag — do not assume squash:

```bash
gh pr merge {pr} --merge     # merge commit
gh pr merge {pr} --squash    # squash
gh pr merge {pr} --rebase    # rebase
```

If the repo enforces a method, the others will be rejected — that itself confirms
the method. Add `--delete-branch` only if the repo convention deletes merged branches.

Never use `--admin` to bypass a failing required check; a red check is a signal,
not an obstacle.

**Classify the call's result, then confirm from platform state** (workflow.md 2-6).
`gh pr merge` submits the GraphQL `mergePullRequest` mutation; with `gh` (behaviour
read from source: gh v2.103.2 `pkg/cmd/pr/merge/merge.go` and `http.go`, whose errors
`internal/ghcmd/cmd.go` prints as `err.Error()`, and which submit
the mutation through go-gh v2.17.0's `Mutate` — `pkg/api/graphql_client.go`,
`pkg/api/errors.go` — and cli/shurcooL-graphql v0.0.4 `graphql.go`, which turn the
response into the error string) an **explicit refusal** is a non-zero exit whose stderr
carries one of:

- a line beginning `GraphQL: ` — go-gh's rendering of an `errors[]` payload in a `200`
  response to the mutation — whose message gives a reason the merge is not allowed.
  `gh`'s own reads before the mutation render their errors payloads the same way;
  either reading of such a line is safe, since a read failing that way means nothing
  was submitted and an uncertain line is not a refusal. An errors payload
  is not automatically a refusal: GitHub can also return one alongside partial results
  when a request exceeds resource limits, and one reporting a timeout, a resource limit,
  or an internal failure is **not a refusal**;
- `is not mergeable:` — printed by `gh` itself from the `mergeStateStatus` it read,
  before it submits the mutation; nothing was sent.

Everything else is **not a refusal**: a line beginning `non-200 OK status code:`
(shurcooL's rendering of any non-`200` response to the mutation, with the status and
body — GitHub may answer a GraphQL request it terminated after 10 seconds with a `502`
or `504`, per
[GitHub Docs, "Rate limits and query limits for the GraphQL API"](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api#timeouts)),
a line beginning `HTTP ` (go-gh's rendering of a non-2xx response to one of `gh`'s own
reads; the output does not say which call failed), a network or TLS error, a killed or
hung command, and **exit 0**. `gh` exits 0 without merging when the base branch requires
a merge queue — it submits the auto-merge mutation instead (`http.go`), so the PR joins
the queue and merges later, outside the one-in-flight loop.
Through a **connector**, the same rule: only a tool result that carries the platform's
refusal reason counts as a refusal, whatever status it came with; a tool error that does not show one is not.

After **every** merge call, refusal or not, read the PR (a read that fails is a
*merge outcome unconfirmed*):

```bash
gh pr view {pr} --json state,mergeCommit --jq '{state, merge_commit: .mergeCommit.oid}'
```

`MERGED` confirms the merge. Anything else confirms nothing unless the call was an
explicit refusal; after a call that was not, it is a *merge outcome unconfirmed*.

## Create and merge a revert PR (auto-revert)

Used by the autonomous auto-revert procedure (verification.md). Identify the
commit the merge produced on the default branch, revert it on a branch, then
open, approve, and merge the revert PR:

```bash
# The commit the merge created on the default branch (merge/squash methods)
gh pr view {pr} --json mergeCommit --jq '.mergeCommit.oid'

git fetch origin
git checkout -b revert-pr-{pr} origin/{default_branch}

# Merge-commit method — revert the merge commit against its first parent:
git revert -m 1 {merge_commit_sha} --no-edit
# Squash method — the squash produced an ordinary commit; no -m:
git revert {merge_commit_sha} --no-edit
# Rebase method — the PR's commits landed individually; identify them on the
# default branch (git log) and revert each, newest first.

git push -u origin revert-pr-{pr}
gh pr create --title "Revert: {original PR title}" \
  --body "Auto-revert of #{pr}: post-merge verification failed — {one-line cause}. Details on #{pr}."
gh pr review {revert_pr} --approve --body "Auto-revert of a failed dependency update."
gh pr merge {revert_pr} --<method>
```

Notes:

- The revert PR goes through the normal merge path (approval + required checks) —
  never `--admin`. If the revert itself is blocked (CI red on the revert, required
  reviewers), **escalate to the human** (verification.md); do not force it.
- Revert Git **before** undoing any B-class apply, so a GitOps controller does not
  re-apply the bad version over the rollback.

## Resolve sibling / superseded PRs

When a major-bump PR supersedes a digest-bump PR (workflow.md 1-2 / 2-6):

```bash
# Close the superseded PR with an explanatory comment
gh pr close {superseded_pr} --comment "Superseded by #{survivor_pr} (major bump includes this digest)."
```

Renovate rebases or recreates its own PRs on its **own schedule**, so closing the
redundant one is usually enough. If the survivor must be brought up to date with
`main` immediately, use `gh pr update-branch` (below) rather than waiting on the bot.

## main divergence: update branch

If the PR is behind `main` and a clean update is possible (workflow.md 2-6):

```bash
gh pr update-branch {pr}            # default: merge `main` into the PR branch (creates a merge commit)
gh pr update-branch {pr} --rebase   # alternative: rebase the PR branch onto `main`
```

`gh pr update-branch` has no fast-forward mode — the default creates a merge commit,
`--rebase` rebases. If either reports a conflict that needs manual resolution,
**stop and ask the user** (per the main-divergence rule) rather than resolving
conflicts unprompted.

## Comment on the PR

Documentation comments (workflow.md 2-8). Comment only when real steps or risk
exist, in English.

```bash
# Pre-comment: manual steps (B/C work) for humans and future agents
gh pr comment {pr} --body "Manual apply required after merge:
1. \`talosctl upgrade-k8s --to X.Y.Z\`
2. Verify nodes report the new version.
(Class B — agent-executable; awaiting approval.)"

# Post-comment: closing applied & verified result
gh pr comment {pr} --body "Applied & verified.
- Merged and reconciled by Flux.
- talosctl upgrade-k8s completed; all nodes on X.Y.Z.
- All workloads Ready at expected replica counts; no regression."
```

## Read bot config

For Phase 0 / detection refinement:

```bash
# Show whichever config file exists
gh api repos/{owner}/{repo}/contents/renovate.json5 -H "Accept: application/vnd.github.raw" 2>/dev/null
gh api repos/{owner}/{repo}/contents/.github/renovate.json -H "Accept: application/vnd.github.raw" 2>/dev/null
```

(Reading the files locally from the checked-out repo is equally fine and usually
simpler.)

## CLAUDE.md Config Example

```markdown
## Code Hosting
- platform: github
- merge_method: rebase
- deploy: flux   # gitops | ci | manual
```
