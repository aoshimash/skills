# Extracting schedule data

## Contents

- [Escalation order](#escalation-order)
- [Sessionize](#sessionize)
- [Other platforms](#other-platforms)
- [Custom event sites](#custom-event-sites)
- [Non-web sources](#non-web-sources)
- [Normalizing what you get](#normalizing-what-you-get)
- [Completeness checks](#completeness-checks)

---

## Escalation order

Try in this order. Stop as soon as you have complete data with full abstracts.

1. **Static fetch of the schedule page.** Cheapest. Works when the page is server-rendered. Often fails on modern conference sites, which render the program client-side — a fetch returns navigation and a shell with no sessions.

2. **A JSON or API endpoint.** Many schedule platforms expose one for their own front end or for embeds. If you can see the page in a browser, look at what the network tab loaded. This gives clean structured data including full abstracts.

3. **Browser storage.** Some schedule apps cache the entire program client-side so they work offline. This is often the single best source: one read yields sessions, speakers, rooms, and categories together.

4. **Text extraction from the rendered page.** Navigate with a browser tool and pull the text. Workable but lossy — abstracts get truncated, and you may need one page load per session.

5. **Manual entry from what the user can see.** Last resort. If it comes to this, ask the user to paste or screenshot the program rather than guessing.

A browser automation tool is usually required for options 2–4, since the data only exists after JavaScript runs. Without one, work options 1 and 5 plus any documented API the platform exposes (Pretalx below is the clean case) — and prefer asking the user to open the page and paste what they see over guessing at undocumented endpoints.

---

## Sessionize

Widely used, including by CNCF events. Schedule pages look like `https://<event-slug>.sessionize.com/schedule`.

**Browser storage holds everything.** After the schedule page loads, `localStorage` contains a `schedule` key with the full program as JSON:

```js
const p = JSON.parse(localStorage.getItem('schedule'));
// p.sessions   — id, title, description, startsAt, endsAt, roomId, speakers[], categoryItems[]
// p.speakers   — id, fullName, tagLine, bio
// p.rooms      — id, name
// p.categories — id, title, items[]  (tracks, difficulty levels, session formats)
```

Build lookup maps for rooms and speakers, then join. Extract in batches rather than dumping everything at once, since abstracts are long:

```js
const rooms = {}; (p.rooms||[]).forEach(r => rooms[r.id] = r.name);
const byId = {}; (p.speakers||[]).forEach(s => byId[s.id] = s.fullName);
const list = p.sessions.map(s => ({
  id: s.id,
  t: (s.startsAt||'').slice(11,16),
  e: (s.endsAt||'').slice(11,16),
  room: rooms[s.roomId] || '',
  title: s.title,
  spk: (s.speakers||[]).map(x => byId[x]).filter(Boolean).join(', ')
}));
```

Then pull descriptions for specific sessions by slicing, to stay within reasonable response sizes:

```js
const s = p.sessions.find(x => x.title.includes('<keyword>'));
(s.description || '').replace(/\s+/g, ' ').slice(0, 700)
```

**Critical: co-located events use separate Sessionize instances.** A community day or pre-conference track will have its own subdomain — for example `<event>-community-day-<year>.sessionize.com` alongside the main `<event>-<year>.sessionize.com`. Loading one does not give you the other. Check for each event the user registered for.

Room names may carry floor prefixes like `4F | 411+412`. Split these — the floor is needed for transition warnings.

---

## Other platforms

**Sched (`sched.com`)** — event sites like `<event>.sched.com`. Has an API for organizers; public schedules are often server-rendered enough for text extraction. Individual session pages carry full abstracts.

**ConfEngine** — used by many agile and regional conferences. Session pages are individually addressable and generally fetchable.

**Pretalx** — open source, common in European and community conferences. Exposes a real REST API at `/api/events/<slug>/talks/` and often an iCal feed. When present, this is the cleanest source available.

**Whova / Bizzabo / Cvent** — mobile-app-first commercial platforms. Web schedules are heavily client-rendered and sometimes require login. Expect to need browser text extraction, and expect abstracts to be truncated in list views.

**Google Sheets or Notion** as the program — occasionally used by community events. Fetchable if published; ask the user for the link.

---

## Custom event sites

Large conferences often build their own program pages over a schedule backend. The visible site and the data source may differ — a Linux Foundation event page, for instance, may render a Sessionize program.

When a custom page resists extraction:

- Look for an embedded iframe pointing at the underlying platform, then go to that platform directly
- Check for an `.ics` export or "add to calendar" links, which sometimes expose per-session data
- Check for a printable or "full schedule" view, which is more often server-rendered

Sponsor-hosted side events usually have a simple standalone page with the agenda in HTML. These are easy to fetch but easy to forget — they are announced by email rather than listed on the main site. Detail beyond the agenda (abstracts, speaker bios) is often absent; record that as unknown rather than inferring.

---

## Non-web sources

**PDF programs** — extract text; watch for multi-column layouts scrambling reading order. Cross-check the result against a rendered page image.

**Images or screenshots of a timetable** — read them directly. Confirm ambiguous times with the user rather than guessing.

**Conference mobile apps with no web equivalent** — ask the user to export or screenshot. Do not attempt to reverse engineer app APIs.

---

## Normalizing what you get

Whatever the source, land on a consistent shape per session:

| Field | Notes |
|---|---|
| id | Stable identifier from the source, for building URLs |
| start / end | Local time. Keep the timezone explicit |
| room | Split floor from room name if combined |
| floor | Needed for transition detection |
| title | |
| speakers | Name plus affiliation. Affiliation informs who to ask what |
| track | If the conference has them |
| level | Capture but distrust |
| abstract | **Full text.** Truncated abstracts cause wrong choices |
| url | Direct link to the session page |

For sessions where the source genuinely lacks abstracts, mark them as such. An empty abstract and an unfetched abstract are different states, and conflating them leads to presenting a session as thin when it is merely unread.

---

## Completeness checks

Before presenting anything for decision:

**Slot × room matrix.** Lay out every time slot against every room. Holes are either real gaps or missing data — resolve which.

**Room census.** Rooms appearing in only part of the day are suspicious. Some are genuinely used for one block; others indicate a partial extraction.

**Duration sanity.** Sessions whose duration differs from the conference norm are worth a second look. They are often keynotes, panels, lightning talk blocks, or extraction errors.

**Event inventory against registrations.** Compare the schedules you have against what the user registered for. A registered event with no schedule extracted is the most common failure.

**Timezone.** Confirm that extracted times are venue-local. Some sources store UTC.
