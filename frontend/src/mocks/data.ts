// Demo pharmacy "Green Life Pharmacy, Bogura".
// Every figure here must match the golden numbers in docs/PLAN.md section 6.
// When Farhan publishes contracts/examples/*.json, prefer those.

import type {
  AccountsOut,
  ActionOut,
  Alert,
  Application,
  CaptureOut,
  Consent,
  DuesOut,
  ExpiryOut,
  ForecastDay,
  ForecastOut,
  FundingPlanOut,
  Lender,
  LogEvent,
  OrderOut,
  PassportEvidence,
  PassportOut,
  Pharmacy,
  TrimOut,
} from "@/lib/types";

export const AS_OF = "2026-10-16";

function addDays(iso: string, n: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export const pharmacy: Pharmacy = {
  id: "green-life",
  name: "Green Life Pharmacy",
  city: "Bogura",
  settings: { gross_margin_pct: 12, cash_buffer: 0, expiry_buffer_days: 30, as_of_date: AS_OF },
};

export const accounts: AccountsOut = {
  period_days: 30,
  sales: 412500,
  gross_margin_pct: 12,
  gross_profit: 49500,
  overheads: 36000,
  net_profit: 13500,
  stock_value: 210000,
  stock_days: 17.4,
  patient_dues: 38000,
  patient_due_days: 2.8,
  active_suppliers: 23,
  top_suppliers: [
    { name: "Supplier A", share_pct: 14.2 },
    { name: "Supplier B", share_pct: 11.8 },
    { name: "Supplier C", share_pct: 9.6 },
    { name: "Supplier D", share_pct: 8.1 },
    { name: "Supplier E", share_pct: 6.9 },
  ],
  slow_movers: [{ product: "Montelukast 10 mg, box of 30", qty: 30, sellable_qty: 12, at_risk_value: 10800 }],
  expiring_value_60d: 18400,
};

export const dues: DuesOut = {
  items: [
    { supplier: "Supplier D", invoice_no: "D-20931", amount: 8450, due_date: addDays(AS_OF, 2), days_left: 2, status: "due_soon" },
    { supplier: "Supplier F", invoice_no: "F-1182", amount: 6200, due_date: addDays(AS_OF, 6), days_left: 6, status: "due_soon" },
    { supplier: "Supplier A", invoice_no: "PO-A-1026", amount: 60000, due_date: addDays(AS_OF, 10), days_left: 10, status: "upcoming" },
    { supplier: "Supplier H", invoice_no: "H-5520", amount: 11300, due_date: addDays(AS_OF, 19), days_left: 19, status: "upcoming" },
  ],
  total_due: 85950,
};

// Daily cash: routine net +1,650/day, plus the known events below.
// Balance at the end of 25 Oct is exactly 41,000; the 60,000 order on 26 Oct makes it −19,000.
function buildForecast(): ForecastOut {
  const start = 34950;
  const events: Record<string, { label: string; inflow?: number; outflow?: number }> = {
    [addDays(AS_OF, 2)]: { label: "Supplier D", outflow: 8450 },
    [addDays(AS_OF, 4)]: { label: "Patient dues collected", inflow: 4200 },
    [addDays(AS_OF, 6)]: { label: "Supplier F", outflow: 6200 },
    [addDays(AS_OF, 10)]: { label: "Supplier A order", outflow: 60000 },
    [addDays(AS_OF, 16)]: { label: "Shop rent", outflow: 18000 },
    [addDays(AS_OF, 19)]: { label: "Supplier H", outflow: 11300 },
    [addDays(AS_OF, 20)]: { label: "Salaries", outflow: 15000 },
    [addDays(AS_OF, 25)]: { label: "Electricity and internet", outflow: 3000 },
  };
  const days: ForecastDay[] = [];
  let balance = start;
  for (let i = 0; i < 30; i++) {
    const date = addDays(AS_OF, i);
    const ev = events[date];
    const routine = i === 10 ? 0 : 1650;
    const inflow = routine + (ev?.inflow ?? 0);
    const outflow = ev?.outflow ?? 0;
    balance = balance + inflow - outflow;
    const items = ev ? [{ label: ev.label, amount: (ev.inflow ?? 0) - (ev.outflow ?? 0) }] : [];
    days.push({ date, inflow, outflow, balance, items });
  }
  return {
    start_cash: start,
    days,
    // Same shape as the engine: later amounts are the extra deficit each payment adds.
    shortfalls: [
      { date: addDays(AS_OF, 10), amount: 19000, cause: "Supplier A order BDT 60,000" },
      { date: addDays(AS_OF, 16), amount: 18000, cause: "Shop rent BDT 18,000" },
      { date: addDays(AS_OF, 19), amount: 11300, cause: "Supplier H BDT 11,300" },
      { date: addDays(AS_OF, 20), amount: 15000, cause: "Salaries BDT 15,000" },
      { date: addDays(AS_OF, 25), amount: 3000, cause: "Electricity and internet BDT 3,000" },
    ],
  };
}

export const forecast: ForecastOut = buildForecast();

export const alerts: Alert[] = [
  {
    id: "al-1",
    kind: "shortfall",
    severity: "critical",
    title: "Short BDT 19,000 on 26 Oct",
    detail: "Supplier A order BDT 60,000 is due. Forecast cash that day is BDT 41,000.",
    created_at: `${AS_OF}T08:00:00Z`,
  },
  {
    id: "al-2",
    kind: "return_window",
    severity: "warning",
    title: "Claim returns worth BDT 9,200",
    detail: "2 batches can still go back to their suppliers before the return window closes.",
    created_at: `${AS_OF}T08:00:00Z`,
  },
  {
    id: "al-3",
    kind: "expiry",
    severity: "warning",
    title: "BDT 18,400 of stock expires within 60 days",
    detail: "6 batches. 4 of them are past their return window.",
    created_at: `${AS_OF}T08:00:00Z`,
  },
];

export const expiry: ExpiryOut = {
  horizon_days: 60,
  batches: [
    { product: "Omeprazole 20 mg, box of 50", batch_no: "OM2409", expiry_date: addDays(AS_OF, 55), days_left: 55, qty: 10, cost_value: 4800, return_eligible: true, supplier: "Supplier B" },
    { product: "Cetirizine 10 mg, box of 100", batch_no: "CT2411", expiry_date: addDays(AS_OF, 48), days_left: 48, qty: 22, cost_value: 4400, return_eligible: true, supplier: "Supplier C" },
    { product: "Amoxicillin 500 mg, box of 50", batch_no: "AX2402", expiry_date: addDays(AS_OF, 25), days_left: 25, qty: 6, cost_value: 3600, return_eligible: false, supplier: "Supplier E" },
    { product: "Metformin 500 mg, box of 100", batch_no: "MF2398", expiry_date: addDays(AS_OF, 20), days_left: 20, qty: 13, cost_value: 2600, return_eligible: false, supplier: "Supplier B" },
    { product: "Oral saline, box of 25", batch_no: "OR2390", expiry_date: addDays(AS_OF, 12), days_left: 12, qty: 6, cost_value: 1800, return_eligible: false, supplier: "Supplier G" },
    { product: "Vitamin B complex, box of 30", batch_no: "VB2385", expiry_date: addDays(AS_OF, 9), days_left: 9, qty: 8, cost_value: 1200, return_eligible: false, supplier: "Supplier D" },
  ],
  at_risk_value: 18400,
  return_eligible_value: 9200,
};

export const orders: OrderOut[] = [
  {
    id: "o-1",
    supplier: "Supplier A",
    due_date: addDays(AS_OF, 10),
    total: 60000,
    lines: [
      { product: "Montelukast 10 mg, box of 30", qty: 30, unit_cost: 600 },
      { product: "Paracetamol 500 mg, box of 100", qty: 40, unit_cost: 300 },
      { product: "Omeprazole 20 mg, box of 50", qty: 25, unit_cost: 480 },
      { product: "Cetirizine 10 mg, box of 100", qty: 30, unit_cost: 200 },
      { product: "Oral saline, box of 25", qty: 40, unit_cost: 300 },
    ],
  },
];

export const trim: TrimOut = {
  order_id: "o-1",
  lines: [
    { product: "Montelukast 10 mg, box of 30", qty: 30, unit_cost: 600, sales_rate_per_day: 0.2, sellable_days: 60, sellable_qty: 12, suggested_qty: 12, at_risk_value: 10800 },
    { product: "Paracetamol 500 mg, box of 100", qty: 40, unit_cost: 300, sales_rate_per_day: 2.1, sellable_days: 400, sellable_qty: 40, suggested_qty: 40, at_risk_value: 0 },
    { product: "Omeprazole 20 mg, box of 50", qty: 25, unit_cost: 480, sales_rate_per_day: 0.9, sellable_days: 300, sellable_qty: 25, suggested_qty: 25, at_risk_value: 0 },
    { product: "Cetirizine 10 mg, box of 100", qty: 30, unit_cost: 200, sales_rate_per_day: 1.1, sellable_days: 330, sellable_qty: 30, suggested_qty: 30, at_risk_value: 0 },
    { product: "Oral saline, box of 25", qty: 40, unit_cost: 300, sales_rate_per_day: 1.6, sellable_days: 520, sellable_qty: 40, suggested_qty: 40, at_risk_value: 0 },
  ],
  original_total: 60000,
  suggested_total: 49200,
  saving: 10800,
};

export const fundingPlan: FundingPlanOut = {
  need: { amount: 8200, needed_by: addDays(AS_OF, 10) },
  options: [
    { key: "trim_order", label: "Trim the slow mover from Supplier A's order", provider: "Your order", amount: 10800, cost_bdt: 0, apr_pct: null, eligible: true, reason: "Only 12 of 30 boxes will sell before expiry.", speed: "Now", certainty: "certain" },
    { key: "return_claims", label: "Claim returns for expiring stock", provider: "Suppliers B and C", amount: 9200, cost_bdt: 0, apr_pct: null, eligible: true, reason: "Arrives as supplier credit, not cash, so it doesn't count before 26 Oct.", speed: "1–2 weeks", certainty: "uncertain" },
    { key: "supplier_extension", label: "Ask Supplier A for 20 more days", provider: "Supplier A", amount: 8200, cost_bdt: 0, apr_pct: null, eligible: true, reason: "You paid 38 of 41 invoices on time.", speed: "1–3 days", certainty: "uncertain" },
    { key: "wallet_loan", label: "Mobile-wallet loan, 3 months", provider: "Wallet Lender", amount: 8200, cost_bdt: 181.97, apr_pct: 9, eligible: true, reason: "Within the BDT 500–30,000 limit.", speed: "Same day", certainty: "certain" },
    { key: "bank_supplier_credit", label: "Bank pays Supplier A now, you repay in 30 days", provider: "Partner Bank", amount: 49200, cost_bdt: 492, apr_pct: 12.2, eligible: true, reason: "1% of the order for 30 days.", speed: "2–3 days", certainty: "certain" },
    { key: "bank_sme_loan", label: "Bank small-business loan", provider: "Partner Bank", amount: 8200, cost_bdt: null, apr_pct: null, eligible: false, reason: "Minimum loan is BDT 200,000, with 12 months of history.", speed: "2–4 weeks", certainty: "certain" },
  ],
  plan: {
    steps: [
      { action_kind: "trim_order", label: "Cut Montelukast from 30 to 12 boxes", amount: 10800, when: AS_OF },
      { action_kind: "extension_request", label: "Ask Supplier A for 20 more days on BDT 8,200", amount: 8200, when: AS_OF },
      { action_kind: "loan_application", label: "If Supplier A hasn't agreed, take a mobile-wallet loan", amount: 8200, when: addDays(AS_OF, 7), fallback_for: "extension_request" },
    ],
    total_cost_bdt: 0,
  },
  naive_cost_bdt: 421.64,
};

const evidence: PassportEvidence[] = Array.from({ length: 41 }, (_, i) => {
  const late = i === 7 || i === 19 || i === 33;
  const due = addDays(AS_OF, -88 + i * 2);
  return {
    invoice_no: `INV-${(3100 + i).toString()}`,
    supplier: `Supplier ${String.fromCharCode(65 + (i % 23))}`,
    due_date: due,
    paid_on: late ? addDays(due, 6) : addDays(due, -1),
    on_time: !late,
    supplier_confirmed: true,
  };
});

export const passport: PassportOut = {
  invoices_total: 41,
  paid_on_time: 38,
  confirmed_share: 1,
  theta_mean: 0.907,
  theta_low_5pct: 0.826,
  default_probability: 0.03,
  score: 0.507,
  advance_rate_pct: 75.2,
  partner_share_pct: 54.4,
  evidence,
};

export const initialActions: ActionOut[] = [
  {
    id: "act-1",
    kind: "return_claim",
    status: "proposed",
    payload: { summary: "Return Omeprazole (OM2409) and Cetirizine (CT2411) to Suppliers B and C", amount: 9200 },
    proposed_by: "agent",
    created_at: `${AS_OF}T08:05:00Z`,
  },
];

export const lenders: Lender[] = [
  { id: "wallet-lender", name: "Wallet Lender", kind: "mobile_wallet", products: [{ key: "wallet_loan", label: "Mobile-wallet loan", apr_pct: 9, fee_pct: null, min_amount: 500, max_amount: 30000 }] },
  {
    id: "partner-bank",
    name: "Partner Bank",
    kind: "bank",
    products: [
      { key: "bank_supplier_credit", label: "Supplier credit", apr_pct: null, fee_pct: 1, min_amount: 10000, max_amount: 500000 },
      { key: "bank_sme_loan", label: "Small-business loan", apr_pct: 13, fee_pct: null, min_amount: 200000, max_amount: 5000000 },
    ],
  },
];

export const initialConsents: Consent[] = [];

export const initialApplications: Application[] = [];

export const initialLogs: LogEvent[] = [
  { id: "lg-1", ts: `${AS_OF}T08:00:00Z`, tier: "T2", component: "FORECAST", event: "shortfall_detected", data: { date: addDays(AS_OF, 10), amount: 19000 } },
  { id: "lg-2", ts: `${AS_OF}T08:00:01Z`, tier: "T2", component: "EXPIRY", event: "batches_at_risk", data: { batches: 6, value: 18400 } },
  { id: "lg-3", ts: `${AS_OF}T08:05:00Z`, tier: "T1", component: "COPILOT", event: "action_proposed", data: { action: "act-1", kind: "return_claim" } },
];

export const sampleCapture: CaptureOut = {
  id: "cap-demo",
  kind: "invoice",
  status: "needs_review",
  extraction: {
    kind: "invoice",
    invoice: {
      supplier_name: "Supplier K",
      invoice_no: "K-77310",
      invoice_date: AS_OF,
      due_date: addDays(AS_OF, 14),
      total: 7500,
      lines: [
        { product: "Paracetamol 500 mg", strength: "500 mg", pack: "box of 100", batch_no: "PC2510", expiry_date: "2028-03-31", qty: 10, unit_cost: 300, line_total: 3000 },
        { product: "Cetirizine 10 mg", strength: "10 mg", pack: "box of 100", batch_no: "CT2507", expiry_date: "2027-11-30", qty: 15, unit_cost: 200, line_total: 3000 },
        { product: "Oral saline", strength: null, pack: "box of 25", batch_no: "OR2506", expiry_date: "2027-06-30", qty: 5, unit_cost: 270, line_total: 1350 },
      ],
    },
    field_confidence: { "invoice.lines[2].unit_cost": 0.3, "invoice.lines[2].qty": 0.5, "invoice.due_date": 0.5 },
    checks: [
      { name: "Line totals", passed: true, detail: "Each line's quantity × price matches its line total." },
      { name: "Invoice total", passed: false, detail: "Lines add up to BDT 7,350 but the invoice says BDT 7,500. The Oral saline price may be 300, not 270." },
      { name: "Dates", passed: true, detail: "Expiry dates are after the invoice date." },
    ],
    suspicious_text: [],
    model: "gpt-6-luna",
    prompt_version: "extraction_v1",
    mode: "replay",
  },
};
