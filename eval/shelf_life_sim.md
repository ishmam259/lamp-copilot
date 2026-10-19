# Shelf-life credit simulation (synthetic)

**200 perturbed pharmacies, seed 2026**, run through the real engines (`python eval/shelf_life_sim.py`). Synthetic: every shop is a perturbed copy of the seed pharmacy, Green Life, not a real shop.

- 200 shops have a shortfall to finance; 0 have none and are left out.
- **The financed amount changes in 72% of shops**: shelf-life credit finances less than the purpose-blind lender because part of the order won't sell before expiry.
- The unperturbed seed reproduces the golden card: 19,000 / 10,800 / 8,200.

Median (P10–P90) per shop:

| Measure | Purpose-blind lender | Shelf-life credit |
|---|---|---|
| Amount financed (BDT) | 25,852 (8,195–44,785) | 18,997 (3,421–35,061) |
| Financed stock that expires unsold (BDT) | 6,158 (0–18,681) | 0 (0–3,174) |
| Interest, wallet loan 9% APR 90 days (BDT) | 574 (182–994) | 422 (76–778) |
| Need left unfinanced after the trim (BDT) | 0 (0–0) | 0 (0–0) |
| Order stock written off at expiry (BDT) | 6,308 (0–19,425) | 0 (0–3,502) |
| Days with negative cash in the 30-day forecast | 20 (18–20) | 20 (15–20) |

## Assumptions

- Purpose-blind: finances the whole untrimmed first shortfall; the order goes ahead as planned.
- Shelf-life credit: finances `need − stock that won't sell before expiry` (engines/passport.py); the owner trims the order to the sellable quantity (engines/expiry.py, 30-day selling buffer).
- Perturbations: cash ×U(0.6, 1.4); daily sales ×U(0.8, 1.2); purchase history per product ×U(0.6, 1.4); order line qty ×U(0.5, 1.8); line expiry shifted U(−30, +150) days.
- Actual sales differ from the engine's estimate: true rate = estimated rate × lognormal(0, 0.25). "Expires unsold" and the write-off are measured against those actual sales.
- Financed stock that expires unsold = unsold value at expiry, capped at the amount financed.
- Interest uses the seed's wallet loan (9% APR, 90 days) for both lenders.
- Need left unfinanced = the trimmed order's shortfall on the same date minus what shelf-life credit finances. The purpose-blind lender finances everything, so 0. For shelf-life credit it is 0 by construction: the trim saves at least as much as the credit withholds.
- Days short counts days below zero in the 30-day forecast before any financing arrives. Most come from later bills (rent, other suppliers), so the trim moves it little.
- Not measured: the cash forecast's error on actual sales. In a simulation the "actual" sales are the noise we inject, so the number would only restate the noise; it needs real daily sales.
