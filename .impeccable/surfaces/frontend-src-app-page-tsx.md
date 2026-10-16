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
THESIS: The shop's money printed like its own shelf: every section is a medicine carton face with an identity band, every date and code an inkjet stamp. It refuses the grey-card, single-blue-accent fintech dashboard.

OWN-WORLD: White carton board on a cool shelf grey ground; identity bands in carton print colours: alert red #D93A2B, cash blue #1E5BB8, stock green #23895A, warning amber #B86A00, ink #1F2328. Barlow for all UI; a typewriter-mono face only for stamped dates, batch and due codes. Small 4px carton corners, 1px hairlines, no shadows beyond a soft lift on press, dashed-frame stamps.

STORY: The owner opens LaMP and immediately reads whether cash holds for the next days. If not, they see why (which order, which date) and tap through to the fix: free cash first, then the cheapest credit. They approve what they agree with; everything else waits for them.

FIRST VIEWPORT: Phone 390 wide. A 6px tri-colour carton band across the top; header with LaMP wordmark and shop name. Cash carton first, red band titled "Cash alert": "Short BDT 19,000", cause line "Supplier A order BDT 60,000 · cash that day BDT 41,000", a DUE 26 OCT stamp, and the primary button "See the fix" at thumb height. Then the blue payments carton (three next dues with stamped dates), then the green expiring-stock carton (BDT 18,400 with an EXP stamp). Bottom tab bar: Today, Cash, Capture, Stock, Funding. Desktop: the same cartons on a 12-column grid with a left navigation rail. Signature move: the inkjet stamp: dates, batches and dues are stamped chips, and an approved action is stamped APPROVED with its date.

FORM: Carton & Strip, position 1 on my ordered list (chosen as IMPECCABLE'S PICK). seed:c7b569297818933e. Kept disciplines: every headline number opens its source invoice or page; money in tabular figures right-aligned; suppliers keep a fixed plate in a stable order; scrolling lists name the date span in view; time-based visuals are drawn to true day scale; no day's balance may cross the cash buffer unseen.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
Logo mark beyond the wordmark; lender-view density on desktop.
