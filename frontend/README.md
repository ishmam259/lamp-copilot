# LaMP frontend

Next.js 16 (App Router, TypeScript), Tailwind 4, shadcn/ui (Base UI), SWR, AI SDK `useChat`. Mobile-first, installable as a PWA, light and dark mode.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Backend

The app always talks to the FastAPI backend: `/api/v1/*` is proxied to it (see `next.config.ts`), so there's no CORS setup. Start the backend first (repo-root README, "Run it"). The default address is `http://127.0.0.1:8000`; to use another, create `.env.local` with `BACKEND_URL=http://host:port`. Chat goes to `POST /api/v1/chat` (the copilot chat stream).

## Docker

`frontend/Dockerfile` builds a small production server (Next.js standalone, port 3000). `BACKEND_URL` is baked in at build time, so it's a build arg, not runtime env (default `http://backend:8000`, the compose service name).

The service block in the repo-root `docker-compose.yml`:

```yaml
  frontend:
    build:
      context: ./frontend
      args:
        BACKEND_URL: http://backend:8000
    ports:
      # 3001 on the host, so it can run next to `npm run dev` on 3000.
      - "3001:3000"
    depends_on:
      - backend
```

Then `docker compose up -d --build` starts the database, API and app; open http://localhost:3001 and load the pharmacy data as in the repo-root README. `npm run dev` keeps http://localhost:3000, so both can run at once.

## Where things are

- `src/lib/forecast.ts`: row labels and amounts taken from the forecast's `items`.
- `src/lib/types.ts`: shapes from `docs/PLAN.md` section 4.3. Keep in sync with `backend/app/schemas`.
- `src/lib/api.ts`: one function per endpoint and the SWR hooks.
- `src/app/*`: screens (Today, Cash, Capture, Stock, Funding, Actions, Passport, Lender view, Audit log).
- `src/components/`: shell, panels, cash route line, live log, chat drawer, theme toggle.

## Design

Full design system: [`DESIGN.md`](../DESIGN.md) at the repo root (tokens, type, components, do's and don'ts). Read it before changing any UI.

Direction "Station Board": railway-green shell, white working panels, one dark-green departures board per screen for the message that matters most. Colour carries state only: red = problem, amber = needs you, green = go/good. Run Impeccable's detector before committing UI changes:

```bash
../.claude/skills/impeccable/scripts/impeccable detect --json http://localhost:3000/
```

Note: after editing `globals.css`, restart the dev server (`rm -rf .next`) if styles don't update.
