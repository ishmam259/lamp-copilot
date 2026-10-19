"use client";

import { useState } from "react";
import { toast } from "sonner";
import { CirclePause, CirclePlay } from "lucide-react";
import { cn } from "cn";
import { setPaused, usePause } from "@/lib/api";

/** "Pause LaMP": stops the copilot and the scheduler from proposing, and blocks approving what they proposed. */
export function PauseToggle({ onRail = false }: { onRail?: boolean }) {
  const { data } = usePause();
  const [busy, setBusy] = useState(false);
  if (!data) return null;
  const paused = data.paused;

  async function toggle() {
    setBusy(true);
    try {
      await setPaused(!paused);
      toast(paused ? "LaMP is back on. It can suggest actions again." : "LaMP is paused. It won't suggest anything until you resume it.");
    } catch {
      toast.error("Couldn't change Pause. Try again.");
    } finally {
      setBusy(false);
    }
  }

  const Icon = paused ? CirclePlay : CirclePause;
  return (
    <button
      type="button"
      role="switch"
      aria-checked={paused}
      aria-label="Pause LaMP"
      disabled={busy}
      onClick={toggle}
      className={cn(
        "inline-flex h-10 items-center gap-1.5 rounded-[var(--radius)] px-3 font-semibold disabled:opacity-60",
        paused
          ? "bg-warn-band text-white"
          : onRail
            ? "text-rail-ink hover:bg-white/10"
            : "border border-rule bg-board text-ink hover:bg-muted"
      )}
    >
      <Icon className="size-5" aria-hidden />
      <span className={onRail ? "sr-only sm:not-sr-only" : undefined}>{paused ? "Resume LaMP" : "Pause LaMP"}</span>
      {onRail && paused && <span className="sm:hidden">Paused</span>}
    </button>
  );
}

export function PausedBanner() {
  const { data } = usePause();
  if (!data?.paused) return null;
  return (
    <p role="status" className="mb-4 rounded-[var(--radius)] border border-warn/40 bg-warn-tint p-3 font-semibold text-warn">
      LaMP is paused. It won&apos;t suggest or follow up on anything, and you can&apos;t approve its suggestions until you resume it. Your own actions still work.
    </p>
  );
}
