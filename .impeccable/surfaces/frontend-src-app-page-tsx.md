---
version: 1
slug: "frontend-src-app-page-tsx"
primary_target: "frontend/src/app/page.tsx"
related_targets: ["frontend/src/app"]
---

## Scope
LaMP owner app (all owner screens) plus the lender view, mobile-first web/PWA. Mode: Operate.

## Audience, job, constraints
Pharmacy owner at the counter on a cheap Android phone in bright light, between customers. Job: see the cash coming, fix shortfalls, stop expiry losses, borrow cheapest. Not a finance expert. Avoid: bank-like, toy-like, too dense. First thing seen: cash in the next days.

## Direction contract
THESIS: The next 30 days of money read like a departures board: one dark-green departures board says what happens next and when; the rest is a calm timetable. It refuses the grey-card, single-accent fintech dashboard. (Owner switched from Carton & Strip to the roll's assigned Station Board after seeing the first build, then asked for the board to be dark green because full yellow looked weird.)

OWN-WORLD: Railway-green shell (#0F4D3A header and desktop rail, white text), light neutral ground with white working panels, one dark-green departures board (#123D30 light / #0F3328 dark, white headline, pale-green sub line, signal-yellow #FFD400 kicker only) used once per screen for the single most important message. Yellow appears nowhere else except the M in the wordmark. Barlow for UI, Barlow Semi Condensed for the board and timetable dates. Colour is state only: red = problem, amber = needs you, green = go/good. Neutral 60 / green 30 / signal 10.

STORY: The owner opens LaMP and the board tells them the next money event that matters ("Short BDT 19,000 on Mon 26 Oct"). Below, a timetable of upcoming money with the cash route line; one green button leads to the fix: free cash first, then the cheapest credit. They approve what they agree with.

FIRST VIEWPORT: Phone 390 wide. Green header: LaMP wordmark (yellow M), theme, Actions with count, white Ask button. Dark-green departures board: yellow kicker "Next stop · Mon 26 Oct · in 10 days", "Short BDT 19,000", cause line. Green "See the fix" button, text link "Cash, day by day". White "Upcoming money" panel: cash route line (true day scale, red stop at the short day, dashed red track after it) and timetable rows (date + weekday, what, signed amount; short rows tinted red). Bottom tab bar. Desktop: green left rail, content grid, audit log column. Signature move: the station board plus the cash route line.

FORM: Station Board, position 7 on my ordered list (the roll's assigned direction). seed:c7b569297818933e. Kept disciplines: every headline number traceable to its source; money in tabular figures right-aligned; suppliers keep a stable order; lists name the date span in view; time drawn to true day scale; no day's balance crosses the buffer unseen.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
Logo mark beyond the wordmark; lender-view density on desktop.
