"use client";

import { useEffect, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { ArrowUp, Check, ListChecks, ShieldAlert, ShieldCheck, Wrench } from "lucide-react";
import { cn } from "cn";
import { PID } from "@/lib/api";

const SUGGESTIONS = [
  "How did we do this month?",
  "Can I pay Supplier A's order next week?",
  "What is expiring?",
  "Why did the bank offer 75%?",
];

type Trace = { traced: number; total: number; blocked: boolean };
type Turn = { id: string; role: "user" | "assistant"; text: string; tools?: string[]; plan?: string[]; trace?: Trace };

/** LaMP chat: POST /api/v1/chat (backend/app/agents/router.py), streamed with the AI SDK UI message protocol. */
export function ChatPanel() {
  return <LiveChat />;
}

function LiveChat() {
  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({ api: "/api/v1/chat", body: { pharmacy_id: PID } }),
  });
  const busy = status === "submitted" || status === "streaming";
  const turns: Turn[] = messages.map((m: UIMessage) => ({
    id: m.id,
    role: m.role === "user" ? "user" : "assistant",
    text: m.parts
      .filter((p) => p.type === "text")
      .map((p) => (p as { text: string }).text)
      .join(""),
    tools: m.parts
      .filter((p) => p.type.startsWith("tool-") || p.type === "dynamic-tool")
      .map((p) => ("toolName" in p ? String((p as { toolName: string }).toolName) : p.type.replace(/^tool-/, "")))
      .filter((t) => t !== "share_plan"),
    plan: m.parts
      .filter((p) => p.type === "tool-share_plan" || ("toolName" in p && (p as { toolName: string }).toolName === "share_plan"))
      .flatMap((p) => ((p as { input?: { steps?: unknown } }).input?.steps as string[] | undefined) ?? []),
    trace: (m.parts.find((p) => p.type === "data-trace") as { data?: Trace } | undefined)?.data,
  }));
  return (
    <ChatFrame
      turns={turns}
      busy={busy}
      error={error ? "LaMP couldn't answer just now. Try again in a moment." : undefined}
      onSend={(text) => sendMessage({ text })}
    />
  );
}

/* ---------- Shared frame ---------- */

function ChatFrame({
  turns,
  busy,
  error,
  onSend,
}: {
  turns: Turn[];
  busy: boolean;
  error?: string;
  onSend: (text: string) => void;
}) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, busy]);

  function submit(text: string) {
    const t = text.trim();
    if (!t || busy) return;
    setDraft("");
    onSend(t);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {turns.length === 0 && (
          <div>
            <p className="text-ink-2">
              Ask about your money in plain words. LaMP checks your real figures before answering, and anything it suggests waits for your approval.
            </p>
          </div>
        )}
        {turns.map((t, ti) => (
          <div key={t.id} className={cn("flex flex-col gap-1.5", t.role === "user" ? "items-end" : "items-start")}>
            {t.plan && t.plan.length > 0 && (
              <div className="w-full max-w-[92%] rounded-[var(--radius)] border border-rule bg-board p-3">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-ink-2">
                  <ListChecks className="size-4" aria-hidden /> LaMP&apos;s plan
                </p>
                <ol className="mt-1.5 space-y-1">
                  {t.plan.map((step, i) => {
                    const done = !(busy && ti === turns.length - 1) || !!t.text;
                    return (
                      <li key={`${step}-${i}`} className="flex items-start gap-2 text-sm text-ink">
                        <span
                          className={cn(
                            "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-[2px] border",
                            done ? "border-cash bg-cash text-primary-foreground" : "border-rule"
                          )}
                          aria-hidden
                        >
                          {done && <Check className="size-3" />}
                        </span>
                        <span>
                          {step}
                          <span className="sr-only">{done ? " (done)" : " (in progress)"}</span>
                        </span>
                      </li>
                    );
                  })}
                </ol>
              </div>
            )}
            {t.tools && t.tools.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {t.tools.map((tool, i) => (
                  <span key={`${tool}-${i}`} className="inline-flex items-center gap-1 rounded-[2px] bg-muted px-2 py-0.5 text-xs font-semibold text-ink-2">
                    <Wrench className="size-3" aria-hidden />{" "}
                    {tool === "propose_action" ? "Proposed an action" : `Checked ${tool.replace(/^get_/, "").replaceAll("_", " ")}`}
                  </span>
                ))}
              </div>
            )}
            <div
              className={cn(
                "max-w-[92%] rounded-[var(--radius)] px-3.5 py-2.5 whitespace-pre-line",
                t.role === "user" ? "bg-primary text-primary-foreground" : "border border-rule bg-board text-ink"
              )}
            >
              {t.text}
            </div>
            {t.trace && t.trace.blocked && (
              <p className="flex items-center gap-1.5 text-xs font-semibold text-alert">
                <ShieldAlert className="size-3.5" aria-hidden /> Held back: a money figure didn&apos;t match LaMP&apos;s engines
              </p>
            )}
            {t.trace && !t.trace.blocked && t.trace.total > 0 && (
              <p className="flex items-center gap-1.5 text-xs font-semibold text-stock">
                <ShieldCheck className="size-3.5" aria-hidden /> {t.trace.traced} of {t.trace.total} money figures traced to LaMP&apos;s engines
              </p>
            )}
          </div>
        ))}
        {busy && <p className="text-sm font-semibold text-ink-2">LaMP is checking your figures…</p>}
        {error && <p className="text-sm font-semibold text-alert">{error}</p>}
        <div ref={endRef} />
      </div>
      <div className="border-t border-rule p-3">
        <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              disabled={busy}
              onClick={() => submit(s)}
              className="h-9 shrink-0 rounded-full border border-rule bg-board px-3 text-sm font-semibold text-ink hover:border-cash hover:text-cash disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(draft);
          }}
          className="flex gap-2"
        >
          <label htmlFor="chat-input" className="sr-only">
            Your question
          </label>
          <input
            id="chat-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask about cash, stock or loans"
            className="h-11 min-w-0 flex-1 rounded-[var(--radius)] border border-input bg-board px-3 text-base placeholder:text-ink-2"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            aria-label="Send"
            className="inline-flex size-11 items-center justify-center rounded-[var(--radius)] bg-primary text-primary-foreground disabled:opacity-50"
          >
            <ArrowUp className="size-5" aria-hidden />
          </button>
        </form>
      </div>
    </div>
  );
}
