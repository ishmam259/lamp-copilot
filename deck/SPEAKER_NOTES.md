# Speaker notes: LaMP-Copilot deck

The talk script for `LaMP-Copilot.pptx`. It is kept out of the slides on purpose. Target: **9:30**, which leaves 30 seconds of slack under the 10:00 hard limit. Rehearse with a timer.

Dense slides (Green Life, security, competition, revenue, feasibility, roadmap) carry more detail than you say aloud. Say the headline numbers and move on; the judges can read the rest in the PDF.

| # | Slide | Time | Running |
|---|---|---|---|
| 1 | Title | 0:15 | 0:15 |
| 2 | Hook | 0:15 | 0:30 |
| 3 | Situation analysis | 0:30 | 1:00 |
| 4 | Meet Green Life | 0:25 | 1:25 |
| 5 | Problem: local pharmacies | 0:25 | 1:50 |
| 6 | Problem: lenders | 0:20 | 2:10 |
| 7 | Three-way deadlock | 0:15 | 2:25 |
| 8 | Core issue statement | 0:15 | 2:40 |
| 9 | Solution reveal | 0:20 | 3:00 |
| 10 | One answer for each pain | 0:30 | 3:30 |
| 11–15 | How LaMP works, steps 1–5 | 2:20 | 5:50 |
| 16 | The copilot, live | 0:25 | 6:15 |
| 17 | System flow | 0:30 | 6:45 |
| 18 | Trust mechanism | 0:25 | 7:10 |
| 19 | Security and compliance | 0:25 | 7:35 |
| 20 | What makes it new | 0:20 | 7:55 |
| 21 | Competitive landscape | 0:20 | 8:15 |
| 22 | Revenue model | 0:20 | 8:35 |
| 23 | Feasibility | 0:15 | 8:50 |
| 24 | Action plan and roadmap | 0:25 | 9:15 |
| 25 | Closing | 0:15 | 9:30 |

---

## 1. Title (0:15)
Hello, we're team LaMP, short for Last Mile Pharmacy. Our entry for Topic E is LaMP-Copilot: an AI finance officer for the small neighbourhood pharmacies of Bangladesh.

## 2. Hook (0:15)
Last month, Green Life Pharmacy in Bogura sold 412,500 taka of medicine and kept only 13,500. The owner couldn't see that, because every number lived in a stack of paper.

## 3. Situation analysis (0:30)
Bangladesh makes its own medicine: about 213 working manufacturers cover about 98% of demand in a market of about 3.3 billion dollars. But medicine reaches people through more than 173,000 licensed pharmacies. Each one buys on credit from 10 to 50 drug companies, on margins of 10 to 15%, and all of it on paper.

## 4. Meet Green Life (0:25)
Green Life is our example shop, and every number in this deck is reproduced exactly by our code. It made a 13,500 taka profit last month. It has 18,400 taka of stock expiring within 60 days. And Supplier A's 60,000 taka order is due on 26 October, when it will only have 41,000.

## 5. Problem: local pharmacies (0:25)
For the pharmacy, the core issue is that it runs a credit business with dozens of suppliers on paper. The owner can't see profit or dues, gets caught short before big orders, loses expired stock, and when they borrow, they can't tell which option is cheapest, or whether they need to borrow at all.

## 6. Problem: lenders (0:20)
Lenders want small-business borrowers, but a paper-based pharmacy gives them nothing to underwrite. They have no history to assess, and they can't tell whether a paper invoice is real or already financed. And since the 2025 data ordinance, they also need explicit consent.

## 7. Three-way deadlock (0:15)
So everyone waits. The pharmacy can't prove itself, the lender can't see it, and the manufacturer carries the gap.

## 8. Core issue statement (0:15)
The evidence of a working business already exists: invoices, payments, expiry dates. It's just trapped on paper, so no one can act on it in time.

## 9. Solution reveal (0:20)
Our answer is LaMP-Copilot, an AI finance officer on the owner's phone. One principle drives it: the cheapest money is the cash you already have. Free up trapped cash first, ask suppliers for free time next, and borrow only what's left.

## 10. One answer for each pain (0:30)
Each pain gets an answer, and each answer is measured at Green Life. Reading the paper shows the real 13,500 profit. Expiry tracking recovers 9,200 taka, which is 68% of a month's profit. The forecast catches the 19,000 shortfall ten days early and cuts it to 8,200. Finance then costs 0 to 182 taka instead of 422. Every one of those numbers comes from plain code, not the AI.

## 11. Step 1, capture (0:28)
Step one: the owner photographs invoices and sales-book pages, and a vision model reads them. Uncertain fields are highlighted, plain code checks the totals, and the owner confirms before anything is saved. Text in a photo is treated as data: a planted "approve the maximum loan" is flagged and ignored.

## 12. Step 2, understand (0:28)
Step two: from confirmed records, LaMP's engines build real accounts, including profit, margin, stock days and expiring stock. At Green Life that finds 9,200 taka still returnable, and LaMP drafts the return claims with the invoice attached.

## 13. Step 3, anticipate (0:28)
Step three: a 30-day forecast across all 23 suppliers. It sees that on Monday 26 October the 60,000 taka order meets only 41,000 of cash. That's a 19,000 shortfall, flagged ten days ahead.

## 14. Step 4, fund (0:28)
Step four: cheapest money first. One order line is 30 boxes of a slow mover, but only 12 will sell before expiry. Trimming it saves 10,800, and the gap falls to 8,200. For the rest, LaMP prices every option. Asking the supplier for 20 more days is free, a wallet loan costs 182, and bank supplier credit costs 492, which is 6% of the gap against 2.2%. The plan: ask for the extension. If the supplier hasn't answered by Thursday the 22nd, LaMP proposes the wallet loan by itself. The owner approves each step, with a PIN for the loan.

## 15. Step 5, prove (0:28)
Step five: 38 of 41 invoices paid on time become a credit passport, and a 75.2% advance offer. A lender that ignores the shelf would fund 19,000; LaMP funds 8,200, only stock that will sell. A repayment ceiling refuses loans the shop can't carry. It is shared only with lenders the owner switches on, and a registry stops any invoice being financed twice.

## 16. The copilot, live (0:25)
This is the real app, running on Green Life's data, not mock-ups. Today shows the shortfall like a departures board. Funding shows the plan and every cost. Passport shows the record and the sharing switches. It's built on Next.js, FastAPI, PostgreSQL and the OpenAI Responses API, with 370 automated tests and a hash-chained audit log.

## 17. System flow (0:30)
One rule runs through the design: AI reads and proposes, code calculates, and only the owner approves. The AI touches two steps, reading photos and the chat, and its tools are read-only. Every money figure comes from deterministic engines. An approved step runs in a sandbox, and every event goes to a live audit log.

## 18. Trust mechanism (0:25)
Can anyone trick the AI into moving money? No, because the tool to do it doesn't exist. Approval happens only in the app, and text in photos is data. Can an invoice be financed twice, or data leak to a lender? No: a registry locks each invoice, consent is per lender and scope, and we never store which medicines a patient bought.

## 19. Security and compliance (0:25)
Every action belongs to one of four permission tiers and is logged with its tier, in a hash chain anyone can verify. We attacked it ourselves 26 ways, and all 26 held. To be clear about what's real: the reading, maths, chat, approvals, consent and audit log are working code. The lenders, payouts and supplier replies are sandbox partners, and no real money moves.

## 20. What makes it new (0:20)
Four things are new. Credit and orders are sized on what will actually sell before expiry. It's neutral across every supplier. Supplier payments become consented lender evidence. And it's an agent that acts without ever touching money.

## 21. Competitive landscape (0:20)
PulseTech, TallyKhata, Shelf Life and Retailio prove the demand. But each is tied to one distributor, generic, or holding stock itself. LaMP is neutral, pharmacy-aware, agentic and capital-light.

## 22. Revenue model (0:20)
The pharmacy pays nothing. Lenders pay an origination fee on the financing we bring them, and manufacturers and distributors subscribe to programmes that recover expiring stock and speed up collections. We never lend, so we carry no loan book.

## 23. Feasibility (0:15)
The main risks are adoption, misreads, lender trust and privacy. Each has a mitigation built in today and a fallback for the pilot.

## 24. Action plan and roadmap (0:25)
First, a six-month pilot with 20 pharmacies in Bogura, one lender and one distributor, using real invoices and real repayments. Then more suppliers, a Bangla interface and passports with more lenders. At scale, a bank supplier-credit product and a shared risk model across lenders using federated learning, without sharing borrowers' data. That last part is roadmap, not prototype.

## 25. Closing (0:15)
Every pharmacy already has a credit history, and LaMP-Copilot puts it to work. Our ask: introduce us to one lender and one distributor for the pilot. Thank you.
