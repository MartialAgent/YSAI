"""
Exp03 — Logprobs C (Confidence via Token Log-Probabilities)
============================================================
Meeting note reference: Section 2 — C (확신도) upgrade
    Current:  Worker self-reports a 0-1 confidence score (subjective, gameable).
    Improved: Send a YES/NO hallucination-probe question to the model with logprobs=True.
              Extract P(YES) and P(NO) from top_logprobs, compute C = P(YES) / (P(YES) + P(NO)).

Why this is better:
  - Self-report confidence is trivially biased upward.
  - Log-probability of the verification token is a model-internal signal, not a generated narrative.
  - No extra generation cost: max_tokens=1 probe.

API call count vs baseline: +1 per node (probe call replaces the json self-report call, net same).
"""
import json
import math
import logging
from openai import OpenAI
from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, WORKER_MODEL, CRITIC_MODEL, EMBEDDING_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import check_similarity, run_critic

logger = logging.getLogger(__name__)
client = OpenAI()


def _generate_two_responses(prompt: str) -> tuple[str, str]:
    responses = []
    for _ in range(2):
        res = client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional strategic analyzer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        responses.append(res.choices[0].message.content)
    return responses[0], responses[1]


def _logprobs_confidence(response: str) -> float:
    """
    Probes the model with a YES/NO factual-accuracy question.
    Returns P(YES) / (P(YES) + P(NO)) derived from logprobs.
    """
    probe = (
        f"Review this response:\n{response}\n\n"
        "Is this response factually accurate, logically consistent, and free of hallucinations? "
        "Answer with exactly one word: YES or NO."
    )
    res = client.chat.completions.create(
        model=WORKER_MODEL,
        messages=[{"role": "user", "content": probe}],
        max_tokens=1,
        logprobs=True,
        top_logprobs=5,
        temperature=0.0,
    )
    try:
        top_lps = res.choices[0].logprobs.content[0].top_logprobs
        prob_map = {lp.token.strip().upper(): math.exp(lp.logprob) for lp in top_lps}
        p_yes = prob_map.get("YES", 0.0)
        p_no = prob_map.get("NO", 0.0)
        total = p_yes + p_no
        return (p_yes / total) if total > 0 else 0.5
    except Exception as e:
        logger.warning(f"[Exp03] Logprobs parse failed: {e}")
        return 0.5


def process_node(node: NodeState) -> NodeState:
    prompt = node.task_description
    if node.input_data:
        prompt = f"Context from previous steps:\n{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\nTask:\n{prompt}"
    else:
        prompt = f"Task:\n{prompt}"

    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
        worker_prompt += f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n{node.evaluation.feedback}"

    logger.info(f"[Exp03-LogprobsC] Processing node {node.node_id}")

    ans_primary, ans_secondary = _generate_two_responses(worker_prompt)
    conf_c = _logprobs_confidence(ans_primary)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_critic(prompt, ans_primary)

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
        logger.warning(f"[Exp03] Node {node.node_id} FAIL — deviation={dev_d:.3f}")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp03] Node {node.node_id} AMBIGUOUS — A-Score={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"[Exp03] Node {node.node_id} PASS — A-Score={a_score:.3f}, C(logprobs)={conf_c:.3f}")

    return node
