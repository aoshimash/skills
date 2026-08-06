# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation in a project matching the Setup
2. Make (or simulate) the described change, then trigger the go skill
3. Follow the described scenario
4. Evaluate against the acceptance criteria listed per case
5. Record results in the Evaluation Log section at the bottom

A **desk-run** — reasoning a case through against the SKILL.md text and
checking the text mandates the expected behavior — is recorded as
`Pass (desk)` / `Fail (desk)`. It verifies what the text prescribes, not
live agent behavior; an interactive run in a matching environment supersedes
it and is recorded as plain `Pass` / `Fail`.

## Test Cases

### Case 1: CLI change verified end to end

- **Persona**: Developer who just added a `--dry-run` flag to a project CLI
- **Setup**: A repository with a runnable CLI; the working tree holds the
  uncommitted flag implementation
- **Initial input**: "go"
- **Expected behavior**:
  - Derives claims from the change (e.g. "`--dry-run` prints the plan and
    writes nothing")
  - Actually runs the CLI with `--dry-run` and observes output and side
    effects — does not conclude from reading the diff
  - Ends with a Verification Report; overall verdict `VERIFIED` with
    per-claim evidence
- **Key criteria**: Behavioral exercise happens; evidence is observed, not
  inferred; report format matches SKILL.md Phase 6

### Case 2: Checks covered by commit hooks are not re-run

- **Persona**: Developer in a repository whose agent instructions state that
  test/lint/format run from pre-commit hooks and must not be run separately
- **Setup**: Hook-framework config present; instructions carry the statement
- **Initial input**: "変更を検証して"
- **Expected behavior**:
  - Check Coverage resolves the checks as covered via the instructions
    (authoritative)
  - No lint/test/format commands are run by the skill
  - The report's `Checks` section lists them as covered, not re-run
  - Behavioral verification of the change still happens
- **Key criteria**: Coverage rule step 1 honored; no duplicated checks;
  behavioral verification is not skipped just because checks are covered

### Case 3: Uncovered checks are the skill's responsibility

- **Persona**: Developer in a repository that defines a test suite and linter
  but has no hooks and no CI
- **Setup**: Manifest defines `test` and `lint` scripts; no hook config, no
  CI definitions
- **Initial input**: "verify this change"
- **Expected behavior**:
  - Check Coverage finds nothing on the delivery path → the skill runs the
    checks itself, auto-fix variants first where defined
  - Check results appear in the report's `Checks` section as run here
- **Key criteria**: Coverage rule step 3; checks actually executed and
  reported

### Case 4: UI-only behavior without browser tooling

- **Persona**: Developer who changed a web app's form validation, in an
  environment with no interactive app driving support
- **Setup**: Dev server startable; no browser/computer-use tooling available
- **Initial input**: "make sure it actually works"
- **Expected behavior**:
  - Server-side behavior is exercised through the fallback (HTTP requests)
  - Behavior observable only in the browser (e.g. inline error rendering) is
    recorded as UNVERIFIABLE with what would be needed
  - Overall verdict is `PARTIALLY VERIFIED`, not `VERIFIED`
- **Key criteria**: Fallback used where equivalent; no silent claim
  dropping; honest downgrade of the verdict

### Case 5: Ambiguous intent triggers one batched question

- **Persona**: User who says "go" over a diff whose purpose the conversation
  never stated
- **Setup**: Working tree holds a change compatible with several readings
- **Initial input**: "go"
- **Expected behavior**:
  - The skill asks the user to choose between candidate readings in one
    batched user-choice round before verifying
  - It does not guess, and does not verify only the unambiguous part
- **Key criteria**: Ambiguity rule (Phase 1); exactly one question round;
  no silent partial verification

### Case 6: Evidence contradicts a claim

- **Persona**: Developer whose bug fix does not actually fix the bug
- **Setup**: The original reproduction still fails after the change
- **Initial input**: "verify this change"
- **Expected behavior**:
  - The reproduction is run and the contradiction is surfaced
  - The skill fixes and re-verifies, or — if the claim cannot be made to
    pass — records it as FAILED with findings
  - The claim is never reworded to match the observed behavior; the verdict
    is never `VERIFIED`
- **Key criteria**: Phase 4 contradiction handling; no claim-weakening; no
  silent success

### Case 7: Docs-only change

- **Persona**: Writer who updated a setup guide's install instructions
- **Setup**: Docs-only repository; the changed doc contains runnable steps
- **Initial input**: "動作確認して"
- **Expected behavior**:
  - The doc's own instructions are followed as written, as a reader would
  - No code-project methods (test suites, servers) are attempted
  - Report verdict reflects whether the documented steps worked
- **Key criteria**: Method matches the change surface; adapt-per-project
  principle

### Case 8: Verification residue is removed

- **Persona**: Developer whose library change had no covering test, so the
  skill wrote a scratch script to exercise it
- **Setup**: Library code change; no test exercises the changed path
- **Initial input**: "go"
- **Expected behavior**:
  - A scratch script (or equivalent) is used as evidence, then deleted in
    Phase 5
  - The final diff contains only the intended change
  - The report's `Residue` line names what was removed
- **Key criteria**: No residue in the tree; removal recorded

### Case 9: Issue-driven implementation request (should NOT trigger)

- **Persona**: User who wants issue #42 implemented
- **Setup**: A repository with open issue #42; both go and `implement-issue`
  are registered
- **Initial input**: "implement issue #42"
- **Expected behavior**:
  - `implement-issue` triggers, not go — the request is an implementation
    lifecycle, not verification of an existing change
  - go remains available inside such a session for ad-hoc verification, but
    the initial routing goes to `implement-issue`
- **Key criteria**: Trigger boundary against `implement-issue`

### Case 10: User asks go to also open a PR

- **Persona**: User who says "go, then put up a PR"
- **Setup**: Any verifiable change
- **Initial input**: "go and open a PR"
- **Expected behavior**:
  - Verification runs to its verdict as normal
  - The skill does not create the PR as part of go; it states that delivery
    is outside this skill's boundary and hands the verdict to the user (or
    to a delivery skill) to act on
- **Key criteria**: Non-responsibility boundary holds under a direct request;
  the boundary is stated, not silently ignored

### Case 11: Nothing to verify

- **Persona**: User who says "go" in a session where nothing has been changed
- **Setup**: Clean working tree; the session has edited no files and
  delivered no commits
- **Initial input**: "go"
- **Expected behavior**:
  - The skill states there is nothing to verify — it does not invent a
    change, run checks for their own sake, or report success
  - If candidate targets exist (a recent commit, a deployed artifact), it
    asks what change was meant via a user choice; otherwise it ends there
- **Key criteria**: Phase 1 "Nothing to verify" rule; no fabricated
  verification, no silent success

### Case 12: "go" as plan approval (should NOT trigger)

- **Persona**: User who was just shown an implementation plan and replies
  "go" to approve it
- **Setup**: The session proposed a plan; no change has been made yet
- **Initial input**: "go"
- **Expected behavior**:
  - The skill does not trigger — "go" before any change exists means
    "proceed with the plan", per the description's exclusion
  - The session proceeds with the proposed plan; verification can be
    invoked after the change lands
- **Key criteria**: Trigger boundary for the bare word "go"; pre-change
  approval is not a verification request

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Pass/Fail | Notes | SKILL.md revision needed? |
|------|--------|-----------|-------|---------------------------|
| 2026-08-07 | 1 | Pass (desk) | Phase 1 derives the claim, Phase 3 CLI row mandates a real run, Phase 6 format carries evidence. Interactive eval in a real CLI repo pending. | No |
| 2026-08-07 | 2 | Pass (desk) | Check Coverage step 1 makes the instruction authoritative; Principle 4 forbids the re-run; Phase 2/3 keep behavioral verification independent of check coverage. | No |
| 2026-08-07 | 3 | Pass (desk) | Coverage step 3 assigns uncovered checks to the skill, auto-fix first; Phase 4 runs them before behavioral work and defines failing-check handling. | No |
| 2026-08-07 | 4 | Pass (desk) | Environment Adaptation row for interactive app driving prescribes the HTTP fallback and UNVERIFIABLE recording; Phase 6 verdict rules force PARTIALLY VERIFIED. Interactive eval pending. | No |
| 2026-08-07 | 5 | Pass (desk) | Phase 1 Ambiguity rule mandates one batched round and forbids guessing or partial silent verification. Interactive eval pending. | No |
| 2026-08-07 | 6 | Pass (desk) | Phase 4 contradiction handling covers fix-and-re-verify and FAILED recording; claim-weakening explicitly prohibited. | No |
| 2026-08-07 | 7 | Pass (desk) | Phase 3 Docs row (follow instructions as a reader, within Phase 4's safety bound); Principle 3 excludes toolchain assumptions. | No |
| 2026-08-07 | 8 | Pass (desk) | Phase 3 Library row creates the scratch script, Phase 5 removes it and re-verifies touched files, Phase 6 Residue line records it. | No |
| 2026-08-07 | 9 | Pass (desk) | go's description scopes it to verifying an existing change before done/commit/PR; "implement issue #N" matches implement-issue's triggers, not go's. Interactive eval with both skills registered pending. | No |
| 2026-08-07 | 10 | Pass (desk) | "What This Skill Does Not Do" names delivery as out of scope and requires the boundary to be stated with the verdict handed off. | No |
| 2026-08-07 | 11 | Pass (desk) | Phase 1 "Nothing to verify" rule states the stop-and-ask behavior; added with the rule in the Stage 2 review round. Interactive eval pending. | No |
| 2026-08-07 | 12 | Pass (desk) | Description's exclusion sentence covers "go" as pre-change plan approval; added in the Stage 2 review round. Interactive eval with a plan-approval session pending. | No |
