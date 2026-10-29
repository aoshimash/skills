---
name: analyze-sessions
description: >
  Analyze the running agent's session history — Codex or Claude Code, or a
  history export the user provides — to detect recurring patterns in skill
  executions and propose improvements to skill definitions and, where that
  agent's configuration surface is confirmed, to its settings or hooks. Use
  when the user says "analyze sessions", "improve skills",
  "analyze skill logs", "セッションを分析", "スキルを改善", "ログを分析",
  "設定を提案", or wants to review skill usage patterns and environment
  configuration.
---

# Analyze Sessions

Analyze an agent's locally stored conversation history to detect recurring
patterns in skill executions and propose concrete improvements to skill
definitions and — for the environment the history came from — to its settings
or hooks.

The history under analysis and the agent running this skill are two different
things. A Claude Code session can analyze Codex history the user points at,
and the reverse; the running agent only decides the *default* source. Every
product-specific fact this skill relies on — where a history store lives, what
its records look like, how a skill invocation shows up in them, which
configuration surface exists — is kept in
[references/history-sources.md](references/history-sources.md) with its
confirmation status, and the instructions below never assume one product.

## Core Principles

1. **Evidence or an explicit gap, never a guess.** Every finding names the
   sessions it was seen in. When the input falls short, the report says
   exactly how — the history could not be reached, its format is unsupported,
   enough history was read but holds no skill execution, or the skill ran
   fewer times than analysis needs — and those four states are never conflated
   (Step 2's outcome table).
2. **Resolve the source, then analyze.** The history store is chosen once
   (Step 1) from what the user named, what the running agent is, and what
   exists on this machine. A missing CLI binary is not a missing history
   store, and a missing store is not "no skill executions".
3. **Product surfaces only where confirmed.** A settings or hook proposal
   targets the product the analyzed history came from, through a
   configuration surface the reference marks **documented** for that product
   (or observed and re-verified on this machine — the reference's legend says
   which statuses count). Where the surface is heuristic or unconfirmed, the
   pattern is still reported — with its evidence and the product documentation
   to consult — but without a configuration snippet. One product's settings
   are never proposed for another.
4. **Privacy.** Raw session content and project-specific paths stay on this
   machine; issues and pull requests carry aggregated findings only.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **Session history access** — read an agent's locally stored conversation transcripts | The running agent's own history store, read directly from disk (Claude Code's per-project transcript directory; Codex's `sessions/` rollouts — locations, formats, and confirmation status in [references/history-sources.md](references/history-sources.md)) | A history export or directory the user provides, in one of the formats the reference describes; with neither, report that no history is reachable (Step 2 outcome **A**) and stop — never fabricate findings |
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |
| **Platform access** — create the issue or pull request that Step 5's Issue / PR output methods produce | A connector or MCP server for GitHub that creates issues and pull requests | The `gh` CLI commands in Step 6; with neither, output the drafted body as Markdown for the user to submit |

User choice is used in three places: selecting the skill to analyze (Step 2),
choosing the output method (Step 5), and approving each improvement (Step 6).
Nothing is written anywhere without the third.

**Platform access** is resolved once, before Step 6's first write, in the
order the other skills in this plugin use: a method the user named, then a
connector or MCP server whose own tool descriptions show it creates issues and
pull requests in this repository, then the `gh` CLI, then — with neither — the
drafted body as Markdown for the user to submit. Keep the method for the rest
of the run, and name it in the report.

## Workflow

### 1. Resolve the History Source

Pick the store to read, in this order, and name the choice in the report:

1. **A source the user named** — a product ("my Codex sessions") or a path to
   an export. Use it; a path is read as *user-provided history* per the
   reference.
2. **The running agent's own store** — identify the agent you are running in
   from your own environment, and use its store when the reference lists one
   and it exists on this machine.
3. **Another known store on this machine** — when the running agent has no
   listed store, or its store does not exist, check which listed stores do
   exist and ask the user (user choice) which to analyze.
4. **None** — report outcome **A** (Step 2) and stop.

Then scope the store to the **current project**, by the rule the reference
gives for that store. The scoping rule derives a location or a filter from the
working directory; **verify the derived location exists** before reading, and
when it does not, list the store and pick the entry that matches the working
directory — or ask. A derivation that silently matches nothing would be
reported as "no sessions", which is the confusion Principle 2 forbids.

### 2. Discover Skill Sessions

Read the **recent** sessions in the scoped store — the 20 most recent files
modified in the last 30 days, or a wider window only when the user names one
— and find the ones in which a skill from this plugin ran.

- **Parse each file as the reference describes for its store.** A file that
  cannot be parsed that way — compressed without a decompressor on `PATH`, a
  first record that is not the shape the reference describes, or a parser the
  check needs (`python3` for Codex rollouts) missing — counts as unsupported or
  unparsed, never as "no executions". The reference's commands print those
  counts beside the number of files read.
- **Detect invocations by the store's marker.** The reference lists, per
  store, the documented or observed marker a skill invocation leaves. Search
  for the skill's qualified name (`aoshimash-skills:<skill-name>`) where the
  store records it that way, and for the heuristic markers the reference gives
  where no marker is documented — and say in the report when detection was
  heuristic.

Report the result as exactly one of these outcomes, with the counts it names:

| Outcome | Condition | Report |
|---|---|---|
| **A. History not reachable** | No store resolved in Step 1, or the resolved store cannot be read (missing directory, no read permission) | `No session history is reachable: <what was tried and why it failed>.` Then stop — nothing below can run |
| **B. Unsupported format** | Files were found but none could be parsed as the reference describes (unsupported or unparsed, in the reference's counts) | `Found N session file(s) in <store>, none in a format this skill can read: <reason, e.g. compressed .zst and no zstd on PATH; first lines that are not session records>.` Say what would make them readable, and stop. When only *some* files are affected, continue with the rest and state the counts in every later message |
| **C. No skill executions** | N files were read (N may be 0) and no skill invocation marker was found in any of them | `No skill execution found in N session(s) from the last <window> (<store>, current project).` Name the window and the detection method, so the user can judge whether N is enough history |
| **D. Insufficient count** | A skill was found, but in fewer than 3 sessions | `Not enough data for pattern analysis yet (K/3 sessions for <skill-name>).` List every skill found with its count |

With 3+ sessions for at least one skill, list which skills were used and how
many sessions each has, and ask the user (user choice) which **single skill**
to analyze. Do not offer an "analyze all" option — analyze one skill per
invocation to keep execution fast.

### 3. Analyze Sessions

For each session file containing the target skill invocation, read the
conversation. Focus on the user and assistant turns to understand the
interaction flow — skip large tool results unless needed for context (e.g.,
to confirm a test failure). Detect these patterns:

#### Skill-Level Patterns

These patterns indicate issues with the skill definition itself:

##### Rejection
User explicitly rejects a proposal or asks to change something. Look for:
- User messages containing negation ("no", "that's wrong", "change this", "違う", "修正して")
- User requesting revisions to plans, drafts, or implementations

##### Retry
A step fails and must be re-done. Look for:
- Tool results showing test/lint/build failures followed by fix attempts
- Repeated tool calls to the same file or command

##### Friction
User experiences confusion or frustration. Look for:
- User asking the same question multiple times
- User requesting clarification on skill behavior
- User expressing frustration or confusion

##### Abandonment
Workflow was not completed. Look for:
- Sessions that start a skill workflow but never reach the final step (e.g., no PR created for implement-issue)

#### Environment-Level Patterns

These patterns indicate issues solvable by the environment's configuration —
permissions, hooks, automation — rather than by skill modifications. Detect
them the same way in every store; only the proposal (Step 4) depends on the
product.

##### Permission Friction
Repeated permission or approval prompts slow down the workflow. Look for:
- The same tool or command being approved multiple times across sessions with short user responses ("yes", "y", "allow", "approve", "許可") immediately following
- User expressing annoyance at repeated prompts
- Patterns where a tool is consistently approved (never denied) across sessions

##### Hook Opportunity
Repeated manual actions suggest automation via the product's lifecycle hooks. Look for:
- The same shell command or sequence executed at the start of multiple sessions (→ a session-start hook)
- Repeated manual validation before specific tool calls (→ a pre-tool-use hook)
- Consistent post-action cleanup steps (→ a post-tool-use or stop hook)

#### Aggregation Thresholds

Aggregate findings across the analyzed sessions using these thresholds:

| Signal | Threshold | Indicates |
|---|---|---|
| Same-step rejection | 2+ sessions | Default approach doesn't match user expectations |
| Same-step retry | 2+ sessions | Instructions unclear or incomplete |
| Similar friction | 2+ sessions | Missing context or explanation |
| Abandonment | 2+ sessions | Workflow too heavy or misaligned |
| Permission friction | 2+ sessions | A permission rule should cover the tool |
| Hook opportunity | 2+ sessions | A manual step should be automated via a hook |

### 4. Present Findings

Open every report with one line that fixes its evidence base:

```
History: <store> · <N> session(s) read · window <30 days, or the one the user named> · detection <marker | heuristic> · unparsed/unsupported files: <K>
```

#### If no patterns found:
```
No recurring patterns found in <skill-name> sessions (N sessions analyzed).
```

#### If patterns found, present a structured report:

Group findings by target:

**Skill Improvements** (changes to SKILL.md):
```
### <pattern description>
- **Type**: Rejection / Retry / Friction / Abandonment
- **Seen in**: X/N sessions
- **Common reason**: "<aggregated reasons>"
- **Root cause**: <what in the skill likely causes this>
- **Proposed fix**: <what to change in SKILL.md>
```

**Environment Proposals** (changes to the product's settings or hooks):

Before writing one, look up the product the analyzed history came from under
"Configuration surface" in
[references/history-sources.md](references/history-sources.md). A proposal
carries a configuration snippet **only** for a surface whose status there
counts as confirmed (documented, or observed and verified on this machine);
otherwise it carries the evidence and the product documentation to consult,
and says that no snippet was produced because the surface is not confirmed.
Never write one product's snippet for another product's history — a Claude
Code settings entry for a Codex pattern, or the reverse.

```
### <pattern description>
- **Type**: Permission Friction / Hook Opportunity
- **Product**: <the product the analyzed history came from>
- **Seen in**: X/N sessions
- **Common reason**: "<aggregated reasons>"
- **Root cause**: <missing configuration>
- **Proposed fix**: Add to <target file> — or — Consult <documentation>; surface unconfirmed, no snippet
- **Configuration** (confirmed surfaces only):
  ```
  <proposed snippet in that product's own format>
  ```
```

### 5. Choose Output Method

After presenting findings, ask the user (user choice) how to proceed:

1. **Issue** — Submit feedback as a GitHub Issue (no code changes)
2. **PR** — Submit with SKILL.md modifications included
3. **Conversation only** — No external submission; review findings in this session only

### 6. Apply Improvements (with approval)

For each improvement suggestion:

1. **Present to the user** — Show the pattern, root cause, and proposed fix.
2. **Ask for approval** (user choice) — Do not modify files without explicit user approval.
3. **If declined**, acknowledge and move to the next suggestion.

#### If "Conversation only" was selected:

Present the full analysis report. No external submission occurs. End the workflow.

#### If "Issue" was selected:

Create an issue for the analyzed skill:

1. Draft the issue body containing:
   - Skill name, the history line from Step 4, and the number of sessions analyzed
   - Each pattern found (description, frequency, root cause, proposed fix)
   - Environment proposals (if any) with their product and, for confirmed surfaces, the configuration snippet
   - Do NOT include raw session data or project-specific details (privacy)
2. Show the draft to the user for review and confirmation.
3. On approval, create the issue (platform access; the reference command):
   ```bash
   gh issue create --title "improve(<skill-name>): <summary>" --body "<drafted body>" --label "enhancement"
   ```
4. Return the issue URL.

#### If "PR" was selected:

Create a PR with the approved fixes for the analyzed skill:

1. Create a branch: `fix/improve-<skill-name>-<description>`
2. Modify the affected skill files.
3. Commit: `fix(<skill-name>): <description>`
4. Show the diff to the user for review and confirmation.
5. Push and create the PR (platform access; the reference command):
   ```bash
   gh pr create --title "fix(<skill-name>): <description>" --body "<summary of changes>"
   ```
6. Return the PR URL.

Note: environment proposals are **not** auto-applied via PR — they are
included in the PR description as recommendations for the user to apply
manually. This avoids modifying the user's environment configuration without
explicit action.

## References

- [references/history-sources.md](references/history-sources.md) — per-agent
  history locations, project scoping, record formats, invocation markers, and
  configuration surfaces, each with its confirmation status; required reading
  for Steps 1, 2, and 4
- [references/eval-cases.md](references/eval-cases.md) — evaluation test cases
  and the evaluation log
