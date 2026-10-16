---
name: LaMP
description: A pharmacy owner's finance officer, read like a railway departures board.
colors:
  rail-green: "#0f4d3a"
  rail-green-pale: "#cfe3d9"
  board-green: "#123d30"
  board-sub: "#d5e6dd"
  signal-yellow: "#ffd400"
  signal-ink: "#111111"
  cash-green: "#0f6b4f"
  cash-tint: "#e3f1eb"
  good-green: "#1e7a4f"
  good-tint: "#e6f3ec"
  problem-red: "#c4301e"
  problem-tint: "#fbeae7"
  needs-you-amber: "#9a5800"
  needs-you-tint: "#fdf1de"
  shelf: "#eef1f3"
  panel-white: "#ffffff"
  ink: "#1f2328"
  ink-quiet: "#4a535c"
  rule: "#dde2e6"
  field-edge: "#c9d0d6"
  muted: "#e9edf0"
  secondary: "#e4e8eb"
typography:
  display:
    fontFamily: "Barlow Semi Condensed, Barlow, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.05
  board-time:
    fontFamily: "Barlow Semi Condensed, Barlow, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.05
  headline:
    fontFamily: "Barlow, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.25
  figure:
    fontFamily: "Barlow, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.25
    fontFeature: "\"tnum\" 1, \"lnum\" 1"
  title:
    fontFamily: "Barlow, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.45
  body:
    fontFamily: "Barlow, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Barlow Semi Condensed, Barlow, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: "0.05em"
rounded:
  chip: "2px"
  stamp: "3px"
  control: "4px"
  panel: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  touch: "44px"
components:
  button-primary:
    backgroundColor: "{colors.rail-green}"
    textColor: "{colors.panel-white}"
    typography: "{typography.title}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "#0d4433"
  button-primary-lg:
    backgroundColor: "{colors.rail-green}"
    textColor: "{colors.panel-white}"
    rounded: "{rounded.control}"
    padding: "0 20px"
    height: "48px"
  button-outline:
    backgroundColor: "{colors.shelf}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "44px"
  button-outline-hover:
    backgroundColor: "{colors.muted}"
  station-board:
    backgroundColor: "{colors.board-green}"
    textColor: "{colors.panel-white}"
    typography: "{typography.display}"
    rounded: "{rounded.panel}"
    padding: "16px 18px 18px"
  carton:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "8px 16px 16px"
  stamp:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.ink-quiet}"
    typography: "{typography.label}"
    rounded: "{rounded.stamp}"
    padding: "1.6px 7.2px"
  stamp-problem:
    backgroundColor: "{colors.problem-tint}"
    textColor: "{colors.problem-red}"
  stamp-needs-you:
    backgroundColor: "{colors.needs-you-tint}"
    textColor: "{colors.needs-you-amber}"
  stamp-good:
    backgroundColor: "{colors.good-tint}"
    textColor: "{colors.good-green}"
  input-field:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 10px"
    height: "44px"
  tier-chip:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  tab-bar-item:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.ink-quiet}"
    height: "64px"
  tab-bar-item-active:
    textColor: "{colors.cash-green}"
---

# Design System: LaMP

## Overview

**Creative North Star: "The Station Board"**

The next 30 days of money read like a railway departures board. One dark-green board at the top of a screen says what happens next and when; everything below it is a calm timetable of white panels on a light neutral ground, framed by a railway-green shell (header on phones, left rail on desktop). The owner reads it at a pharmacy counter on a cheap Android phone in bright light, between customers, so the system is high-contrast, large-targeted and sparing with colour.

Colour is a signal, not decoration. The neutral ground carries about 60% of a screen, railway green about 30% (shell, primary buttons, the "go" state), and signal yellow under 10%: it appears only in the board's time cell and in the M of the wordmark. Red, amber and green mark state and nothing else. Depth is flat: panels are separated by hairline rules, not shadows.

The system rejects the grey-card, single-accent fintech dashboard, and it rejects a full-yellow board (the owner saw one in an earlier build and asked for the dark green that shipped).

**Key Characteristics:**
- One dark-green departures board per screen, at most, for the single most important message.
- Railway-green shell; white working panels on a cool light-grey shelf.
- Colour carries state only: red = problem, amber = needs you, green = go / good.
- Barlow for the interface, Barlow Semi Condensed for the board and timetable dates.
- Money in tabular figures, right-aligned, exactly as the engine returned it.
- Flat surfaces, hairline rules, 8px panel corners, 44px minimum touch targets.
- Light and dark mode; "Match device" by default.

## Colors

A cool neutral timetable framed in railway green, with one signal yellow and three state colours.

### Primary
- **Railway Green** (rail-green): the shell (phone header, desktop rail), primary buttons, the browser theme colour. Text on it is white; quiet text on it is Pale Rail Green (rail-green-pale).
- **Board Green** (board-green): the departures board background only. Its headline is white; its supporting line is Board Sub (board-sub), a pale green.

### Secondary
- **Signal Yellow** (signal-yellow): the board's time cell ("Mon 26 Oct · in 10 days") and the M of the wordmark on the green shell. Nowhere else. Signal Ink (signal-ink) is reserved for any text placed on yellow.
- **Cash Green** (cash-green): links, the active tab, the focus ring and caret, the cash-route track while cash holds. Cash Tint (cash-tint) is the accent hover wash.

### Tertiary (state)
- **Problem Red** (problem-red) with **Problem Tint** (problem-tint): shortfalls, overdue dues, suspicious documents, the short stop and dashed track on the cash route, short rows in the timetable.
- **Needs-You Amber** (needs-you-amber) with **Needs-You Tint** (needs-you-tint): items waiting for the owner's approval, due-soon stamps, uncertain OCR fields.
- **Good Green** (good-green) with **Good Tint** (good-tint): money coming in, "You kept", approved items, recoverable stock.

### Neutral
- **Shelf** (shelf): the app ground behind panels.
- **Panel White** (panel-white): panels, the phone tab bar, the desktop audit-log column, input fields.
- **Ink** (ink): primary text and figures. **Ink Quiet** (ink-quiet): secondary text, panel titles in neutral panels, inactive tabs.
- **Rule** (rule): hairline borders and list dividers. **Field Edge** (field-edge): input borders.
- **Muted** (muted) and **Secondary** (secondary): stamp and chip fills, skeletons, secondary buttons.

Dark mode is the same world after closing time: ground #101417, panels #191f24, ink #e9edf0, rules #2b333a, rail #0d3f30, board #0f3328, signal #f5cc00. State colours lighten for text (red #ff8f80, amber #f2b45c, green #7fd3a6, cash #86d4b0) and their tints darken; anything on a coloured band keeps white text.

### Named Rules
**The One Signal Rule.** Signal yellow appears in exactly two places: the time cell on the departures board and the M of the wordmark. Never as a button, highlight, badge or chart colour.

**The State-Only Rule.** Red means a problem, amber means the owner must act, green means go or good. A colour never labels a topic or a section. The audit log's tier chips are neutral grey for that reason.

**The 60 / 30 / 10 Rule.** Neutral ground about 60%, railway green about 30%, signal under 10%.

## Typography

**Display Font:** Barlow Semi Condensed (with Barlow, sans-serif)
**Body Font:** Barlow (with sans-serif)
**Label/Mono Font:** Barlow Semi Condensed, used as the `--font-board` and `font-mono` family for dates, times and stamps

**Character:** Barlow is plain and legible, closer to signage than to a bank; its semi-condensed cut is the departures-board voice, used where a line has to hold a lot in a narrow column.

### Hierarchy
- **Display** (700, 2.25rem, 1.05): the board headline ("Short BDT 19,000"). Semi-condensed. One per screen.
- **Board time** (700, 1.25rem): the signal-yellow time cell beside or below the board headline.
- **Headline** (700, 1.75rem, 2rem on desktop, 1.25): page titles.
- **Figure** (700, 1.75rem, tabular lining figures): the headline money figure inside a panel. Smaller figures use the same tabular setting at 1rem to 1.25rem.
- **Title** (600, 0.9375rem): panel titles, in Ink Quiet, or in the state colour with its icon when the panel carries a state.
- **Body** (400, 1rem, 1.45): all running text; 0.875rem for secondary lines.
- **Label** (700, 0.8125rem, 0.05em, uppercase): stamps only (dates, batch codes, due marks), set like a timetable column.

### Named Rules
**The Tabular Money Rule.** Every money figure and count uses tabular lining figures and sits right-aligned in its column, so amounts line up like a price list.

**The No-Kicker Rule.** No small tracked-uppercase line above a heading. The heading carries itself; dates and context go in a stamp or in the board's time cell, which sits inside the headline row.

## Layout

Mobile-first from 360px. On phones: a sticky railway-green header (wordmark, theme switch, passport, actions with a count, a white Ask button), a single content column with 16px gutters, and a fixed white bottom tab bar of five 64px tabs (Today, Cash, Capture, Stock, Funding). Content leaves 112px at the bottom so the tab bar never covers it.

From 1024px the header becomes a 232px railway-green left rail and content moves into a 12-column grid (typically 7 + 5) inside a 1080px column with 32px gutters. From 1280px a 340px white audit-log column docks on the right.

Spacing runs on a 4px base: 8px inside tight groups, 12px between list items and row cells, 16px panel padding and stacking gap on phones, 20px grid gap on desktop, 24px below page titles on desktop. Lists name the date span they show in the panel header.

The cash route is drawn on a true day scale: each day is the same width, so stops sit where they fall in time. Stops less than 2 days apart merge into one stop (today, the last day and the first short day always keep their own), and the merged stop's tooltip lists everything it covers.

### Named Rules
**The 44px Rule.** Every touch target is at least 44px tall: default buttons, icon buttons, header links, rail links, inputs, theme switch. Large buttons are 48px; tabs are 64px.

## Elevation & Depth

Flat. Panels sit on the shelf with a 1px rule border and no shadow; depth comes from the white-on-grey tonal step and from hairline dividers. The only box-shadow in the system is the departures board's signage frame, a 1px inner white line at 16% plus a 1px outer ring in the board's own colour, which reads as a sign edge, not lift. The desktop top bar uses a slight backdrop blur over 90% shelf so content scrolls under it cleanly.

### Shadow Vocabulary
- **Signage frame** (`box-shadow: inset 0 0 0 1px rgb(255 255 255 / 0.16), 0 0 0 1px var(--board-bg)`): the departures board only.

### Named Rules
**The No-Nesting Rule.** No filled box inside a panel. Inside a white panel, group with hairline dividers, a 2px ink rule above totals, or a full-bleed row tint for a state (the red short row), never a second filled card.

## Shapes

Small, practical corners. Panels and the board use 8px; buttons, inputs, header links and alert lines use 4px; stamps use 3px; audit-log tier chips use 2px. Pills appear only for count badges and thin bar-chart tracks. Borders are 1px hairlines; totals get a 2px ink top rule. The cash route is a 5px rounded line with circular stops: a 7px hollow green stop for today, 5.5px hollow stops for events, a 9px filled red stop ringed in ink for the first short day, and a dashed red track after it.

## Components

### Buttons
Solid, plain and large: built for a thumb at a counter.
- **Shape:** gently squared (4px).
- **Primary:** railway green with white 0.9375rem semibold text, 44px tall, 16px side padding; large is 48px tall with 20px padding and a 1rem label. One primary per screen region; on Today it is "See the fix".
- **Hover / Focus:** hover darkens the green by mixing in 12% black; focus shows a 3px cash-green ring at 50%; press nudges 1px down.
- **Outline:** shelf background, rule border, ink text; hover fills with muted grey. Used for secondary actions inside panels ("Review and approve", "Recover BDT ...").
- **Text link:** cash-green semibold with a trailing arrow, 44px tall when standalone ("Cash, day by day").

### Chips
- **Stamp:** semi-condensed 0.8125rem bold uppercase with 0.05em tracking, muted fill, quiet ink, 3px corners. Tones follow state: problem (overdue), needs-you (due soon), good (approved). Used for dates, batch codes and due marks.
- **Tier chip (audit log):** 2px corners, muted fill, ink bold xs text. Always neutral; tiers are categories, not states.
- **Count badge:** a pill in problem red with white tabular figures, on Actions only.

### Cards / Containers
- **Corner Style:** 8px.
- **Background:** panel white on the shelf.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** 1px rule.
- **Internal Padding:** 14px top, 16px sides for the head; 8px top and 16px elsewhere for the body.
- **Title:** semibold 0.9375rem in Ink Quiet with an optional right-aligned aside (date span, count). When the panel carries a state, the title takes that state colour and its icon (alert circle, hand, check circle). The state never becomes a coloured fill or band.

### Inputs / Fields
- **Style:** 44px tall, white field, 1px field-edge border, 4px corners, semibold 1rem tabular figures for amounts; label above in xs semibold quiet ink.
- **Focus:** 2px cash-green outline at a 2px offset; caret in cash green.
- **Uncertain:** amber border and amber tint, with "· check" in amber beside the label.

### Navigation
- **Phone header:** railway green, wordmark (white with a yellow M), 44px icon links with a 10% white hover and 15% white for the current page, white Ask button with green text.
- **Phone tab bar:** white, five equal tabs, 24px icons over xs semibold labels; inactive in quiet ink, active in cash green with a 3px cash-green bar along the top edge.
- **Desktop rail:** railway green, 44px links in pale rail green; hover 10% white, current page 15% white with white text.

### Departures Board (signature)
Board green, 8px corners, the signage frame, 16px top and 18px side and bottom padding. The headline is semi-condensed white at 2.25rem; the time cell sits in the same heading row in signal yellow at 1.25rem (below the figure on phones, on the right from 640px); the supporting line is pale board-sub green at 1.0625rem medium. Used at most once per screen (Today and Funding carry one) for the single message that matters most. When there is no shortfall it says so plainly ("Cash holds for 30 days").

### Cash Route and Timetable (signature)
The cash route sits at the top of the "Upcoming money" panel (see Layout for scale and merging). Under it, timetable rows run date (semi-condensed bold, weekday below), what (named from the forecast's `items`), and a signed right-aligned tabular amount; incoming money is good green, outgoing is ink. A short day's row takes a full-bleed problem tint and a red "Short ..." line under the amount.

## Do's and Don'ts

### Do:
- **Do** use one departures board per screen at most, in board green with a white headline, for the single most important message.
- **Do** keep signal yellow to the board's time cell and the wordmark's M.
- **Do** use colour for state only: problem red, needs-you amber, go or good green. Keep audit-log tier chips neutral.
- **Do** set every money figure in tabular lining figures, right-aligned.
- **Do** show every money figure exactly as the engine returned it and label rows from the forecast's `items`; the frontend never adds, subtracts or derives money.
- **Do** draw the cash route on a true day scale and merge stops less than 2 days apart.
- **Do** make every touch target at least 44px.
- **Do** support light and dark mode through next-themes with the class strategy, defaulting to "Match device".
- **Do** delete `frontend/.next` and restart the dev server after editing `globals.css` on Windows; the stale cache otherwise serves old tokens.

### Don't:
- **Don't** put a tracked uppercase kicker or eyebrow above a heading.
- **Don't** nest a filled box inside a panel; use dividers, rules or a full-bleed row tint.
- **Don't** use yellow for buttons, highlights, badges or charts, and don't make the board yellow.
- **Don't** colour a panel, chip or band by topic.
- **Don't** add shadows to panels or buttons.
- **Don't** compute, round or re-total money in the frontend.
