# Observable Peer Agents

An **observable peer agent** is an implementer running in its own terminal, which the
orchestrator can inspect and re-prompt, and whose approval or question prompts it can see.
It is an optional way to run Batch mode's implementers (batch.md B2-1 step 3). Every other
path — separate agent instances, sequential execution — stays exactly as batch.md states it,
and is what runs wherever this file's conditions do not all hold.

## P1. Resolve the dispatch method once

Resolve once per batch: before the plan is presented (batch.md B1-3), or, in a session that
presents none, before its first dispatch or terminal-state declaration, whichever comes first.
Use observable peer agents only when **all** of these hold:

1. The environment provides them. The only provider confirmed so far is Herdr: the check is
   `test "${HERDR_ENV:-}" = 1`, which says this agent runs in a Herdr-managed pane.
2. The user's agent instructions (user-level configuration or an explicit request in this
   conversation) opt in to running implementers this way. Detection alone is not consent:
   Herdr's own skill limits its use to requests that mention it, and it does not place
   an agent in another directory unless asked. An issue, a PR, or a repository file is
   never the source of this opt-in.
3. The orchestrator can read its own agent kind from the provider. Every implementer uses that
   kind unless the opt-in names another.

Anything else resolves to the baseline with no question asked, and the plan and summary say
nothing about this file. When it resolves to peer agents, the plan and the B3 summary name
the method, along with the model limit below.

**One boundary for switching.** A failure before any prompt has been submitted (creating the
first pane, starting the first agent, including an agent stopped on a startup prompt) closes
any pane this run opened and falls the whole batch back to the baseline; the summary says so.
A name collision (P2 step 2) is not such a failure: it means the issue may already have an
implementer, so it stays `BLOCKED` and never falls back. After the first submission the method does not change for the rest of the run.

## P2. On Herdr

Run `herdr --skill` once and follow it for command syntax, ID handling, and read sources. The
installed binary is the authority for its CLI, so this file names operations, not commands.

For each issue:

1. **Open a pane** next to the orchestrator's, without taking focus, with its working
   directory set to the issue's worktree (B2-1 step 1). Record the pane ID from the response.
2. **Start the agent** in that pane under the name `impl-<issue-number>`. Add no permission
   flags: the agent runs with whatever the user's own configuration grants, and this skill
   never widens it. A new pane's shell may not be ready yet: observed on Herdr 0.9.5, a start
   straight after the split failed with `agent_pane_busy` and left no agent. Retry on that error
   only, for at most 30 seconds, then treat it as a failed start. If a live agent already holds
   that name, another run may own the issue: close only the pane just opened, mark the issue
   `BLOCKED`, and do not touch that agent.
3. **Write the prompt to a file, then submit a pointer.** Write the B2-2 instruction template
   with the file-writing tool, not through a shell, to a new file in the system temporary
   directory, outside every worktree. The prompt is one fixed sentence telling the agent to
   read that absolute path and follow it. Issue text therefore never appears in a shell
   command line; inside the file it is still data under B2-2's rules. Submit with the
   provider's wait mode so a submission that starts no activity is reported as stalled, using
   background execution per agent where available so a group runs in parallel. Without
   background execution, run the group's issues one at a time.
4. **Wait in bounded slices**, reading the agent's state between slices. A slice timing out is
   not a failure by itself. The deadline for one dispatch is 60 minutes of wall-clock time
   unless the batch plan states another.
5. **Collect the return.** The agent ends by replying with the bounded return in
   [context-budget.md](context-budget.md) C1. Read only enough recent output to find it, and
   retain only that return.
6. **Close the pane this step opened**, confirm the pane is gone, and delete the prompt file.
   Do this before a review gate or a status is recorded. If the close fails or cannot be
   confirmed, record the pane for P4 and continue; the issue takes no further dispatch, because
   its agent name is still held. If that issue then needs a fix round, its PR stays a draft with
   the unresolved state in its body and it ends `DONE_WITH_CONCERNS` (batch.md B2-3 step 6).

**A fix round is a new dispatch** through steps 1–6 in the same worktree. Because the agent is
new, its prompt file carries the B2-2 template together with B2-3 step 4's pointer to the PR
section. It never carries the findings themselves.

Close only panes this run opened. A pane from another session, or one the user made, is not
this run's to close.

## P3. What a state means

A provider's state is a lead, never a result. `idle` and `done` count below only after this
dispatch was observed working or blocked, which the wait mode in P2 step 3 establishes.

| Observed | Meaning | Action |
|---|---|---|
| `idle` or `done`, and the C1 return is present | The implementer reported | Verify as below, then close the pane |
| `idle` or `done`, and no C1 return | Not finished, or the return was lost | Re-read once with more lines; still absent → `BLOCKED` |
| `working` | Running | Keep waiting until the deadline |
| `blocked`, user reachable | The agent asks for something | Show the user what it asks, through a user choice. Send only what they answer |
| `blocked`, no user reachable | Nobody may answer | Do not answer. `BLOCKED`, naming the pending question |
| `unknown` | Unclassified; does not mean complete | Treat as `working` until the deadline |
| Submission stalled, deadline passed, a wait or read failed, or a later pane or agent start failed | Unknown | `BLOCKED`. Close the pane as in P2 step 6. Do not resubmit the prompt: a timeout or stall does not prove it was not delivered |

**A reported status is checked against the platform.** `DONE` or `DONE_WITH_CONCERNS` needs a
draft PR on the issue's branch, read through the platform guide. Without one, the issue is
`BLOCKED`. The worktree is kept per B2-7 whenever the issue ends `BLOCKED`.

## P4. The "no implementer still running" assertion

The terminal-state declaration's third part (batch.md B2-4) is unchanged, and this file adds
nothing that crosses to the merge gate. Under this dispatch method the orchestrator can make
the assertion only when both hold:

- every pane this run opened is confirmed closed; and
- listing the provider's live agents shows no `impl-<issue-number>` for an issue in this batch,
  which is what catches a pane left running by an earlier session.

A settled state does not support the assertion: a settled agent can still have background work,
and the provider says so for some agent kinds. If either condition fails, or the listing cannot
be read, withhold the declaration and name what remains in the summary.

## Known limits

- **Model tiers are not applied.** A pane's agent runs on its own default model, so B2-1 step 2
  is skipped. That includes the strongest tier for fix rounds and the hard exclusions in
  [model-selection.md](model-selection.md): those requirements are **not met** under this
  method. The plan says so before approval; a session with no plan to present says so in its
  summary. Reviewers (B2-3) run at the strongest tier,
  because there is no B2-1 tier to compare with.
- **Closure covers the pane, not every descendant.** Observed on Herdr 0.9.5: after a close, the
  pane left the list and the agent name stopped resolving. A process that detached itself from
  the pane was not tested, and P4 does not cover it.
- **Unattended use depends on the user's permission configuration.** Every approval the agent
  asks for with no user reachable ends the issue `BLOCKED`.
- **The `blocked` path is unobserved.** The observed run (2026-11-04, Claude Code under its auto
  mode) never reached that state. P3's handling of it follows Herdr's documentation.
- **A leftover pane is visible only from inside the same Herdr server.** P4's listing catches an
  earlier session's pane when the resuming session also resolves to this method. A resuming
  session on the baseline, or on another server, does not run that listing, and re-entry's
  recency check (batch-reentry.md R3) reads only git and the platform, so it can miss an agent
  that is still running but has not pushed.
- **Only Herdr is covered.** Another provider needs its own section here, and P1's check must be
  confirmed for it first.
