# LaMP-Copilot

An AI finance officer for neighborhood pharmacies. It turns supplier invoices and a paper sales book into real accounts, manages cash across many suppliers, recovers money tied up in expiring stock, and finds the cheapest way to fund the next order.

Entry for the 2026 Shenzhen International FinTech Competition (FinTechathon), International Track, **Topic E: SME Finance Copilot**. Deadline: 20 Oct 2026, 23:59 Beijing time (21:59 Bangladesh time).

**Demo video (4:51, English and Chinese subtitles):** https://youtu.be/YPS1GpFBRPQ

## Start here
1. [docs/IDEA_AND_PROBLEM.md](docs/IDEA_AND_PROBLEM.md): the problem, the idea and the demo story
2. [docs/PLAN.md](docs/PLAN.md): architecture, API contract, golden numbers, milestones, team rules
3. Your task file in [docs/tasks/](docs/tasks/)

Background research with sources: [docs/LaMP_Idea_Brief.md](docs/LaMP_Idea_Brief.md). `docs/archive/` holds an older version of the idea; don't build from it.

## Team
Each person works only in their own folders, so no two people edit the same file.

| Person | Part | Share | Task file |
|---|---|---|---|
| **Farhan Tahsin Khan** | Engines & API, LLM client, photo reading, evaluation | 49% | [docs/tasks/farhan-engines-api.md](docs/tasks/farhan-engines-api.md) |
| **A K M Ishmam Tahmid** (@ishmam259, team lead) | Frontend, copilot chat, documents, pitch | 51% | [docs/tasks/ishmam259-frontend-pitch.md](docs/tasks/ishmam259-frontend-pitch.md) |

The spec for the AI work is in [docs/tasks/pritom-agents-docs.md](docs/tasks/pritom-agents-docs.md); Pritom left the team on 17 Oct and his part is split as above.

Farhan writes the shared API contract (`contracts/`, `backend/app/schemas/`) and the sample pharmacy (`seed/`) first. Everyone else builds against those.

**Commit about every 10 minutes and push each time** (`git pull --rebase` first). No AI attribution lines in commits. Full rules: [docs/PLAN.md](docs/PLAN.md) section 1, and for AI coding tools [CLAUDE.md](CLAUDE.md) (Claude Code) and [AGENTS.md](AGENTS.md) (Codex/ChatGPT), which hold the same rules.

## Stack
- **Frontend:** Next.js (TypeScript), Tailwind, shadcn/ui, Recharts, Vercel AI SDK `useChat`
- **Backend:** Python FastAPI, Pydantic, PydanticAI, OpenAI Responses API (`gpt-6-luna`)
- **Data:** PostgreSQL
- **Ops:** Docker Compose, pytest

## Setup
Copy `.env.example` to `.env` and add your own OpenAI API key. Never commit `.env`. The team's total OpenAI budget is $20; tests and the demo use replay mode, which makes no API calls.

## Run it
You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) running. Python 3.12 and Node 20+ are only needed for the tests, the demo script and the frontend.

**1. Start the database, the API and the frontend**
```bash
cp -n .env.example .env   # -n keeps an .env you already filled in
docker compose up -d --build
```
On first start the API loads the demo pharmacy, Green Life Pharmacy in Bogura. The first build takes a few minutes. The copied `.env` has `DEV_MODE=true`, which turns on the demo controls (Reset, the supplier-reply simulator) and a dev registry key; nothing else needs filling in. The owner PIN is `2468`.

| What | Where |
|---|---|
| App (built frontend, live API) | http://127.0.0.1:3001 |
| API | http://127.0.0.1:8000/api/v1/health |
| API docs (try every endpoint) | http://127.0.0.1:8000/docs |
| Live audit log (SSE) | http://127.0.0.1:8000/api/v1/logs/stream |
| PostgreSQL | `localhost:5433`, user/password/database `lamp` |

Use `127.0.0.1` rather than `localhost`: some Docker Desktop setups on Windows don't answer on IPv6. The database is on host port 5433 because a local PostgreSQL install often already holds 5432.

**2. Optional: run the frontend in dev mode** (in another terminal, for editing the UI)
```bash
cd frontend
npm ci
echo "NEXT_PUBLIC_API_MODE=live" > .env.local
echo "BACKEND_URL=http://127.0.0.1:8000" >> .env.local
npm run dev
```
Open http://localhost:3000. Without `.env.local` the frontend runs on its built-in mock data.

**3. Reset the demo**
- `POST /api/v1/dev/reset` loads the seed only. Use it before a live demo, where the owner photographs the 2 invoices and the sales-book page.
- `POST /api/v1/dev/reset?with_demo_captures=true` loads the seed plus those three captures already confirmed. Every golden number in [docs/PLAN.md](docs/PLAN.md) section 6 holds in this state.

**4. Run the scripted demo and export the execution trace**
```bash
python scripts/demo_run.py
```
It runs the whole story against the API, checking each golden number: reset, captures, accounts, expiry, return claim, order trim, funding plan, supplier extension, consent, loan application, a refused duplicate application, and the lender's decision. Then it writes `logs/sandbox_execution_trace.log`. `python scripts/export_trace.py` exports the log on its own at any time.

**Live judge link (Render).** `render.yaml` sets up a free PostgreSQL database, the API (`backend/Dockerfile.render`) and the frontend. In Render: New → Blueprint → this repo. Then set `BACKEND_URL` on `lamp-web` to the API's URL (for example `https://lamp-api.onrender.com`) and redeploy it. Chat stays in replay (no OpenAI key on the server), reset loads the demo captures, and the demo resets itself every 60 minutes because judges share one database. Free services sleep when idle, so the first request can take about a minute.

**5. Run the tests**
```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m pytest
```
Tests use an in-memory SQLite database by default. To run them against the Docker PostgreSQL, create a test database once (`docker compose exec db createdb -U lamp lamp_test`), then set `TEST_DATABASE_URL=postgresql+psycopg://lamp:lamp@127.0.0.1:5433/lamp_test` before running pytest.

**Replay vs live mode.** `LLM_MODE=replay` (the default, used by tests and the demo script) makes no OpenAI calls. The demo photos in `seed/images/` and the 27 evaluation photos in `eval/images/` replay from saved recordings; any other photo returns a sample draft to correct. The copilot chat answers its four suggested questions offline from the same engines. Set `LLM_MODE=live` and `OPENAI_API_KEY` in `.env` to read real photos with OpenAI. The team budget is $20, so keep live runs short.

**Regenerating files.** `python scripts/build_seed.py` rebuilds `seed/` from the numbers in that script. `python scripts/export_openapi.py` rebuilds `contracts/openapi.json` and `contracts/examples/` from real API responses.
