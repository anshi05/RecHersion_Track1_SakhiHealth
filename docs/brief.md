# Project Brief: Unified Women's Health Platform (PS1)

*Master context document for the AI coding agent. Read fully before doing anything else.*

---

## 0. How to use this document (instructions to the agent)

1. **Read this entire brief first.** It contains the problem statement, product vision, architecture, data model, agent specs, build order and demo plan.
2. **Do not start implementing yet.** The next task you will be given is to create a `guide.md` (a concise, developer-facing build guide derived from this brief). Implementation starts only after that.
3. When writing `guide.md`, keep the build order in Section 15, the data model in Section 8 and the API in Section 12 as the source of truth. Improve them if you find gaps, but flag every deviation.
4. If something is ambiguous, state your assumption explicitly and continue. Ask the human only for decisions that block progress.
5. **Hackathon rule of thumb:** a working, polished, demo-able slice beats a broad, broken one. When in doubt, cut scope, never quality of the core flow.

---

## 1. Hackathon context

We are participating in a hackathon with two problem-statement tracks. **We chose PS1.**

**PS1: Women's Healthcare (CHOSEN)**

> Design and build a digital solution that addresses challenges in women's healthcare, such as gaps in diagnosis, symptom tracking, health awareness, or access to meaningful clinical insights. Develop an innovative solution that empowers women to better understand and manage their health.

**PS2: Women's Safety (NOT chosen)**

> Challenges in physical and digital environments: harassment, unsafe situations, privacy breaches, online threats, identity misuse. Build a solution that enables women to protect themselves, seek assistance or prevent harm, sensitive to safety and privacy.

**Why PS1:** PS2 is the more crowded track (SOS buttons, live location, fake calls). PS1 has fewer teams, rewards data visualization, and its wording ("gaps in diagnosis", "meaningful clinical insights") signals judges want something smarter than a period tracker.

**What judges will likely score:** innovation, real-world impact, technical implementation, UI/visualization quality, feasibility, ethical handling of sensitive health data, and demo clarity. Prize money is on offer, so the demo must be flawless.

---

## 2. Product vision

**Name (working):** *Sakhi Health* (placeholder; the team can rename).

**One-liner:** A life-stage women's health companion that follows a woman from first periods to pregnancy to menopause, spots symptom patterns doctors often miss, and helps her walk into the clinic prepared.

**Core insight:** Women's conditions (PCOS, endometriosis, thyroid disorders, anemia, perimenopause) are frequently dismissed or diagnosed late (endometriosis is often cited as taking 7 to 10 years; *verify the figure and source before putting it in the pitch*). Part of the gap is communication: patients cannot summarize months of symptoms in a 5-minute consult. We turn scattered daily logs into a structured, evidence-style **"health story"** a doctor can read in 60 seconds.

**Platform framing:** Not four apps. **One central hub + one orchestrator + four specialist agents** sharing one data model and one set of services. Women's health needs change by life stage, and the app adapts to who the user is *right now*.

### Positioning and ethics (non-negotiable)

- The product provides **awareness, pattern detection and doctor-prep. It does NOT diagnose or prescribe.**
- Wording is always "patterns commonly associated with..." and "consider discussing with a doctor", never "you have X".
- Every flag shows the **reasoning** (which inputs triggered it). Explainability is a feature.
- Privacy-first: minimal data collection, no real PII in demo, consent screen, delete-my-data option.

---

## 3. Goals and non-goals

**Goals (MVP)**

- Single web app (mobile-responsive) with a unified timeline and daily check-in.
- Orchestrator that routes to the right agent(s) and visibly shows its decision.
- Four agents with rule-based, explainable logic.
- Doctor-ready PDF report.
- Hindi + English UI toggle (at least for key screens and report).
- Three seeded demo personas switchable in one click.
- Visually impressive dashboard (heatmaps, cycle timeline, risk gauges).

**Non-goals (do not build)**

- Real authentication providers, payments, real telemedicine, real doctor directory integrations.
- Training ML models. Use rules plus LLM for language only.
- Image/ultrasound analysis, wearables integration.
- Anything that claims clinical validation.

---

## 4. Users and demo personas

| Persona | Age | Stage | Story | Agent(s) that activate |
| --- | --- | --- | --- | --- |
| **Priya** | 24 | Reproductive | Irregular cycles (35 to 60 days), acne, facial hair growth, fatigue, weight gain | Health Story + PCOS/Endo Screener |
| **Meena** | 46 | Perimenopause | Cycle changes, night sweats, poor sleep, mood swings, palpitations | Health Story + Menopause Companion |
| **Sunita** | 28 | Pregnant (week \~30) | Rising BP readings, headaches, swelling, low Hb | Health Story + Maternal Monitor (urgent alert) |
| *(optional)* **Ananya** | 19 | Reproductive | Severe period pain, pain with intercourse, missing college | Health Story + Endo screening path |

Each persona has **\~90 days of seeded daily logs** so charts look rich on first load.

---

## 5. System architecture

```
                 ┌──────────────────────────┐
                 │       CENTRAL HUB        │
                 │ Profile · Daily check-in │
                 │  Unified health timeline │
                 └────────────┬─────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │    ORCHESTRATOR AGENT    │
                 │ Reads profile + logs     │
                 │ Decides which agents run │
                 └─┬──────┬───────┬───────┬─┘
                   │      │       │       │
            ┌──────▼─┐ ┌──▼─────┐ ┌▼──────┐ ┌▼────────┐
            │Health  │ │PCOS /  │ │Meno-  │ │Maternal │
            │Story   │ │Endo    │ │pause  │ │Monitor  │
            └───┬────┘ └───┬────┘ └──┬────┘ └───┬─────┘
                └──────────┴────┬────┴──────────┘
                                ▼
                 ┌──────────────────────────┐
                 │     SHARED SERVICES      │
                 │ Rule engine · LLM layer  │
                 │ Care navigator · PDF     │
                 │ Safety guardrails · i18n │
                 └──────────────────────────┘
```

**Design principles**

1. **One shared engine, thin agents.** Each agent is a small module implementing a common interface; heavy lifting lives in shared services.
2. **Rules decide, LLM explains.** Flags, scores and routing are deterministic and testable. The LLM only writes plain-language summaries, doctor questions and translations. The app must still work (with template text) if the LLM call fails.
3. **Safety bypass.** Maternal red flags and any emergency symptom skip the normal flow and show an urgent screen.
4. **Everything explainable.** Every output carries `evidence[]` listing the inputs and rules that produced it.

---

## 6. Tech stack (recommended; change only with reason)

| Layer | Choice | Notes |
| --- | --- | --- |
| Frontend | Next.js (React) + TypeScript + Tailwind | Responsive, mobile-first |
| Charts | Recharts (heatmap may need a custom grid) | Cycle timeline, symptom heatmap, gauges |
| Backend | FastAPI (Python) | Agents are Python modules |
| DB | SQLite (via SQLModel/SQLAlchemy) | Zero setup; swappable for Supabase |
| LLM | Claude API (server-side only, key in `.env`) | Summaries, doctor questions, Hindi |
| PDF | ReportLab (server) or jsPDF (client) | Pick one; must render Hindi (bundle a Devanagari font such as Noto Sans Devanagari) |
| Voice input | Web Speech API | Optional, English/Hindi |
| Testing | pytest for rule engine | Unit tests on every rule |

Repo layout:

```
/frontend     Next.js app
/backend
  /app
    main.py
    /api          routers
    /agents       base.py, orchestrator.py, health_story.py, pcos_endo.py, menopause.py, maternal.py
    /services     rules.py, llm.py, pdf.py, navigator.py, guardrails.py, i18n.py
    /models       SQLModel tables
    /seed         personas + log generators
  /tests
/docs             brief.md, guide.md
```

---

## 7. Shared agent interface

Every agent implements:

```python
class Agent:
    name: str
    def applies(self, ctx: UserContext) -> ApplicabilityResult   # used by orchestrator
    def analyze(self, ctx: UserContext) -> AgentResult
```

`AgentResult` (JSON-serializable):

```json
{
  "agent": "pcos_endo",
  "status": "flag | watch | ok | urgent",
  "score": 0.0,
  "headline": "Patterns commonly associated with PCOS",
  "evidence": [{"rule": "cycle_gt_35d", "detail": "4 of last 5 cycles longer than 35 days", "weight": 2}],
  "suggested_tests": ["Pelvic ultrasound", "Fasting glucose / HbA1c", "Free testosterone", "TSH", "Prolactin"],
  "specialist": "Gynecologist / Endocrinologist",
  "questions_for_doctor": [],
  "charts": [],
  "disclaimer_key": "not_a_diagnosis"
}
```

`UserContext` = profile + last N days of logs + cycle events + any measurements (BP, Hb, weight) + language.

---

## 8. Data model

**users / profile**

- `id, name, dob (age derived), language (en/hi), life_stage (reproductive | pregnant | perimenopausal | postmenopausal | unknown), is_pregnant, lmp_date, edd_date, height_cm, weight_kg, known_conditions[], medications[], region, created_at`

**daily\_logs** (one row per user per day)

- `id, user_id, date, flow (none|spotting|light|medium|heavy), pain_level (0-10), pain_location[], mood (1-5), energy (1-5), sleep_hours, sleep_quality (1-5), stress (1-5)`
- symptom booleans/levels: `acne, hirsutism, hair_thinning, bloating, headache, nausea, hot_flash_count, night_sweats, palpitations, vaginal_dryness, joint_pain, brain_fog, breast_tenderness, discharge_type, pain_during_intercourse, pain_bowel_urinary, fatigue (1-5)`
- `notes (free text), voice_transcript`

**cycle\_events**

- `id, user_id, start_date, end_date, length_days (computed), flow_summary`

**measurements** (mainly maternal, also general)

- `id, user_id, date, type (bp | hemoglobin | weight | glucose | fetal_movement_count | tsh), value_1, value_2 (e.g. diastolic), unit`

**agent\_runs**

- `id, user_id, run_at, orchestrator_decision (JSON: agents activated + reasons), results (JSON)`

**reports**

- `id, user_id, generated_at, language, file_path, summary_json`

Provide an ER diagram in `guide.md`. Seeding must populate all tables for all personas.

---

## 9. Orchestrator specification

Runs on: new check-in, persona switch, profile update, "Run analysis" button.

**Routing rules (evaluate in order; multiple agents may activate)**

1. **Health Story**: always active.
2. **Maternal Monitor**: if `is_pregnant == true` (or life\_stage = pregnant). If maternal danger signs are present, mark `urgent` and short-circuit to the emergency screen.
3. **Menopause Companion**: if age >= 40 AND (any of: cycle length variability > 7 days, cycles skipped, hot flashes, night sweats, sleep disturbance, vaginal dryness) OR life\_stage in (perimenopausal, postmenopausal). Not when pregnant.
4. **PCOS/Endo Screener**: if age 13 to 45, not pregnant, AND (any of: avg cycle length > 35 days or < 21 days, 3+ cycles in last 6 outside 21 to 35 days, acne + hirsutism, severe pain >= 7 on period days, pain during intercourse, pelvic pain cyclical). Skip when Menopause is the dominant match unless symptoms specifically fit.

**Output of orchestrator** (shown in the UI as a visible "agent routing" panel):

```json
{
  "activated": ["health_story", "menopause"],
  "skipped": [{"agent": "pcos_endo", "reason": "Age 46 and symptoms fit perimenopause better"}],
  "reasons": {"menopause": "Age 46; night sweats on 14 of last 30 days; cycle variability 11 days"}
}
```

**This panel is a key demo moment. Animate it** (agents lighting up one by one).

---

## 10. Agent specifications

> **Clinical note:** thresholds below are reasonable starting points for an awareness tool. Put them all in a single `config/clinical_rules.yaml` with a comment citing the source (Rotterdam criteria, WHO anemia thresholds, ACOG/WHO hypertension in pregnancy, MRS scale). Add a TODO to verify with a clinician before any real use.

### 10.1 Health Story Agent (core showpiece)

**Purpose:** Convert raw logs into a story a doctor can digest quickly.

**Computes**

- Cycle stats: average length, variability (SD), last 6 cycles, regularity label.
- Symptom frequency per cycle phase (menstrual, follicular, ovulatory, luteal).
- Trends: pain, mood, energy, sleep over time; week-over-week change.
- Correlations (simple, explainable): e.g. poor sleep vs next-day mood, pain vs cycle day, stress vs headache.
- "What changed recently" summary (last 14 vs previous 14 days).

**Outputs**

- Timeline + symptom heatmap data.
- LLM-written plain-language summary (in selected language), grounded ONLY in computed stats passed in the prompt.
- **Questions to ask your doctor** (5 to 8, LLM-generated from flags).
- **Doctor-ready PDF report** (see Section 11).

### 10.2 PCOS / Endometriosis Screener

**PCOS logic (Rotterdam-inspired, 2 of 3 criteria):**

| Criterion | Proxy from app data | Weight |
| --- | --- | --- |
| Oligo/anovulation | Avg cycle > 35 days, or < 8 cycles/year, or 3+ irregular cycles in 6 | 2 |
| Hyperandrogenism signs | Acne persistent, hirsutism, hair thinning | 2 |
| Polycystic ovaries | Cannot be known from app. Ask user: "Have you had an ultrasound showing this?" | 1 (optional) |
| Supporting | Weight gain/BMI >= 25, fatigue, family history, skin darkening | 0.5 each |

Score bands: low / moderate / high likelihood of *pattern match*. Always list "exclusions a doctor would check" (thyroid, prolactin, non-classic CAH).

**Endometriosis logic (symptom pattern):**

- Severe dysmenorrhea (pain >= 7 on period days, interferes with daily life), chronic pelvic pain, pain during intercourse, cyclical bowel/urinary pain, infertility history, fatigue, family history.
- Weighted score with explicit "red flag combination" (e.g. severe period pain + pain with intercourse + cyclical bowel pain).

**Outputs:** risk gauge per condition, evidence list, suggested tests, specialist type, cost-aware navigator (see 11.4), "diagnostic delay" awareness card.

### 10.3 Menopause / Perimenopause Companion

- Based on the **Menopause Rating Scale (MRS)** style grouping: somatic (hot flashes, sweating, heart discomfort, sleep, joint/muscle), psychological (mood, irritability, anxiety, exhaustion), urogenital (vaginal dryness, bladder, sexual).
- Staging hint (awareness only): early perimenopause (cycle variability), late perimenopause (60+ days without period), post-menopause (12 months without period).
- Tracks hot-flash frequency and night-sweat patterns, plus triggers (stress, late sleep, caffeine if logged).
- **Awareness cards:** bone health (calcium, vitamin D, weight-bearing exercise, ask about bone density scan), heart risk, sleep hygiene, when to see a doctor (very heavy bleeding, bleeding after 12 months without a period, new severe symptoms).
- Outputs: symptom burden score (mild/moderate/severe), pattern charts, questions for doctor, lifestyle guidance. **Do not recommend hormone therapy.** Only suggest discussing options with a doctor.

### 10.4 Maternal Health Monitor

**Inputs:** gestational age (from LMP), BP, hemoglobin, weight, fetal movement, danger-sign checklist, ANC visit dates.

**Urgent danger signs (any one triggers URGENT, bypass everything):** severe headache, blurred vision / flashing lights, convulsions, heavy vaginal bleeding, leaking fluid, severe abdominal pain, reduced or absent fetal movement, high fever, swelling of face/hands with headache, difficulty breathing, BP >= 160/110.

**Threshold alerts (configurable):**

- BP >= 140/90 on two readings: hypertension-in-pregnancy alert (possible pre-eclampsia pattern, see a doctor the same day).
- Hemoglobin < 11 g/dL: anemia alert; < 7 g/dL: severe, urgent.
- Rapid weight gain, persistent swelling, low fetal movement counts.
- Missed ANC checkups vs recommended schedule.

**UI:** gestational-week progress bar, BP trend chart with threshold bands, Hb trend, ANC checklist, danger-sign quick-check, **red full-screen urgent state** with "Call 108 (ambulance) / 112" and nearest-facility placeholder. Mention ASHA-worker mode (simple, large buttons) as a future extension; a simple toggle is enough.

---

## 11. Shared services

### 11.1 Rule engine

Pure functions + YAML config. Each rule returns `{fired: bool, evidence: str, weight: float}`. 100% unit tested. Agents compose rules.

### 11.2 LLM layer (Claude API)

- Server-side only. Structured prompts that receive **computed facts only**, never raw guesses.
- Tasks: patient-friendly summary, doctor questions, Hindi translation/simplification, "explain this flag".
- System prompt must forbid diagnosis, medication advice and dosage; require "consider discussing with a doctor" tone.
- Fallback: template strings if API fails (demo must not break offline).
- Cache responses per `(user, data-hash, language)` to keep the demo fast.

### 11.3 PDF report

Sections: header (name, age, date range, disclaimer), one-paragraph story, key stats table, cycle timeline chart, symptom heatmap, agent findings with evidence, "what changed recently", questions to ask the doctor, suggested tests to discuss, appendix with raw data summary. One to two pages, clean typography, available in English and Hindi.

### 11.4 Care navigator

Static JSON dataset (no live integrations): condition to specialist type, typical tests, India-specific pointers (government hospitals, Jan Aushadhi, e-Sanjeevani telemedicine, PMSMA for pregnancy, Janani Suraksha Yojana). **Verify every scheme/fact before showing it** and label "informational".

### 11.5 Guardrails

- Emergency keyword/regex check on free-text notes and voice transcripts.
- Disclaimer injector on every result and report.
- Output filter: reject LLM text containing diagnosis claims or drug/dose advice; fall back to template.

### 11.6 i18n

`en.json` / `hi.json` for all UI strings. LLM handles dynamic text; static text is pre-translated.

---

## 12. API design (REST)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/personas` | List demo personas |
| POST | `/api/session/switch` | Switch active persona |
| GET/PUT | `/api/profile` | Read/update profile |
| POST | `/api/logs` | Submit daily check-in |
| GET | `/api/logs?from&to` | Logs for charts |
| POST | `/api/measurements` | Add BP/Hb/weight etc. |
| GET | `/api/timeline` | Unified timeline data |
| POST | `/api/analyze` | Run orchestrator + agents, returns routing + results |
| GET | `/api/agents/{name}` | Latest result for one agent |
| POST | `/api/report` | Generate PDF (lang param), returns file URL |
| POST | `/api/explain` | LLM explains a flag in plain language |
| DELETE | `/api/user/data` | Delete-my-data |

---

## 13. Frontend: pages and visualizations

1. **Landing / persona switcher.** Pick Priya, Meena or Sunita. Consent and disclaimer banner.
2. **Home dashboard.** Greeting, life-stage chip, today's check-in CTA, **orchestrator routing panel** (animated), top insights, quick stats.
3. **Daily check-in.** Tap-based sliders and chips, optional voice note, under 60 seconds to complete. Emergency symptom shortcut.
4. **Timeline.** Cycle bars across months, flow intensity, pain overlays, event markers.
5. **Symptom heatmap.** Symptoms x days (or x cycle day), colour intensity. Hero visual.
6. **Agent detail pages.** Risk gauges (PCOS/Endo), symptom burden radar (Menopause), BP/Hb trends with threshold bands + gestation progress (Maternal).
7. **Doctor report.** Preview, language toggle, Download PDF, "questions to ask your doctor" checklist.
8. **Urgent screen.** Full red takeover for maternal/emergency flags.
9. **Settings.** Language, privacy, delete data.

Design direction: calm, warm and trustworthy (soft purples/teals/corals, rounded cards), large touch targets, accessible contrast, dark mode optional. Skeleton loaders and smooth transitions; it should look like a real product, not a hackathon form.

---

## 14. Seed data

Script generates \~90 days per persona with realistic noise and the intended patterns:

- **Priya:** cycles of 38, 52, 41, 60 days; acne and hirsutism on most days; fatigue 3 to 4; weight trending up.
- **Meena:** cycles drifting 24 to 70 days; 10 to 18 night-sweat days per month; sleep 4.5 to 5.5 h; mood dips.
- **Sunita:** week 30; BP creeping 118/76 to 142/92 over 6 weeks, with a final reading triggering urgent alert; Hb 10.2; mild swelling and headaches.

Generators must be deterministic (seeded RNG) so the demo is reproducible.

---

## 15. Step-by-step build order

Each phase ends with an **acceptance check**. Do not start the next phase until it passes.

**Phase 0: Setup (30 to 45 min)**

- Repo, folders, env files, FastAPI + Next.js skeletons, SQLite, lint/format, CORS, health-check endpoint.
- *Accept:* frontend can call `/api/health`.

**Phase 1: Shared core**

- DB models + migrations, profile CRUD, daily log + measurement endpoints, cycle computation from logs.
- *Accept:* POST a log, read it back, cycle events computed.

**Phase 2: Seed data + persona switcher**

- Seed script for 3 personas; persona switch endpoint and UI.
- *Accept:* switching persona changes all data shown.

**Phase 3: Rule engine + agent interface**

- `clinical_rules.yaml`, rule functions, `Agent` base class, unit tests.
- *Accept:* tests pass for each rule with fixtures from each persona.

**Phase 4: Health Story agent + visualizations**

- Cycle stats, correlations, timeline chart, symptom heatmap.
- *Accept:* Priya's dashboard shows convincing charts.

**Phase 5: Orchestrator + routing panel**

- Routing logic, `/api/analyze`, animated routing UI.
- *Accept:* Priya activates PCOS; Meena activates Menopause (PCOS skipped with reason); Sunita activates Maternal.

**Phase 6: PCOS/Endo agent + gauge UI.** *Accept:* explainable score with evidence list.

**Phase 7: LLM layer + guardrails.** Summary, doctor questions, explain-flag, fallbacks, caching. *Accept:* works with and without API key; forbidden-content filter tested.

**Phase 8: PDF report (English).** *Accept:* one click gives a clean, doctor-ready PDF for each persona.

**Phase 9: Maternal agent + urgent screen.** *Accept:* Sunita's last BP reading triggers the red screen.

**Phase 10: Menopause agent + charts.** *Accept:* MRS-style burden score and pattern charts render.

**Phase 11: Hindi support.** UI strings, LLM output, PDF font. *Accept:* full demo flow works in Hindi.

**Phase 12: Polish.** Animations, loaders, empty/error states, responsive pass, accessibility, privacy/delete-data, disclaimers everywhere.

**Phase 13: Demo prep.** Rehearse the script, record a backup video, prepare deck, deploy (Vercel + Render/Railway) or run locally with a fallback.

**Cut order if time runs short:** Hindi in PDF, then voice input, then Menopause depth, then Maternal depth. **Never cut:** Health Story, orchestrator panel, PDF, PCOS agent, one working urgent alert.

---

## 16. Demo script (3 minutes)

1. **Hook (20s):** the diagnostic-delay problem and one statistic (verified).
2. **Priya (60s):** open dashboard, heatmap and timeline; orchestrator lights up PCOS agent; show explainable gauge; click **Generate doctor report**; show PDF.
3. **Switch to Meena (35s):** the same app adapts; PCOS skipped with a reason, Menopause activated; show burden chart.
4. **Switch to Sunita (35s):** log a high BP reading live; red urgent screen fires.
5. **Hindi toggle (15s):** flip language, report regenerates.
6. **Close (15s):** privacy, ethics, life-stage vision, roadmap (ASHA mode, clinic integration, wearables).

**Pitch line:** *"Women's health isn't one problem, it's a journey. Existing apps are period trackers. We built a life-stage companion that spots patterns doctors miss and gets her ready for the clinic."*

---

## 17. Testing and quality checklist

- Unit tests for every rule and routing decision (use persona fixtures).
- Snapshot test for orchestrator output per persona.
- LLM output filter tests (no diagnosis/drug/dose language).
- Manual test: kill network, confirm template fallbacks.
- Lighthouse/accessibility sanity check; works on a phone viewport.
- No secrets committed; `.env.example` provided.

---

## 18. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Scope creep across four agents | Shared engine, strict build order, cut list |
| Medical inaccuracy | Rules in one config with cited sources, clinician-verify TODO, awareness-only wording |
| LLM failure or latency during demo | Cache + template fallback + pre-generated sample reports |
| Hindi PDF rendering issues | Bundle Devanagari font early (Phase 8 test) |
| Judges question data privacy | Consent screen, delete-data, no real PII, optional local-only mode in roadmap |

---

## 19. Open assumptions (confirm with the team)

- Team size and hours available (assumed: 2 to 4 people, 24 to 36 hours).
- Web app only (no native mobile).
- Deployment target (assumed: local demo plus optional hosted link).
- Final product name and branding.

---

## 20. Next steps for the agent

1. Confirm you have read and understood this brief by replying with a **short summary (under 200 words)** and a list of any clarifying questions or assumptions.
2. Wait for the instruction to generate **`guide.md`**: a concise developer guide containing the repo structure, setup commands, ER diagram, API contract, per-phase task checklists with acceptance criteria, and conventions.
3. After `guide.md` is approved, implement **phase by phase**, running tests and reporting progress after each phase.
