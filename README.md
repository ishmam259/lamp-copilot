# LaMP-Copilot

An AI finance officer for neighborhood pharmacies. It turns supplier invoices and a paper sales book into real accounts, manages cash across many suppliers, recovers money tied up in expiring stock, and finds the cheapest way to fund the next order.

Entry for the 2026 Shenzhen International FinTech Competition (FinTechathon), International Track, **Topic E: SME Finance Copilot**. Deadline: 20 Oct 2026, 23:59 Beijing time (21:59 Bangladesh time).

## Start here
1. [docs/IDEA_AND_PROBLEM.md](docs/IDEA_AND_PROBLEM.md): the problem, the idea and the demo story
2. [docs/PLAN.md](docs/PLAN.md): architecture, API contract, golden numbers, milestones, team rules
3. Your task file in [docs/tasks/](docs/tasks/)

Background research with sources: [docs/LaMP_Idea_Brief.md](docs/LaMP_Idea_Brief.md). `docs/archive/` holds an older version of the idea; don't build from it.

## Team
Each person works only in their own folders, so no two people edit the same file.

| Person | Part | Share | Task file |
|---|---|---|---|
| **Farhan** | Engines & API | 34% | [docs/tasks/farhan-engines-api.md](docs/tasks/farhan-engines-api.md) |
| **Pritom** | AI agents & documents | 33% | [docs/tasks/pritom-agents-docs.md](docs/tasks/pritom-agents-docs.md) |
| **@ishmam259** (team lead) | Frontend & pitch | 33% | [docs/tasks/ishmam259-frontend-pitch.md](docs/tasks/ishmam259-frontend-pitch.md) |

Farhan writes the shared API contract (`contracts/`, `backend/app/schemas/`) and the sample pharmacy (`seed/`) first. Everyone else builds against those.

**Commit about every 10 minutes and push each time** (`git pull --rebase` first). No AI attribution lines in commits. Full rules: [docs/PLAN.md](docs/PLAN.md) section 1 and [CLAUDE.md](CLAUDE.md).

## Stack
- **Frontend:** Next.js (TypeScript), Tailwind, shadcn/ui, Recharts, Vercel AI SDK `useChat`
- **Backend:** Python FastAPI, Pydantic, PydanticAI, OpenAI Responses API (`gpt-6-luna`)
- **Data:** PostgreSQL
- **Ops:** Docker Compose, pytest

## Setup
Copy `.env.example` to `.env` and add your own OpenAI API key. Never commit `.env`. The team's total OpenAI budget is $20; tests and the demo use replay mode, which makes no API calls.

## Run it
Farhan will fill this in once the services exist.
