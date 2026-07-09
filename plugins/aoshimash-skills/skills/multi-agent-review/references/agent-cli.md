# Agent CLI Reference

## Diff Preparation

Save the diff to a temporary file to avoid pipe issues across shell invocations.

```bash
DIFF_FILE=$(mktemp /tmp/multi-review-XXXXXX)
echo "$DIFF_FILE"
```

**Important — Per-call shell isolation:**
- Most agents run each shell command in an independent shell; variables (`$DIFF_FILE`) and `trap` do not persist across tool calls.
- Read the `mktemp` output and embed the literal path in subsequent commands.
- Because `trap` does not persist, do not rely on it for cleanup — clean up explicitly (see Cleanup).

**Template suffix:** The `mktemp` template must end with `X` characters (macOS BSD `mktemp` constraint). Do not append extensions like `.diff` after the `X`s.

### PR diff

```bash
gh pr diff <PR_NUMBER> > <DIFF_FILE>
if [ $? -ne 0 ]; then
  echo "Error: gh pr diff failed"
  rm -f <DIFF_FILE>
  exit 1
fi
```

### Local diff

```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
{
  git diff "origin/${DEFAULT_BRANCH}...HEAD"
  git diff
  git diff --cached
} > <DIFF_FILE>
```

After writing the diff file, verify it is non-empty:

```bash
if [ ! -s <DIFF_FILE> ]; then
  echo "No changes found"
  rm -f <DIFF_FILE>
  exit 0
fi
echo "Diff saved to <DIFF_FILE> ($(wc -l < <DIFF_FILE>) lines)"
```

## CLI Invocation

All CLIs are run with **background execution** (see the Environment Adaptation section in SKILL.md) for parallel execution; without it, invoke the CLIs sequentially — results are identical, total wall-clock time increases. Each CLI runs in read-only / prompt mode to prevent code changes.

### Installation Check

Before invoking each CLI, verify it is installed:

```bash
command -v <cli_name> >/dev/null 2>&1
```

If not found, skip the agent and note it in the results.

### Claude CLI

```bash
claude --model opus -p \
  "<review_prompt>" \
  < <DIFF_FILE>
```

### Codex CLI

Codex `exec` may ignore stdin redirection and reference the local worktree's `git diff`. Use `cat` + pipe to pass diff content.

```bash
cat <DIFF_FILE> | codex exec -m gpt-5.3-codex -s read-only \
  "<review_prompt>"
```

### Gemini CLI

```bash
gemini --model gemini-3-pro-preview -p \
  "<review_prompt>" \
  < <DIFF_FILE>
```

## Review Prompt Template

The `<review_prompt>` placeholder is replaced with the assembled prompt containing all perspectives. The prompt structure:

```
Review the following code diff. For each issue found, output structured markdown.

## Review Perspectives
<perspectives listed here>

## Output Format
For each issue, use this format:
### [Critical/Warning/Suggestion] <title>
- **File:** path/to/file:L<line>
- **Issue:** <description>
- **Fix:** <concrete suggestion>

If no issues are found, output: "No issues found."
```

## Error Handling

| Situation | Action |
|-----------|--------|
| CLI not installed | Skip, note in results |
| CLI timeout (5 min) | Use completed results only, note timed-out agent |
| Rate limit (429 / "rate limit" / "too many requests" in output) | Wait 30s and retry once. If still failing, skip the agent |
| CLI exits with non-zero code | Skip, note the error |
| Empty output | Skip, note the agent returned no results |

## Cleanup

Delete the temp diff file on **every exit path** — success, error, or early termination.

```bash
rm -f <DIFF_FILE>
```
