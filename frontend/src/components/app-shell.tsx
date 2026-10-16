"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  BadgeCheck,
  Camera,
  HandCoins,
  Inbox,
  Landmark,
  MessageCircle,
  PackageOpen,
  RotateCcw,
  ScrollText,
  Sun,
  Wallet,
} from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import { cn } from "cn";
import { API_MODE, resetDemo, useActions, usePharmacy } from "@/lib/api";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ChatPanel } from "@/components/chat-panel";
import { LiveLog } from "@/components/live-log";
import { ThemeToggle } from "@/components/theme";

const OWNER_NAV = [
  { href: "/", label: "Today", icon: Sun },
  { href: "/cash", label: "Cash", icon: Wallet },
  { href: "/capture", label: "Capture", icon: Camera },
  { href: "/stock", label: "Stock", icon: PackageOpen },
  { href: "/funding", label: "Funding", icon: HandCoins },
];

const MORE_NAV = [
  { href: "/actions", label: "Actions", icon: Inbox },
  { href: "/passport", label: "Passport", icon: BadgeCheck },
];

const OTHER_NAV = [
  { href: "/lender", label: "Lender view", icon: Landmark },
  { href: "/log", label: "Audit log", icon: ScrollText },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-extrabold tracking-tight text-ink", className)}>
      La<span className="text-cash">M</span>P
    </span>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: pharmacy } = usePharmacy();
  const { data: actions } = useActions();
  const [chatOpen, setChatOpen] = useState(false);
  const pending = actions?.filter((a) => a.status === "proposed").length ?? 0;
  const isLender = pathname.startsWith("/lender");

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[232px_1fr] xl:grid-cols-[232px_1fr_340px]">
      {/* Desktop rail */}
      <aside className="sticky top-0 hidden h-dvh flex-col border-r border-rule bg-board lg:flex">
        <div className="print-strip" />
        <div className="px-5 pt-5 pb-4">
          <Link href="/" className="text-2xl">
            <Wordmark />
          </Link>
          <p className="mt-1 text-sm text-ink-2">{pharmacy ? `${pharmacy.name}, ${pharmacy.city}` : " "}</p>
        </div>
        <nav aria-label="Main" className="flex flex-1 flex-col gap-0.5 px-3">
          {[...OWNER_NAV, ...MORE_NAV].map((item) => (
            <RailLink key={item.href} {...item} active={isActive(pathname, item.href)} badge={item.href === "/actions" ? pending : 0} />
          ))}
          <div className="mt-5 mb-1 px-3 text-xs font-semibold tracking-wide text-ink-2 uppercase">Other views</div>
          {OTHER_NAV.map((item) => (
            <RailLink key={item.href} {...item} active={isActive(pathname, item.href)} />
          ))}
        </nav>
        <div className="space-y-2 border-t border-rule p-4">
          <ThemeToggle withLabel className="-ml-3" />
          <ModeNote />
          <button
            type="button"
            onClick={() => resetDemo()}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-2 hover:text-ink"
          >
            <RotateCcw className="size-4" aria-hidden /> Reset demo data
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-h-dvh min-w-0 flex-col">
        <header className="sticky top-0 z-30 bg-board/95 backdrop-blur-sm supports-[backdrop-filter]:bg-board/85 lg:hidden">
          <div className="print-strip" />
          <div className="flex items-center gap-3 border-b border-rule px-4 py-2.5">
            <Link href="/" className="text-[1.6rem] leading-none">
              <Wordmark />
            </Link>
            <span className="min-w-0 flex-1 truncate text-sm text-ink-2">{pharmacy?.name}</span>
            <ThemeToggle />
            <Link
              href="/actions"
              aria-label={`Actions, ${pending} waiting for you`}
              className="relative inline-flex size-11 items-center justify-center rounded-[var(--radius)] text-ink hover:bg-muted"
            >
              <Inbox className="size-5" aria-hidden />
              {pending > 0 && (
                <span className="num absolute top-1.5 right-1.5 min-w-5 rounded-full bg-alert-band px-1 text-center text-xs leading-5 font-bold text-white">
                  {pending}
                </span>
              )}
            </Link>
            {!isLender && (
              <button
                type="button"
                onClick={() => setChatOpen(true)}
                className="inline-flex h-11 items-center gap-1.5 rounded-[var(--radius)] bg-primary px-3 font-semibold text-primary-foreground"
              >
                <MessageCircle className="size-5" aria-hidden /> Ask
              </button>
            )}
          </div>
        </header>

        {/* Desktop top bar */}
        <div className="sticky top-0 z-30 hidden items-center justify-end gap-3 border-b border-rule bg-shelf/90 px-8 py-3 backdrop-blur-sm lg:flex">
          {isLender ? (
            <span className="text-sm font-semibold text-ink-2">Viewing as a lender. You only see pharmacies that shared their passport with you.</span>
          ) : (
            <button
              type="button"
              onClick={() => setChatOpen(true)}
              className="inline-flex h-10 items-center gap-2 rounded-[var(--radius)] bg-primary px-4 font-semibold text-primary-foreground hover:bg-[color-mix(in_srgb,var(--primary),black_12%)]"
            >
              <MessageCircle className="size-5" aria-hidden /> Ask LaMP
            </button>
          )}
        </div>

        <main className="mx-auto w-full max-w-[1080px] flex-1 px-4 pt-4 pb-28 lg:px-8 lg:pt-6 lg:pb-12">{children}</main>

        {/* Phone tab bar */}
        <nav
          aria-label="Main"
          className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-rule bg-board pb-[env(safe-area-inset-bottom)] lg:hidden"
        >
          {OWNER_NAV.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-16 flex-col items-center justify-center gap-1 text-xs font-semibold",
                  active ? "text-cash" : "text-ink-2"
                )}
              >
                {active && <span className="absolute inset-x-4 top-0 h-[3px] bg-cash" aria-hidden />}
                <Icon className="size-6" aria-hidden />
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Desktop live log column */}
      <aside className="sticky top-0 hidden h-dvh flex-col border-l border-rule bg-board xl:flex">
        <LiveLog compact />
      </aside>

      <Sheet open={chatOpen} onOpenChange={setChatOpen}>
        <SheetContent side="right" className="w-full gap-0 p-0 sm:max-w-md">
          <SheetHeader className="border-b border-rule">
            <SheetTitle className="text-lg">Ask LaMP</SheetTitle>
          </SheetHeader>
          <ChatPanel />
        </SheetContent>
      </Sheet>

      <Toaster position="top-center" richColors closeButton />
    </div>
  );
}

function RailLink({
  href,
  label,
  icon: Icon,
  active,
  badge = 0,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  active: boolean;
  badge?: number;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex h-11 items-center gap-3 rounded-[var(--radius)] px-3 font-semibold",
        active ? "bg-cash-tint text-cash" : "text-ink hover:bg-muted"
      )}
    >
      <Icon className="size-5" aria-hidden />
      <span className="flex-1">{label}</span>
      {badge > 0 && <span className="num rounded-full bg-alert-band px-2 text-xs leading-5 font-bold text-white">{badge}</span>}
    </Link>
  );
}

function ModeNote() {
  return (
    <p className="text-xs leading-snug text-ink-2">
      {API_MODE === "mock" ? "Demo data. " : ""}Lenders and payouts are simulated.
    </p>
  );
}
