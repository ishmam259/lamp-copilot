// Shapes mirror docs/PLAN.md section 4.3. When Farhan's contracts/ land,
// keep these in sync with backend/app/schemas.

export type ISODate = string;

export interface Pharmacy {
  id: string;
  name: string;
  city: string;
  settings: {
    gross_margin_pct: number;
    cash_buffer: number;
    expiry_buffer_days: number;
    as_of_date: ISODate;
  };
}

export interface AccountsOut {
  period_days: number;
  sales: number;
  gross_margin_pct: number;
  gross_profit: number;
  overheads: number;
  net_profit: number;
  stock_value: number;
  stock_days: number;
  patient_dues: number;
  patient_due_days: number;
  active_suppliers: number;
  top_suppliers: { name: string; share_pct: number }[];
  slow_movers: { product: string; qty: number; sellable_qty: number; at_risk_value: number }[];
  expiring_value_60d: number;
}

export type DueStatus = "overdue" | "due_soon" | "upcoming";

export interface DuesOut {
  items: {
    supplier: string;
    invoice_no: string;
    amount: number;
    due_date: ISODate;
    days_left: number;
    status: DueStatus;
  }[];
  total_due: number;
}

export interface ForecastDay {
  date: ISODate;
  inflow: number;
  outflow: number;
  balance: number;
}

export interface ForecastOut {
  start_cash: number;
  days: ForecastDay[];
  shortfalls: { date: ISODate; amount: number; cause: string }[];
}

export type AlertKind = "shortfall" | "expiry" | "return_window" | "patient_dues" | "suspicious_document";

export interface Alert {
  id: string;
  kind: AlertKind;
  severity: "critical" | "warning" | "info";
  title: string;
  detail: string;
  created_at: string;
}

export interface ExpiryBatch {
  product: string;
  batch_no: string;
  expiry_date: ISODate;
  days_left: number;
  qty: number;
  cost_value: number;
  return_eligible: boolean;
  supplier: string;
}

export interface ExpiryOut {
  horizon_days: number;
  batches: ExpiryBatch[];
  at_risk_value: number;
  return_eligible_value: number;
}

export interface OrderOut {
  id: string;
  supplier: string;
  due_date: ISODate;
  total: number;
  lines: { product: string; qty: number; unit_cost: number }[];
}

export interface TrimLine {
  product: string;
  qty: number;
  unit_cost: number;
  sales_rate_per_day: number;
  sellable_days: number;
  sellable_qty: number;
  suggested_qty: number;
  at_risk_value: number;
}

export interface TrimOut {
  order_id: string;
  lines: TrimLine[];
  original_total: number;
  suggested_total: number;
  saving: number;
}

export interface FundingOption {
  key: string;
  label: string;
  provider: string;
  amount: number;
  cost_bdt: number | null;
  apr_pct: number | null;
  eligible: boolean;
  reason: string;
  speed: string;
  certainty: "certain" | "uncertain";
}

export interface FundingPlanOut {
  need: { amount: number; needed_by: ISODate };
  options: FundingOption[];
  plan: {
    steps: { action_kind: ActionKind; label: string; amount: number; when: ISODate; fallback_for?: string }[];
    total_cost_bdt: number;
  };
  naive_cost_bdt: number;
}

export interface PassportEvidence {
  invoice_no: string;
  supplier: string;
  due_date: ISODate;
  paid_on: ISODate;
  on_time: boolean;
  supplier_confirmed: boolean;
}

export interface PassportOut {
  invoices_total: number;
  paid_on_time: number;
  confirmed_share: number;
  theta_mean: number;
  theta_low_5pct: number;
  default_probability: number;
  score: number;
  advance_rate_pct: number;
  partner_share_pct: number;
  evidence: PassportEvidence[];
}

export type ActionKind = "return_claim" | "extension_request" | "loan_application" | "set_aside" | "trim_order";
export type ActionStatus = "proposed" | "approved" | "rejected" | "executed" | "failed";

export interface ActionOut {
  id: string;
  kind: ActionKind;
  status: ActionStatus;
  payload: Record<string, unknown> & { summary?: string; amount?: number };
  proposed_by: "owner" | "agent";
  created_at: string;
  decided_at?: string;
  result?: Record<string, unknown> & { summary?: string };
}

export interface Lender {
  id: string;
  name: string;
  kind: "mobile_wallet" | "bank";
  products: { key: string; label: string; apr_pct: number | null; fee_pct: number | null; min_amount: number; max_amount: number }[];
}

export interface Consent {
  id: string;
  lender_id: string;
  scopes: string[];
  granted_at: string;
}

export interface Application {
  id: string;
  pharmacy_id: string;
  pharmacy_name: string;
  lender_id: string;
  product_key: string;
  amount: number;
  status: "pending" | "approved" | "declined";
  passport: PassportOut;
  decision?: { approved: boolean; payout_ref?: string; reason: string };
  created_at: string;
}

export interface LogEvent {
  id: string;
  ts: string;
  tier: "T0" | "T1" | "T2" | "T3";
  component: string;
  event: string;
  data: Record<string, unknown>;
}

export interface ExtractionLine {
  product: string;
  strength?: string | null;
  pack?: string | null;
  batch_no: string;
  expiry_date: ISODate;
  qty: number;
  unit_cost: number;
  line_total: number;
}

export interface ExtractionResult {
  kind: "invoice" | "sales_page";
  invoice?: {
    supplier_name: string;
    invoice_no: string;
    invoice_date: ISODate;
    due_date: ISODate;
    total: number;
    lines: ExtractionLine[];
  };
  sales_page?: {
    days: { date: ISODate; cash_sales: number; credit_sales: number; dues_collected: number; expenses: number }[];
  };
  field_confidence: Record<string, number>;
  checks: { name: string; passed: boolean; detail: string }[];
  suspicious_text: string[];
  model: string;
  prompt_version: string;
  mode: "live" | "replay";
}

export interface CaptureOut {
  id: string;
  kind: "invoice" | "sales_page";
  status: "needs_review" | "confirmed";
  image_url?: string;
  extraction: ExtractionResult;
}
