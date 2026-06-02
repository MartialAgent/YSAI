# Exp02 — Baseline (SaaS Pricing Graph, Strict Constraints)

> **One-line verdict:** Even with hard numerical constraints, the single GPT critic is too lenient — all nodes pass easily, revealing same-model bias as the core problem to fix in Exp03–07.

**Date:** 2026-04-17 | **Script:** `exp/260413_exp02_saas_baseline.py` | **State:** `state_exp02.json`

---

## Quick Verdict

| Check | Result | Note |
|-------|--------|------|
| All nodes pass? | ✅ Yes (3/3) | No retries needed |
| Strict constraints enforced? | ⚠️ Partially | Critic is too lenient to penalize missing constraints |
| A-Scores discriminating? | ❌ No | All very low (0.012–0.047) — no differentiation |
| Same-model bias visible? | ❌ Yes (problem) | GPT judges GPT — scores are inflated |
| Useful as baseline? | ✅ Yes | Reference point for Exp03–07 comparison |

---

## Score Guide

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **A-Score** | < 0.1 | 0.1 – 0.4 | > 0.4 |
| **S (similarity)** | > 0.9 | 0.7 – 0.9 | < 0.7 |
| **C (confidence)** | > 0.8 | 0.5 – 0.8 | < 0.5 |
| **D (deviation)** | < 0.2 | 0.2 – 0.6 | ≥ 0.7 |

---

## Graph Structure

```
A_Pricing ──(R=0.9)──► B_ROI ──(R=0.5)──► C_AdCopy
```

| Node | Hard Constraints | Why It Matters |
|------|-----------------|----------------|
| A_Pricing | Pro = 2.5× Basic; Enterprise must include "Advanced Zero-Trust Security" + "500GB" | If wrong, all downstream calculations break |
| B_ROI | Exact math: (Savings - Cost) / Cost × 100, using A's prices | Numerical precision required |
| C_AdCopy | Must cite exact ROI % from B | Propagation fidelity test |

---

## Node Results

| Node | Status | A-Score | D | Verdict |
|------|--------|---------|---|---------|
| A_Pricing | ✅ PASS | 0.047 | ~0.05 | ⚠️ Suspiciously low — pricing constraints barely penalized |
| B_ROI | ✅ PASS | 0.012 | ~0.01 | ROI math is deterministic — low score expected |
| C_AdCopy | ✅ PASS | 0.032 | ~0.03 | ⚠️ Low despite often missing exact ROI % |

---

## ✅ What Worked

- **B_ROI scores correctly**: ROI math is mechanically verifiable and the model gets it right. A-Score=0.012 is genuinely low — a correct result.
- **Stable reference point**: 3 runs of this graph produce consistent scores. Good as a fixed comparison baseline.

## ❌ What's Lacking

- **Critic doesn't penalize constraint violations hard enough**: A_Pricing should score higher if constraints aren't met, but the GPT critic gives D≈0.05. This is the **same-model bias problem** — GPT is lenient toward GPT-generated pricing designs.
- **C_AdCopy gets away with missing ROI**: The ad copy often doesn't cite the exact ROI number, but the critic still gives near-zero D. In Exp04 (QAG), this node fails 1/3 quiz questions.
- **No differentiation between nodes**: A-Scores range only 0.012–0.047. The evaluator can't tell which node is better or worse.
- **3-node graph is too simple**: Doesn't stress-test propagation, condition auditing, or synthesis. (Fixed in Exp03–07 with 7-node graph.)

## 🔧 What's Needed Next

- Replace single GPT critic with logprobs C (→ Exp03) or quiz-based D (→ Exp04)
- Use multi-LLM judges to eliminate same-model leniency (→ Exp06)
- Extend graph to 7 nodes including omission traps and synthesis nodes (→ Exp03–07)
