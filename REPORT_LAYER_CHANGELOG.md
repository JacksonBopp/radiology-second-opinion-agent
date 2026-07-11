# GenAI Report Generation Layer - Changelog

## Phase 4, 5, and 6 Report-Layer Tasks Completed

This document outlines the completions for Bryan's scope (GenAI & NLP
Engineer): structured report generation, the clinical language layer,
confidence calibration, and report quality evaluation, built on top of
Amrit's already-completed `src/agent` LangGraph pipeline.

### 1. Structured Report Schemas — `src/reports/schemas.py` (Task 4.7)
- `RadiologyReport`, `ReportSection`, `FindingSummary`, `DifferentialEntry`,
  `GuidelineReference`, and a 5-level `ConfidenceLevel` enum.
- Kept intentionally separate from `src.agent.state.AgentState`: the
  agent state is LangGraph's internal working structure, while these
  models are the external report contract consumed by the frontend
  report viewer and evaluation tooling.

### 2. Prompt Engineering — `src/reports/prompts.py` (Task 4.8)
- `SYSTEM_PROMPT` + `build_report_prompt()` for Claude 3 Haiku (the model
  already selected for the Retrieval/Diagnosis agents per the approved
  implementation plan).
- Hard rules baked into the prompt: never invent findings/citations,
  preserve the Diagnosis Agent's ranking instead of re-ranking, always
  hedge language, respond with schema-conformant JSON only.

### 3. Confidence Calibration — `src/reports/calibration.py` (Task 5.7)
- Maps raw/Bayesian-updated probabilities to 5 calibrated confidence
  buckets and clinician-facing phrases (e.g. "moderate confidence
  (approximately 55%)").
- Includes a `temperature` hook (logit-space temperature scaling) ready
  to receive a fitted calibration curve once Nick's models produce a
  real calibration set (Tasks 3.6 / 7.5) — currently a no-op (1.0).
- `summarize_uncertainty()` produces the report's overall confidence
  level and caveat text, discounting single-diagnosis differentials.

### 4. Radiology Report Style Adapter — `src/reports/style.py` (Task 5.10)
- Deterministic mock-mode section templates (Findings / Impression /
  Recommendation) consistent with the "mock data first" pattern used in
  `src.agent.diagnosis` and `src.agent.literature`.
- `enforce_radiology_register()` strips conversational/overconfident
  phrasing ("I think", "definitely", "100% certain") from any section
  text, mock- or LLM-generated, so both paths converge on one house style.

### 5. Report Generation Pipeline — `src/reports/generator.py` (Tasks 5.8, 5.9, 6.10)
- `generate_report(state)`: builds a full `RadiologyReport` from a
  completed (or partial) `AgentState`.
- **Mock mode** (default, no API key): fully deterministic, runs in CI.
- **LLM mode** (`ANTHROPIC_API_KEY` set): calls Claude 3 Haiku with the
  Task 4.8 prompts and parses structured JSON back into the same
  schema; falls back to mock mode on any error (missing package,
  network failure, malformed JSON) so the report layer never hard-fails.
- Preserves (never recomputes) the Diagnosis Agent's probability
  ranking, adding 1-indexed `rank` and calibrated language per entry.
- Surfaces `clinical_guidelines` from the Literature Agent as
  `GuidelineReference` entries with per-reference relevance text.

### 6. Report Quality Evaluation — `src/reports/evaluation.py` (Tasks 6.9, 7.8)
- `evaluate_report_quality()` computes: completeness (expected sections
  present/non-trivial), groundedness (a cheap hallucination check — do
  Impression/Recommendation sections actually reference a known
  differential diagnosis), and optional lexical overlap against a real
  radiologist report when one is available for the same case.
- Deliberately does not attempt to score clinical correctness — that
  requires a licensed radiologist. `passes_minimum_bar` is a CI/dashboard
  gate, not a clinical sign-off.

### 7. API Integration — `src/api/routes/reports.py`
- New `POST /reports` endpoint: runs the LangGraph analysis graph and
  the report generator in one call, returning the full `RadiologyReport`.
  Reuses the existing `AnalysisRequest` schema and auth dependency from
  `/analyze` so the frontend can call either endpoint interchangeably.
- Registered in `src/api/main.py`.

### 8. Testing — `tests/test_reports.py`
- 18 tests covering calibration bucketing/temperature scaling, style
  register enforcement, prompt construction (including empty-input
  edge cases), mock-mode report generation end-to-end, and evaluation
  (complete report, missing-section flag, hallucination flag, reference
  overlap).

### Dependencies
- Added `anthropic` to `requirements.txt` (only invoked when
  `ANTHROPIC_API_KEY` is set; mock mode has no new runtime dependency).

### Summary
Bryan's report-generation and clinical-language layer is code-complete
and fully testable in mock mode today. The moment real API keys and
Nick's trained vision models are available, `generate_report()` starts
calling Claude 3 Haiku automatically (no code changes required), and
`calibration.py`'s temperature hook is ready to take a fitted
calibration curve from Nick's model outputs.
