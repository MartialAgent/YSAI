# AgentDAG — Experiment Guide

All experiments use the same **B2B SaaS Pricing graph** (3 nodes, strict numerical constraints)
so that evaluation differences are directly comparable across runs.

---

## Baseline Architecture (A-Score)

```
A-Score = α × (1 - S) + β × D × (1 - C)
```

| Component | Symbol | Baseline Method |
|-----------|--------|----------------|
| Similarity | S | Cosine similarity between two worker responses |
| Confidence | C | Worker self-reports a 0–1 score (JSON) |
| Deviation  | D | Single critic LLM assigns a 0–1 error score |

Current defaults: `α = 0.5`, `β = 0.5`, `A_SCORE_THRESHOLD = 0.4`

---

## Experiment Index

| Exp | Script | What changes | Meeting note ref |
|-----|--------|-------------|-----------------|
| 01 | `exp/260413_exp01_baseline.py` | Baseline — Autonomous Driving graph | — |
| 02 | `exp/260413_exp02_saas_baseline.py` | Baseline — SaaS Pricing graph (strict constraints) | — |
| 03 | `exp/260413_exp03_logprobs_c.py` | **C upgrade**: Logprobs instead of self-report | Section 2 — C (확신도) |
| 04 | `exp/260413_exp04_qag_d.py` | **D upgrade**: QAG quiz validation | Section 2 — D (편차), QAG |
| 05 | `exp/260413_exp05_geval_d.py` | **D upgrade**: G-Eval CoT + probabilistic scoring | Section 1 — G-Eval |
| 06 | `exp/260413_exp06_multi_llm.py` | **D upgrade**: Multi-LLM judge averaging | Section 3 & 5 — 동일 모델 편향 |
| 07 | `exp/260413_exp07_dss.py` | **+ DSS**: Dependency Sensitivity Score diagnostic | Section 7 — DSS |

---

## How to Run

```bash
# Prerequisites
cp .env.example .env          # add your OPENAI_API_KEY
poetry install                # or: pip install -r requirements.txt

# Run from project root (always)
python exp/260413_exp01_baseline.py     # Exp01 — baseline, Autonomous Driving graph
python exp/260413_exp02_saas_baseline.py # Exp02 — baseline, SaaS Pricing graph
python exp/260413_exp03_logprobs_c.py   # Exp03 — Logprobs C
python exp/260413_exp04_qag_d.py        # Exp04 — QAG D
python exp/260413_exp05_geval_d.py      # Exp05 — G-Eval D
python exp/260413_exp06_multi_llm.py    # Exp06 — Multi-LLM Judge
python exp/260413_exp07_dss.py          # Exp07 — DSS diagnostic
```

**Naming convention:** `YYMMDD_expNN_description.py`  
New experiments go in `exp/` with the date they were created as prefix.

Each run saves state to its own JSON file (`state_expXX.json`), so runs are isolated
and can be resumed if interrupted mid-graph.

---

## Experiment Details

### Exp03 — Logprobs C
**File:** `src/evaluators/exp_logprobs_c.py`

**Problem with baseline C:**  
The worker LLM self-reports its own confidence. This is trivially biased upward —
models rarely admit uncertainty in a structured JSON field.

**Solution:**  
After generating the primary response, send a separate 1-token YES/NO probe:
> "Is this response factually accurate, logically consistent, and free of hallucinations?"

Extract log-probabilities of the YES and NO tokens:
```
C = P(YES) / (P(YES) + P(NO))
```

**Why better:** This is a model-internal signal, not a generated narrative.
The model cannot "choose" to be confident — the probability distribution is its true belief.

**Extra API calls per node:** Same as baseline (replaces the JSON self-report call).

---

### Exp04 — QAG D
**File:** `src/evaluators/exp_qag_d.py`

**Problem with baseline D:**  
A single critic LLM assigns a holistic 0–1 score. This is subjective and varies
significantly across runs (stochastic LLM output).

**Solution (RAGAS-inspired):**  
1. Generate 3 quiz questions from the task input (what a correct response *must* answer).
2. Test whether the worker's output alone can answer each question correctly.
3. `D = 1 - (correct / total)` — objective and auditable.

**Why better:** Pass/fail per question is deterministic and verifiable.
The evaluation is task-specific: questions are derived from the actual constraints.

**Extra API calls per node:** +3 (1 quiz gen + 3 answer checks vs 1 critic call).

---

### Exp05 — G-Eval D
**File:** `src/evaluators/exp_geval_d.py`

**Solution (Galileo AI / G-Eval paper):**  
3-stage evaluation:
1. LLM writes a task-specific evaluation rubric (CoT checklist, 3–5 items).
2. LLM scores the response 1–5 following the rubric.
3. Instead of using the raw token "4", compute the **weighted average of log-probabilities**
   over all score tokens (1, 2, 3, 4, 5):
   ```
   score = Σ (i × P(token_i)) / Σ P(token_i)
   ```
   Example: P(4)=0.80, P(5)=0.20 → score = 4.2 (more stable than random 4-or-5 sampling).

Normalized to deviation: `D = 1 - ((score - 1) / 4)`

**Why better:** Rubric is always task-relevant. Probabilistic aggregation removes
single-sample variance from the score.

**Extra API calls per node:** +1 (rubric gen) + same critic call with logprobs.

---

### Exp06 — Multi-LLM Judge
**File:** `src/evaluators/exp_multi_llm.py`

**Problem:**  
Same-model bias: GPT tends to score GPT-generated responses more favorably
(observed in class, Prof. Noh Albert). A single judge introduces systematic leniency.

**Solution:**  
Run the identical critic prompt against each model in `JUDGE_MODELS`:
```python
JUDGE_MODELS = ["gpt-4o-mini", "gpt-4o"]
```
Average their deviation scores: `D = mean(D_gpt4o_mini, D_gpt4o)`

This implements **SAC³-M** (model-level cross-check consistency) from Section 4.

**To extend:** Add more models to `JUDGE_MODELS` in `src/evaluators/exp_multi_llm.py`.
If Anthropic/Gemini API keys are available, cross-family judges would be ideal.

**Extra API calls per node:** ×N where N = len(JUDGE_MODELS) (currently 2×).

---

### Exp07 — DSS (Dependency Sensitivity Score)
**File:** `src/evaluators/exp_dss.py`

**Formula:**
```
DSS(node_i) = Δ(Output) / Δ(Input)
            = cosine_distance(output_original, output_perturbed)
```
Perturbation is fixed at 1 unit (prepend an alternative-framing instruction),
so DSS reduces to pure output divergence measurement.

**Interpretation:**
- `DSS < 0.1` — stable node, small input changes → similar outputs
- `DSS > 0.3` — high-risk upstream node, small input changes → large output drift
  → downstream nodes may cascade errors

DSS is a **diagnostic metric** logged alongside A-Score. It does not change
the PASS/FAIL/AMBIGUOUS routing — it identifies which nodes need closer human review.

**Extra API calls per node:** +2 (1 perturbed worker call + 1 embedding comparison).

---

## Score Comparison Table (A-Score)

> Lower A-Score = better quality (less ambiguity/deviation). All runs on the same SaaS Pricing graph.

| Node | Exp02 baseline | Exp03 Logprobs C | Exp04 QAG D | Exp05 G-Eval D | Exp06 Multi-LLM | Exp07 DSS |
|------|---------------|-----------------|------------|---------------|----------------|----------|
| A_Pricing | 0.079 | 0.213 ↑ | 0.020 | 0.027 | 0.116 | 0.131 |
| B_ROI | 0.011 | 0.008 | 0.019 | 0.006 | 0.016 | 0.013 |
| C_AdCopy | 0.037 | 0.071 ↑ | 0.092 ↑ | 0.027 | 0.045 | 0.036 |

**Key findings:**
- **Exp03 (Logprobs C):** A-Scores increase significantly — logprobs shows C≈0.000, revealing the baseline self-report was masking real uncertainty.
- **Exp04 (QAG D):** Detected C_AdCopy failing 2/3 factual quiz questions (D=0.667) — far more sensitive than the baseline critic.
- **Exp05 (G-Eval D):** Most stable and lowest A-Scores — CoT rubric + probabilistic scoring reduces noise.
- **Exp06 (Multi-LLM):** Cross-model disagreement found on A_Pricing (GPT=0.5, Claude=0.0, Gemini=0.0). Averaging mitigates same-model bias.
- **Exp07 (DSS):** A_Pricing flagged as HIGH-RISK upstream node (DSS=0.349) — A-Score alone would miss this fragility.

## Per-Component Comparison

| Exp | S method | C method | D method | Extra |
|-----|----------|----------|----------|-------|
| 02 | Cosine | Self-report JSON | GPT-4o critic | — |
| 03 | Cosine | **Logprobs YES/NO** | GPT-4o critic | — |
| 04 | Cosine | Self-report JSON | **QAG quiz (3 Qs)** | — |
| 05 | Cosine | Self-report JSON | **G-Eval CoT+logprobs** | — |
| 06 | Cosine | Self-report JSON | **3-model avg (GPT/Claude/Gemini)** | — |
| 07 | Cosine | Self-report JSON | GPT-4o critic | **DSS diagnostic** |

---

## File Map

```
src/
  evaluator.py              ← Baseline evaluator (unchanged)
  evaluators/
    exp_logprobs_c.py       ← Exp03: C via logprobs
    exp_qag_d.py            ← Exp04: D via QAG
    exp_geval_d.py          ← Exp05: D via G-Eval
    exp_multi_llm.py        ← Exp06: D via multi-LLM averaging
    exp_dss.py              ← Exp07: baseline + DSS diagnostic
  graphs.py                 ← Shared test graph definitions
  orchestrator.py           ← Accepts process_fn= for swappable evaluators
  models.py                 ← Data models (NodeState, EvaluationResult, etc.)
  config.py                 ← Thresholds and model names

exp/                          ← All experiment run scripts (YYMMDD_expNN_name.py)
  260413_exp01_baseline.py   ← Exp01: baseline, Autonomous Driving
  260413_exp02_saas_baseline.py ← Exp02: baseline, SaaS Pricing
  260413_exp03_logprobs_c.py ← Exp03 runner
  260413_exp04_qag_d.py      ← Exp04 runner
  260413_exp05_geval_d.py    ← Exp05 runner
  260413_exp06_multi_llm.py  ← Exp06 runner
  260413_exp07_dss.py        ← Exp07 runner
```
