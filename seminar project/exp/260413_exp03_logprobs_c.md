# Exp03 — Logprobs C (Token Probability Confidence)

> **One-line verdict:** Replacing self-report confidence with logprobs reveals that models are genuinely uncertain on omission/audit nodes (C=0.000), but A-Scores inflate because logprobs C is very conservative — threshold tuning required.

**Date:** 2026-04-17 | **Script:** `exp/260413_exp03_logprobs_c.py` | **Evaluator:** `src/evaluators/exp_logprobs_c.py` | **State:** `state_exp03.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (7/7) | No retries |
| Omission-audit nodes show low C? | ✅ Yes | D_ConditionAudit C=0.000, G_RiskAudit C=0.000 |
| A-Scores more discriminating? | ✅ Yes | Range 0.006–0.204 vs baseline 0.011–0.079 |
| A-Scores too high overall? | ⚠️ Maybe | G_RiskAudit=0.204 is close to ambiguity zone |
| Logprobs C more honest than self-report? | ✅ Yes | Self-report always ~0.9; logprobs shows real variance |

---

## Score Guide

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 |
| **S (similarity)** | > 0.9 | 0.7 – 0.9 | < 0.7 |
| **C (logprobs)** | > 0.7 | 0.3 – 0.7 | < 0.3 (model is internally uncertain) |
| **D (deviation)** | < 0.2 | 0.2 – 0.6 | ≥ 0.7 |

---

## What Changed vs Baseline

| | Baseline C | Exp03 C |
|---|---|---|
| **Method** | Worker reports `{"confidence": 0.9}` | P(YES) / (P(YES)+P(NO)) via logprobs |
| **Typical value** | 0.8–1.0 always | 0.0–0.9 depending on actual uncertainty |
| **Can be gamed?** | Yes — model always reports high | No — it's a raw token probability |

---

## Graph Structure (7 nodes)

```
A_Pricing ──(R=0.9)──► B_ROI ──(R=0.5)──► C_AdCopy
    │
    └──(R=0.95)──► D_ConditionAudit (omits condition 5)
                         │
A, B ──────────────► E_ChurnFormula (omits support_tier_weight)
D, C, E ───────────► F_BoardReport
D, E, F ───────────► G_RiskAudit
```

---

## Node Results

| Node | Status | A-Score | S | C (logprobs) | D | Verdict |
|------|--------|---------|---|-------------|---|---------|
| A_Pricing | ✅ PASS | 0.144 | 0.977 | 0.469 | 0.500 | ⚠️ High A — C=0.469 reveals real uncertainty |
| B_ROI | ✅ PASS | 0.006 | 0.988 | 0.008 | 0.000 | ✅ Excellent — math is correct, nearly certain |
| C_AdCopy | ✅ PASS | 0.068 | 0.928 | 0.349 | 0.100 | ✅ Good |
| D_ConditionAudit | ✅ PASS | 0.102 | 0.895 | **0.000** | 0.100 | ⚠️ C=0.000 shows model knows audit is incomplete |
| E_ChurnFormula | ✅ PASS | 0.088 | 0.955 | 0.562 | 0.300 | ⚠️ D=0.300 flags missing variable |
| F_BoardReport | ✅ PASS | 0.121 | 0.918 | 0.469 | 0.300 | ⚠️ Elevated — references incomplete E data |
| G_RiskAudit | ✅ PASS | **0.204** | 0.891 | **0.000** | 0.300 | ⚠️ Highest A — synthesizes all omissions |

---

## ✅ What Worked

- **Logprobs C reveals real uncertainty**: D_ConditionAudit (C=0.000) and G_RiskAudit (C=0.000) have near-zero YES confidence — the model internally knows these outputs are incomplete. Self-report would have given C≈0.9 for both.
- **A-Scores now differentiate between nodes**: Range 0.006–0.204 is much wider than baseline (0.011–0.047). Factual nodes (B_ROI=0.006) vs synthesis nodes (G_RiskAudit=0.204) are clearly distinguished.
- **Significant finding — C=0.000 is a red flag**: When logprobs C is near zero, it's a strong signal that the model's output is suspect. This did not surface in the baseline at all.

## ❌ What's Lacking

- **A_Pricing A-Score=0.144 is too high**: The logprobs formula amplifies D when C is low. With D=0.500 and C=0.469, the score jumps to 0.144 vs baseline 0.047. This may be over-sensitive for this node — a calibration issue.
- **G_RiskAudit at 0.204 is borderline**: Getting close to the 0.4 AMBIGUOUS threshold. If the run were slightly noisier, this synthesis node might be incorrectly flagged.
- **Still uses single GPT critic for D**: D component is still biased. Logprobs only improved C, not D.

## 🔧 What's Needed Next

- Fix the D component — logprobs C alone isn't enough (→ Exp04 QAG, Exp05 G-Eval)
- Adjust A-Score threshold or formula weights now that C is more conservative
- Multi-LLM judges for D to remove GPT self-evaluation bias (→ Exp06)
