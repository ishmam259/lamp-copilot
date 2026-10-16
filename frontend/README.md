# LaMP frontend

Next.js 16 (App Router, TypeScript), Tailwind 4, shadcn/ui (Base UI), SWR, AI SDK `useChat`. Mobile-first, installable as a PWA, light and dark mode.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Mock or live data

- **Mock (default):** everything runs in the browser from `src/mocks/data.ts`, which matches the golden numbers in `docs/PLAN.md`. Approving actions really changes state, and the chat gives pre-recorded answers. "Reset demo data" (desktop rail) or a page reload starts over.
- **Live:** create `.env.local` with:

  ```
  NEXT_PUBLIC_API_MODE=live
  BACKEND_URL=http://localhost:8000
  ```

  `/api/v1/*` is proxied to the FastAPI backend (see `next.config.ts`), so there's no CORS setup. Chat goes to `POST /api/v1/chat` (Pritom's stream).

## Where things are

- `src/lib/types.ts`: shapes from `docs/PLAN.md` section 4.3. Keep in sync with `backend/app/schemas`.
- `src/lib/api.ts`: one function per endpoint, SWR hooks, and the mock store.
- `src/app/*`: screens (Today, Cash, Capture, Stock, Funding, Actions, Passport, Lender view, Audit log).
- `src/components/`: shell, panels, cash route line, live log, chat drawer, theme toggle.

## Design

Full design system: [`DESIGN.md`](../DESIGN.md) at the repo root (tokens, type, components, do's and don'ts). Read it before changing any UI.

Direction "Station Board": railway-green shell, white working panels, one dark-green departures board per screen for the message that matters most. Colour carries state only: red = problem, amber = needs you, green = go/good. Run Impeccable's detector before committing UI changes:

```bash
../.claude/skills/impeccable/scripts/impeccable detect --json http://localhost:3000/
```

Note: after editing `globals.css`, restart the dev server (`rm -rf .next`) if styles don't update.
