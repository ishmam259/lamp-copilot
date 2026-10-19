"use client";

import { useEffect, useRef, useState } from "react";
import { BellRing, X } from "lucide-react";
import { subscribeLogs } from "@/lib/api";
import type { LogEvent } from "@/lib/types";

const AUDIENCES = new Set(["owner", "admin"]);
const DISMISSED_KEY = "lamp:notify-asked";

const supported = () => typeof window !== "undefined" && "Notification" in window;

async function registration(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) return null;
  try {
    return await navigator.serviceWorker.register("/sw.js");
  } catch {
    return null;
  }
}

async function show(e: LogEvent) {
  const title = String(e.data.title ?? "LaMP");
  const options: NotificationOptions = {
    body: String(e.data.body ?? ""),
    tag: e.id,
    icon: "/icon.svg",
    data: { link: String(e.data.link ?? "/actions") },
  };
  const reg = await registration();
  if (reg) {
    await navigator.serviceWorker.ready;
    await reg.showNotification(title, options);
  } else {
    new Notification(title, options).onclick = () => window.focus();
  }
}

/**
 * Turns `notify` events on the live log into desktop notifications (CORE-06). Rendered only
 * after the PIN. Asks permission once; works while the app is open in any tab, including a
 * background tab. Clicking opens the linked approval; it never approves anything.
 */
export function NotificationBridge() {
  const [ask, setAsk] = useState(() => {
    if (!supported() || Notification.permission !== "default") return false;
    try {
      return localStorage.getItem(DISMISSED_KEY) !== "1";
    } catch {
      return true;
    }
  });
  const since = useRef(0);

  useEffect(() => {
    if (!supported()) return;
    since.current = Date.now();
    registration();

    const seen = new Set<string>();
    return subscribeLogs((e) => {
      // The stream replays the backlog first; only events from now on become notifications.
      // Ids restart after a reset, so the key includes the time.
      const key = `${e.id}@${e.ts}`;
      if (e.event !== "notify" || seen.has(key) || Date.parse(e.ts) < since.current - 5000) return;
      if (!AUDIENCES.has(String(e.data.audience))) return;
      seen.add(key);
      if (Notification.permission === "granted") show(e).catch(() => {});
    });
  }, []);

  function remember() {
    setAsk(false);
    try {
      localStorage.setItem(DISMISSED_KEY, "1");
    } catch {
      /* storage blocked */
    }
  }

  if (!ask) return null;
  return (
    <div role="dialog" aria-label="Desktop alerts" className="fixed right-4 bottom-20 z-40 w-[min(22rem,calc(100vw-2rem))] rounded-[8px] border border-rule bg-board p-4 shadow-lg lg:bottom-4">
      <div className="flex items-start gap-3">
        <BellRing className="mt-0.5 size-5 shrink-0 text-cash" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ink">Get desktop alerts?</p>
          <p className="mt-0.5 text-sm text-ink-2">LaMP tells you when a follow-up needs your approval, even if this tab is in the background. Alerts never approve anything.</p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={async () => {
                await Notification.requestPermission().catch(() => "denied");
                remember();
              }}
              className="h-9 rounded-[var(--radius)] bg-primary px-3 text-sm font-semibold text-primary-foreground"
            >
              Turn on
            </button>
            <button type="button" onClick={remember} className="h-9 rounded-[var(--radius)] px-3 text-sm font-semibold text-ink-2 hover:text-ink">
              Not now
            </button>
          </div>
        </div>
        <button type="button" onClick={remember} aria-label="Close" className="text-ink-2 hover:text-ink">
          <X className="size-4" aria-hidden />
        </button>
      </div>
    </div>
  );
}
