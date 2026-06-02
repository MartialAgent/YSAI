# Meeting Notes — 2026-04-01
**Topic:** AgentDAG Evaluation Architecture Discussion  
**Focus:** Improving A-Score beyond shallow similarity metrics

---

## Overview

Current A-Score has a known weakness: it relies on shallow similarity (cosine similarity), which is insufficient for robust LLM agent evaluation. This meeting explored 7 directions for improving the evaluation architecture.

---

## 1. G-Eval — LLM-as-Judge with Probabilistic Scoring

### How it works (3 stages)

**Stage 1: Rubric Definition (Evaluation Prompting)**
- Developer writes natural-language criteria for what to evaluate
- Does **not** require ground truth labels
- Example: *"Rate this answer's 'expertise' on a 1–5 scale. Expertise means citing specific figures and using business terms accurately."*

**Stage 2: Chain-of-Thought Checklist Generation**
- LLM is asked to generate its own evaluation sub-steps before scoring
- Example internal steps:
  1. Check if specific figures (ROI %, prices) are present
  2. Check if domain terms like *Churn rate*, *LTV* are used
  3. Check if reasoning flows without logical gaps

**Stage 3: Form-filling + Probabilistic Score Aggregation**
- LLM evaluates using its generated checklist, then outputs a score
- **Key insight:** Rather than taking the raw output token ("4"), G-Eval computes a **weighted average of log-probabilities** across all score tokens (1–5)
- Example: if P(4) = 80%, P(5) = 20% → final score = **4.2** (more stable and precise)

### Platform
- Galileo AI is noted as using this approach (AI observability + eval engineering platform)

### Concern
> Current agent pipeline: ~5 API calls per request. G-Eval may increase this to **8–10 calls**. Cost and latency tradeoff needs consideration.

---

## 2. A-Score 2.0 — Recommended Hybrid Upgrade

Current A-Score components (D, S, C) can each be improved:

| Component | Current | Proposed Upgrade |
|-----------|---------|-----------------|
| **S** (Similarity) | Cosine similarity | SelfCheckGPT-style local **NLI (Natural Language Inference)** contradiction check |
| **C** (Confidence) | Model self-report | **API Logprobs** (token probability statistics) — fully automatic |
| **D** (Deviation) | Simple critic prompting | **QAG (Question-Answer Generation)** or **G-Eval prompting** |

### Supplementary Approaches

#### Reflexion — Self-Reflection Agent Evaluation
- Instead of numeric scores, a Critic writes **trajectory feedback** (short-term memory notes)
- Worker agent reads its own reflection on the next retry: *"Last time I missed section A"*
- Use case: replace score-based cutoffs with a **feedback loop** as the node pass/fail criterion

#### QAG — Question-Answer Generation (Hallucination Detection)
- More transparent and mathematical than G-Eval's subjective scoring
- **Process:**
  1. Generate 3 quiz questions from the previous node's output (Input)
  2. Test whether the current node's output (Output) alone can answer them correctly
- **Integration:** Use quiz pass rate as the **D (Deviation)** component in A-Score
- Favored in RAGAS (RAG evaluation framework)

---

## 3. Cross-Model Evaluation — Using Different LLMs as Judges

**Problem identified (from class):** GPT tends to score GPT-generated answers more favorably (same-model bias).

**Proposal:** Use the **average score from multiple different LLMs** as the evaluation baseline, rather than relying on a single judge model.

> Action item: Search for existing papers on cross-model judge averaging. Check with Professor Kim Jaehyeong's group and Hoik's last-year project (who ran answers through 4 models rotating).

---

## 4. SAC³ — Semantic-Aware Cross-check Consistency

**Paper:** [arXiv:2311.01740](https://arxiv.org/abs/2311.01740)  
**Reference:** [Blog summary (Korean)](https://yoonschallenge.tistory.com/1052)

### Motivation
Standard self-consistency misses two failure modes:
1. **Question-level hallucination** — ambiguous questions cause inconsistent answers
2. **Model-level hallucination** — model consistently gives the same wrong answer

### Method
SAC³ combines:
- **Semantic perturbation:** Rephrase the same question multiple ways and check answer stability
- **Cross-model consistency:** Compare answers across different LLMs

### Scoring Components

| Score | Description |
|-------|-------------|
| **SC² (Self-check)** | Consistency across multiple samples for the same question Q₀. Low score = high consistency = likely factual |
| **SAC³-Q (Question-level)** | Consistency across semantically equivalent rephrasings Q₁~Qₖ. Consistent wrong answers across rephrasings → hallucination risk ↑ |
| **SAC³-M (Model-level)** | Cross-check with a verifier LM. If GPT says "No" but other models say "Yes" → GPT may be hallucinating |
| **SAC³-QM** | Combined question + model-level cross-check |

**Final Score formula:**  
`Final = SC² + λ × (SAC³-Q + SAC³-M)`  
where λ = verifier LM trust weight (default 1.0; higher for specialized domain models)

---

## 5. Personal Idea 1 — Multi-LLM Judge Averaging (SAC³ Integration)

Extending the cross-model evaluation idea (Section 3) using SAC³-style cross-checking:

- **Hypothesis:** Same-model bias is a real problem (validated by Professor Noh Albert's class observation)
- **Proposal:** Average scores from N different LLM judges as the evaluation signal

**Action items:**
- Search for existing literature on multi-judge averaging
- Ask Professor Kim Jaehyeong if related papers exist
- Get insight from Hoik's prior project (ran 4-model rotating evaluation)

---

## 6. Personal Idea 2 — Confusion Matrix Approach

*(To be elaborated)*  
Apply confusion matrix analysis to agent evaluation outputs — potential for precision/recall-style diagnostics on node-level pass/fail decisions.

---

## 7. GPT Recommendation — Dependency Sensitivity Score (DSS)

**Motivation:** Particularly relevant for DAG-structured agents.

**Definition:**
> "If we slightly perturb this node's input, how much does the downstream output change?"

$$\text{DSS}(\text{node}_i) = \frac{\Delta(\text{Output}_{\text{downstream}})}{\Delta(\text{Input}_i)}$$

- **High DSS** = high-risk upstream node (small input change causes large downstream cascade)
- Could be integrated as a **node risk weight** in A-Score

---

## Appendix — Referenced Paper

### "Towards a Science of Scaling Agent Systems"
**arXiv:** [2512.08296](https://arxiv.org/abs/2512.08296)

**5 Key Findings:**

1. **Tool–Coordination Trade-off:** Within a fixed token budget, complex tool-heavy tasks *degrade* with more agent communication. Coordination overhead consumes cognitive budget needed for tool use.

2. **Capability Saturation:** If a single agent already achieves ≥45% accuracy, adding more agents provides little or negative gain. A sufficiently capable solo agent beats a team.

3. **Error Amplification by Structure:**
   - Independent (no-communication) agents: **17.2× error amplification**
   - Centralized (manager-supervised) agents: **4.4× error amplification**

4. **Optimal Structure by Task Type:**

   | Task Type | Best Structure | Gain |
   |-----------|---------------|------|
   | Parallelizable (e.g. finance analysis) | Centralized multi-agent | +80.8% |
   | Dynamic web navigation | Decentralized | favorable |
   | Sequential reasoning | Single agent | multi-agent −39~70% |

5. **Predictive Model:** Researchers built a model that predicts optimal agent structure from task characteristics alone — **87% accuracy** on unseen tasks.

**Key takeaway:**  
> More agents ≠ better. Optimize based on **task sequentiality** and **tool use density**, not intuition.

---

## Summary — Recommended A-Score 2.0 Roadmap

```
S (Similarity):   Cosine → SelfCheckGPT NLI contradiction check
C (Confidence):   Self-report → API Logprobs weighted statistics  
D (Deviation):    Critic prompt → QAG quiz validation or G-Eval CoT
+ DSS:            Add Dependency Sensitivity Score as node risk weight
+ Cross-model:    Multi-LLM judge averaging (SAC³-inspired)
```
