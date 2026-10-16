# LaMP-Copilot

An AI finance officer for neighborhood pharmacies. It turns supplier invoices and a paper sales book into real accounts, manages cash across many suppliers, recovers money tied up in expiring stock, and finds the cheapest way to fund the next order.

Entry for the 2026 Shenzhen International FinTech Competition (FinTechathon), International Track, **Topic E: SME Finance Copilot**. Deadline: 20 Oct 2026, 23:59 Beijing time (UTC+8).

The full idea, research and scope are in [docs/LaMP_Idea_Brief.md](docs/LaMP_Idea_Brief.md). `docs/archive/` holds an older version of the idea; don't build from it.

## Stack
- **Frontend:** Next.js (TypeScript), Tailwind, shadcn/ui, Recharts, Vercel AI SDK `useChat`
- **Backend:** Python FastAPI, Pydantic, PydanticAI, OpenAI Responses API (`gpt-6-luna`)
- **Data:** PostgreSQL
- **Ops:** Docker Compose, pytest

## Who owns what
Each account works only in its own folders, so no two people edit the same file.

| Account | Share | Folders |
|---|---|---|
| 1: Engines & API | 34% | `backend/app/api`, `backend/app/engines`, `backend/app/db`, `contracts/`, `seed/`, `tests/`, `docker-compose.yml` |
| 2: AI agents & documents | 33% | `backend/app/agents`, `eval/`, `docs/` |
| 3: Frontend & pitch | 33% | `frontend/`, `deck/`, `video/` |

Account 1 writes the shared API contract (`contracts/`) and the sample pharmacy (`seed/`) first. Everyone else builds against those.

## Setup
Copy `.env.example` to `.env` and add your OpenAI API key. Never commit `.env`.

Run instructions will be added once the services exist.
