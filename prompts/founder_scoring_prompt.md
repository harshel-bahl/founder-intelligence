You're evaluating **founder potential** along two axes:

1) **Entrepreneurial Experience (0–4)** — how much real, repeatable founder evidence exists.
2) **Contrarian / "Chip-on-Shoulder" Multiplier (1.0–1.5)** — how strongly the person chooses non-linear, high-variance paths.

You'll get:
- `profile_url`: {profile_url}
- `name_guess`: {name_guess}
- `evidence_json`: structured evidence including parsed page snippets (LinkedIn/blog/etc.) and search evidence (titles, links, snippets, domains).

**IMPORTANT: First assess source confidence, then only use high-confidence sources for scoring. Do NOT invent evidence. Derive contrarian signals strictly from the provided evidence (bios, press, timelines).**

---

### Step 1: Source Attribution Confidence (0.0–1.0)

For each piece of evidence, assess whether it actually refers to the target person:
- **1.0 (Certain):** Clear name match + contextual details (company, location, timeline) align
- **0.8 (Very Likely):** Name match + some contextual alignment, minimal ambiguity
- **0.6 (Probable):** Name match but limited context to verify identity
- **0.4 (Uncertain):** Common name, conflicting or missing context
- **0.2 (Unlikely):** Probable name collision, mismatched context
- **0.0 (Wrong Person):** Clear evidence of different person

**Only use sources with confidence ≥ 0.5 for scoring.**

---

### Step 2: Entrepreneurial Experience (0–4)

Focus on **concrete achievements and scale**. Be generous for proven builders.

- **4 (Exceptional):** Billion-dollar company founder/co-founder OR multiple unicorn-scale companies OR clear category-defining innovation with massive impact. Examples: Elon Musk, Reid Hoffman, founders of Scale AI, Anthropic, OpenAI at significant scale.

- **3.5-3.9 (Near-Exceptional):** High-growth company founder with substantial scale (hundreds of millions in valuation/revenue) OR repeat successful founder with strong track record. Clear evidence of building something significant.

- **3.0-3.4 (Strong):** Venture-backed founder/CEO/CTO with meaningful traction (Series A+ raised, or clear PMF signals) OR established serial entrepreneur. Evidence of real company building, not just starting.

- **2.0-2.9 (Moderate):** Raised seed/pre-seed OR YC/top accelerator graduate with traction OR repeat founding team member OR significant early employee (#1-10) at high-growth company who then founded.

- **1.0-1.9 (Emerging):** Clear entrepreneurial intent: building something, accelerator participant, "stealth" mentions, startup advisor/angel, entrepreneurship-focused roles, patents in relevant domains.

- **0.0-0.9 (Limited):** No clear entrepreneurial signals OR exclusively large corporate/academic roles with no building experience.

---

### Step 3: Contrarian Multiplier (1.0–1.5)

Derive from the evidence only. This dimension captures willingness to take non‑default, high‑variance paths with real personal downside. When in doubt, use judgment and explain. The lists below are **illustrative, not exhaustive** — treat them as **patterns**. If a source clearly implies the same pattern (even with different phrasing), it qualifies.

Look for signals such as:
- Explicit dropouts or program departures (HS/college/grad)
- Major field switches with shipped work (e.g., quant/finance → infra/ML startup; physics → ML)
- Very early roles at unproven companies (pre‑PMF, pre‑funding)
- Quitting stable paths/jobs/schools to build; self‑funded stretches
- Unconventional relocations or retreats with purpose (international, remote, monastery, deep work sabbaticals)
- Publicly contrarian bets/takes tied to execution (going against consensus in domain and shipping)
- Repeated shutdowns/restarts, fast pivots, willingness to scrap sunk costs
- Choosing difficult/underserved users or gnarly infra problems when easier options existed

Bucket guidance (pick one, pattern‑match at a high level):

**Bucket A — Standard (1.0–1.1)**
High‑level criteria: default path adherence with minor deviations. Decisions generally minimize personal downside.
- Example patterns (non‑exhaustive): linear school → internship → big‑co ladder; minor job switches within same track; “building in public” without costly decisions; side projects that don’t alter trajectory.

**Bucket B — Moderate (1.15–1.35)**
High‑level criteria: at least one clear, costly, non‑default decision that materially increased variance.
- Example patterns (non‑exhaustive):
  - Leave of absence or dropout to build (e.g., **MIT dropout** to start)
  - **Quant/finance → startup founder**, with shipped product and users
  - Quit FAANG/bank/PhD to bootstrap; relocate to build in an unusual place
  - Repeated very‑early roles across startups; multi‑month deep work retreat tied to a specific build

**Bucket C — High (1.4–1.5)**
High‑level criteria: sustained pattern of non‑default choices with real downside, or multiple strong signals over time.
- Example patterns (non‑exhaustive):
  - Repeated program departures; multiple cross‑domain pivots with shipped systems
  - Shutdowns and restarts; building against industry consensus and being right
  - Long, uncomfortable bets (remote fieldwork, harsh constraints) that led to shipped, consequential outcomes

Notes:
- If evidence clearly supports “top‑tier contrarian,” assign 1.5. Do not anchor on 1.0 for high‑achieving founders when the record shows repeated, costly variance‑seeking behavior.
- If evidence is ambiguous, choose the lower bucket and explain the uncertainty.
- Do not infer from vibes; every claim must be grounded in the provided sources.

> **Default is 1.0** unless clear evidence exists in the provided sources.

---

### Step 4: Combine Scores

- Assign `entrepreneurial_score ∈ [0.0, 4.0]` and `contrarian_multiplier ∈ [1.0, 1.5]`
- Apply multiplier: `final_score = round(min(4.0, entrepreneurial_score * contrarian_multiplier), 2)`
- **No diminishing returns** — let exceptional founders get full credit

---

### Output Format

First provide source confidence assessments, then final scoring:

{{
  "source_confidence_assessments": [
    {{"source": "title/snippet/domain", "confidence": 0.0, "reasoning": "why this confidence level"}}
  ],
  "high_confidence_sources_used": ["list of sources with confidence ≥ 0.5"],
  "entrepreneurial_score": 0.0,
  "contrarian_multiplier": 1.0,
  "final_score": 0.0,
  "entrepreneurial_evidence_points": ["specific evidence from high-confidence sources only"],
  "contrarian_evidence_points": ["specific evidence from high-confidence sources only"],
  "summary": "Reasoning for scores based on high-confidence evidence.",
  "confidence": 0.0
}}

Here is the structured evidence (pages + search) as JSON:
{evidence_json}
