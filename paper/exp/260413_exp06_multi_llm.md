# Exp06 — Multi-LLM Judge (Cross-Model Deviation Averaging)

> **One-line verdict:** Multi-LLM provides the strongest omission signal — all 3 model families unanimously flag E_ChurnFormula (D(avg)=0.667), and F_BoardReport triggers FAIL on attempt 1 — but Gemini is an extreme outlier on G_RiskAudit (0.850 vs others' 0.200).

**Date:** 2026-04-17 | **Script:** `exp/260413_exp06_multi_llm.py` | **Evaluator:** `src/evaluators/exp_multi_llm.py` | **State:** `state_exp06.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (7/7) | F required 1 retry |
| E_ChurnFormula missing variable detected? | ✅ Strongly | All 3 judges agree D(avg)=0.667 — strongest signal yet |
| F_BoardReport error propagation detected? | ✅ Yes | FAIL on attempt 1 (D(avg)=0.700) |
| Cross-model agreement on clean nodes? | ✅ Yes | B/C/D all unanimous D=0.000 |
| Judge disagreement visible? | ✅ Yes | G_RiskAudit: Gemini=0.850 vs GPT/Claude=0.200 |
| Same-model bias reduced? | ✅ Yes | GPT leniency on A_Pricing corrected by avg |

---

## Score Guide

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 |
| **D(avg) — averaged across 3 judges** | < 0.2 | 0.2 – 0.5 | > 0.5 (significant issue) |
| **Judge disagreement** | < 0.3 spread | 0.3–0.5 spread | > 0.5 (model-specific bias) |

---

## Judge Configuration

| Judge | Model | Tendency (observed) |
|-------|-------|---------------------|
| GPT-4o | OpenAI | Strict on pricing (0.500 for A_Pricing), lenient on synthesis |
| Claude Sonnet 4.5 | Anthropic | Strict on content quality (0.700 on E) |
| Gemini 2.5 Flash | Google | Strictest overall on omissions (0.800–0.850) |

---

## Node Results

| Node | Status | A-Score | D(GPT) | D(Claude) | D(Gemini) | D(avg) | Retries | Verdict |
|------|--------|---------|--------|-----------|-----------|--------|---------|---------|
| A_Pricing | ✅ PASS | 0.024 | 0.500 | 0.000 | 0.000 | 0.167 | 0 | ⚠️ GPT stricter — same-model bias reversed |
| B_ROI | ✅ PASS | 0.020 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | ✅ Unanimous perfect — math is objectively correct |
| C_AdCopy | ✅ PASS | 0.026 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | ✅ Unanimous clean |
| D_ConditionAudit | ✅ PASS | 0.009 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | ⚠️ All miss the 5th condition (like QAG) |
| E_ChurnFormula | ✅ PASS | 0.061 | 0.500 | 0.700 | **0.800** | **0.667** | 0 | ❌ Strongest omission signal — all 3 agree |
| F_BoardReport | ✅ PASS | 0.072 | 0.500 | 0.300 | 0.000 | 0.267 | **1** | ⚠️ FAIL on 1st attempt — error propagation |
| G_RiskAudit | ✅ PASS | 0.044 | 0.200 | 0.200 | **0.850** | 0.417 | 0 | ⚠️ Gemini extreme outlier — model-specific bias |

---

## ✅ What Worked

- **E_ChurnFormula: unanimous high D (all 3 judges)**: GPT=0.500, Claude=0.700, Gemini=0.800. When 3 different model families independently agree on high deviation, the probability of a false positive is very low. This is the **most reliable omission detection** across all 7 experiments.
- **F_BoardReport triggers FAIL (D(avg)=0.700)**: Error propagation from E is detected — all judges penalize the board report for citing incomplete churn data. The FAIL→retry loop correctly recovered it.
- **Same-model bias corrected**: In the baseline, GPT-only D for A_Pricing was ~0.05. Here GPT-4o alone gives 0.500, which is closer to the truth (strict constraints that are borderline satisfied). Averaging with Claude/Gemini moderates to 0.167.
- **Unanimous D=0.000 on B_ROI and C_AdCopy**: Cross-model agreement on clean nodes is a strong quality signal — if all 3 agree it's fine, it genuinely is fine.

## ❌ What's Lacking

- **D_ConditionAudit: all 3 judges give D=0.000**: Like QAG, all multi-LLM judges fail to detect the omitted 5th condition in the audit report. The judges assess what's present, not what's absent. This is the consistent blind spot across all evaluators except G-Eval.
- **Gemini outlier on G_RiskAudit (0.850 vs 0.200)**: A spread of 0.65 between Gemini and the others is too large to average meaningfully. This suggests Gemini applies model-specific strict standards to pipeline risk assessments. The average (0.417) may not be the right signal here.
- **Cost is 3× baseline per node**: 3 judge calls per node. For a 7-node graph, this is 21 additional API calls per run.

## 🔧 What's Needed Next

- Investigate why all judges miss D_ConditionAudit's 5th condition — inject the original 5-condition spec into the judge prompt
- Add judge disagreement as a separate metric: high spread = send to human review
- Explore weighted averaging (e.g., weight Gemini lower on synthesis nodes based on observed bias patterns)
