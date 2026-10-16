"use client";

import { useEffect, useState } from "react";
import { ThemeProvider as NextThemes, useTheme } from "next-themes";
import { Monitor, Moon, Sun } from "lucide-react";
import { cn } from "cn";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemes attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </NextThemes>
  );
}

const ORDER = ["system", "light", "dark"] as const;
const META = {
  system: { icon: Monitor, label: "Theme: match device" },
  light: { icon: Sun, label: "Theme: light" },
  dark: { icon: Moon, label: "Theme: dark" },
};

/** Cycles match-device → light → dark. */
export function ThemeToggle({ className, withLabel = false, onRail = false }: { className?: string; withLabel?: boolean; onRail?: boolean }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  const current = (mounted && (theme as (typeof ORDER)[number])) || "system";
  const { icon: Icon, label } = META[current];
  const next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      aria-label={`${label}. Switch to ${META[next].label.replace("Theme: ", "")}`}
      title={label}
      className={cn(
        "inline-flex h-11 items-center gap-2 rounded-[var(--radius)]",
        onRail ? "text-rail-2 hover:bg-white/10 hover:text-rail-ink" : "text-ink-2 hover:bg-muted hover:text-ink",
        withLabel ? "px-3 text-sm font-semibold" : "w-11 justify-center",
        className
      )}
    >
      <Icon className="size-5" aria-hidden />
      {withLabel && <span>{label.replace("Theme: m", "M").replace("Theme: l", "L").replace("Theme: d", "D")}</span>}
    </button>
  );
}
