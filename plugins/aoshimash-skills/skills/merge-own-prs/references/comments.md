# Comments: Collect, Decide, Fix, Reply, Resolve

Detailed procedure for Phase 2 step 3 ([workflow.md](workflow.md) "2-3"). The rule it serves: **every review conversation on the PR ends with a reply, and every thread ends resolved** — whether or not code changed — and the human approves what each reply says before it is posted.

## Table of Contents

- [C-1: Collect](#c-1-collect)
- [C-2: Classify and group](#c-2-classify-and-group)
- [C-3: Propose an action and a reply](#c-3-propose-an-action-and-a-reply)
- [C-4: The human's decisions](#c-4-the-humans-decisions)
- [C-5: Implement and check the fixes](#c-5-implement-and-check-the-fixes)
- [C-6: Post replies and resolve](#c-6-post-replies-and-resolve)
- [Reply wording](#reply-wording)

## C-1: Collect

Read all three kinds, every page ([platform-github.md](platform-github.md) "Read review threads", "Read reviews and conversation comments"):

| Kind | Handled when |
|---|---|
| **Review thread** (inline, on a line or file) | it is resolved |
| **Review body** (the text submitted with a review) | a later comment by the account links to that review |
| **Conversation comment** (the PR's general timeline) | a later comment by the account links to that comment |

Collect each unhandled item whose author is not the account. Items the account wrote itself — including this skill's own earlier reviews — are not collected; an unresolved thread the account started is collected only if someone else replied in it. Outdated threads are collected like any other: the reply says what happened to that code. Empty review bodies are skipped.

The "links to" rule is why every reply this skill posts outside a thread starts with a link to the item it answers (see [Reply wording](#reply-wording)): it makes "handled" readable from the PR alone on the next round or the next run.

## C-2: Classify and group

- **Author type** — `Bot` when the author is a GitHub App or bot account, `Human` otherwise ([platform-github.md](platform-github.md) gives the field).
- **Kind of request** — a change request, a question, or a report with no request (CI summaries, coverage, plan output, deploy previews, a bot's "no issues found").
- **Group** items that make the same point, across reviewers and lines, into one item. A group is `Human` when any member is human. Keep every member's id: each one gets its reply and its thread resolved.

Self-review findings from 2-2 join here as `Bot`-type items with no thread to reply to.

## C-3: Propose an action and a reply

For each item, decide what you would do and draft the reply:

| Action | When | Reply says |
|---|---|---|
| **Fix** | the point is right and in scope | what changed and the commit (filled in after the push) |
| **Decline** | the point is wrong, already handled, or the current approach is deliberate | why the current code stays, in one or two sentences |
| **Track** | right but out of this PR's scope | that an issue was opened, with its link (created after approval) |
| **Answer** | a question with no change needed | the answer |
| **Acknowledge** | a report with no request | a one-line acknowledgement of what it reported (e.g. that the plan output matches the intent) |

A report with no request still gets a reply when it is a review (thread or review body). A conversation comment that is purely a report — an automated summary that repeats on every push — may be proposed as **No reply**, but only as a proposal the human approves in the batch; it is never dropped silently.

Scope guard: a Fix does only what the comment asks. A broader change that a comment suggests goes in as Track, or as a separate proposal in the batch.

## C-4: The human's decisions

Present proposals in the user's language. For each item show: who said it (`Human`/`Bot`, login), where (file:line or "review" / "conversation"), the point in one line, the proposed action, and the draft reply.

- **Human items — one at a time.** Ask per item (user choice): **as proposed** / **another action** (fix, decline, track, answer — the user picks; the draft is rewritten to match and shown again) / **edit the reply** (the user gives the wording). Human feedback is where judgement matters, so each gets its own decision.
- **Bot items and self-review findings — one batch.** Show them as a numbered table, then ask once (user choice): **approve all** / **change some** (the user names the numbers and the new action; changed items are shown again) / **skip all fixes** (every item becomes Decline or Acknowledge with a reason the user approves).

Human items come first, so their fixes can inform the batch. An answer that changes an action changes only that item. The decision covers the action and the reply text; the commit SHA and issue link are filled in afterwards without asking again, unless the fix ends up different from what was approved (C-5).

## C-5: Implement and check the fixes

In the PR's worktree ([targets.md](targets.md) "A local checkout per repository"):

1. Make each approved Fix. Run the repository's checks (formatter, linter, tests its docs name) until clean.
2. **Check intent.** For each Fix answering a `Human` item, a separate agent instance compares the change with the comment: does it do what was asked (intent), only what was asked (scope), and nothing else visibly (side effects). Without separate instances, check it here and mark the reply's record `SELF-REVIEWED` in the brief. `Bot` items and findings are checked here against the same three questions.
3. A fix that fails a check gets one more attempt. If it still fails, or it turned out different from the approved description, show the human the difference and ask: **post as is** / **change the fix** / **drop the fix** (the reply becomes Decline or Track, shown before posting).
4. Commit following the repository's convention (fixes may share a commit; one commit per round is fine). Push without force. A rejected push stops the fixes: report it in the brief.
5. Create the issues for Track items, each linking back to the comment.

## C-6: Post replies and resolve

After the push (so every SHA exists) and the issue creation:

1. Post each approved reply ([platform-github.md](platform-github.md) "Reply"): inside the thread for a review thread; as a conversation comment that starts with a link to the review or comment it answers, for the other two kinds. One reply per group member — a group of three threads gets three replies (the second and third may point to the first).
2. Resolve every thread that got a reply ([platform-github.md](platform-github.md) "Resolve a thread"). A thread the account cannot resolve (permission, locked) is reported in the brief.
3. Re-read the threads: none of the collected ones may still be unresolved. One that is goes to the brief as open.

## Reply wording

- **Language** — the comment's language; a group in mixed languages → the majority's.
- **Human** — one short opening thanks, then the substance. **Bot** — the substance only.
- **Content by action:**

| Action | Human | Bot |
|---|---|---|
| Fix | "Thanks — fixed in {sha}: {what changed}." | "Fixed in {sha}: {what changed}." |
| Decline | "Thanks for the note. Keeping the current approach because {reason}." | "Keeping the current approach: {reason}." |
| Track | "Good point — out of scope for this PR; tracked in {issue}." | "Out of scope; tracked in {issue}." |
| Answer | "{answer}" | "{answer}" |
| Acknowledge | "Thanks — {what was noted}." | "Noted: {what was noted}." |

- **Outside a thread** the reply starts with `Re: {link to the review or comment}` on its own line.
- Never quote secrets, tokens, or internal URLs from the diff into a reply.
