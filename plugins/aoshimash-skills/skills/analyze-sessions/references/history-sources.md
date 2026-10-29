# History Sources

Where each supported agent keeps its conversation history, how to scope it to
the current project, what its records look like, how a skill invocation shows
up in them, and which configuration surface a proposal may target. SKILL.md
Steps 1, 2, and 4 read this file; nothing product-specific lives in SKILL.md.

Every fact here carries a confirmation status, and the status decides what the
skill may do with it:

| Status | Meaning | What the skill may do |
|---|---|---|
| **documented** | Stated in the product's own documentation or source, fetched on the date given | Rely on it; cite it in the report when it matters |
| **observed** | Seen on a real installation on the date given, not found in documentation | Rely on it only after the verification step beside it passes on the machine at hand, and label it observed in the report |
| **heuristic** | A detection rule inferred from observation where the product documents no marker | Use it for discovery only, label the detection heuristic in every report that relies on it, and never let it drive a configuration snippet |
| **unconfirmed** | Neither documented nor observed | Do not act on it: report the pattern without a snippet, and point at the documentation to consult |

A product changes before this file does. A verification step that fails on
the machine at hand outranks this file: report what was found, and do not
force the recorded shape onto it.

## Resolution Order (SKILL.md Step 1)

1. A source the user named.
2. The running agent's own store, when the agent is one listed below and its
   store exists on this machine.
3. Another listed store that exists on this machine, chosen by the user.
4. None — outcome **A**.

To tell which agent you are running in, use your own environment — the product
named in your system context, or the tools you were given — not the binaries on
`PATH`. On the machine this file was verified on (2026-10-29) the Codex history
directory existed while no `codex` binary was on `PATH`. The presence or
absence of a CLI never decides whether a store exists; the directory test in
each section below does.

## Outcome States (SKILL.md Step 2)

| Outcome | Decided by |
|---|---|
| **A. History not reachable** | The store's directory test fails, or the directory cannot be read |
| **B. Unsupported format** | Files exist but the per-store parse check below fails for them (a compressed file with no decompressor on `PATH`; a first line that is not the expected record) |
| **C. No skill executions** | Files parsed, none carries the store's invocation marker |
| **D. Insufficient count** | A skill's marker appears in 1 or 2 sessions |

## Claude Code

### Location — documented

On Claude Code, each session's transcript is written to
`projects/<project>/<session>.jsonl` under the Claude Code configuration
directory, which is `~/.claude` by default or the directory `CLAUDE_CONFIG_DIR`
names (code.claude.com/docs/en/claude-directory, "Application data", fetched
2026-10-29). The same page documents that subagent transcripts live beside the
session file under `projects/<project>/<session>/subagents/` in the same format,
and that transcripts are deleted once older than `cleanupPeriodDays` (default
30 days) — so the 30-day window of Step 2 is also the most history a default
installation keeps.

### Project scoping — documented rule, observed to apply to the transcript directory

On Claude Code, `<project>` is the working directory's absolute path with every
character other than letters and digits replaced by `-`. The rule is documented
for the session scratchpad directory on the same page; that it also names the
transcript directory is observed (2026-10-29): a worktree checked out at
`/Users/you/dev/repo/.claude/worktrees/x` had its transcripts under
`-Users-you-dev-repo--claude-worktrees-x`. Note the leading `-`: an earlier
revision of this skill stripped it, derived a directory that did not exist, and
would have reported "no sessions" for a project with history — which is why
the derivation is verified rather than trusted:

```bash
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
project="$(pwd | sed 's/[^A-Za-z0-9]/-/g')"
SESSION_DIR="$CLAUDE_DIR/projects/$project"
if [ ! -d "$CLAUDE_DIR/projects" ] || [ ! -r "$CLAUDE_DIR/projects" ] || [ ! -x "$CLAUDE_DIR/projects" ]; then echo "no readable Claude Code transcript store at $CLAUDE_DIR/projects"
elif [ -d "$SESSION_DIR" ]; then echo "store: $SESSION_DIR"
else echo "no derived directory for $(pwd); entries in the store:"; ls "$CLAUDE_DIR/projects"; fi
```

The first branch is outcome **A**: the store itself is missing or unreadable.
When only the derived directory is missing, the listing shows the actual
entries: pick the one that matches the working directory, or ask the user.

### Discovery — verified command

List the 20 most recent session files from the last 30 days that carry a skill
invocation from this plugin:

```bash
find "$SESSION_DIR" -maxdepth 1 -name '*.jsonl' ! -name '*.orphaned-*' -mtime -30 -type f -print0 \
  | xargs -0 -r ls -t | head -20 | tr '\n' '\0' \
  | xargs -0 -r grep -l 'aoshimash-skills:' 2>/dev/null
```

Three details carry weight. The BSD `xargs` on macOS has no `-d` flag, hence
the `tr` step. GNU `xargs` runs its command once even on empty input, which
would turn an empty store into `ls -t` of the working directory and a `grep`
over the repository's own files — `-r` stops that on GNU `xargs` and is
accepted by the BSD one, so the same line runs on both (both executed
2026-10-29, see the Verification Log). And `! -name '*.orphaned-*'` leaves out
the previous transcripts Claude Code sets aside for a session (documented on
the page above), so one session is counted once. `-maxdepth 1` keeps subagent
transcripts (in per-session subdirectories) out of the session count; read
them for context when a session needs it.

### Record format — documented shape, observed fields

The page above documents the transcript as the conversation's messages, tool
calls, and tool results plus the request metadata Claude Code sent, one JSON
object per line. Observed (2026-10-29): each object has a top-level `type`
whose values include `user`, `assistant`, `attachment`, `last-prompt`,
`queue-operation`, `custom-title`, `pr-link`, and `mode`; the conversation is
in the `user` and `assistant` records. Parse check: the file's lines are JSON
objects with a `type` field. A file that fails it is unsupported (outcome
**B** material).

### Invocation marker — observed

Two forms, both seen in a real transcript of this plugin's `implement-issue`
run (2026-10-29):

- the invoking `user` record wraps the command as
  `<command-name>/aoshimash-skills:<skill-name></command-name>` — with a
  leading slash, so a pattern written without it misses the record;
- `assistant` records produced under the skill carry an
  `"attributionSkill":"aoshimash-skills:<skill-name>"` field.

Search for the qualified name `aoshimash-skills:<skill-name>`; it matches both
forms. Count a session once per skill.

### Permission prompts — unconfirmed record shape

No documented record shape for a permission prompt or its approval was
confirmed. Detect permission friction by the heuristic in SKILL.md Step 3
(short approval replies following a tool call) and say so in the report.

### Configuration surface — documented

On Claude Code, settings live in `~/.claude/settings.json` (user scope, every
project), `.claude/settings.json` (project scope, shared through version
control), and `.claude/settings.local.json` (project scope, personal), and the
`permissions.allow` list approves listed tool uses without a prompt while the
`hooks` setting runs commands at lifecycle points
(code.claude.com/docs/en/settings-reference and
code.claude.com/docs/en/claude-directory, fetched 2026-10-29).

| Pattern | Surface | Status |
|---|---|---|
| Permission friction | A `permissions.allow` entry in a settings file — user scope for a tool used across projects, the personal project-scope file for a project-specific one | documented |
| Hook opportunity | A `hooks` entry in a settings file, on the `SessionStart`, `PreToolUse`, `PostToolUse`, or `Stop` event | documented — hooks are defined in the JSON settings files above, and all four events are in the product's event list (code.claude.com/docs/en/hooks, fetched 2026-10-29) |

Snippet form for a permission rule (the rule syntax is the product's own):

```json
{
  "permissions": {
    "allow": ["Bash(gh api:*)"]
  }
}
```

## Codex

### Location — documented directory, observed layout

Codex keeps session rollouts under `sessions/` and archived ones under
`archived_sessions/` in its home directory — the constants `SESSIONS_SUBDIR`
and `ARCHIVED_SESSIONS_SUBDIR` in `codex-rs/rollout/src/lib.rs` of
`openai/codex` (read 2026-10-29). The home directory is `~/.codex` unless
`CODEX_HOME` names another (learn.chatgpt.com/docs/agent-configuration/agents-md,
fetched 2026-10-29). Observed layout (2026-10-29):
`sessions/<YYYY>/<MM>/<DD>/rollout-<timestamp>-<id>.jsonl`, with most files
compressed as `.jsonl.zst`. The configuration reference documents a separate
`history.jsonl` controlled by `history.persistence` ("Control whether Codex
saves session transcripts to history.jsonl",
learn.chatgpt.com/docs/config-file/config-reference, fetched 2026-10-29);
observed, its records carry only `session_id`, `text`, and `ts` — prompt
lines, not a transcript — so use it to locate a session, never as the
conversation.

```bash
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
if [ -d "$CODEX_DIR/sessions" ]; then echo "store: $CODEX_DIR/sessions"; else echo "no Codex session store at $CODEX_DIR/sessions"; fi
```

Reading this store needs two ordinary tools that are not assumed: `python3`
(any 3.x) for the parse check in the scoping loop, and `zstd` for compressed
rollouts. The commands below say which one is missing; the skill then reports
rather than guessing.

### Compressed rollouts — observed

A `.jsonl.zst` file needs `zstd` on `PATH` (`zstd -dc "$f"`); without it,
those files are outcome **B** material: count them, continue with the plain
`.jsonl` files if any, and tell the user that installing `zstd` makes the rest
readable. Decompress to a pipe or to a location outside the repository — never
into the working tree.

### Project scoping — observed

The first record of a rollout is a `session_meta` record whose `payload.cwd` is
the session's working directory (observed 2026-10-29 across every rollout on
the verification machine). Scope by comparing `cwd` with the working directory
— a session started in a subdirectory counts, one started in another worktree
of the same repository does not, which is the same per-directory rule Claude
Code's project directory applies — reading only the first line of each file:

```bash
cwd_here="$(pwd)"
command -v python3 >/dev/null 2>&1 || echo "python3 is not on PATH: the parse check cannot run, so every file below counts as unparsed — stop and report" >&2
find "$CODEX_DIR/sessions" -type f \( -name '*.jsonl' -o -name '*.jsonl.zst' \) -mtime -30 -print0 \
  | { read_n=0; unparsed=0; unsupported=0
      while IFS= read -r -d '' f; do
        case "$f" in
          *.zst) if command -v zstd >/dev/null 2>&1; then first="$(zstd -dc "$f" 2>/dev/null | head -1)"; else unsupported=$((unsupported+1)); continue; fi;;
          *) first="$(head -1 "$f")";;
        esac
        if cwd="$(printf '%s' "$first" | python3 -I -c 'import json,sys; o=json.loads(sys.stdin.read()); p=o.get("payload"); ok=o.get("type")=="session_meta" and isinstance(p,dict) and "cwd" in p; print(p["cwd"]) if ok else sys.exit(1)' 2>/dev/null)"; then
          read_n=$((read_n+1))
          case "$cwd" in "$cwd_here"|"$cwd_here"/*) printf '%s\0' "$f";; esac
        else
          unparsed=$((unparsed+1))
        fi
      done
      echo "rollouts read: $read_n; unparsed (first line not a session_meta record with a cwd): $unparsed; unsupported (.zst without zstd): $unsupported" >&2; } \
  | xargs -0 -r ls -t | head -20
```

The listing on stdout is the scoped session set, already cut to the 20 most
recent by modification time as Step 2 says; the summary line on stderr is what
separates the outcomes:

| Summary | Outcome |
|---|---|
| Files listed | Proceed with them; carry non-zero `unparsed` / `unsupported` counts into every later message |
| Nothing listed, `rollouts read` > 0 | **C** with N = 0 for this working directory — say so, and offer the store's other working directories (the distinct `cwd` values) rather than widening the scope silently |
| All three counts 0 | **C** with N = 0 — the store holds nothing in the window |
| `rollouts read` = 0 and `unparsed` + `unsupported` > 0 | **B** — name both counts and what would make the files readable |
| The `python3` line printed | Nothing was parsed: stop and report that the parse check needs `python3` |

The parse check is inside the loop: a first line that is not JSON, not a
`session_meta` record, or has no `cwd` — including the empty line a failed
decompression leaves — is counted as `unparsed`, never as a session without
executions. The `-I` flag keeps the interpreter from importing a `json.py`
planted in the repository being analyzed, since the loop runs from that
working directory. When the user names a wider window than 30 days, change
`-mtime -30` to match and say so in the report's history line.

### Record format — observed

One JSON object per line with `type`, `payload`, `timestamp`, and `ordinal`
(2026-10-29). Observed `type` values: `session_meta`, `turn_context`,
`event_msg`, `response_item`, `token_usage_record`, `world_state`. The
conversation turns are `response_item` records whose `payload.type` is
`message`, with `payload.role` of `user`, `assistant`, or `developer`;
`event_msg` records carry lifecycle events such as `task_started` and
`task_complete`. No documentation of this shape was found in the Codex
documentation on 2026-10-29. Parse check: the first line is a JSON object with
`type` equal to `session_meta`. A file that fails it is unsupported.

### Invocation marker — heuristic

Codex documents how a skill is invoked — `$<skill-name>` in a prompt, or
implicitly by description (learn.chatgpt.com/docs/build-skills, fetched
2026-10-29) — but not how an invocation is recorded. Observed (2026-10-29):
user text containing `$<skill-name>`, and the skill's `SKILL.md` path appearing
in `developer`-role messages and in `session_meta` once the skill was loaded.
Search for both `$<skill-name>` and `<skill-name>/SKILL.md`, count a session
only when the match is tied to this plugin (the `aoshimash-skills` path
segment, or an exact skill name from this plugin), and report the detection as
heuristic.

### Configuration surface — documented

User-level configuration lives in `~/.codex/config.toml`; a project-scoped
`.codex/config.toml` loads only in trusted projects
(learn.chatgpt.com/docs/config-file/config-reference, fetched 2026-10-29).
Lifecycle hooks are configured in `~/.codex/hooks.json` or an inline `[hooks]`
table in `config.toml`, or per project in `<repo>/.codex/hooks.json`, which
loads only when the project's `.codex/` layer is trusted; the documented events
are `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`,
`PostToolUse`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`,
`Stop`, `Interrupt`, and `SessionEnd`, and hooks are enabled by default
(learn.chatgpt.com/docs/hooks, fetched 2026-10-29).

| Pattern | Surface | Status |
|---|---|---|
| Hook opportunity | `hooks.json` (user or project) or `[hooks]` in `config.toml`, on one of the documented events above | documented for the file locations and event names; the entry's JSON/TOML shape was not confirmed — take it from the hooks page at proposal time and say so in the proposal |
| Permission friction | A per-command allow rule in user configuration | unconfirmed — the configuration reference showed only administrator-enforced `rules.prefix_rules` in `requirements.toml`, which can prompt or forbid but never allow. Report the pattern with its evidence and point at the Codex sandbox-and-approvals documentation; produce no snippet |

## User-Provided History

A path the user gives — a file or a directory, scanned non-recursively for
`*.jsonl` and `*.jsonl.zst` unless the user says otherwise. Decide the format
from the first line of a file, then apply that store's section above:

| First line | Treat as |
|---|---|
| A JSON object with `type` `session_meta` and a `payload.cwd` | Codex rollout |
| A JSON object with a `type` of `user`, `assistant`, or one of the other Claude Code values above | Claude Code transcript |
| Anything else | Outcome **B**: report the first record's keys (structure, not content) and ask the user how roles and text are encoded. Never infer findings from a file that was not parsed |

Project scoping does not apply unless the user asks for it: an export is
analyzed as given.

## Verification Log

Commands in this file were run as written — extracted from this file, not
retyped — on 2026-10-29. macOS 27 (BSD `xargs`, bash and zsh) against the real
stores on the verification machine; Linux in local `ubuntu:24.04` (GNU
findutils 4.9.0) and `debian:12` (no `python3`) containers against scratch
stores. Counts only; no session content was read into this record.

| Check | Result |
|---|---|
| Claude Code derivation + directory test, from a worktree path (macOS) | Derived `-Users-…-skills--claude-worktrees-…`; directory exists. The earlier derivation (leading `-` stripped, `.` kept) named a directory that does not exist |
| Claude Code store test with `CLAUDE_CONFIG_DIR` pointed at an empty directory, and at one whose `projects/` has mode 000 | `no readable Claude Code transcript store at …/projects` in both cases (outcome **A**); no listing attempted |
| Claude Code discovery pipeline (macOS, bash and zsh) | 8 recent transcripts carried a marker in the worktree's directory, 1 in the main checkout's; identical under both shells. In that transcript the marker appeared in both forms described above, and the skill's earlier pattern (no leading slash) matched neither |
| Claude Code discovery pipeline on an empty project directory, with a file containing the marker in the working directory | macOS: no output. `ubuntu:24.04`, GNU `xargs`: no output as shipped; the same pipeline with `-r` removed listed the working directory's `CLAUDE.md` as a session file — the failure `-r` prevents |
| Codex store test (macOS) | `sessions/` present under `~/.codex` while `codex` was not on `PATH` |
| Codex store test with `CODEX_HOME` pointed at an empty directory | `no Codex session store at …/sessions` (outcome **A**) |
| Codex scoping loop, this worktree as the working directory (macOS, bash and zsh) | `rollouts read: 22; unparsed: 0; unsupported: 0`, nothing listed — outcome **C** with N = 0 for this directory |
| Codex scoping loop with `zstd` hidden from `PATH` | `rollouts read: 4; unparsed: 0; unsupported (.zst without zstd): 18` — the 4 plain files are still read, the 18 compressed ones counted as unsupported |
| Codex scoping loop with `python3` hidden from `PATH` (macOS), and in `debian:12` which ships none | The `python3` line printed; every file counted as unparsed (`read: 0; unparsed: 22` on the real store, `read: 0; unparsed: 1` on the scratch store); nothing listed |
| Codex scoping loop on a scratch store holding seven files | Listed: the `session_meta` rollout whose `cwd` is the working directory and the compressed one whose `cwd` is a subdirectory of it, most recent first; not listed: the `session_meta` rollout for another directory (read, out of scope) and a `response_item` first line carrying this directory's `cwd` (unparsed). Summary `read: 3; unparsed: 4` — the wrong-type, non-JSON, empty, and corrupt-`.zst` files are the 4 unparsed |
| Codex `history.jsonl` keys | `session_id`, `text`, `ts` only |
