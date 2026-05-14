# Exp08 — Improved A-Score (Kendall's W + Discordance + Adjusted Confidence + Urgency)

> **One-line verdict:** The new formula correctly identifies F_BoardReport (A=0.156) and G_RiskAudit (A=0.113) as the most ambiguous nodes — driven by concern count dampening C_adj — while keeping clean nodes near zero. C_adj is the standout improvement: it silently penalizes nodes that hedge or express uncertainty.

**Date:** 2026-04-18 | **Script:** `exp/260413_exp08_ascore_improved.py` | **Evaluator:** `src/evaluators/exp_ascore_improved.py` | **State:** `state_exp08.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (7/7) | No retries |
| Formula correctly implemented? | ✅ Yes | Fixed from stub (dev_d=0.0) to full Kendall's W + C_adj |
| F_BoardReport flagged as most uncertain? | ✅ Yes | A=0.156, C_adj=0.345 (4 concerns) |
| C_adj dampens correctly on omission nodes? | ✅ Yes | E_ChurnFormula C_adj=0.429 (Z=2), F/G C_adj=0.345 (Z=4) |
| More discriminating than baseline? | ✅ Yes | Wider range: 0.028–0.156 vs baseline 0.012–0.047 |
| No false positives on clean nodes? | ✅ Yes | B_ROI=0.039, D_ConditionAudit=0.028 |

---

## Formula (what changed vs. baseline)

### Previous formula (Exp01–02 baseline):
```
A = α(1 - S) + β × D × (1 - C)

S = cosine similarity between 2 responses
C = worker self-report confidence (always ~0.8–1.0)
D = single GPT critic score
```

### New formula (Exp08):
```
A = α(1 - W) + β × (D / C_adj) × U

W     = Kendall's W proxy — mean pairwise cosine sim across k=3 responses
D     = Discordance — how far primary response deviates from the group mean
Z     = Number of concern/uncertainty keywords in the primary response
C_adj = C × (1 / (1 + ln(1 + Z)))   ← confidence dampened by expressed worries
U     = Urgency multiplier (1.0 for general QA)
```

### What each term adds:

| Component | Role | Why it matters |
|-----------|------|----------------|
| **W (Kendall's)** | Measures group concordance across 3 responses | More robust than 2-response cosine S; catches cases where 2/3 agree but 1 diverges |
| **D (Discordance)** | Primary response vs. group deviation | Identifies when a specific response is the outlier |
| **C_adj** | Confidence adjusted by concern keywords | Prevents high self-report C from masking uncertainty expressed in the text |
| **U** | Urgency multiplier | Allows domain-specific amplification (medical, financial) — 1.0 here |

---

## Score Guide

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 |
| **W (Kendall's)** | > 0.95 | 0.85 – 0.95 | < 0.85 (low concordance) |
| **D (Discordance)** | < 0.05 | 0.05 – 0.15 | > 0.15 |
| **C_adj** | > 0.7 | 0.3 – 0.7 | < 0.3 (heavily dampened) |
| **Z (concerns)** | 0 | 1–2 | 3+ (model is hedging a lot) |

---

## Node Results

| Node | Status | A-Score | W | D | C | Z | C_adj | Verdict |
|------|--------|---------|---|---|---|---|-------|---------|
| A_Pricing | ✅ PASS | 0.072 | 0.941 | 0.077 | 0.900 | 0 | 0.900 | ⚠️ D=0.077 moderate — pricing design has variation |
| B_ROI | ✅ PASS | 0.039 | 0.973 | 0.030 | 1.000 | 1 | 0.591 | ✅ Low A — ROI math stable; Z=1 dampens C slightly |
| C_AdCopy | ✅ PASS | 0.062 | 0.942 | 0.052 | 0.800 | 0 | 0.800 | ✅ Good — creative task, expected slight discordance |
| D_ConditionAudit | ✅ PASS | **0.028** | 0.971 | 0.028 | 1.000 | 0 | 1.000 | ✅ Best score — audit is highly stable and consistent |
| E_ChurnFormula | ✅ PASS | 0.058 | 0.962 | 0.034 | 0.900 | **2** | 0.429 | ⚠️ Z=2 halves C_adj — model hedges on omitted variable |
| F_BoardReport | ✅ PASS | **0.156** | 0.929 | 0.083 | 0.900 | **4** | 0.345 | ❌ Highest A — 4 concerns, C_adj=0.345, D highest |
| G_RiskAudit | ✅ PASS | 0.113 | 0.937 | 0.056 | 0.900 | **4** | 0.345 | ⚠️ High A — risk synthesis triggers 4 concern keywords |

---

## ✅ What Worked

- **C_adj is the key differentiator**: F_BoardReport and G_RiskAudit both have Z=4 (the model uses many hedge words when synthesizing incomplete data). C_adj drops to 0.345, amplifying D/C_adj significantly. This is exactly the intended behavior — the formula is stricter when the model itself signals uncertainty.

- **E_ChurnFormula Z=2**: The model hedges twice when producing the intentionally incomplete churn formula (`support_tier_weight` missing). C_adj drops from 0.900 to 0.429 — the concern dampening correctly picks up on the model's internal uncertainty about the missing variable, even though no external critic is involved.

- **D_ConditionAudit A=0.028 (best in experiment)**: All 3 responses produce nearly identical audit reports (W=0.971, D=0.028) and Z=0 (no hedging). The audit node is confident and consistent — C_adj=1.000 stays full. Lowest A-Score is correct for this stable node.

- **A_Pricing D=0.077 (highest raw discordance)**: Among the 3 pricing responses there is more variation in tier naming and structure. The formula correctly captures this without a critic call.

- **No false positives**: Clean nodes (B_ROI, D_ConditionAudit, C_AdCopy) all stay under 0.070.

## ❌ What's Lacking

- **No external critic (D is self-measured)**: D is computed from embedding distance between worker responses, not from a critic's assessment of correctness. A response can be consistently wrong (low D, high W) and still get a low A-Score. Compare E_ChurnFormula: D=0.034 (stable) despite intentional variable omission — the formula doesn't catch the content error, only the inter-response variance.

- **Z keyword counting is crude**: "however", "note that", "assumption" are treated equally regardless of context. A response saying "Note that this is a best-practice approach" has Z=1 even if the content is perfectly correct. This could over-penalize well-calibrated cautious outputs.

- **U=1.0 always**: Urgency multiplier is unused in this experiment. In high-stakes domains (medical, financial) U should be higher — but no mechanism exists yet to set it per-node or per-domain.

- **C_adj=0.345 for F/G doesn't trigger AMBIGUOUS**: A=0.156 and A=0.113 are below the 0.4 threshold. Despite the high concern count and dampened confidence, the system still passes these nodes. A domain-specific threshold or C_adj floor trigger would be needed.

## 🔧 What's Needed Next

- **Add external D signal**: Combine C_adj dampening with QAG quiz questions or G-Eval rubric scoring for D — get both internal uncertainty (Z) and external correctness check
- **Per-domain U values**: Allow nodes or graph definitions to specify U (e.g., financial nodes U=2.0)
- **C_adj threshold routing**: If C_adj < 0.4, route to AMBIGUOUS regardless of A-Score — the model is expressing too much uncertainty to be trusted
- **Smarter Z counting**: Weight concern keywords by context (e.g., "assumption" in a creative brief is benign; "assumption" in a medical diagnosis is critical)

---

## Comparison: Exp08 vs. Baseline (Exp02)

| Node | Baseline A | Exp08 A | Change | Driver |
|------|-----------|---------|--------|--------|
| A_Pricing | 0.047 | 0.072 | ↑ +0.025 | D=0.077 raises the score |
| B_ROI | 0.012 | 0.039 | ↑ +0.027 | Z=1 dampens C_adj slightly |
| C_AdCopy | 0.032 | 0.062 | ↑ +0.030 | D=0.052 from creative variance |
| D_ConditionAudit | — | **0.028** | New | Best score — stable + confident |
| E_ChurnFormula | — | 0.058 | New | Z=2 flags hedging on missing variable |
| F_BoardReport | — | **0.156** | New | Z=4 + D=0.083 = strongest signal |
| G_RiskAudit | — | 0.113 | New | Z=4 on synthesis task |
