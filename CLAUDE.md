# Sakhi Health (PS1 hackathon)

Life-stage women's health companion: one hub, one orchestrator, four rule-based agents (Health Story, PCOS/Endo, Menopause, Maternal). Turns ~90 days of logs into an explainable "health story" plus a doctor-ready PDF, in English and Hindi, with three seeded personas (Priya, Meena, Sunita). Rules decide, the LLM only explains. Awareness only: never diagnose, prescribe or name doses; every flag carries `evidence[]`.

## Stack
Next.js 16 + React 19 + TS + Tailwind 4 + shadcn/ui (base-nova) + motion + Recharts + lucide + canvas-confetti · FastAPI + SQLModel + SQLite (Python 3.13) · Claude API (server-side, template fallback) · fpdf2 + uharfbuzz + Noto Devanagari · pytest, ruff, eslint.

## Repo map
- `frontend/src/{app,components/{ui,viz,motion},lib,types,messages}`
- `backend/app/{api,agents,services,models,seed}`, `backend/config/clinical_rules.yaml`, `backend/tests`
- `docs/guide.md`: build guide (phases §5, types §4, API §3, design §8)
- `docs/brief.md`: original brief (do not re-read)
- `.claude/agents/`: phase subagents

## Commands
- BE: `cd backend && source .venv/Scripts/activate && uvicorn app.main:app --reload --port 8000`
- Seed: `python -m app.seed.run` (from backend/)
- FE: `cd frontend && npm run dev` (/api proxied to :8000)
- Test BE: `ruff check app tests -q && pytest -q --no-header -x`
- Test FE: `npm run lint -- --quiet && npx tsc --noEmit && npm run build`
- Types: `npm run gen:types` after any `schemas.py` change

## Conventions
- snake_case JSON both sides; agent ids `health_story|pcos_endo|menopause|maternal`
- Thresholds only in `clinical_rules.yaml` (with `source:`); rules are pure functions
- Wording: "patterns commonly associated with…", "consider discussing with a doctor"
- BE errors → `{error:{code,message}}`; LLM/PDF failures degrade, never break the demo
- UI: use `frontend-design` skill; tokens + motion rules in guide §8; respect reduced motion
- Commit per phase: `feat(p<N>): <phase name>`; never commit `.env`

## Current phase
**Phase 2: Seed + persona switch** done. Next: Phase 3.

## Token rules
- Never re-read `docs/brief.md`; use this file plus the relevant guide phase row and §5.1 note.
- Use Grep/Glob and line ranges, not whole-file reads.
- Delegate each phase to its subagent (guide §5 Owner); subagents return summaries only.
- Write each file once, complete. No exploratory rewrites, unrequested refactors or long replies.
- Batch independent tool calls. Run tests quietly (failures only).
- After each phase: acceptance check → `qa-reviewer` → commit → `docs-scribe` updates pointer → tell user to `/clear`.
- Plan mode before any phase with budget L (P4, P8, P12).
- Prefer well-known libraries over custom code.
