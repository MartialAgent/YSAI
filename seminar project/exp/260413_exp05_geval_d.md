# Exp05 — G-Eval D (CoT Rubric + Probabilistic Scoring)

> **One-line verdict:** G-Eval is the most sensitive evaluator tested — it catches both missing variables (E: 2 retries, score 3.685/5) AND the audit's missing condition (D: 4.349/5, D=0.163) that QAG missed. F_BoardReport scores 2.857/5, proving error propagation is detectable.

**Date:** 2026-04-17 | **Script:** `exp/260413_exp05_geval_d.py` | **Evaluator:** `src/evaluators/exp_geval_d.py` | **State:** `state_exp05.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (7/7) | E required 2 retries |
| Missing variable detected (E)? | ✅ Yes | Score 3.685/5, D=0.329, needed 2 retries |
| Missing condition detected (D)? | ✅ Yes | Score 4.349/5, D=0.163 — QAG missed this |
| Error propagation detected (F)? | ✅ Yes | Score 2.857/5, D=0.536 — lowest in experiment |
| Most sensitive evaluator so far? | ✅ Yes | Catches omissions QAG and baseline miss |

---

## Score Guide

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 |
| **G-Eval score** | 4.5–5.0 | 3.0–4.5 | < 3.0 (→ FAIL risk) |
| **D (G-Eval)** | < 0.1 | 0.1 – 0.4 | > 0.4 (significant issues) |

---

## How G-Eval Works (3 stages)

```
Stage 1: GPT writes a 3–5 item rubric checklist for the task (CoT)
Stage 2: GPT scores 1–5 with logprobs (max_tokens=1)
Stage 3: Weighted average = Σ(i × P(token_i)) / Σ P(token_i)
          → D = 1 - ((score - 1) / 4)
```

**vs. QAG**: QAG asks specific factual questions. G-Eval forces the judge to enumerate required elements first — catches structural omissions, not just missing facts.

---

## Node Results

| Node | Status | A-Score | D (G-Eval) | G-Eval Score | Retries | Verdict |
|------|--------|---------|-----------|--------------|---------|---------|
| A_Pricing | ✅ PASS | 0.021 | 0.044 | 4.823/5 | 0 | ✅ Near-perfect pricing design |
| B_ROI | ✅ PASS | 0.003 | 0.000 | **5.000/5** | 0 | ✅ Perfect — math is deterministic |
| C_AdCopy | ✅ PASS | 0.025 | 0.001 | 4.998/5 | 0 | ✅ Very good ad copy |
| D_ConditionAudit | ✅ PASS | 0.043 | 0.163 | 4.349/5 | 0 | ⚠️ Rubric noticed incomplete audit — QAG missed this |
| E_ChurnFormula | ✅ PASS | 0.062 | 0.329 | 3.685/5 | **2** | ⚠️ Missing variable flagged — took 3 attempts |
| F_BoardReport | ✅ PASS | 0.054 | **0.536** | **2.857/5** | 0 | ❌ Lowest score — incomplete upstream data detected |
| G_RiskAudit | ✅ PASS | 0.038 | 0.232 | 4.073/5 | 0 | ⚠️ Moderate — identifies partial risks |

---

## ✅ What Worked

- **G-Eval catches what QAG misses (D_ConditionAudit)**: QAG gave D=0.000 (3/3 pass). G-Eval gives D=0.163 (4.349/5) — the CoT rubric prompted the judge to enumerate all 5 required conditions before scoring, revealing the 5th was not checked.
- **F_BoardReport error propagation detected (D=0.536)**: The board report receives the lowest G-Eval score because it must reference E's incomplete churn formula. This is **error propagation caught by evaluation** — a downstream node penalized for an upstream node's omission.
- **E_ChurnFormula FAIL→retry works**: Scores of 2.120 and 1.906 on attempts 1–2 triggered FAIL (D≥0.7). The model incorporated critic feedback on attempt 3 and reached 3.685/5. The retry loop correctly rescued the node.
- **B_ROI: P(5)=0.9999** — Near-perfect certainty for mechanically correct math. G-Eval confirms what should be certain.

## ❌ What's Lacking

- **F_BoardReport passes despite D=0.536**: The A-Score formula still passes F (A=0.054 < 0.4 threshold). A more sensitive threshold would flag F as needing human review. The low G-Eval score doesn't translate to AMBIGUOUS routing.
- **E_ChurnFormula takes 2 retries**: The retry loop solves it, but 3× API calls is expensive. Better to catch omissions earlier (upstream) rather than discovering them through FAIL cycles.
- **Still single GPT judge for G-Eval**: The rubric is generated and scored by the same GPT model. Cross-model rubric generation would be more robust (→ Exp06).

## 🔧 What's Needed Next

- Lower the A-Score AMBIGUOUS threshold or add a G-Eval score threshold — F_BoardReport at 2.857/5 should route to AMBIGUOUS, not PASS
- Combine G-Eval with multi-LLM judges for rubric scoring (→ Exp06)
- Investigate whether retry feedback is actually used by the model (did E improve because of feedback, or just luck?)
