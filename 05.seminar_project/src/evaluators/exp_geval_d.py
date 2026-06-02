"""
Exp05 — G-Eval D (Chain-of-Thought Rubric + Probabilistic Score Aggregation)
=============================================================================
Meeting note reference: Section 1 — G-Eval (3-stage mechanism)
    Stage 1: LLM writes a task-specific evaluation rubric (CoT).
    Stage 2: LLM scores the response (1–5) following the rubric.
    Stage 3: Instead of taking the raw "4" token, compute a weighted average
             over log-probabilities of score tokens 1–5 for stability.
             D = 1 - normalized(weighted_score)

Why this is better than a plain critic:
  - The rubric is derived from the actual task, so evaluation criteria are always relevant.
  - Probabilistic aggregation removes the variance of a single stochastic token selection.
    Example: P(4)=0.8, P(5)=0.2 → score=4.2 instead of a random flip between 4 and 5.
  - Cited in meeting as the Galileo AI platform's approach.

API calls vs baseline: +1 (rubric gen) in exchange for similar critic call structure.
"""
import json
import math
import logging
from openai import OpenAI
from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, CRITIC_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import check_similarity, generate_worker_response

logger = logging.getLogger(__name__)
client = OpenAI()

_SCORE_TOKENS = {"1", "2", "3", "4", "5"}


def run_geval(task_prompt: str, worker_response: str) -> tuple[float, str]:
    """
    G-Eval 3-stage evaluation.
    Returns (deviation_score 0–1, feedback string).
    """
    # Stage 1: Generate task-specific evaluation rubric (CoT)
    rubric_prompt = (
        f"You are designing a grading rubric for this task:\n{task_prompt}\n\n"
        "Write a step-by-step evaluation checklist (3–5 items) for assessing a response to this task. "
        "Focus on: factual accuracy, numerical correctness, constraint adherence, logical consistency, completeness. "
        "Output as a numbered list only."
    )
    rubric_res = client.chat.completions.create(
        model=CRITIC_MODEL,
        messages=[{"role": "user", "content": rubric_prompt}],
        temperature=0.0,
    )
    rubric = rubric_res.choices[0].message.content.strip()

    # Stage 2 + 3: Score with logprobs for probabilistic aggregation
    scoring_prompt = (
        f"Task:\n{task_prompt}\n\n"
        f"Evaluation Rubric:\n{rubric}\n\n"
        f"Response to Evaluate:\n{worker_response}\n\n"
        "Follow the rubric step by step. Then output a single integer score:\n"
        "1 = completely wrong / hallucinated\n"
        "2 = mostly wrong, major gaps\n"
        "3 = partially correct\n"
        "4 = mostly correct, minor issues\n"
        "5 = perfect, fully meets all criteria\n"
        "Output ONLY the integer (1, 2, 3, 4, or 5). No other text."
    )
    score_res = client.chat.completions.create(
        model=CRITIC_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict evaluator. Output only a single digit."},
            {"role": "user", "content": scoring_prompt},
        ],
        max_tokens=1,
        logprobs=True,
        top_logprobs=5,
        temperature=0.0,
    )

    # Stage 3: Weighted average over score token logprobs
    weighted_score = 3.0  # neutral default
    try:
        top_lps = score_res.choices[0].logprobs.content[0].top_logprobs
        prob_map = {}
        for lp in top_lps:
            token = lp.token.strip()
            if token in _SCORE_TOKENS:
                prob_map[token] = math.exp(lp.logprob)

        total_prob = sum(prob_map.values())
        if total_prob > 0:
            weighted_score = sum(int(t) * p for t, p in prob_map.items()) / total_prob
            logger.info(f"[Exp05] G-Eval prob_map={prob_map}, weighted={weighted_score:.3f}")
        else:
            # Fallback to raw token if logprobs gave nothing in 1-5
            raw = score_res.choices[0].message.content.strip()
            if raw in _SCORE_TOKENS:
                weighted_score = float(raw)
    except Exception as e:
        logger.warning(f"[Exp05] G-Eval logprobs parse failed: {e}")

    # Normalize 1–5 → 0–1 deviation (inverted: higher score = lower deviation)
    deviation = 1.0 - ((weighted_score - 1.0) / 4.0)
    feedback = (
        f"G-Eval Score: {weighted_score:.2f}/5 → deviation={deviation:.3f}\n"
        f"Rubric used:\n{rubric}"
    )
    return deviation, feedback


def process_node(node: NodeState) -> NodeState:
    prompt = node.task_description
    if node.input_data:
        prompt = f"Context from previous steps:\n{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\nTask:\n{prompt}"
    else:
        prompt = f"Task:\n{prompt}"

    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
        worker_prompt += f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n{node.evaluation.feedback}"

    logger.info(f"[Exp05-GEval] Processing node {node.node_id}")

    ans_primary, ans_secondary, conf_c = generate_worker_response(worker_prompt)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_geval(prompt, ans_primary)

    a_score = ALPHA * (1.0 - sim_s) + BETA * dev_d * (1.0 - conf_c)

    node.output_data = ans_primary
    node.evaluation = EvaluationResult(
        similarity_score=sim_s,
        confidence_score=conf_c,
        deviation_score=dev_d,
        ambiguity_index=a_score,
        feedback=feedback,
    )

    if dev_d >= 0.7:
        node.status = NodeStatus.FAIL
        logger.warning(f"[Exp05] Node {node.node_id} FAIL — deviation={dev_d:.3f}")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp05] Node {node.node_id} AMBIGUOUS — A-Score={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"[Exp05] Node {node.node_id} PASS — A-Score={a_score:.3f}, D(G-Eval)={dev_d:.3f}")

    return node
