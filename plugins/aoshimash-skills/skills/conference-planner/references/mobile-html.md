# The mobile schedule HTML

> The canonical implementation is `../assets/template.html` — a complete
> working app with placeholder data. Generate a schedule by replacing its data
> blocks, not by writing new HTML, so every schedule shares one UI. This file
> records the design behind the template; read it before extending the
> template so additions stay coherent.

## Contents

- [What it is for](#what-it-is-for)
- [Hard constraints](#hard-constraints)
- [Layout: the floor rail](#layout-the-floor-rail)
- [Transition rows](#transition-rows)
- [Time awareness](#time-awareness)
- [Session cards](#session-cards)
- [Tabs](#tabs)
- [Data shape](#data-shape)
- [Implementation skeleton](#implementation-skeleton)
- [Optional: glossary](#optional-glossary)
- [Optional: preparation notes](#optional-preparation-notes)
- [Persistence](#persistence)
- [Verification](#verification)

---

## What it is for

One question, asked while standing up with a bag on one shoulder: **where do I go next, and what is this talk about.**

Everything else is secondary. A beautiful schedule that requires two taps to find the room number has failed.

---

## Hard constraints

**Zero external requests.** Venue Wi-Fi collapses under a few thousand attendees. No CDN fonts, no CDN scripts, no remote images, no analytics. System font stack only. The file must render fully in airplane mode.

**Single file.** One `.html` with inline `<style>` and `<script>`. It gets emailed, dropped in cloud storage, added to a home screen. Multiple files break all of that.

**No browser storage in the default build.** Use in-memory state so the file behaves identically in restrictive viewers. On claude.ai, the artifact preview blocks `localStorage` and `sessionStorage`, and the failure is silent. Offer a persistence patch separately if the user will self-host.

**Mobile viewport first.** Include `viewport-fit=cover` and respect `env(safe-area-inset-*)` so a sticky header does not collide with a notch.

---

## Layout: the floor rail

A two-column grid per row. Left column is narrow (~46px) and carries the floor; right column is the session card.

```
┌────┬──────────────────────────────┐
│ 5F │ 11:30–12:00 · 501            │
│ ▏  │ Session title                │
│ ▏  │ Speaker, Affiliation         │
└────┴──────────────────────────────┘
```

The floor badge is filled with a per-floor color, and a thin vertical spine in the same color runs down beside the card. Scrolling the day produces a visible color band — the user reads their movement pattern without reading any text.

Assign one distinct hue per floor plus one for offsite. Keep them saturated enough to distinguish in sunlight. A dark theme reads better in dim session rooms and uses less battery on OLED.

Non-session rows (travel, meals, registration) get a muted dashed treatment so they recede.

---

## Transition rows

Insert automatically between consecutive items whose floor differs. Compute the gap from the previous item's end to the next item's start:

```
    ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    │ 移動 5F → 3F  ┄┄┄┄┄┄┄  10分
```

Below a threshold (10 minutes works well), switch to a warning color. This is the single most useful automatic feature — it surfaces problems that are invisible when reading a schedule as a list.

UI label strings — the 移動/分 in the example above, tab names, badges — live in the template's `UI` object. Set them to the user's language; the examples in this file show a Japanese build.

Skip the row when either side is a non-venue item, to avoid noise around travel and meals.

---

## Time awareness

On load, compare today's date against the event days:

- **During the event** — open the current day's tab, add a `NOW` badge to the in-progress session, scroll it into view, and dim sessions already ended
- **Outside the event** — open the first day

Re-render on a one-minute interval so the current session advances without interaction. Provide a "jump to now" control, since the user will have scrolled away.

Guard the interval so it only re-renders when a day tab is active — re-rendering a glossary while the user is typing in a search box destroys their input.

---

## Session cards

Collapsed, a card shows time, room, title, speaker, and track. Tapping expands it.

Expanded, order the content by what is needed soonest:

1. **The pre-session reminder** — first, because it is what gets read in the 90 seconds before a talk starts. Three to five bullets: the main claim, the contrast with another session, a movement warning, what to ask. Visually distinct (tinted background, accent border)
2. **Content summary** — from the abstract
3. **Agenda** — for single-track events with an internal running order
4. **Question candidates**
5. **Notes** — why this session was chosen, connections to others
6. **Link** to the session page

The reminder being first is deliberate. Descriptions are read the night before; reminders are read in the doorway.

---

## Tabs

One per event day, then auxiliary tabs. Keep them in a horizontally scrolling sticky row with the scrollbar hidden.

Auxiliary tabs worth having, in rough priority: preparation notes, glossary. Resist adding more — every tab is a swipe between the user and their room number.

---

## Data shape

Keep all content in plain data structures at the top of the script, separate from rendering. Editing content should never require touching layout code.

```js
const DAYS = [{
  id: "d1", label: "7/29 水", date: "2026-07-29", sub: "Day 1",
  items: [{
    t: "11:30", e: "12:00",        // start, end — "HH:MM"
    f: "5F", room: "501",           // floor drives color and transitions
    title: "…",
    spk: "Speaker, Affiliation",
    n: "Track",                     // small tag
    plain: false,                   // true = muted row (travel, meals)
    body: {
      pre:  ["…"],                  // pre-session reminder bullets
      d:    "…",                    // content summary (may contain <b>)
      prog: ["…"],                  // agenda, for single-track events
      ask:  "…",                    // question candidate
      note: "…",                    // rationale, cross-references
      id:   "…"                     // session id for URL construction
    }
  }]
}];
```

Floor-to-color mapping lives in a small lookup so adding a floor is one line.

---

## Implementation skeleton

```js
const FC = {"1F":"var(--f1)","3F":"var(--f3)","5F":"var(--f5)","OFF":"var(--off)","—":"var(--none)"};
const toMin = t => { const [h,m] = t.split(":").map(Number); return h*60+m; };
const esc = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;");

function nowInfo() {
  const n = new Date();
  const p = x => String(x).padStart(2,"0");
  return { date: `${n.getFullYear()}-${p(n.getMonth()+1)}-${p(n.getDate())}`,
           mins: n.getHours()*60 + n.getMinutes() };
}

function renderDay(day) {
  const { date, mins } = nowInfo();
  const isToday = date === day.date;
  let h = "";
  day.items.forEach((it, i) => {
    const prev = day.items[i-1];
    // transition row on floor change
    if (prev && prev.f !== it.f && it.f !== "—" && prev.f !== "—") {
      const gap = toMin(it.t) - toMin(prev.e || prev.t);
      h += transitionRow(prev.f, it.f, gap, gap <= 10);
    }
    const state = !isToday ? ""
      : mins >= toMin(it.t) && mins < toMin(it.e || it.t) ? "now"
      : mins >= toMin(it.e || it.t) ? "past" : "";
    h += card(it, state, `c-${day.id}-${i}`);
  });
  return h;
}

// escape only user-visible plain text; body fields intentionally allow <b>
```

Expansion toggles a class rather than rebuilding, so scroll position survives. When a re-render is unavoidable, save `window.scrollY` and the set of open card ids, then restore both.

---

## Optional: glossary

Worth adding when sessions will use unfamiliar vocabulary and the user wants to look things up mid-talk.

A search box filtering across both term and definition, with terms grouped by domain. Tag each entry with the sessions where it appears, so the user can see why a term is present.

Include terms that will actually cause a stall — newly announced tools, project-specific jargon, acronyms introduced without expansion. Terms the user works with daily are wasted space, though when in doubt keep them: knowing a term and recalling it under time pressure are different.

When filtering re-renders the list, preserve focus and cursor position in the search input.

---

## Optional: preparation notes

If the user wants study material, organize it by **the night before** rather than by priority tier. "What do I read tonight" is the actual question; "what is most important overall" is not actionable at 23:00 after a day of talks.

Per night, list topics with an estimated reading time and the sessions each serves. Note which are essential and which can wait for the morning commute. Keep the total honest — a night after an evening event has less capacity than a night at home.

---

## Persistence

If the user self-hosts, three lines add persistence for read-state or checkboxes:

```js
// on change
localStorage.setItem('state', JSON.stringify([...doneSet]));

// on init
try { doneSet = new Set(JSON.parse(localStorage.getItem('state') || '[]')); } catch(e) {}
```

Mention this rather than including it by default. On claude.ai, the artifact preview blocks browser storage and the failure is silent.

---

## Verification

Where a JavaScript runtime is available, `../scripts/verify-template.js` performs
every check below in one pass:

```
node scripts/verify-template.js path/to/schedule.html
```

It evaluates the target file's inline script, so point it only at schedules this
skill generated. Without a runtime, confirm the same things by hand.

Before delivering, confirm mechanically:

**The script parses.** Extract the script body and construct a function from it. A stray backtick inside a template literal — easy to introduce when generating code through a shell heredoc — produces a file that renders as a blank page.

**Every class used exists in the CSS.** Collect class names from `class="..."` attributes including template-interpolated ones, collect selectors from the stylesheet, and diff. Mechanical renames across CSS and template strings break this quietly.

**The document closes properly** and tag counts balance.

**No external URLs** except session links intended to be tapped.

**No personal content** if a shared version was requested — check for addresses, routes, lodging, employer projects, private plans.

If the file will go through a size-limited publish path, measure the byte length rather than estimating.
