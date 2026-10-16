import type { ForecastDay } from "@/lib/types";

/** Big moves worth a row. Uses the engine's named items; falls back to size for older payloads. */
export function isNamedMove(d: ForecastDay) {
  return d.items ? d.items.length > 0 : d.outflow >= 5000 || d.inflow >= 4000;
}

/** The signed amount of the named moves that day, exactly as the engine reports it. */
export function dayAmount(d: ForecastDay) {
  return d.items && d.items.length > 0 ? d.items.reduce((s, x) => s + x.amount, 0) : d.inflow - d.outflow;
}

/** What happens that day, in the owner's words. */
export function dayLabel(d: ForecastDay, supplier?: string) {
  if (d.items && d.items.length > 0) return d.items.map((x) => x.label).join(", ");
  return supplier ?? "Bills and spending";
}
