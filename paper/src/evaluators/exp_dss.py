"""
Exp07 — DSS (Dependency Sensitivity Score)
===========================================
Meeting note reference: Section 7 — GPT recommendation: Dependency Sensitivity Score
    Formula: DSS(node_i) = Δ(Output_downstream) / Δ(Input_i)
    Intuition: "If we slightly perturb this node's input, how much does its output change?"
               High DSS = high-risk upstream node. Small input shift → large output cascade.

Implementation approach:
  After a node produces its primary output (using the baseline evaluator),
  re-run the worker with a semantically-perturbed version of the same prompt.
  Measure the cosine distance between original and perturbed outputs.
  DSS = cosine_distance(original_output, perturbed_output)
       (perturbation magnitude is fixed at 1 unit, so DSS reduces to pure output divergence)

DSS is reported as a diagnostic metric alongside A-Score.
Nodes with DSS > DSS_HIGH_RISK_THRESHOLD are flagged as high-risk upstream nodes.

API calls vs baseline: +2 per node (perturbed worker call + embedding comparison).
"""
import json
import logging
import numpy as np
from openai import OpenAI
from src.config import (
    ALPHA, BETA, A_SCORE_THRESHOLD,
    WORKER_MODEL, CRITIC_MODEL, EMBEDDING_MODEL,
)
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import check_similarity, generate_worker_response, run_critic

logger = logging.getLogger(__name__)
client = OpenAI()

DSS_HIGH_RISK_THRESHOLD = 0.3   # cosine distance above this → flag as high-risk


def _perturb_prompt(prompt: str) -> str:
    """
    Applies a fixed semantic perturbation to the prompt.
    We prepend an alternative framing instruction so the model is nudged
    toward a slightly different angle — exposing output sensitivity.
    """
    return (
        "Consider an alternative perspective before answering. "
        "Re-examine any assumptions in the following task critically:\n\n"
    ) + prompt


def _cosine_distance(text1: str, text2: str) -> float:
    """Returns 1 - cosine_similarity (0=identical, 1=orthogonal)."""
    try:
        res = client.embeddings.create(
            input=[text1[:8000], text2[:8000]], model=EMBEDDING_MODEL
        )
        v1 = np.array(res.data[0].embedding)
        v2 = np.array(res.data[1].embedding)
        similarity = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        return 1.0 - similarity
    except Exception as e:
        logger.warning(f"[Exp07] DSS embedding failed: {e}")
        return 0.0


def compute_dss(original_prompt: str, original_output: str) -> float:
    """
    Runs the worker once more with a perturbed prompt.
    DSS = cosine_distance(original_output, perturbed_output).
    """
    perturbed_prompt = _perturb_prompt(original_prompt)
    try:
        res = client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional strategic analyzer."},
                {"role": "user", "content": perturbed_prompt},
            ],
            temperature=0.7,
        )
        perturbed_output = res.choices[0].message.content
        dss = _cosine_distance(original_output, perturbed_output)
        logger.info(f"[Exp07] DSS computed: {dss:.3f}")
        return dss
    except Exception as e:
        logger.warning(f"[Exp07] DSS worker call failed: {e}")
        return 0.0


def process_node(node: NodeState) -> NodeState:
    prompt = node.task_description
    if node.input_data:
        prompt = f"Context from previous steps:\n{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\nTask:\n{prompt}"
    else:
        prompt = f"Task:\n{prompt}"

    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
        worker_prompt += f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n{node.evaluation.feedback}"

    logger.info(f"[Exp07-DSS] Processing node {node.node_id}")

    ans_primary, ans_secondary, conf_c = generate_worker_response(worker_prompt)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_critic(prompt, ans_primary)

    a_score = ALPHA * (1.0 - sim_s) + BETA * dev_d * (1.0 - conf_c)

    # DSS computation (additional pass with perturbed input)
    dss = compute_dss(worker_prompt, ans_primary)
    dss_flag = dss > DSS_HIGH_RISK_THRESHOLD
    dss_note = (
        f"\nDSS (Dependency Sensitivity Score): {dss:.3f}"
        + (" ⚠ HIGH-RISK upstream node" if dss_flag else " — stable")
    )

    node.output_data = ans_primary
    node.evaluation = EvaluationResult(
        similarity_score=sim_s,
        confidence_score=conf_c,
        deviation_score=dev_d,
        ambiguity_index=a_score,
        feedback=feedback + dss_note,
    )

    if dss_flag:
        logger.warning(
            f"[Exp07] Node {node.node_id} flagged HIGH-RISK DSS={dss:.3f} > {DSS_HIGH_RISK_THRESHOLD}"
        )

    if dev_d >= 0.7:
        node.status = NodeStatus.FAIL
        logger.warning(f"[Exp07] Node {node.node_id} FAIL — deviation={dev_d:.3f}")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp07] Node {node.node_id} AMBIGUOUS — A-Score={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(
            f"[Exp07] Node {node.node_id} PASS — A-Score={a_score:.3f}, DSS={dss:.3f}"
        )

    return node
