"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { LockKeyhole } from "lucide-react";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { ApiError, LOCKED_EVENT, PID, UNLOCKED_EVENT, apiGet, errorDetail, unlock } from "@/lib/api";

const PIN_LENGTH = 4;

/**
 * Owner screens need a session (an HttpOnly cookie set after the PIN). Shows the PIN screen
 * on first load and whenever any call returns 401. The lender view uses lender keys instead.
 */
export function PinGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const lenderView = pathname.startsWith("/lender");
  const [state, setState] = useState<"checking" | "locked" | "open">("checking");

  useEffect(() => {
    let alive = true;
    apiGet(`/pharmacies/${PID}/pause`)
      .then(() => alive && setState("open"))
      .catch((e) => alive && setState(e instanceof ApiError && e.status === 401 ? "locked" : "open"));
    const lock = () => setState("locked");
    const open = () => setState("open");
    window.addEventListener(LOCKED_EVENT, lock);
    window.addEventListener(UNLOCKED_EVENT, open);
    return () => {
      alive = false;
      window.removeEventListener(LOCKED_EVENT, lock);
      window.removeEventListener(UNLOCKED_EVENT, open);
    };
  }, []);

  if (lenderView || state === "open") return <>{children}</>;
  if (state === "checking") return <div className="min-h-dvh bg-shelf" aria-busy="true" />;
  return <PinScreen />;
}

function PinScreen() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(value: string) {
    if (value.length !== PIN_LENGTH || busy) return;
    setBusy(true);
    setError(null);
    try {
      await unlock(value);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 401
          ? "That PIN isn't right. Try again."
          : e instanceof ApiError && e.status === 429
            ? errorDetail(e, "Too many wrong PINs. Try again later.")
            : "Couldn't reach LaMP. Try again."
      );
      setPin("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-rail px-4 text-rail-ink">
      <div className="w-full max-w-sm text-center">
        <p className="font-board text-[2.5rem] leading-none font-extrabold tracking-tight">
          La<span className="text-signal">M</span>P
        </p>
        <div className="mt-8 rounded-[8px] bg-shelf p-6 text-ink">
          <LockKeyhole className="mx-auto size-7 text-cash" aria-hidden />
          <h1 className="mt-3 text-xl font-bold">Enter your PIN</h1>
          <p className="mt-1 text-sm text-ink-2">Your books and approvals stay locked until you do.</p>
          <form
            className="mt-5 flex justify-center"
            onSubmit={(e) => {
              e.preventDefault();
              submit(pin);
            }}
          >
            <label htmlFor="owner-pin" className="sr-only">
              Owner PIN
            </label>
            <InputOTP
              id="owner-pin"
              maxLength={PIN_LENGTH}
              value={pin}
              onChange={setPin}
              onComplete={submit}
              disabled={busy}
              autoFocus
              inputMode="numeric"
              pattern="^[0-9]*$"
              aria-invalid={!!error}
            >
              <InputOTPGroup>
                {Array.from({ length: PIN_LENGTH }, (_, i) => (
                  <InputOTPSlot key={i} index={i} className="size-14 text-2xl" />
                ))}
              </InputOTPGroup>
            </InputOTP>
          </form>
          <p role="status" aria-live="polite" className="mt-3 min-h-5 text-sm font-semibold text-alert">
            {error ?? (busy ? <span className="text-ink-2">Checking…</span> : null)}
          </p>
          <p className="mt-2 text-xs text-ink-2">Sandbox demo PIN: 2468</p>
        </div>
      </div>
    </main>
  );
}

/** Asks the owner PIN again before an approval that needs it (loan applications). */
export function PinPrompt({
  title,
  onSubmit,
  onCancel,
}: {
  title: string;
  /** true when done; false for a wrong PIN; a string to show (for example the lockout). */
  onSubmit: (pin: string) => Promise<boolean | string>;
  onCancel: () => void;
}) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(value: string) {
    if (value.length !== PIN_LENGTH || busy) return;
    setBusy(true);
    setError(null);
    const ok = await onSubmit(value);
    setBusy(false);
    if (ok !== true) {
      setError(ok === false ? "That PIN isn't right. Try again." : ok);
      setPin("");
    }
  }

  return (
    <div className="text-center">
      <p className="text-sm text-ink-2">{title}</p>
      <div className="mt-4 flex justify-center">
        <InputOTP
          aria-label="Owner PIN"
          maxLength={PIN_LENGTH}
          value={pin}
          onChange={setPin}
          onComplete={submit}
          disabled={busy}
          autoFocus
          inputMode="numeric"
          pattern="^[0-9]*$"
          aria-invalid={!!error}
        >
          <InputOTPGroup>
            {Array.from({ length: PIN_LENGTH }, (_, i) => (
              <InputOTPSlot key={i} index={i} className="size-12 text-xl" />
            ))}
          </InputOTPGroup>
        </InputOTP>
      </div>
      <p role="status" aria-live="polite" className="mt-3 min-h-5 text-sm font-semibold text-alert">
        {error}
      </p>
      <button type="button" onClick={onCancel} className="mt-2 text-sm font-semibold text-ink-2 hover:text-ink">
        Cancel
      </button>
    </div>
  );
}
