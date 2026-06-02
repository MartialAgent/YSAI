"""
Exp06 — Multi-LLM Judge (Cross-Model Deviation Averaging)
==========================================================
Meeting note reference: Section 3 & Section 5 — same-model bias (동일 모델 편향)
    Problem:  GPT tends to score GPT-generated answers more favorably (same-model bias).
    Solution: Run the critic role across 3 different LLM families independently:
              - OpenAI GPT-4o
              - Anthropic Claude Sonnet
              - Google Gemini Pro
              Average their deviation scores → less biased D.
    Relation: Practical implementation of SAC³-M (model-level cross-check consistency).

API calls vs baseline: 3× (one per judge family).
"""
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

import anthropic
from google import genai
from openai import OpenAI

from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, WORKER_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus
from src.evaluator import check_similarity, generate_worker_response

logger = logging.getLogger(__name__)

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

JUDGE_CONFIGS = [
    {"provider": "openai",    "model": "gpt-4o"},
    {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    {"provider": "gemini",    "model": "gemini-2.5-flash"},
]

CRITIC_SYSTEM = "You are a ruthless factual critic. Evaluate objectively regardless of which AI generated the response."

def _critic_prompt(task_prompt: str, worker_response: str) -> str:
    return (
        f"Task Prompt:\n{task_prompt}\n\n"
        f"Worker Response:\n{worker_response}\n\n"
        "Evaluate the response for logical flaws, hallucinations, and factual errors. "
        "Assign a deviation/error score from 0.0 to 1.0:\n"
        "  0.0 = perfect, no flaws\n"
        "  0.5 = significant issues\n"
        "  1.0 = completely wrong or hallucinated\n"
        "Return ONLY valid JSON: {\"deviation_score\": <float>, \"feedback\": \"<one paragraph>\"}"
    )


def _judge_openai(task_prompt: str, worker_response: str) -> tuple[float, str]:
    res = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM},
            {"role": "user", "content": _critic_prompt(task_prompt, worker_response)},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    data = json.loads(res.choices[0].message.content)
    return float(data.get("deviation_score", 0.5)), data.get("feedback", "")


def _judge_anthropic(task_prompt: str, worker_response: str) -> tuple[float, str]:
    res = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system=CRITIC_SYSTEM,
        messages=[{"role": "user", "content": _critic_prompt(task_prompt, worker_response)}],
        temperature=0.0,
    )
    raw = res.content[0].text.strip()
    # Extract JSON from response (Claude may add surrounding text)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    data = json.loads(raw[start:end]) if start != -1 else {}
    return float(data.get("deviation_score", 0.5)), data.get("feedback", "")


def _judge_gemini(task_prompt: str, worker_response: str) -> tuple[float, str]:
    from google.genai import types
    prompt = CRITIC_SYSTEM + "\n\n" + _critic_prompt(task_prompt, worker_response)
    res = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0),
    )
    raw = res.text.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    data = json.loads(raw[start:end]) if start != -1 else {}
    return float(data.get("deviation_score", 0.5)), data.get("feedback", "")


_JUDGES = {
    "openai":    _judge_openai,
    "anthropic": _judge_anthropic,
    "gemini":    _judge_gemini,
}


def run_multi_llm_critic(task_prompt: str, worker_response: str) -> tuple[float, str]:
    """
    Runs the critic prompt against GPT-4o, Claude Sonnet, and Gemini Pro.
    Returns (average_deviation, per-judge breakdown).
    """
    scores = []
    feedback_lines = []

    for cfg in JUDGE_CONFIGS:
        provider = cfg["provider"]
        model    = cfg["model"]
        try:
            score, fb = _JUDGES[provider](task_prompt, worker_response)
            scores.append(score)
            feedback_lines.append(f"[{provider} / {model}] score={score:.3f}\n  {fb}")
            logger.info(f"[Exp06] Judge {provider}/{model}: deviation={score:.3f}")
        except Exception as e:
            logger.warning(f"[Exp06] Judge {provider}/{model} failed: {e}")

    avg = sum(scores) / len(scores) if scores else 0.5
    providers = [c["provider"] for c in JUDGE_CONFIGS]
    header = (
        f"Multi-LLM Average Deviation: {avg:.3f}\n"
        f"Judges: {providers}\n"
        f"Individual scores: {[f'{s:.3f}' for s in scores]}\n"
    )
    return avg, header + "\n".join(feedback_lines)


def process_node(node: NodeState) -> NodeState:
    prompt = node.task_description
    if node.input_data:
        prompt = f"Context from previous steps:\n{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\nTask:\n{prompt}"
    else:
        prompt = f"Task:\n{prompt}"

    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
        worker_prompt += f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n{node.evaluation.feedback}"

    logger.info(f"[Exp06-MultiLLM] Processing node {node.node_id} with {len(JUDGE_CONFIGS)} judges")

    ans_primary, ans_secondary, conf_c = generate_worker_response(worker_prompt)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_multi_llm_critic(prompt, ans_primary)

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
        logger.warning(f"[Exp06] Node {node.node_id} FAIL — avg_deviation={dev_d:.3f}")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"[Exp06] Node {node.node_id} AMBIGUOUS — A-Score={a_score:.3f}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"[Exp06] Node {node.node_id} PASS — A-Score={a_score:.3f}, D(avg)={dev_d:.3f}")

    return node
