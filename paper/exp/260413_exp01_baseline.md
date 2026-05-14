# Exp01 — Baseline (Autonomous Driving Graph)

> **One-line verdict:** The critic successfully caught an intentional omission (FAIL→retry), and a downstream detection node correctly identified the missing condition — basic pipeline integrity confirmed.

**Date:** 2026-04-17 | **Script:** `exp/260413_exp01_baseline.py` | **State:** `state.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (5/5) | C required 1 retry |
| Omission detected? | ✅ Yes | Critic caught missing "Premium tier" on 1st attempt |
| Downstream detection? | ✅ Yes | D_ConditionCheck identified omission correctly |
| A-Scores reasonable? | ✅ Yes | All well below 0.4 threshold |
| Creative node variance? | ⚠️ High | E_Copy A=0.133 — expected but watch threshold |

---

## Score Guide (how to read results)

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 (→ AMBIGUOUS) |
| **S (similarity)** | > 0.9 | 0.7 – 0.9 | < 0.7 (inconsistent) |
| **C (confidence)** | > 0.8 | 0.5 – 0.8 | < 0.5 (uncertain) |
| **D (deviation)** | < 0.2 | 0.2 – 0.6 | ≥ 0.7 (→ FAIL) |

---

## Graph Structure

```
A_Trend → B_Model → C_PricingFormula → D_ConditionCheck → E_Copy
                         (omits "Premium tier" intentionally)
```

| Node | Role | Trap? |
|------|------|-------|
| A_Trend | Analyze 3 autonomous driving trends | — |
| B_Model | Design subscription revenue model | — |
| C_PricingFormula | Pricing formula — **intentionally omits "Premium" tier** | ✅ Omission trap |
| D_ConditionCheck | Detect which tier was omitted + commercial impact | ✅ Detection node |
| E_Copy | Write 5 marketing email subject lines | — |

---

## Node Results

| Node | Status | A-Score | D | Retries | Verdict |
|------|--------|---------|---|---------|---------|
| A_Trend | ✅ PASS | 0.059 | — | 0 | Good — open-ended, low variance |
| B_Model | ✅ PASS | 0.024 | — | 0 | Good — well-anchored by A |
| C_PricingFormula | ✅ PASS | 0.041 | 0.7 (1st) | **1** | Needed retry — omission correctly flagged |
| D_ConditionCheck | ✅ PASS | 0.075 | — | 0 | Good — identified missing tier |
| E_Copy | ⚠️ PASS | **0.133** | — | 0 | Highest score — creative variance is expected |

---

## ✅ What Worked

- **Omission → FAIL routing works**: C_PricingFormula received D≥0.7 on attempt 1. The critic caught the intentional omission without any special tooling. This validates the core FAIL-detection mechanism.
- **Downstream detection works**: D_ConditionCheck (A=0.075) correctly identified the missing Premium tier. The pipeline can propagate error awareness, not just error.
- **Retry + feedback loop works**: After FAIL, the critic's feedback was injected back into the prompt. C passed on retry — the self-correction loop functions correctly.

## ❌ What's Lacking

- **No numerical constraints**: This graph is creative/open-ended. A-Scores are low because the critic has nothing concrete to fault. Results are not comparable to strict-constraint graphs (Exp02+).
- **S and C not tracked per-node**: Results table doesn't show S/C breakdowns — partial visibility into what's driving each A-Score.
- **Single GPT critic**: Same model that generates also judges. Known same-model leniency bias (see Exp06 for fix).

## 🔧 What's Needed Next

- Run with stricter numerical constraints to stress-test FAIL detection (→ Exp02)
- Replace self-report C with logprobs C (→ Exp03)
- Use multi-LLM judges to remove same-model bias (→ Exp06)
