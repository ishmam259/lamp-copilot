const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function parse(iso: string): Date {
  return new Date(iso.length === 10 ? `${iso}T00:00:00Z` : iso);
}

/** 412500 -> "412,500"; -17350 -> "−17,350" with a true minus sign. */
export function num(n: number, decimals = 0): string {
  const s = Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return n < 0 && s.replace(/[0.,]/g, "") !== "" ? `−${s}` : s;
}

/** 412500 -> "BDT 412,500"; keeps paisa only when present. */
export function bdt(n: number): string {
  const hasFraction = Math.round(n * 100) % 100 !== 0;
  return `BDT ${num(Math.abs(n), hasFraction ? 2 : 0)}`;
}

/** Signed money for timetable rows: "+ 4,200" / "− 8,450". */
export function signed(n: number): string {
  if (n === 0) return "0";
  return `${n > 0 ? "+" : "−"} ${num(Math.abs(n))}`;
}

/** "2026-10-26" -> "26 Oct" */
export function shortDate(iso: string): string {
  const d = parse(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
}

/** "2026-10-26" -> "Mon 26 Oct" */
export function dayDate(iso: string): string {
  const d = parse(iso);
  return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
}

/** "2026-10-26" -> "26 OCT 26" for stamps */
export function stampDate(iso: string): string {
  const d = parse(iso);
  return `${String(d.getUTCDate()).padStart(2, "0")} ${MONTHS[d.getUTCMonth()].toUpperCase()} ${String(d.getUTCFullYear()).slice(2)}`;
}

export function weekday(iso: string): string {
  return DAYS[parse(iso).getUTCDay()];
}

export function daysBetween(fromIso: string, toIso: string): number {
  return Math.round((parse(toIso).getTime() - parse(fromIso).getTime()) / 86400000);
}

export function inDays(n: number): string {
  if (n === 0) return "today";
  if (n === 1) return "tomorrow";
  if (n < 0) return `${-n} days ago`;
  return `in ${n} days`;
}

export function timeOfDay(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
