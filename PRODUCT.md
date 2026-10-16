# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

Mobile-first web app, installable on Android as a PWA (home-screen icon, camera access, last data viewable offline). The same app serves a desktop web view for lenders. Not a native store app; a store listing can wrap the PWA later if needed.

## Users

- **Primary: the pharmacy owner.** Runs a small neighborhood pharmacy in Bangladesh, buys from 10–50 pharma suppliers, keeps records on paper (supplier invoices and a handwritten sales book), and serves customers at the counter while using the app. Not a finance expert. Job: know where the money stands, avoid cash crunches before big supplier payments, stop losing money to expiring stock, and borrow only when needed, at the lowest cost.
- **Secondary: a lender reviewer** (bank, mobile-wallet lender, or distributor finance partner). Sees a pharmacy's credit passport only after the owner consents, and decides on an application. Uses a desktop.

## Product Purpose

LaMP is an AI finance officer for neighborhood pharmacies. It turns photographed supplier invoices and sales-book pages into real accounts, manages cash across many suppliers, recovers money tied up in expiring stock, and builds a cheapest-first funding plan when a shortfall is coming. Success: the owner sees a clear financial picture within minutes of onboarding, avoids at least one cash crunch or expiry loss, and pays less for credit than they otherwise would.

## Positioning

- Neutral across all of a pharmacy's suppliers, not tied to one distributor's financing.
- Pharmacy-specific: batches, expiry dates and return windows drive both cash advice and credit sizing ("expiry-aware working capital").
- "The cheapest money is the cash you already have": trapped cash first, free supplier terms second, the cheapest credit last.
- The AI reads and proposes; plain code calculates every money figure; the owner approves every action.

## Operating Context

- Used at the pharmacy counter on a cheap Android phone, often in bright light, between customers, on sometimes-slow mobile data.
- Inputs are photos of paper supplier invoices and handwritten sales-book pages, which the owner reviews and corrects before saving.
- Actions (return claims, supplier extension requests, loan applications, order trims) are proposed by the owner or the copilot and only run after the owner approves.
- Lenders see data only within per-lender consent.
- Currency: Bangladeshi taka (BDT). Language: English only.

## Capabilities and Constraints

- Three jobs (FinTechathon 2026 Topic E): business financial analysis, cash-flow management and alerts, financing-option matching.
- Screens: home, capture and review, accounts, cash (forecast and supplier-dues calendar), expiry, orders, funding plan, credit passport and consent, actions inbox, copilot chat; lender inbox and passport view; live audit log.
- All money math is deterministic backend code; the AI (OpenAI `gpt-6-luna`) only reads documents and chats.
- No patient medicine data is stored; patient dues are amounts only.
- No blockchain. English only.
- Lenders, payouts and supplier replies are simulated in the current version.
- Deadline for the competition submission: 20 Oct 2026.

## Brand Commitments

- Name: **LaMP** (short for Last Mile Pharmacy). "LaMP-Copilot" is the name used in competition documents.
- No logo, colors or fonts decided yet.

## Evidence on Hand

- Demo pharmacy "Green Life Pharmacy, Bogura" with fixed, checked figures in `docs/PLAN.md` section 6 (e.g. 30-day sales BDT 412,500, net profit BDT 13,500, shortfall BDT 19,000 → 8,200 after trimming).
- No real customers, testimonials, partner lenders or pilots exist yet. Don't fabricate any.

## Product Principles

1. Show the money truth plainly: every figure in BDT, every number explained in everyday words.
2. The owner decides. The copilot proposes; nothing touches money or outside parties without an explicit approval.
3. Cheapest money first: always show what can be freed before what must be borrowed.
4. Trust is earned with evidence: show where each number came from (which invoice, which page).
5. Built for the counter: fast, readable at a glance, usable one-handed between customers.

## Accessibility & Inclusion

- Cheap Android phones: small screens (from 360 px wide), modest CPU, slow or patchy mobile data. Keep pages light and usable while data loads.
- Bright shop lighting: strong contrast and large tap targets.
- Owners aren't finance experts: plain language, no unexplained jargon.
- Baseline: WCAG 2.2 AA.
