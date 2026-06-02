"""
Exp04 — QAG D (Question-Answer Generation for Deviation)
=========================================================
Meeting note reference: Section 2 — D (편차) upgrade, QAG
    Current:  Critic LLM assigns a subjective 0-1 deviation score.
    Improved: Generate 3 factual quiz questions from the task input.
              Test whether the worker's output alone can answer them correctly.
              D = 1 - (correct_answers / total_questions)

Why this is better:
  - Objective and verifiable: pass/fail per question, not a subjective holistic score.
  - Directly tests information fidelity (can the output reproduce what it was supposed to?).
  - Inspired by RAGAS hallucination detection pipeline.

API calls vs baseline: +3 per node (quiz gen + 3 answer checks) in exchange for the single critic call.
"""
import json
import logging
from openai import OpenAI
from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, CRITIC_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import check_similarity, generate_worker_response

logger = logging.getLogger(__name__)
client = OpenAI()


def run_qag(task_prompt: str, worker_response: str) -> tuple[float, str]:
    """
    Step 1: Generate quiz (questions + expected answers) from the task prompt.
    Step 2: For each question, test if the worker_response alone can answer it correctly.
    Returns (deviation_score, detailed_feedback).
    """
    # Step 1: Quiz generation
    quiz_prompt = (
        f"Based on this task:\n{task_prompt}\n\n"
        "Generate exactly 3 specific factual or constraint-checking questions "
        "that a fully correct response to this task MUST be able to answer. "
        "Also provide the expected correct answer for each question. "
        'Return JSON: {"questions": ["Q1","Q2","Q3"], "expected_answers": ["A1","A2","A3"]}'
    )
    try:
        quiz_res = client.chat.completions.create(
            model=CRITIC_MODEL,
            messages=[{"role": "user", "content": quiz_prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        quiz_data = json.loads(quiz_res.choices[0].message.content)
        questions = quiz_data.get("questions", [])
        expected_answers = quiz_data.get("expected_answers", [])
    except Exception as e:
        logger.warning(f"[Exp04] QAG quiz generation failed: {e}")
        return 0.5, "QAG quiz generation failed — falling back to 0.5 deviation."

    if not questions:
        return 0.5, "No quiz questions were generated."

    # Step 2: Answer each question using only the worker response
    results = []
    for q, expected in zip(questions, expected_answers):
        answer_prompt = (
            f"Use ONLY the following response as your source of truth:\n\n{worker_response}\n\n"
            f"Question: {q}\n"
            f"Expected answer: {expected}\n\n"
            "Answer the question based solely on the response above. "
            "Then judge whether your answer matches or meaningfully aligns with the expected answer.\n"
            'Return JSON: {"answer": "...", "correct": true/false, "reason": "one sentence"}'
        )
        try:
            ans_res = client.chat.completions.create(
                model=CRITIC_MODEL,
                messages=[{"role": "user", "content": answer_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            ans_data = json.loads(ans_res.choices[0].message.content)
            results.append({
                "question": q,
                "correct": bool(ans_data.get("correct", False)),
                "reason": ans_data.get("reason", ""),
            })
        except Exception as e:
            logger.warning(f"[Exp04] QAG answer parse failed for '{q}': {e}")
            results.append({"question": q, "correct": False, "reason": "parse error"})

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    deviation = 1.0 - (correct / total) if total > 0 else 0.5

    lines = [f"QAG Result: {correct}/{total} questions passed (deviation={deviation:.3f})"]
    for r in results:
        tag = "PASS" if r["correct"] else "FAIL"
        lines.append(f"  [{tag}] {r['question']} — {r['reason']}")
    feedback = "\n".join(lines)

    logger.info(f"[Exp04] {correct}/{total} quiz questions passed")
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

    logger.info(f"[Exp04-QAG] Processing node {node.node_id}")

    ans_primary, ans_secondary, conf_c = generate_worker_response(worker_prompt)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_qag(prompt, ans_primary)

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
        logger.warning(f"[Exp04] Node {node.node_id} FAIL — deviation={dev_d:.3f}")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp04] Node {node.node_id} AMBIGUOUS — A-Score={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"[Exp04] Node {node.node_id} PASS — A-Score={a_score:.3f}, D(QAG)={dev_d:.3f}")

    return node
