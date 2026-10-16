# LaMP-Copilot: rules for AI coding sessions

This repo is a FinTechathon 2026 team entry (International Track, Topic E: SME Finance Copilot). Three people build it, each with their own AI coding session. Follow these rules exactly.

## Read first
- `docs/IDEA_AND_PROBLEM.md`: what we're building and why
- `docs/PLAN.md`: architecture, contract, golden numbers, milestones
- `docs/tasks/<person>.md`: the task list for whoever you're working with

## Ownership: only edit your person's folders
| Person | Folders |
|---|---|
| Farhan (engines & API) | `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/schemas/`, `backend/app/db/`, `backend/app/engines/`, `backend/app/api/`, `contracts/`, `seed/green_life.json`, `seed/demo_captures/`, `tests/engines/`, `tests/api/`, `scripts/`, `logs/`, `docker-compose.yml`, `.env.example`, README "Run it" section |
| Pritom (agents & docs) | `backend/app/agents/`, `tests/agents/`, `eval/`, `seed/images/`, `docs/technical/`, `docs/security/` |
| @ishmam259 (frontend & pitch, team lead) | `frontend/`, `deck/`, `video/`, `docs/IDEA_AND_PROBLEM.md`, `docs/PLAN.md`, `docs/tasks/`, `CLAUDE.md` |

If a change is needed outside your person's folders, stop and tell them to ask the owner. Never edit `contracts/` or `backend/app/schemas/` unless you're working with Farhan.

## Git
- Commit about every 10 minutes and push each time. Run `git pull --rebase` before pushing.
- Everyone commits to `main`. Folder ownership prevents conflicts. On a rebase conflict, stop and ask the human.
- Commit messages are short and plain, prefixed by area: `engines: ...`, `agents: ...`, `frontend: ...`, `docs: ...`.
- **Never add `Co-Authored-By` lines or any AI or Claude attribution** to commits or PR descriptions. Commits are made under the human's own git identity.
- Never commit `.env` or any API key.

## Technical rules
- The app uses **OpenAI** (`gpt-6-luna` by default) through the **Responses API**, called only from `backend/app/agents/`. Don't add Anthropic or other LLM SDKs to the app.
- All money math lives in `backend/app/engines/` as deterministic Python. The LLM never computes money.
- The chat agent's tools are read-only plus `propose_action`. Never give it a tool that approves, executes, transfers money or contacts anyone.
- Engines use `settings.as_of_date` from the pharmacy, never the real clock.
- Tests never call the OpenAI API (`LLM_MODE=replay`).
- **OpenAI budget is $20 total for the team.** Avoid loops that call the API; resize images to ≤ 1,600 px.
- The golden numbers in `docs/PLAN.md` section 6 must be reproduced exactly.
- English only in the app, docs and UI. No blockchain.
- Don't store medicine names linked to patients; patient dues are amounts only.
- Check current library docs (OpenAI SDK, PydanticAI, Next.js, AI SDK) before using an API name you aren't sure of.

## Deadline
Submission closes **20 Oct 2026, 23:59 Beijing time (21:59 Bangladesh time)**. Team freeze: 20 Oct, 18:00 Bangladesh time.
