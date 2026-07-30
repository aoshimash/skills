# Evaluation Test Cases

Cases 1–6 evaluate the planning flow (extraction → slot resolution), cases
7–8 the calendar phase, cases 9–11 the mobile HTML phase, and case 12 the
personal/shared boundary.

## How to Run

1. Start a new conversation and trigger the conference-planner skill.
2. Provide the case's initial input; answer follow-ups as the persona would.
3. Score the run against the Criteria below.
4. Record the run in the Evaluation Log at the bottom.

## Criteria

| # | Criterion | Pass condition |
|---|---|---|
| 1 | User decides every slot | Parallel options are presented neutrally; a recommendation appears only when the user asked for one; no slot is auto-decided — including pre-conference/community days and evening events |
| 2 | Process size announced | Before the first slot question, the number of decisions is stated per day and in total; the count is restated when scope changes |
| 3 | Slot-by-slot pacing | One slot per round, chronological; a terse answer ("B") is confirmed and the flow advances; slots are never batched into one mega-question |
| 4 | Source inventory from registrations | The user is asked what they registered for; co-located/pre-conference days are checked as separate schedule instances; sponsor/offsite events are considered |
| 5 | Abstracts read in full | Every parallel option's summary is drawn from the abstract body, with specific claims/numbers/tools; titles and difficulty tags are never the basis of a summary |
| 6 | Completeness verified | A slot × room matrix (or equivalent) is checked before decisions start; recording availability is established early |
| 7 | Calendar hygiene | Existing events on the conference dates are checked first; nothing is deleted without confirmation; events carry room in location, pre-session reminder + unchosen parallels in description; travel blocks registered; consecutive short talks grouped |
| 8 | Calendar fallback | Without a calendar integration, an `.ics` file is produced with the same content rules, and the user is warned that duplicates cannot be detected on this path |
| 9 | Template-based HTML | The mobile HTML is generated from `assets/template.html` by replacing only the data blocks; UI labels set to the user's language via `UI`; no external requests; no browser storage in the default build |
| 10 | Product notes stay conditional | claude.ai-specific behavior (artifact preview storage block, ~64KB publish limit) is applied only when that product is in play, never presented as universal |
| 11 | Study add-ons offered | Glossary and per-night preparation notes are proactively offered; included only when accepted; tabs dropped when declined |
| 12 | Personal by default, scrubbed on request | Personal logistics are included by default; a shared version is produced only on request, deliberately scrubbed and verified |
| 13 | Extraction degrades gracefully | Without browser automation, the flow uses static fetch / documented APIs, then asks the user to paste or screenshot — never guesses schedule data |
| 14 | Size limits surfaced | When a size constraint bites, the trade-off is raised and the user chooses what is cut; content is never trimmed silently |

## Planning Flow Cases

### Case 1: Schedule URL with a "what should I attend" ask

- **Persona**: Engineer attending a two-day conference, shares the Sessionize
  schedule URL and asks "どのセッションを聞けばいい?"
- **Expected behavior**: registration inventory question first; extraction via
  the escalation order; slot × room matrix and recording status before any
  decision; then slot-by-slot walk where the explicit "which should I attend"
  ask licenses a per-slot recommendation — but every pick is still confirmed
  by the user.
- **Criteria**: 1, 2, 4, 5, 6

### Case 2: Count announcement and pacing

- **Persona**: Attendee with the schedule already extracted in-conversation
- **Expected behavior**: before the first slot question, the decision count is
  announced per day and in total; each round covers exactly one slot with all
  parallel options, structural facts (asymmetric slots, block structure,
  transitions), and no recommendation unless asked.
- **Criteria**: 1, 2, 3

### Case 3: Terse mid-flow answers

- **Persona**: User who replies "B", then "2つ目", without further comment
- **Expected behavior**: each terse reply is treated as a decision, confirmed
  in one line, and the next slot is presented — no re-litigation, no skipping
  ahead to batch the remaining slots.
- **Criteria**: 3

### Case 4: "The community day doesn't matter"

- **Persona**: User who says the pre-conference community day can be decided
  automatically ("適当でいいよ")
- **Expected behavior**: the day still gets the slot-by-slot treatment; the
  agent may compress presentation but does not silently pick sessions; the
  community day's schedule is fetched from its own instance (separate
  subdomain), not assumed to be inside the main program.
- **Criteria**: 1, 3, 4

### Case 5: Extraction without browser automation

- **Persona**: User on an agent with no browser tool; the schedule page is
  client-rendered so a static fetch returns an empty shell
- **Expected behavior**: static fetch attempted; documented APIs considered
  (e.g. Pretalx); then the user is asked to open the page and paste or
  screenshot the program. No session data is invented; unfetched abstracts
  are marked as unfetched, not treated as empty.
- **Criteria**: 5, 13

### Case 6: Hidden third option

- **Persona**: User whose extracted slot shows two rooms, but the room census
  shows a third room active in adjacent slots
- **Expected behavior**: the hole in the slot × room matrix is resolved
  (re-extraction or explicit confirmation that the room is dark) before the
  slot is presented for decision.
- **Criteria**: 5, 6

## Calendar Cases

### Case 7: Existing umbrella block

- **Persona**: User whose calendar already holds an all-day "Conference" block
  on both days
- **Expected behavior**: existing events are read before writing; the overlap
  is reported and the user is asked what to do with the umbrella block —
  nothing is deleted or duplicated without confirmation. Events follow the
  structure rules (prefix, room in location, reminder + unchosen parallels in
  description); travel blocks and grouped short talks appear.
- **Criteria**: 7

### Case 8: No calendar integration

- **Persona**: User on an agent with no calendar tool connected
- **Expected behavior**: an `.ics` file is generated with one VEVENT per
  event, same content rules; the user is told existing events could not be
  checked and what to look for before importing.
- **Criteria**: 7, 8

## Mobile HTML Cases

### Case 9: Standard build

- **Persona**: User asking for the venue schedule file ("会場用のHTMLを作って")
- **Expected behavior**: output is `assets/template.html` with only the data
  blocks replaced; UI strings in the user's language; transition rows appear
  where floors change with warnings on tight gaps; glossary and prep-note
  add-ons are offered before building; delivery method is asked.
- **Criteria**: 9, 11

### Case 10: Publish on claude.ai with a large file

- **Persona**: User on claude.ai whose filled schedule exceeds 64KB and who
  asks to publish it as an artifact
- **Expected behavior**: byte length is measured; the limit is raised as a
  trade-off with options for what to cut; nothing is trimmed silently. On any
  other delivery path the 64KB note never appears.
- **Criteria**: 10, 14

### Case 11: Self-host persistence

- **Persona**: User who will host the file on their home server and wants
  checked-off sessions remembered
- **Expected behavior**: the default build ships without browser storage; the
  persistence patch is offered as a separate addition for the self-hosted
  copy, with the claude.ai preview limitation explained only if that context
  applies.
- **Criteria**: 9, 10

## Boundary Case

### Case 12: "Share it with my team"

- **Persona**: User who, after receiving a personal schedule containing hotel
  and travel details, asks for a version to share with colleagues
- **Expected behavior**: a scrubbed copy is produced deliberately — personal
  logistics, private notes, and employer-sensitive content removed — and the
  scrub is verified before delivery; the personal version is left intact.
- **Criteria**: 12

## Evaluation Log

### 2026-07-30 — Initial import (desk-check)

Skill imported into the repository from a standalone `.skill` package, with
these changes: Environment Adaptation section added (user choice, browser
automation, calendar integration — each with a fallback); `.ics` fallback for
Phase 3; claude.ai-specific notes made conditional; decision-count
announcement added to Phase 2; Japanese triggers added to the description;
canonical `assets/template.html` added and Phase 4 rewritten around it;
placeholder session id and UI-language note fixed in `mobile-html.md`.

`assets/template.html` verified mechanically per the Verification section of
`mobile-html.md`: script body parses (`new Function`), every class emitted by
the render code exists in the stylesheet, no external URLs, 18,858 bytes.

Desk-check of the cases against the skill text (static inspection):

| Case | Result | Notes |
|------|--------|-------|
| 1 | Pass | Phase 1 "Ask the user what they registered for"; matrix + recording checks; "If asked for a recommendation, give one" |
| 2 | Pass | Phase 2 "Announce the size of the process before the first question" |
| 3 | Pass | "The user may go quiet … That is a decision. Confirm it, then move to the next slot" |
| 4 | Pass | "Deciding a day because it looks minor" pitfall; co-located separate-instance warnings in SKILL.md and data-extraction.md |
| 5 | Pass | Environment Adaptation browser-automation fallback; data-extraction.md escalation note + "unfetched ≠ empty" |
| 6 | Pass | "Verify completeness before proceeding" + data-extraction.md room census |
| 7 | Pass | Phase 3 duplicate check + "Never delete existing events without confirming" + event structure rules |
| 8 | Pass | Phase 3 `.ics` path + "existing events cannot be read — say so" |
| 9 | Pass | Phase 4 "Start from `assets/template.html`" + template's UI object + add-on offer |
| 10 | Pass | claude.ai notes are prefixed "On claude.ai," in SKILL.md and mobile-html.md |
| 11 | Pass | "Avoid browser storage" principle + mobile-html.md Persistence section |
| 12 | Pass | Scope section personal default + "Mixing personal logistics" pitfall + mobile-html.md verification item |

All 12 cases pass the desk-check. This entry records a static evaluation
(instructions inspected against expected behavior); no live conversational
run was performed for the import. Cases 1 (full extraction against a live
Sessionize instance) and 9 (template fill on a real program) exercise the
highest-risk paths and are the first candidates for a live run.
