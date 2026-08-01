---
name: conference-planner
description: >
  Plan attendance at a multi-day conference with parallel session tracks —
  extract the full schedule, compare parallel sessions slot by slot so the
  user picks each one, register the choices to their calendar (or deliver an
  .ics file), and generate a single-file mobile HTML schedule for use at the
  venue. Use this whenever the user mentions attending a conference, tech
  event, or summit and wants help choosing sessions, building a schedule,
  planning which talks to attend, or preparing for the event — including
  follow-up requests like adding co-located/pre-conference days, registering
  sessions to a calendar, or making a phone-friendly schedule. Also use when
  the user shares a conference schedule URL and asks what to attend. Triggers
  include "plan my conference schedule", "which sessions should I attend",
  "カンファレンスの聴講計画を立てて", "どのセッションを聞くか選びたい",
  "セッション選びを手伝って", "タイムテーブルから予定を組んで",
  "カンファレンスの予定をカレンダーに登録して",
  "会場用のスケジュール表を作って".
---

# Conference Planner

Turn a conference program into a decided schedule, a calendar, and something usable on a phone at the venue.

The hard parts are not what they appear. Getting complete schedule data is harder than it looks, session titles mislead, and at the venue the binding constraint is walking between rooms rather than session content. This skill encodes those lessons.

## Scope and non-goals

Produce three things:

1. **A decided schedule** — every time slot resolved, chosen by the user
2. **Calendar events** — one per session, with enough context to be useful standing in a hallway
3. **A single-file mobile HTML** — works offline, oriented around "where do I go next"

Default to a personal version containing the user's own logistics (travel, lodging, private notes). If they later want to share or publish it, offer to produce a scrubbed copy — do not assume a shared version is wanted.

## The one rule that matters most

**The user chooses every session. Do not decide for them.**

Present the parallel options for a slot, summarize each faithfully, surface the trade-offs, then stop and wait. This is not politeness — the user knows their own context, and a plan they assembled is one they will actually follow.

Two consequences worth internalizing:

- If asked for a recommendation, give one. Unprompted, present options and stay neutral.
- The user may go quiet on the framing and just say "B". That is a decision. Confirm it, then move to the next slot.

It is easy to slip on this when a day looks minor — a pre-conference day, a community track, an evening event. Those slots get the same treatment.

## Environment Adaptation

This skill targets any agent implementing the Agent Skills spec. Instructions
below use capability terms; map them to your environment as follows.

| Capability | With native support (example) | Fallback |
|---|---|---|
| **User choice** — present numbered options, wait for an explicit selection | Structured question tool (e.g. Claude Code's `AskUserQuestion`) | Numbered options as plain text; wait for the user's reply |
| **Browser automation** — load a JavaScript-rendered page and read its network traffic, storage, or rendered text | Browser tool (e.g. Claude in Chrome) | Static fetch plus any documented API the platform exposes; when neither yields the data, ask the user to open the page and paste or screenshot the program (options 1 and 5 in `references/data-extraction.md`) |
| **Calendar integration** — read and create events on the user's calendar | Connected calendar tool (e.g. a Google Calendar connector) | Generate an `.ics` file — one `VEVENT` per event, same content rules as Phase 3 — and have the user import it |
| **Script execution** — run a helper script to verify a generated file | JavaScript runtime (e.g. `node`) | Perform the same checks by hand, following the Verification section of `references/mobile-html.md` |

---

## Phase 1: Get the complete schedule

Incomplete data poisons everything downstream. A slot with a hidden third option produces a wrong choice.

### Find every data source

Conferences fragment across sources. Assume more exist than you have found:

- **Main conference** — usually one schedule system
- **Co-located / pre-conference days** — frequently a **separate instance** of the same system, on a different subdomain. A community day, an unconference, a workshop track
- **Sponsor-hosted side events** — often an entirely independent site, sometimes only announced by email
- **Offsite sessions** — training, sprints, socials. May require separate registration

Ask the user what they registered for before starting. Registration confirmation emails are the reliable inventory. Then verify each has its own schedule.

### Extract the data

See `references/data-extraction.md` for concrete techniques per platform, and the escalation order when a page is JavaScript-rendered.

The short version: try structured data before scraping text, and scraping before manual entry. Many conference schedule apps hold the entire program in browser storage or a JSON endpoint, which yields clean data in one shot.

### Read every abstract in full

This is the step most likely to be skipped and most likely to change decisions.

**Titles and difficulty tags are unreliable.** A talk marked "Beginner" may carry the most novel content in its track. A generic title may hide a specific technical constraint that matters enormously to the user. The information that flips a choice is usually in the body of the abstract, not the title.

Read all parallel sessions for every slot the user will attend — including ones that look obviously wrong. That judgment is often based on the title.

### Verify completeness before proceeding

Build a slot × room matrix and check for holes. Rooms that appear in some slots but not others are a signal — either a genuine gap or missing data. Resolve it before moving on.

Also establish early: **will sessions be recorded?** This changes the entire calculus. If recordings are published, the unique value of being present is the Q&A and the hallway conversations, and preparation should aim at being able to ask a good question rather than at understanding the talk. If not recorded, coverage matters more. Ask, or check the event FAQ.

---

## Phase 2: Resolve slots one at a time

Work chronologically. For each slot, present every parallel option and wait.

**Announce the size of the process before the first question.** Count the slots that need a decision and state it up front, per day and in total — "Day 1 has 5 contested slots, Day 2 has 6, so 11 decisions ahead". The walk is deliberately one slot at a time so each option gets read properly; knowing the length is what makes that bearable. Restate the count when scope changes — a day added, a track dropped.

### What each option needs

- Title, speaker with affiliation, room, exact duration
- A faithful summary drawn from the abstract — not from the title. Include specific claims, numbers, and named tools, since those are what distinguish options
- Track or category if the conference uses them

### What the slot needs

Beyond the individual options, surface the structural facts:

- **Asymmetric slots** are common — one room runs a 30-minute talk while another runs two 15-minute talks. Say so explicitly, and note that the short pair can be taken together
- **Block structure** — many conferences assign each room to a community or theme for a stretch. Choosing one option may commit the next two slots by proximity. Flag this when it applies
- **Room and floor transitions** with the actual gap in minutes
- **Consecutive short talks** in the same room can be attended without decision cost. Group them
- **Hard constraints** — a hard departure time for an offsite event, a session that requires separate registration

### After the slots are resolved

Extract the **cross-cutting axes**: two to four threads that run through the chosen sessions. These are what turn a list of talks into a coherent experience, and they make individual sessions memorable.

The useful ones are often oppositions — two sessions taking incompatible positions on the same question — or progressions, where several sessions address consecutive stages of one problem. Look for sessions that share a named tool, a standard, or a failure mode.

Also worth assembling if the user wants it: a list of people to catch and what to ask each, keyed to the sessions where they appear. Note which social events immediately follow which sessions, since that is when speakers are reachable.

---

## Phase 3: Register to the calendar

Register through the calendar integration available in the environment; without one, fall back to an `.ics` file (see Environment Adaptation). Every content rule below applies to both paths.

Check existing events for the conference dates first. The user may already have blocks registered, and duplicates are worse than nothing.

**Never delete existing events without confirming.** If a previously-registered umbrella block now overlaps the detailed events, say so and ask what to do with it. On the `.ics` path existing events cannot be read — say so, and tell the user what to look for before importing.

### Event structure

One event per session. Prefix titles consistently (e.g. `[EventName] `) so the conference is scannable in a month view.

Put in the location field the specific room, not just the venue — that is what the user reads on their phone while moving.

The description carries what a hallway glance needs:

- Speaker and affiliation
- A summary of the content
- **A short pre-session reminder** — the main claim, the contrast with another session, a movement warning, what to ask. Three to five bullets. This is the highest-value part
- **The parallel sessions not chosen** — for when plans change or the user wants to find recordings later
- The session URL

### Practical shaping

- **Register travel and transitions as events**, especially tight ones and offsite departures. A 40-minute walk between venues deserves a calendar block
- **Group consecutive short talks** into one event rather than three. Three five-minute notifications is noise
- Note venue quirks that will bite: badge pickup hours, a lobby on an unexpected floor, a building with no direct connection

---

## Phase 4: Build the mobile HTML

**Start from `assets/template.html`.** It is a complete working schedule app with placeholder data: replace the data blocks at the top of its script (`EVENT`, `UI`, `FLOORS`, `URLBASE`, `DAYS`, `GLOSSARY`, `PREP`) and leave the styles and interaction code untouched, so every schedule this skill produces shares one UI. All UI label strings live in the `UI` object — set them to the user's language. Extend the template only for a feature the user asked for that it does not cover.

Read `references/mobile-html.md` for the design rationale behind the template — needed to extend it coherently.

The design principles that matter:

**No external requests.** Venue Wi-Fi degrades badly when several thousand people share it. No CDN fonts, no CDN scripts, no remote images. Everything inline, single file. It should work in airplane mode.

**Organize around movement, not content.** The question the user actually has at the venue is "where do I go next". Make the room and floor the most visually prominent element, color-code by floor, and insert transition rows automatically wherever the floor changes, showing the gap in minutes with a warning below some threshold.

**Be time-aware.** During the event, open the current day, mark the in-progress session, scroll to it, and dim what has passed.

**Include the pre-session reminder.** The same content as the calendar description, positioned as the first thing visible when a session expands.

**Avoid browser storage.** Keep state in memory so the file behaves identically in restrictive viewers. On claude.ai, the artifact preview blocks `localStorage` and the failure is silent. If the user will self-host, offer the small patch that adds persistence.

**Offer the study add-ons** rather than waiting to be asked: a searchable glossary of terms that will appear in the sessions, and per-night preparation notes. Both exist in the template as auxiliary tabs — fill them when accepted, drop the tabs when declined.

### Verify before delivering

Run `scripts/verify-template.js` against the filled file where a JavaScript runtime is available; without one, work through the Verification section of `references/mobile-html.md` by hand. A stray backtick produces a blank page and a renamed class produces unstyled markup — both are invisible until the user opens the file at the venue.

### Delivery

Ask how they intend to open it, since this determines the approach. Options include a self-hosted URL over a private network (works well if they already have that infrastructure), a static host, or a file in cloud storage as an offline fallback. Note that iOS Files previews may restrict JavaScript, so a local-HTML-capable app may be needed for the file fallback.

On claude.ai, the built-in artifact publish feature is also an option; files above roughly 64KB appear to fail there, so measure the byte length first. Reducing size means cutting content, so raise it as a trade-off rather than silently trimming.

---

## Known pitfalls

**Assuming one schedule source.** Co-located days routinely live on a separate subdomain. Sponsor events live off-platform entirely.

**Trusting titles and difficulty tags.** Read the abstracts.

**Deciding a day because it looks minor.** Pre-conference and community days get the same slot-by-slot treatment.

**Optimizing session content while ignoring geometry.** A ten-minute transition between distant floors, against the flow of a keynote hall emptying, is a real constraint. Stairs may beat elevators.

**Editing a file after presenting it.** If a file has been shown to the user and then modified on disk, the displayed version can go stale. Re-present it, or write the final version in one pass.

**Silently cutting content to meet a size limit.** State the constraint and let the user choose what goes.

**Compressing prose without verifying.** When trimming a generated file, verify afterward that scripts still parse and styles still resolve. Mechanical rename passes across CSS and template strings break easily.

**Mixing personal logistics into something shareable.** Home addresses, travel routes, lodging, employer projects, private plans. If a shared version is ever requested, scrub deliberately and verify.
