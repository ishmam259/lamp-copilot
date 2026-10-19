"use client";

import { useState } from "react";
import { toast } from "sonner";
import { RotateCcw } from "lucide-react";
import { resetDemo } from "@/lib/api";

/** "Reset demo": puts the shared sandbox back to the start of the story, after a confirm. */
export function ResetDemoButton({ className = "" }: { className?: string }) {
  const [busy, setBusy] = useState(false);
  async function onClick() {
    if (!window.confirm("Reset the demo? Every approval, capture and log entry goes back to the start of the story.")) return;
    setBusy(true);
    try {
      await resetDemo();
      toast.success("Demo reset to the start.");
    } catch {
      toast.error("Couldn't reset. Demo controls may be off on this server.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <button type="button" onClick={onClick} disabled={busy} className={className}>
      <RotateCcw className={`size-5 ${busy ? "animate-spin" : ""}`} aria-hidden /> {busy ? "Resetting…" : "Reset demo"}
    </button>
  );
}
