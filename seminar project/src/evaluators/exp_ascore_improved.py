"""
Exp08 — Improved A-Score (Kendall's W + Discordance + Adjusted Confidence + Urgency)

Formula: A = α(1 - W) + β * (D / C_adj) * U

W   : Kendall's concordance proxy — mean pairwise cosine sim across k=3 responses
D   : Discordance — how far the primary response deviates from the group
C   : Self-report confidence (0–1)
Z   : Number of concern/uncertainty keywords in primary response
C_adj = C * (1 / (1 + ln(1 + Z)))  — dampens C when model expresses worries
U   : Urgency multiplier (default 1.0 for general QA)
"""
import json
import math
import logging
import numpy as np
from openai import OpenAI

from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, WORKER_MODEL, EMBEDDING_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import _cosine_similarity

logger = logging.getLogger(__name__)
client = OpenAI()

K_RESPONSES = 3   # number of worker responses for Kendall's W
U_DEFAULT   = 1.0  # urgency multiplier (general QA = 1.0)
C_ADJ_FLOOR = 0.01 # prevent D/C_adj explosion

CONCERN_KEYWORDS = [
    "uncertain", "unclear", "might", "possibly", "perhaps", "concern",
    "risk", "ambiguous", "not sure", "limited", "incomplete", "missing",
    "however", "caveat", "note that", "assumption", "estimated",
    "approximate", "caution", "warning", "doubt", "questionable",
]


# ── helpers ────────────────────────────────────────────────────────────────

def _generate_k_responses(prompt: str) -> list[str]:
    responses = []
    for _ in range(K_RESPONSES):
        res = client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional strategic analyzer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        responses.append(res.choices[0].message.content)
    return responses


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    res = client.embeddings.create(
        input=[t[:8000] for t in texts], model=EMBEDDING_MODEL
    )
    return [item.embedding for item in res.data]


def _kendall_w(embeddings: list[list[float]]) -> float:
    """
    Kendall's W proxy: mean pairwise cosine similarity across k responses.
    W ∈ [0, 1].  High W = high concordance (agents agree).
    """
    sims = []
    k = len(embeddings)
    for i in range(k):
        for j in range(i + 1, k):
            sims.append(_cosine_similarity(embeddings[i], embeddings[j]))
    return float(np.mean(sims))


def _discordance(primary_emb: list[float], all_embs: list[list[float]]) -> float:
    """
    D = how far primary response deviates from the group.
    D = 1 - mean_sim(primary, others).  D ∈ [0, 1].
    """
    others = [e for i, e in enumerate(all_embs) if i != 0]
    if not others:
        return 0.0
    sims = [_cosine_similarity(primary_emb, o) for o in others]
    return 1.0 - float(np.mean(sims))


def _self_report_confidence(response: str) -> float:
    prompt = (
        f"You previously generated this response:\n{response}\n\n"
        "Evaluate the confidence of your own response considering whether it is "
        "factual, logical, and without hallucination. "
        "Rate your confidence from 0.0 to 1.0. "
        "Return ONLY a JSON object with a single key 'confidence' containing the float value."
    )
    res = client.chat.completions.create(
        model=WORKER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    try:
        data = json.loads(res.choices[0].message.content)
        return float(data.get("confidence", 0.5))
    except Exception:
        return 0.5


def _count_concerns(text: str) -> int:
    """Count concern/uncertainty keywords — used to compute Z for C_adj."""
    text_lower = text.lower()
    return sum(1 for kw in CONCERN_KEYWORDS if kw in text_lower)


# ── main evaluator ──────────────────────────────────────────────────────────

def process_node(node: NodeState) -> NodeState:
    prompt = node.task_description
    if node.input_data:
        prompt = (
            f"Context from previous steps:\n"
            f"{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\n"
            f"Task:\n{prompt}"
        )
    else:
        prompt = f"Task:\n{prompt}"

    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
        worker_prompt += (
            f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n"
            f"{node.evaluation.feedback}"
        )

    logger.info(f"[Exp08-ImprovedA] Processing node {node.node_id}")

    # 1. Generate k=3 worker responses
    responses = _generate_k_responses(worker_prompt)
    primary = responses[0]

    # 2. Embed all k responses
    embeddings = _get_embeddings(responses)

    # 3. Kendall's W (concordance proxy)
    W = _kendall_w(embeddings)

    # 4. Discordance D (primary vs. group)
    D = _discordance(embeddings[0], embeddings)

    # 5. Self-report confidence C
    C = _self_report_confidence(primary)

    # 6. Concern count Z → Adjusted confidence C_adj
    Z = _count_concerns(primary)
    C_adj = C * (1.0 / (1.0 + math.log(1.0 + Z)))
    C_adj = max(C_adj, C_ADJ_FLOOR)

    # 7. Urgency U (default 1.0)
    U = U_DEFAULT

    # 8. Improved A-Score:  A = α(1-W) + β * (D/C_adj) * U
    a_score = ALPHA * (1.0 - W) + BETA * (D / C_adj) * U
    a_score = min(a_score, 1.0)  # clamp

    feedback = (
        f"W(Kendall)={W:.3f}  D(discordance)={D:.3f}  "
        f"C={C:.3f}  Z(concerns)={Z}  C_adj={C_adj:.3f}  U={U:.1f}  "
        f"→ A={a_score:.3f}"
    )
    logger.info(f"[Exp08] {node.node_id} | {feedback}")

    node.output_data = primary
    node.evaluation = EvaluationResult(
        similarity_score=W,       # W repurposes the S field
        confidence_score=C_adj,   # C_adj repurposes the C field
        deviation_score=D,
        ambiguity_index=a_score,
        feedback=feedback,
    )

    if a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp08] Node {node.node_id} AMBIGUOUS — A={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"[Exp08] Node {node.node_id} PASS — A={a_score:.3f}")

    return node
