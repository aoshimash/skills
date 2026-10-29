# Evaluation Test Cases

## How to Run

For each test case:
1. Start a new conversation
2. Trigger the analyze-sessions skill
3. Follow the described scenario
4. Evaluate against the acceptance criteria listed per case
5. Record results in the Evaluation Log section at the bottom

Two kinds of result are recorded, and the log says which: **executed** — the
command or check was actually run, as written in the skill's files, on a real
store — and **desk-checked** — the case was reasoned through against the
shipped text without running an agent. A desk-check verifies what the text
prescribes, not whether an agent follows it.

Outcome letters (**A**–**D**) refer to SKILL.md Step 2's outcome table.

## Test Cases

### Case 1: History not reachable (outcome A)

- **Persona**: User on a machine where the running agent's history store does not exist — a fresh installation, or a configuration directory (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`) pointing somewhere empty
- **Setup**: The store's directory test in `references/history-sources.md` fails; the user names no other source
- **Initial input**: "セッションを分析して"
- **Expected behavior**:
  - Reports outcome **A** with what was tried (the store path tested) and why it failed
  - Does NOT report "no skill executions" or "no patterns", and does NOT proceed to analysis
  - Offers another listed store only if one exists on the machine
- **Key criteria**: An unreachable store is reported as unreachable, never as empty
- **Fixture**: The store tests run with the configuration directory pointed at an empty directory (see the log, 2026-10-29)

### Case 2: Fewer than 3 sessions for a skill (outcome D)

- **Persona**: User who has used implement-issue once or twice
- **Setup**: The scoped store holds 1–2 session files carrying the `aoshimash-skills:implement-issue` marker
- **Initial input**: "analyze sessions"
- **Expected behavior**:
  - Opens with the history line (store, sessions read, window, detection method)
  - Lists the skills found with their counts and reports insufficient data (K/3)
  - Does NOT attempt pattern analysis
- **Key criteria**: Threshold enforcement, clear messaging
- **Fixture**: This plugin's own repository, main checkout, on 2026-10-29 — one recent transcript carried the marker (1/3)

### Case 3: Pattern detection with 3+ sessions

- **Persona**: User who has used create-issue 4 times, with repeated friction in step 3
- **Setup**: 4 session files with create-issue invocations; 3 sessions show user rejecting the initial draft
- **Initial input**: "analyze skill logs"
- **Expected behavior**:
  - Detects the rejection pattern at draft step
  - Presents structured report with frequency, root cause, and proposed fix
  - Findings are grouped under "Skill Improvements"
  - Asks user to choose output method (Issue / PR / Conversation only)
- **Key criteria**: Pattern detection accuracy, structured report format

### Case 4: Output method — Conversation only

- **Persona**: User who wants to review findings without external submission
- **Setup**: Same as Case 3
- **Initial input**: Choose "Conversation only" when asked for output method
- **Expected behavior**:
  - Full analysis report is presented in conversation
  - No platform write (no `gh` command, no connector call) is executed
  - Workflow ends cleanly
- **Key criteria**: No side effects, complete report in conversation

### Case 5: Output method — Issue creation

- **Persona**: User who wants to submit feedback as an Issue
- **Setup**: Same as Case 3
- **Initial input**: Choose "Issue" when asked for output method
- **Expected behavior**:
  - Draft issue body is shown for review before submission
  - Issue body does NOT contain raw session data or project-specific paths
  - On approval, the issue is created through the resolved platform access (the `gh issue create` reference command, or a connector that creates issues) with appropriate title, body, and label
  - Issue URL is returned
- **Key criteria**: Privacy filtering, user confirmation before submission, correct platform usage

### Case 6: Output method — PR creation

- **Persona**: User who wants to submit improvements as a PR
- **Setup**: Same as Case 3
- **Initial input**: Choose "PR" when asked for output method
- **Expected behavior**:
  - Proposed SKILL.md changes are shown as a diff for review
  - On approval, branch is created, changes committed, and PR opened
  - PR URL is returned
- **Key criteria**: User confirmation before code changes, correct branch/commit/PR flow

### Case 7: User requests multi-skill analysis

- **Persona**: User with sessions across multiple skills
- **Setup**: 3+ sessions each for implement-issue and create-issue
- **Initial input**: "全スキルを分析して"
- **Expected behavior**:
  - Lists available skills with session counts
  - Prompts user to select a **single** skill to analyze (does NOT analyze all at once)
  - After analysis completes, user can re-invoke the skill for the next skill
- **Key criteria**: Single-skill enforcement, clear guidance to re-invoke for other skills

### Case 8: Permission friction pattern detection (Claude Code history)

- **Persona**: User who repeatedly approves the same tool across sessions
- **Setup**: 4 Claude Code session files with implement-issue invocations; 3 sessions show the user approving `Bash(gh api:*)` with short responses ("y", "yes", "allow") multiple times
- **Initial input**: "セッションを分析して"
- **Expected behavior**:
  - Detects the permission friction pattern for `Bash(gh api:*)`
  - Findings are grouped under "Environment Proposals" with **Product: Claude Code**
  - Proposed fix includes a specific `permissions.allow` entry (e.g., `"Bash(gh api:*)"`) — a confirmed surface for Claude Code per `references/history-sources.md`
  - Proposed fix specifies the target settings file (user scope or the personal project-scope file)
  - Configuration snippet is included in the report
- **Key criteria**: Environment-level pattern detection, actionable proposal on a confirmed surface

### Case 9: Mixed output with skill and environment proposals

- **Persona**: User with both skill-level and environment-level patterns
- **Setup**: 5 session files with create-issue invocations; 3 sessions show rejection at draft step AND 3 sessions show repeated permission approval for the same tool
- **Initial input**: "improve skills"
- **Expected behavior**:
  - Report contains both "Skill Improvements" and "Environment Proposals" sections
  - Skill improvement has type Rejection with SKILL.md fix
  - Environment proposal has type Permission Friction, names its product, and carries a snippet only when the product's surface is confirmed
  - When "Issue" output is selected, both types appear in the issue body
  - When "PR" output is selected, environment proposals are in the PR description (not auto-applied)
- **Key criteria**: Dual-target report, correct grouping, environment proposals not auto-applied

### Case 10: Cross-repository rule collection request (should NOT trigger)

- **Persona**: User who wants hand-written conventions in their own GitHub repositories promoted into the shared rule corpus
- **Setup**: Session history exists for several skills, so analyze-sessions would have data to work with
- **Initial input**: "collect the hand-written rules from my other repos and add the good ones to the shared corpus"
- **Expected behavior**:
  - analyze-sessions does **not** trigger — `collect-agent-rules` does
  - No session files are read
  - The boundary is the data source: analyze-sessions reads the running agent's session history on this machine; `collect-agent-rules` reads `AGENTS.md` in remote repositories
- **Key criteria**: Trigger boundary against `collect-agent-rules`; no session scan for a repository-scanning request

### Case 11: Japanese rule collection phrasing (should NOT trigger)

- **Persona**: Same as Case 10, phrasing the request in Japanese
- **Setup**: Same as Case 10
- **Initial input**: "自分のリポジトリから共通化できる規約を集めて共通ルールに追加して"
- **Expected behavior**:
  - analyze-sessions does **not** trigger — `collect-agent-rules` does
  - "集めて" / "収集" over repositories is not the same request as "セッションを分析" / "ログを分析" over session history
  - No session files are read, and no environment proposal is produced
- **Key criteria**: Japanese trigger boundary; "collect from repos" is not "analyze sessions"

### Case 12: Skill improvement request (should still trigger)

- **Persona**: User who wants their skills improved from observed usage
- **Setup**: 3+ sessions exist for at least one skill
- **Initial input**: "スキルを改善して"
- **Expected behavior**:
  - analyze-sessions **does** trigger, unchanged by the cases above
  - Sessions are discovered and the user is asked which single skill to analyze
- **Key criteria**: The boundary cases above must not suppress analyze-sessions' own trigger phrases

### Case 13: Unsupported format — compressed Codex rollouts without a decompressor (outcome B)

- **Persona**: Codex user whose rollouts are stored compressed, on a machine without `zstd`
- **Setup**: The Codex store exists and its rollouts are `.jsonl.zst`; `zstd` is not on `PATH`
- **Initial input**: "analyze sessions"
- **Expected behavior**:
  - The scoping command reports every `.zst` file as unsupported and reads none of them
  - Reports outcome **B** with the file count and the reason (compressed, no `zstd`), and what would make them readable
  - Does NOT report "no skill executions" and does NOT proceed to analysis
  - When plain `.jsonl` rollouts also exist, continues with those and states the unsupported count in every later message
- **Key criteria**: Unreadable files are counted as unreadable, never as empty history
- **Fixture**: The real Codex store on the verification machine (135 of 139 rollouts compressed; 18 of the 22 in the 30-day window), run with `zstd` removed from `PATH` (log, 2026-10-29)

### Case 14: No skill executions in the window (outcome C)

- **Persona**: User whose store is readable but holds no recent session for this working directory, or none that ran a skill
- **Setup**: The Codex store exists and is readable; scoping to the working directory yields no rollout from the last 30 days
- **Initial input**: "ログを分析"
- **Expected behavior**:
  - Reports outcome **C** with N (here 0) and the window, so the user can judge whether the history is sufficient
  - Offers the store's other working directories rather than widening the scope silently
  - Does NOT report outcome **A** (the store was reachable) or **B** (the files were readable)
- **Key criteria**: Empty-but-readable is distinguished from unreachable and from unreadable
- **Fixture**: This plugin's worktree on 2026-10-29 — the Codex store held 22 rollouts from the last 30 days machine-wide and none for this working directory

### Case 15: Derived project directory does not exist (Claude Code)

- **Persona**: Claude Code user working in a git worktree
- **Setup**: The derivation rule produces a directory name; a wrong rule (one that strips the leading `-` or keeps `.`) names a directory that is not there, while the store itself has an entry for the working directory
- **Initial input**: "セッションを分析して"
- **Expected behavior**:
  - Verifies the derived directory exists before reading; on a miss, lists the store's entries and picks the one matching the working directory (or asks)
  - Never reports "no sessions" on the strength of a derivation alone
- **Key criteria**: Derivation is verified, not trusted
- **Fixture**: This worktree's path on 2026-10-29 — the documented rule derived an existing directory; the skill's earlier rule derived one that does not exist

### Case 16: Codex history — environment proposals stay on Codex's confirmed surface

- **Persona**: User running in Codex whose rollouts show the same setup command at every session start and repeated approval prompts for the same command
- **Setup**: Case 8's scenario — this repository's own eval fixture since #36 (2026-03-14) — with the history coming from a Codex store instead of Claude Code: 4 readable rollouts for the working directory with the plugin's `implement-issue` invoked (heuristic marker), 3 showing the same approval repeated, 3 showing the same session-start command
- **Initial input**: "設定を提案"
- **Expected behavior**:
  - Hook opportunity → an environment proposal with **Product: Codex**, targeting `hooks.json` (or `[hooks]` in `config.toml`) on the documented `SessionStart` event, and saying the entry's exact shape is taken from the Codex hooks page at proposal time
  - Permission friction → reported with its evidence and the Codex documentation to consult, and **no configuration snippet**, because that surface is unconfirmed
  - No `settings.json` / `permissions.allow` proposal appears anywhere: that is Claude Code's surface, not Codex's
  - The history line says detection was heuristic
- **Key criteria**: Confirmed-surface gating per product; no cross-product settings
- **Fixture**: Derived from a repository artifact (Case 8, unchanged since #36), not from a live rollout exhibiting the pattern — none in the verification machine's 30-day window was inspected for repeated approvals, so this case is desk-checked on a synthetic setup. The real `config.toml` on that machine (keys `model`, `notify`, `[projects.*] trust_level` observed) shows the Codex configuration surface exists; the hooks page was fetched 2026-10-29

### Case 17: User-provided history — a Claude Code session analyzes the Codex store

- **Persona**: User in a Claude Code session who says "analyze my Codex sessions for this repo from September"
- **Setup**: The Codex store exists; the user names it as the source and names a window wider than the default 30 days
- **Initial input**: "analyze my Codex sessions for this repo from September"
- **Expected behavior**:
  - Resolves the source from the user's words (resolution order step 1), not from the running agent, and widens the `-mtime` window to the one the user named
  - Applies the Codex section of `references/history-sources.md`: first-line `session_meta` parse check, `payload.cwd` scoping, heuristic invocation markers (`$<skill-name>`, `<skill-name>/SKILL.md`)
  - The history line names the Codex store, the widened window, and marks detection heuristic
- **Key criteria**: The analyzed store and the running agent are decoupled; a user-named window is honored and reported
- **Fixture**: The five Codex rollouts whose `cwd` is this plugin's main checkout, all dated 2026-09-05 — outside the shipped loop's default 30-day window on 2026-10-29, which is why the case names a window: every one contains the plugin's `SKILL.md` paths and two contain `$<skill-name>` mentions (counted by a retyped survey, log 2026-10-29); the shipped loop at its default window lists none of them

### Case 18: CLI absent, store present

- **Persona**: User whose Codex history was written by the desktop app or IDE extension; no `codex` binary is on `PATH`
- **Setup**: `command -v codex` fails; the Codex home directory holds `sessions/`
- **Initial input**: "analyze my Codex sessions"
- **Expected behavior**:
  - Resolves the store by the directory test, not by the binary, and proceeds
  - Does NOT report outcome **A**
- **Key criteria**: A missing CLI is not a missing history store
- **Fixture**: The verification machine on 2026-10-29 — no `codex` on `PATH`, 139 rollouts under `~/.codex/sessions`

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Pass/Fail | Notes | SKILL.md revision needed? |
|------|--------|-----------|-------|---------------------------|
| 2026-03-07 | 3 | Pass | Simulated with real data (5 create-issue + 5 implement-issue sessions). Detected language friction (5/5), interrupts (2/5), rejections (5/5). Structured report format works. | No |
| 2026-03-07 | 4 | Pass | Simulated: "Conversation only" selected, no external commands executed. | No |
| 2026-03-07 | 7 | Pass | Simulated cross-skill analysis with create-issue (5) and implement-issue (5). Per-skill findings presented. | Consider adding guidance to distinguish permission rejections from user rejections |
| 2026-03-14 | 7 | Pending | Case 7 redesigned in #32 to test single-skill enforcement. Requires interactive eval after merge. | N/A |
| 2026-03-14 | 8 | Pending | New case added in #36. Requires sessions with repeated tool permission approvals for interactive eval. | N/A |
| 2026-03-14 | 9 | Pending | New case added in #36. Requires sessions with both skill-level and environment-level patterns for interactive eval. | N/A |
| 2026-07-26 | 10 | Pending | New case added in #83 for the trigger boundary against `collect-agent-rules`. Requires an interactive eval with both skills registered. | N/A |
| 2026-07-26 | 11 | Pending | New case added in #83 — Japanese phrasing of the same boundary. Requires an interactive eval with both skills registered. | N/A |
| 2026-07-26 | 12 | Pending | New case added in #83 to confirm cases 10–11 do not suppress this skill's own trigger phrases. Requires an interactive eval. | N/A |

### 2026-10-29 — Agent-neutral history sources (Refs #135)

**What changed.** The skill no longer assumes Claude Code: SKILL.md is
product-neutral and `references/history-sources.md` carries every product
fact with a confirmation status (documented / observed / heuristic /
unconfirmed) and the date it was confirmed. Step 2 distinguishes four outcomes
— history not reachable (A), unsupported format (B), no skill executions in N
readable sessions (C), insufficient count (D) — and the reference's commands
print the counts those outcomes turn on (files read, unparsed, unsupported).
Environment proposals carry a snippet only on a surface confirmed for the
product the history came from. The `compatibility` declaration naming Claude
Code was removed, so the `claude-paths` check now applies to this skill
(green). The Stage 2 review of PR #157 found that the first shipped commands
did not deliver two of these claims — GNU `xargs` ran `ls`/`grep` over the
working directory on an empty store, and the Codex loop counted unparseable
first lines as sessions read — and both were fixed and re-run before the
results below were recorded.

**Executed** — commands extracted from `references/history-sources.md` and run
as written: macOS 27 (BSD `xargs`; bash and zsh) against the real stores on
the implementing machine, and Linux containers (`ubuntu:24.04` for GNU
`xargs`, `debian:12` for a machine without `python3`) against scratch stores.
Counts only; no session content was read into the record. The reference's own
Verification Log holds the full table; the rows that decide a case:

| Check | Result |
|---|---|
| Claude Code derivation + directory test (Case 15) | From this worktree, the documented rule derived an existing directory; the skill's previous rule (leading `-` stripped, `.` kept) derived one that does not exist |
| Claude Code discovery pipeline (Case 2) | Main checkout: 1 recent transcript carried `aoshimash-skills:implement-issue` → outcome D (1/3); this worktree: 8. Both marker forms (`<command-name>/aoshimash-skills:…</command-name>` on the invoking user record, `attributionSkill` on assistant records) present in the real transcript; the previous pattern without the slash matched neither. On an empty project directory with a marker-bearing file in the working directory: no output on macOS and on GNU `xargs`; with `-r` removed, GNU `xargs` listed that file as a session — the regression the shipped line now prevents |
| Claude Code store test with `CLAUDE_CONFIG_DIR` pointed at an empty directory, and at an unreadable `projects/` (Case 1) | `no readable Claude Code transcript store at …/projects` → outcome A, no listing attempted |
| Codex store test (Case 18) | `sessions/` present under `~/.codex` while `codex` was not on `PATH` |
| Codex scoping loop (Case 14) | Store readable; for this worktree's working directory: nothing listed, `rollouts read: 22; unparsed: 0; unsupported: 0` → outcome C with N = 0. Same under zsh |
| Codex scoping loop with `zstd` hidden from `PATH` (Case 13) | Nothing listed, `rollouts read: 4; unparsed: 0; unsupported (.zst without zstd): 18` — the 4 plain rollouts in the window were still read, the 18 compressed ones counted as unsupported → B for those files, with the count carried into every later message |
| Codex scoping loop with `python3` hidden (macOS) and in `debian:12` (Case 13) | The `python3` line printed and every file counted as unparsed (`read: 0; unparsed: 22`, and `read: 0; unparsed: 1` on the scratch store) → stop and report, never C |
| Codex scoping loop on a scratch store of seven files (Cases 13, 14) | Two `session_meta` rollouts for this directory listed (one compressed, subdirectory `cwd`); one for another directory read but not listed; a `response_item` first line carrying this directory's `cwd`, a non-JSON line, an empty file, and a corrupt `.zst` all counted unparsed (`read: 3; unparsed: 4`) — none mistaken for a session |
| Codex store test with `CODEX_HOME` pointed at an empty directory (Case 1) | `no Codex session store at …/sessions` → outcome A |
| Survey of the whole Codex store (retyped Python, not a shipped command — context for Cases 13, 14, 17) | 139 rollouts, 135 compressed; every first line parsed as `session_meta` with a `payload.cwd`; 20 distinct working directories; 22 rollouts newer than 30 days; 5 under this plugin's main checkout, all from 2026-09-05, every one carrying the plugin's `SKILL.md` paths and two carrying `$<skill-name>` mentions |
| `history.jsonl` under `~/.codex` | Records carry `session_id`, `text`, `ts` only — prompt lines, not a transcript |

**Documentation fetched in the session** (the "documented" facts in the
reference): code.claude.com/docs/en/claude-directory (transcript path,
project-directory rule for the scratchpad, retention), code.claude.com/docs/en/settings-reference
(settings file paths, `permissions.allow`, `hooks`), code.claude.com/docs/en/hooks
(hook events, settings-file configuration), learn.chatgpt.com/docs/config-file/config-reference
(`config.toml` path, `history.persistence`, `features.hooks`, `rules.prefix_rules`),
learn.chatgpt.com/docs/hooks (hook file locations, events, trust),
learn.chatgpt.com/docs/agent-configuration/agents-md (`CODEX_HOME`),
learn.chatgpt.com/docs/build-skills (`$<skill-name>` invocation), and
`codex-rs/rollout/src/lib.rs` in `openai/codex` (`sessions`, `archived_sessions`).

| Date | Case # | Pass/Fail | Notes | SKILL.md revision needed? |
|------|--------|-----------|-------|---------------------------|
| 2026-10-29 | 1 | Pass (executed, both stores) | Store tests report outcome A with the path tested — missing and unreadable alike; no "no sessions" message | No |
| 2026-10-29 | 2 | Pass (executed discovery; report desk-checked) | Real fixture 1/3 for implement-issue on the main checkout | No |
| 2026-10-29 | 3–7, 9 | Pass (desk-checked) | Unchanged logic; wording follows the Environment Proposals rename; Case 5 allows a connector for the write | No |
| 2026-10-29 | 8 | Pass (desk-checked) | Claude Code surface confirmed in the reference, snippet allowed | No |
| 2026-10-29 | 10–12 | Pass (desk-checked) | Trigger boundary unchanged; description still carries the same trigger phrases | No |
| 2026-10-29 | 13 | Pass (executed) | `zstd` hidden: 18 unsupported, 4 plain read; `python3` hidden: 22 unparsed, 0 read; unparseable first lines on the scratch store counted unparsed — each path reports B or stops, never C | No |
| 2026-10-29 | 14 | Pass (executed) | 22 read, 0 for this working directory → C with N = 0; the scratch store's out-of-scope rollout read and not listed | No |
| 2026-10-29 | 15 | Pass (executed) | Old derivation misses, new derivation hits; the block lists the store on a miss | No |
| 2026-10-29 | 16 | Pass (desk-checked, synthetic setup) | Fixture derived from the repository's Case 8 artifact, not a live rollout; Codex hook proposal on a documented event, permission friction without a snippet, no `settings.json` | No |
| 2026-10-29 | 17 | Pass (desk-checked; marker presence from the retyped survey) | The five 2026-09-05 rollouts lie outside the default window, so the shipped loop at 30 days lists none of them; the case now names a wider window, which the reference tells the agent to honor and report | No |
| 2026-10-29 | 18 | Pass (executed) | Store resolved by directory test while the CLI is absent | No |

Not run: no live Codex session was available on the implementing machine (the
`codex` CLI is not installed), so Cases 16 and 17 verify what the text
prescribes for a Codex-run session, not an agent following it there; and the
Codex loop with `python3` present was executed on macOS only. Running the
skill end to end inside Codex remains an open verification item.
