---
name: go
description: >
  Finish a change at a consistent verification bar — derive what the change
  claims to make true, exercise those claims end to end in the project's own
  environment, run only the checks that no project automation already covers,
  remove the scaffolding verification left behind, and end with an explicit
  per-claim verification verdict. Never reports success without observed
  evidence: a change that cannot be verified ends NOT VERIFIED with the
  reason, never with silence. Use after making a change and before reporting
  it done or handing it to commit/PR — when the user says "go", "verify this
  change", "make sure it actually works", "test it end to end",
  "動作確認して", "変更を検証して", "ちゃんと動くか確かめて",
  "最後まで検証して", or asks whether a change really works. A bare "go"
  said to approve a proposed plan before any change exists means "proceed",
  not this skill.
---

# Go

Every change ends at the same verification bar: the change's intended behavior
has been **observed**, or the final report says — explicitly — that it has
not. Which commands that takes differs per project; the bar does not.

This skill exists because verification quality otherwise varies by session:
sometimes a change is exercised end to end, sometimes the session stops at
"the code looks right" and reports done. `go` replaces that variance with one
fixed contract: claims, evidence, verdict.

## Core Principles

1. **Verification is observation, not inference.** A claim is verified only
   when the changed behavior has been observed from the outside: the command
   run, the endpoint called, the flow driven, the documented steps followed.
   Reading the diff and concluding "this should work" is never evidence. A
   green check suite is supporting evidence, not verification — unless a
   specific test demonstrably exercises the changed behavior.
2. **Claims drive the plan.** Verification starts from what the change claims
   to make true — bug X no longer reproduces, command Y accepts flag Z, the
   doc's steps work as written — never from a fixed checklist. Every claim
   gets a method, and every method produces evidence tied back to its claim.
3. **Adapt to the project; assume no toolchain.** Discover what this project
   is and how it is exercised — its instructions, its manifests, its runnable
   surface — before choosing any verification method. A method that fits a
   web app is meaningless in a docs-only repository.
4. **Rely on the project's automation; never duplicate it.** Where a check is
   already wired to run on the change's delivery path (commit hooks, CI),
   trust it and do not re-run it. Where the project defines a check that
   nothing runs automatically, running it is this skill's job. The decision
   procedure is "Check Coverage" in Phase 2.
5. **The verdict is the deliverable, and it is honest.** Every run ends with
   a visible Verification Report whose overall verdict is `VERIFIED`,
   `PARTIALLY VERIFIED`, or `NOT VERIFIED`. When verification is impossible
   or inconclusive, the report says so and says why — proceeding as if it had
   succeeded is the one prohibited outcome.
6. **Leave no residue.** Scratch scripts, temporary instrumentation, and
   ad-hoc fixtures created while verifying are removed before the verdict;
   when their removal touches the change itself, re-verify what it touched.
7. **Verification only.** No commit, push, PR, or general code cleanup — the
   boundary is written down in "What This Skill Does Not Do".

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |
| **Background execution** — keep a long-lived process (dev server, watcher) running while exercising it | Background shell (e.g. Claude Code's background Bash) | Shell job control (`command &` with output redirected to a file), stopped when verification ends; run long non-interactive commands sequentially |
| **Interactive app driving** — drive a running app's UI to observe behavior | Browser/computer-use tooling (e.g. Claude Code's browser tools) | Exercise the same behavior through non-interactive surfaces (HTTP requests, CLI); behavior observable only through an interactive UI is recorded as unverifiable in this environment (Phase 6), never claimed as verified |

## Workflow

### Phase 1: Establish the Change and Its Claims

Identify the change under verification: in a git repository, the working
tree's pending diff (plus any commits this session made that are not yet
delivered); otherwise, the files edited in this session. The conversation
provides the intent behind it.

**Nothing to verify.** When no change exists — the working tree is clean and
the session has edited nothing undelivered — do not invent one and do not
report success: state that there is nothing to verify, and ask what change
was meant (a specific commit, a deployed artifact) via a user choice when
candidates exist, or end there.

Derive the change's **claims** — the statements that should now be observably
true. Phrase each one so that a single observation can confirm or refute it
("`--dry-run` prints the plan and writes nothing", not "dry-run works").
A typical change yields one to four claims; a long list usually means the
claims are restating the diff instead of its intent.

**Ambiguity rule.** When the intent is too ambiguous to derive claims from —
the conversation does not say what the change was supposed to accomplish, and
the diff alone is compatible with several readings — ask the user to choose
between the candidate readings in **one** batched round (see Environment
Adaptation), then proceed. Never guess, and never verify only the
unambiguous part while silently dropping the rest.

### Phase 2: Discover the Project's Verification Surface

Learn how this project is checked and how it is exercised, in that order:

1. **Project instructions** — the repository's agent instructions (e.g.
   `AGENTS.md`, `CLAUDE.md`), `CONTRIBUTING`, `README`. These may state
   outright how checks run and how the project is exercised.
2. **Defined checks** — what the project itself defines as its checks:
   formatter, linter, type check, test suite, build. Found in manifests, task
   runners, and tool configs.
3. **Runnable surface** — how the change can be exercised: a CLI entry
   point, a dev server, an installable package, a doc with instructions, an
   eval procedure.

**Check Coverage.** For each defined check, decide who runs it:

1. The project's instructions are authoritative. An instruction like "checks
   run from pre-commit hooks; do not run them separately" settles the
   question — rely on the hooks and do not re-run.
2. Otherwise, a check is **covered** when automation on the change's delivery
   path is wired to run it: commit hooks (a hook-framework config, hook
   wiring in the package manifest) or CI definitions triggered on push/PR.
   Covered checks are trusted, not re-run — the automation is the project's
   own bar, and duplicating it burns time to add nothing.
3. A check nothing covers is **this skill's responsibility**: run it in
   Phase 4, auto-fix variants first where the project defines them.

Coverage applies to **whole-suite checks**, not to evidence: running the one
focused test that demonstrates a claim is evidence-gathering (Phase 4), and
is never "duplication" — even when CI also runs the full suite later.

### Phase 3: Plan Verification per Claim

For each claim, choose the method that observes it most directly, using the
surfaces found in Phase 2:

| Change surface | How to exercise it |
|---|---|
| CLI | Run the affected commands with real arguments; check output and exit code |
| Service / API | Start it (background execution), issue real requests against the changed behavior |
| Web UI | Drive the changed flow (interactive app driving); HTTP-level exercise as the fallback |
| Library code | Run the narrowest test that exercises the changed behavior; absent one, a scratch script that calls it (removed in Phase 5) |
| Bug fix | Reproduce the bug's original conditions and observe it not recurring |
| Docs | Follow the doc's own instructions as written, as its reader would — within Phase 4's safety bound |
| Config / schema / IaC | Feed it to the tool that consumes it: validate, dry-run, plan |
| Skill / prompt text | Desk-run its eval cases against the changed text — this observes what the text mandates, not live agent behavior; the evidence says which |

A claim no method can reach in this environment — missing tooling, no
runnable surface, interactive-only behavior with no fallback — is marked
**unverifiable** now, carried to Phase 6, and never quietly dropped.

### Phase 4: Execute and Capture Evidence

Run the uncovered checks from Phase 2 first — they are cheap and catch what
would waste the behavioral runs. A failing check is handled like
contradicting evidence: fix and re-run it. A check that cannot be brought to
pass stays in the report as failed and caps the overall verdict (Phase 6).
Then exercise each claim per the plan, capturing concrete evidence: the
command and its output, the request and its response, the observed behavior.

**Safety bound.** Never execute privileged, system-mutating, or
fetch-and-execute steps just to verify — `sudo` installs, `curl | sh`,
global package installs, destructive migrations. Verify such steps by
inspection instead (the URL resolves, the package and version exist) or
record the claim unverifiable. This bounds every surface, docs most of all.

**When evidence contradicts a claim**, the change is not done — verification
found what it exists to find. Fix the change, re-run that claim's
verification, and re-run any check the fix affects. If the claim cannot be
made to pass, record it as failed with the findings; weakening the claim to
match the observed behavior is the same silent failure Principle 5 prohibits.

**When a method fails for environmental reasons** (tool missing, server will
not start here, credentials absent), do not improvise a weaker method and
call it equivalent — record the claim unverifiable with what would be needed,
and continue with the remaining claims.

### Phase 5: Remove Verification Residue

Delete what verification created and the change does not need: scratch
scripts, temporary logging or instrumentation, ad-hoc fixtures, generated
output. Compare the final diff against the intended change — anything present
only because of Phases 3–4 goes. When removal touches files the change
itself modified, re-run the affected claim's verification once more.

### Phase 6: Report the Verdict

End with a visible report:

```
Verification Report: <VERIFIED | PARTIALLY VERIFIED | NOT VERIFIED>

Claims:
1. <claim> — VERIFIED: <method> — <evidence>
2. <claim> — FAILED: <what was observed instead>
3. <claim> — UNVERIFIABLE: <why; what would be needed>

Checks:
- <check>: covered by <automation>, not re-run
- <check>: run here — <result>

Residue: <removed items | none>
Gaps: <coverage gaps worth the author's attention | none>
```

Overall verdict: `VERIFIED` only when every claim is verified **and** no
check run here remains failing; `PARTIALLY VERIFIED` when at least one claim
is verified and at least one is not, or when a check run here remains
failing; `NOT VERIFIED` when no claim is verified. Overriding all of the
above: a failed claim that defeats the change's central purpose makes the
verdict `NOT VERIFIED`.

**Impossible or inconclusive verification.** When claims are unverifiable or
evidence is inconclusive, the verdict is `PARTIALLY VERIFIED` or
`NOT VERIFIED`, and the report states per claim why, and what would make it
verifiable (a missing tool, a runnable environment, a decision from the
user). Never present an unverified change as done, never let an unverifiable
claim disappear from the report, and never substitute "the checks passed" for
the verdict — checks are one line of the report, not its conclusion.

## What This Skill Does Not Do

- **Delivery.** No commit, no push, no PR — verification is the invariant
  every change needs; what happens after it varies by context. The report
  hands the author (or the delivering skill, e.g. this plugin's
  `implement-issue`) an evidence-backed verdict to act on.
- **General code cleanup.** It removes only its own verification residue.
  Refactoring, simplification, and style belong to review tooling — on
  Claude Code, run `/simplify` separately if that pass is wanted.
- **Building check infrastructure.** A project with no linter or no tests
  gets its gap reported under `Gaps`, not a bootstrapped toolchain.
- **Writing durable tests.** A missing regression test for the verified
  change is reported under `Gaps`; adding it is the author's decision.
- **Judging beyond the evidence.** The verdict states what was observed,
  not whether the change should merge.

## References

- [references/eval-cases.md](references/eval-cases.md) — evaluation test
  cases and the evaluation log
