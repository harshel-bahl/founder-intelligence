## Founder Intelligence

Founder Intelligence is a focused tool that reads public evidence and returns a fast, transparent view of founder potential.

It consolidates high-signal sources (LinkedIn, personal blogs/newsletters, press) and uses an LLM to score two dimensions:
- Entrepreneurial Experience (0–4)
- Contrarian “Chip‑on‑Shoulder” Multiplier (1.0–1.5)

Outputs include structured JSON and a clean UI: scores, concise reasoning, evidence bullets, a per‑source confidence table, and the full traversal log for auditability.

<img width="1905" height="1194" alt="image" src="https://github.com/user-attachments/assets/bd3915c0-d769-446f-87a7-5d92e728b57a" />

<img width="1650" height="1190" alt="image" src="https://github.com/user-attachments/assets/e55d93ba-0da0-47f0-b727-3d35c34cb775" />

<img width="1644" height="1192" alt="image" src="https://github.com/user-attachments/assets/38fda668-d8e4-4f41-a247-9780de4dd59b" />

<img width="1568" height="1198" alt="image" src="https://github.com/user-attachments/assets/cafbbeca-9736-46d1-8cfc-215ebda85f6c" />

---

## Purpose

Quick takes are often too shallow (only LinkedIn) or too noisy (unfiltered search). This system aims for the middle:
- Collect a compact set of credible signals in one pass
- Attribute each source to the correct person (name collisions are common)
- Apply a clear rubric and show the work

The ethos: evidence‑grounded, conservative when uncertain, and fast enough for shortlists.

---

## Architecture

- `app_streamlit.py` — Streamlit UI
  - Sidebar configuration, LinkedIn URL input, two tabs (Summary & Analysis, Detailed Reports), CSV export

- `agent.py` — Business logic
  - Fetches LinkedIn and (if needed) personal sources via SerpAPI
  - Parses visible page text (BeautifulSoup)
  - Packages evidence and calls the LLM
  - Unwraps errors cleanly (useful messages over opaque retries)

- `prompts/founder_scoring_prompt.md` — Rubric and output spec
  - Per‑source attribution confidence (0.0–1.0)
  - Entrepreneurial (0–4) + Contrarian (1.0–1.5)
  - Strict JSON response with bullets and summary

Separation of concerns enables prompt iteration without code changes and UI updates without touching the agent.

---

## Flow (end‑to‑end)

1) User pastes LinkedIn URLs in the UI.  
2) The agent parses LinkedIn; if thin, it discovers personal sources (blog, Substack, Medium, GitHub, simple sites).  
3) Entrepreneurial queries (press, Crunchbase, accelerator mentions) run via SerpAPI.  
4) The LLM first assigns a per‑source confidence score (0.0–1.0) to verify the person; only sources ≥0.5 are used for scoring.  
5) The model scores Entrepreneurial (0–4) and Contrarian (1.0–1.5), returns evidence‑backed bullets and JSON.  
6) The UI presents summary and details and supports CSV export.

Note: There is no separate “contrarian search” pass. Contrarian signals are inferred from the same evidence (bios, press, timelines) to reduce bias and noise.

---

## Scoring (at a glance)

- Entrepreneurial (0–4)
  - 4.0: Category‑defining/unicorn‑scale outcomes; repeated, proven company building
  - 3.5–3.9: High‑growth with substantial scale or repeat strong outcomes
  - 3.0–3.4: Venture‑backed founder/CEO/CTO with meaningful traction (e.g., Series A+ or clear PMF)
  - 2.0–2.9: Seed/pre‑seed, top accelerator with traction, early founding‑team roles, or notable pre‑PMF scope
  - 1.0–1.9: Intent without hard outcomes yet
  - 0.0–0.9: Limited/unclear signal

- Contrarian (1.0–1.5)
  - Derived strictly from provided evidence
  - Looks for: dropouts/program departures; large field switches with execution; very early roles; quitting stable paths to build; purposeful relocations/retreats; public contrarian bets with shipped work
  - Buckets: Standard (1.0–1.1), Moderate (1.15–1.35), High (1.4–1.5)

- Final score
  - `final_score = round(min(4.0, entrepreneurial_score * contrarian_multiplier), 2)`
  - No artificial tapering—4.0 is reachable when the record supports it

The 1.5 cap keeps Experience primary while recognizing real, high‑variance choices.

---

## Source Attribution Confidence (0.0–1.0)

Each source is scored for identity attribution (company, location, timeline). Only sources with confidence ≥0.5 are used in scoring. This reduces bias from name collisions and ensures the system links the right evidence to the right person. The UI exposes counts, averages, and the full table for review.

---

## Error Handling

- OpenAI calls retried with backoff; falls back when `response_format` is not supported
- Defensive JSON parsing with raw content surfaced on errors
- Tenacity errors unwrapped to reveal root causes (auth, length, rate limits)
- Prompt formatting safeguarded to avoid brace/placeholder issues

The UI surfaces useful errors and still shows traversal context.

---

## Configuration & Defaults

Set via the UI (persisted to env vars at runtime):
- `SERPAPI_API_KEY` (required)
- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `OPENAI_TEMPERATURE` (default `0.1` for 4o variants; forced to `1.0` for non‑4o models for consistency)
- `RESULTS_PER_QUERY` (default `5`)
- `PER_PROFILE_QUERIES` (default `2`)
- `LINKEDIN_LI_AT` (optional; use within ToS)

---

## Quick Start

Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run
```bash
streamlit run app_streamlit.py
# or
python app.py
```

Use
- Paste LinkedIn URLs (one per line)
- Add keys in the sidebar
- Click “Run Scoring” (button next to the text box)
- Read the summary, expand details, export CSV if needed

---

## Design Choices

This is intended as a fast, transparent first pass—not a replacement for deep diligence - human intervention will be required to assess data.

- Prompt‑as‑data: the rubric lives in a markdown file
  - Why: scoring rules change as calibration improves; keeping them in `prompts/` makes edits obvious and reviewable.
  - Effect: quick iterations, clean diffs, and reproducible results tied to a prompt version.

- No contrarian search pass
  - Why: separate “contrarian” queries tend to cherry‑pick; deriving contrarian from the same bios/press/timelines avoids selection bias.
  - Effect: less noise, fairer comparisons across people, simpler mental model for why a score moved.

- Conservative multiplier (1.0–1.5)
  - Why: it’s easy to over‑read contrarian signals from thin text; a cap keeps Experience as the main driver.
  - Effect: stable rankings under messy evidence; standouts can still hit 4.0, weak signals won’t dominate.

- No tapering math
  - Why: tapering hides true outliers; if the record supports it, the score should show it.
  - Effect: clearer, more honest scores; exceptional founders aren’t flattened.

- Source confidence first (≥0.5 to count)
  - Why: name collisions and thin bios are common; per‑source attribution cuts out the wrong person’s press.
  - Effect: fewer misattributions, better trust in the bullets, easier auditing.

- UI / logic split
  - Why: interface changes and scoring logic evolve at different speeds.
  - Effect: safer refactors, simpler tests, faster product tweaks.

- Resilient API layer
  - Why: endpoints and formats change; retries, fallbacks, and clear error messages prevent dead ends.
  - Effect: fewer mystery failures, faster fixes, smoother runs.

---

## Limitations & Future Ideas

- Small public footprints can limit validation and yield false negatives
- Not particularly performant, would require optimizations and wise design decisions to increase throughput
- LinkedIn HTML evolves; the agent parses visible text and falls back to personal sources
- LLM calibration needs to be more thorooughly assessed accross edge cases and a wider distribution of evaluation data to assess performance

Planned:
- Caching to reduce time and quota
- Optional org enrichments (investors, boards, patents)
- “Evidence too thin” flag with next‑step suggestions
- More thoroughly syntheize evidence from pages using deep search style LLM chaining
- Provide tooling to agent to help parse text
