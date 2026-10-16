import { CircleAlert, CircleCheck, Hand } from "lucide-react";
import { cn } from "cn";

export type Tone = "alert" | "cash" | "stock" | "warn" | "ink";

/**
 * A white panel. Tone is a state, not a topic: "alert" = problem, "warn" = needs you,
 * "stock" = good news. Anything else stays neutral.
 */
export function Carton({
  tone,
  title,
  aside,
  children,
  className,
  bodyClassName,
  as: Tag = "section",
  headingLevel = 2,
}: {
  tone: Tone;
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  as?: "section" | "article" | "div";
  headingLevel?: 2 | 3;
}) {
  const H = headingLevel === 2 ? "h2" : "h3";
  const Icon = tone === "alert" ? CircleAlert : tone === "warn" ? Hand : tone === "stock" ? CircleCheck : null;
  const titleColour = tone === "alert" ? "text-alert" : tone === "warn" ? "text-warn" : tone === "stock" ? "text-stock" : "text-ink-2";
  return (
    <Tag className={cn("carton", className)}>
      <div className="carton-head">
        <H className={cn("inline-flex items-center gap-1.5 text-[0.9375rem] font-semibold", titleColour)}>
          {Icon && <Icon className="size-4 shrink-0" aria-hidden />}
          {title}
        </H>
        {aside && <div className="text-sm text-ink-2">{aside}</div>}
      </div>
      <div className={cn("p-4 pt-2", bodyClassName)}>{children}</div>
    </Tag>
  );
}

/** Inkjet-stamped code: dates, batch numbers, due marks. */
export function Stamp({
  children,
  tone,
  className,
  approved = false,
}: {
  children: React.ReactNode;
  tone?: Exclude<Tone, "ink">;
  className?: string;
  approved?: boolean;
}) {
  return <span className={cn("stamp", tone && `stamp-${tone}`, approved && "stamp-approved", className)}>{children}</span>;
}

export function PageTitle({ title, sub }: { title: string; sub?: React.ReactNode }) {
  return (
    <div className="mb-4 lg:mb-6">
      <h1 className="text-[1.75rem] leading-tight font-bold text-ink lg:text-[2rem]">{title}</h1>
      {sub && <p className="mt-1 text-ink-2">{sub}</p>}
    </div>
  );
}

export function Skel({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-[var(--radius)] bg-muted", className)} aria-hidden />;
}

export function LoadError({ what }: { what: string }) {
  return (
    <p role="alert" className="rounded-[var(--radius)] border border-alert/40 bg-alert-tint p-4 font-semibold text-alert">
      Couldn&apos;t load {what}. Check the connection and pull to refresh.
    </p>
  );
}
