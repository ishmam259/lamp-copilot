"use client";

import { useEffect, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { ArrowUp, Wrench } from "lucide-react";
import { cn } from "cn";
import { API_MODE, PID, proposeAction } from "@/lib/api";

const SUGGESTIONS = [
  "How did we do this month?",
  "Can I pay Supplier A's order next week?",
  "What is expiring?",
  "Why did the bank offer 75%?",
];

type Turn = { id: string; role: "user" | "assistant"; text: string; tools?: string[] };

export function ChatPanel() {
  return API_MODE === "live" ? <LiveChat /> : <DemoChat />;
}

/* ---------- Live: Pritom's /api/v1/chat, AI SDK UI message stream ---------- */

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
      .map((p) => ("toolName" in p ? String((p as { toolName: string }).toolName) : p.type.replace(/^tool-/, ""))),
  }));
  return (
    <ChatFrame
      turns={turns}
      busy={busy}
      error={error ? "LaMP couldn't answer. Check your connection and try again." : undefined}
      onSend={(text) => sendMessage({ text })}
    />
  );
}

/* ---------- Demo: scripted answers built from the same figures as the screens ---------- */

const DEMO_ANSWERS: { match: RegExp; tools: string[]; text: string; propose?: () => Promise<unknown> }[] = [
  {
    match: /month|profit|how did/i,
    tools: ["get_accounts"],
    text:
      "In the last 30 days you sold BDT 412,500. At a 12% margin that's BDT 49,500 gross profit. After rent, salaries and utilities (BDT 36,000), you kept BDT 13,500.\n\nThe biggest drain to watch: BDT 18,400 of stock expires in the next 60 days.",
  },
  {
    match: /supplier a|pay|order|short/i,
    tools: ["get_forecast", "get_trim", "get_funding_plan"],
    text:
      "Not as it stands. On 26 Oct the Supplier A order is BDT 60,000, but you'll have about BDT 41,000. That's BDT 19,000 short.\n\nFirst, cut Montelukast from 30 to 12 boxes: it sells about 1 box every 5 days, so only 12 will sell before expiry. That saves BDT 10,800 and leaves you BDT 8,200 short.\n\nFor the BDT 8,200, ask Supplier A for 20 more days (free). If they haven't agreed by 23 Oct, take a mobile-wallet loan for BDT 182 in interest. I've put both in Actions for you to approve.",
    propose: async () => {
      await proposeAction("trim_order", { summary: "Cut Montelukast from 30 to 12 boxes on Supplier A's order", amount: 10800, order_id: "o-1" });
      await proposeAction("extension_request", { summary: "Ask Supplier A for 20 more days on BDT 8,200", amount: 8200, supplier: "Supplier A" });
    },
  },
  {
    match: /expir|stock|return/i,
    tools: ["get_expiry"],
    text:
      "6 batches worth BDT 18,400 expire within 60 days. Two of them, Omeprazole (BDT 4,800) and Cetirizine (BDT 4,400), can still go back to Suppliers B and C. That's BDT 9,200 you can recover. The return claim is waiting in Actions.\n\nThe other 4 batches are past their return window. Sell them first.",
  },
  {
    match: /bank|75|passport|offer|credit/i,
    tools: ["get_passport"],
    text:
      "Because of your payment record. You paid 38 of your last 41 supplier invoices on time, and every one was confirmed by the supplier. LaMP takes a cautious view of that record (0.826 on a 0 to 1 scale) and combines it with a 3% default risk.\n\nThat earns a 75.2% advance. Each on-time payment pushes it up.",
  },
];

function DemoChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);

  async function send(text: string) {
    const id = String(Date.now());
    setTurns((t) => [...t, { id: `u${id}`, role: "user", text }]);
    setBusy(true);
    const answer = DEMO_ANSWERS.find((a) => a.match.test(text));
    await new Promise((r) => setTimeout(r, 900));
    if (answer?.propose) await answer.propose();
    setTurns((t) => [
      ...t,
      answer
        ? { id: `a${id}`, role: "assistant", text: answer.text, tools: answer.tools }
        : {
            id: `a${id}`,
            role: "assistant",
            text: "I can help with your accounts, cash ahead, expiring stock, suppliers and funding. Try one of the questions below.",
          },
    ]);
    setBusy(false);
  }

  return <ChatFrame turns={turns} busy={busy} onSend={send} demo />;
}

/* ---------- Shared frame ---------- */

function ChatFrame({
  turns,
  busy,
  error,
  onSend,
  demo = false,
}: {
  turns: Turn[];
  busy: boolean;
  error?: string;
  onSend: (text: string) => void;
  demo?: boolean;
}) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [turns.length, busy]);

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
          <div className="space-y-3">
            <p className="text-ink-2">
              Ask about your money in plain words. LaMP checks your real figures before answering, and anything it suggests waits for your approval.
            </p>
            {demo && <p className="text-xs text-ink-2">Demo mode: answers are pre-recorded from the demo pharmacy's figures.</p>}
          </div>
        )}
        {turns.map((t) => (
          <div key={t.id} className={cn("flex flex-col gap-1.5", t.role === "user" ? "items-end" : "items-start")}>
            {t.tools && t.tools.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {t.tools.map((tool, i) => (
                  <span key={`${tool}-${i}`} className="inline-flex items-center gap-1 rounded-[2px] bg-muted px-2 py-0.5 text-xs font-semibold text-ink-2">
                    <Wrench className="size-3" aria-hidden /> Checked {tool.replace(/^get_/, "").replaceAll("_", " ")}
                  </span>
                ))}
              </div>
            )}
            <div
              className={cn(
                "max-w-[92%] rounded-[var(--radius)] px-3.5 py-2.5 whitespace-pre-line",
                t.role === "user" ? "bg-cash text-white" : "border border-rule bg-board text-ink"
              )}
            >
              {t.text}
            </div>
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
            className="inline-flex size-11 items-center justify-center rounded-[var(--radius)] bg-cash text-white disabled:opacity-50"
          >
            <ArrowUp className="size-5" aria-hidden />
          </button>
        </form>
      </div>
    </div>
  );
}
