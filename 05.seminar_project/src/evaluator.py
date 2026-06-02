import json
import logging
import numpy as np
from openai import OpenAI
from src.config import ALPHA, BETA, A_SCORE_THRESHOLD, WORKER_MODEL, CRITIC_MODEL, EMBEDDING_MODEL
from src.models import NodeState, EvaluationResult, NodeStatus

logger = logging.getLogger(__name__)

client = OpenAI()

def _cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def check_similarity(text1: str, text2: str) -> float:
    try:
        res = client.embeddings.create(input=[text1[:8000], text2[:8000]], model=EMBEDDING_MODEL)
        v1 = res.data[0].embedding
        v2 = res.data[1].embedding
        return _cosine_similarity(v1, v2)
    except Exception as e:
        logger.error(f"Error checking similarity: {e}")
        return 0.0

def generate_worker_response(prompt: str) -> tuple[str, str, float]:
    """Generates two responses to measure S, and asks for confidence C for the first one."""
    responses = []
    # Generation step
    for _ in range(2):
        res = client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[{"role": "system", "content": "You are a professional strategic analyzer."},
                      {"role": "user", "content": prompt}],
            temperature=0.7 # Entropy
        )
        responses.append(res.choices[0].message.content)
    
    # Self-reflection for Confidence C
    confidence_prompt = (
        f"You previously generated this response:\n{responses[0]}\n\n"
        "Evaluate the confidence of your own response considering whether it is factual, logical, and without hallucination. "
        "Rate your confidence from 0.0 to 1.0. "
        "Return ONLY a JSON object with a single key 'confidence' containing the float value."
    )
    conf_res = client.chat.completions.create(
        model=WORKER_MODEL,
        messages=[{"role": "user", "content": confidence_prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    confidence = 0.5
    try:
        conf_data = json.loads(conf_res.choices[0].message.content)
        confidence = float(conf_data.get("confidence", 0.5))
    except Exception as e:
        logger.warning(f"Failed to parse confidence score: {e}")

    return responses[0], responses[1], confidence

def run_critic(prompt: str, worker_response: str) -> tuple[float, str]:
    """Runs the critic to analyze logical flaws and deviation D."""
    critic_prompt = (
        f"Task Prompt:\n{prompt}\n\n"
        f"Worker Response:\n{worker_response}\n\n"
        "As a stringent critic, evaluate the response for logical flaws, hallucinations, and factual errors. "
        "Calculate a deviation/error score from 0.0 to 1.0 (where 0.0 is perfect with no flaws, and 1.0 is completely flawed or completely hallucinated). "
        "Return your evaluation as a JSON object with keys 'deviation_score' (float) and 'feedback' (string)."
    )
    crit_res = client.chat.completions.create(
        model=CRITIC_MODEL,
        messages=[{"role": "system", "content": "You are a ruthless factual critic."},
                  {"role": "user", "content": critic_prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    deviation = 0.0
    feedback = ""
    try:
        crit_data = json.loads(crit_res.choices[0].message.content)
        deviation = float(crit_data.get("deviation_score", 0.0))
        feedback = crit_data.get("feedback", "")
    except Exception as e:
        logger.warning(f"Failed to parse critic score: {e}")

    return deviation, feedback

def process_node(node: NodeState) -> NodeState:
    """Executes a single node, running worker, critic, and calculating A-Score."""
    prompt = node.task_description
    if node.input_data:
        prompt = f"Context from previous steps:\n{json.dumps(node.input_data, ensure_ascii=False, indent=2)}\n\nTask:\n{prompt}"
    else:
        prompt = f"Task:\n{prompt}"
    
    logger.info(f"Processing node {node.node_id} (Retry: {node.retry_count})")
    
    worker_prompt = prompt
    if node.status == NodeStatus.FAIL and node.evaluation:
         worker_prompt += f"\n\nCRITIC FEEDBACK FROM PREVIOUS RUN (Fix these issues):\n{node.evaluation.feedback}"
         
    ans_primary, ans_secondary, conf_c = generate_worker_response(worker_prompt)
    sim_s = check_similarity(ans_primary, ans_secondary)
    dev_d, feedback = run_critic(prompt, ans_primary)

    # A = alpha * (1 - S) + beta * D * (1 - C)
    a_score = ALPHA * (1.0 - sim_s) + BETA * dev_d * (1.0 - conf_c)
    
    node.output_data = ans_primary
    node.evaluation = EvaluationResult(
        similarity_score=sim_s,
        confidence_score=conf_c,
        deviation_score=dev_d,
        ambiguity_index=a_score,
        feedback=feedback
    )
    
    # State routing
    if dev_d >= 0.7: 
        node.status = NodeStatus.FAIL
        logger.warning(f"Node {node.node_id} failed. Deviation matches error threshold ({dev_d}).")
    elif a_score > A_SCORE_THRESHOLD:
        node.status = NodeStatus.AMBIGUOUS
        logger.warning(f"Node {node.node_id} is ambiguous. A-Score {a_score:.3f} > {A_SCORE_THRESHOLD}")
    else:
        node.status = NodeStatus.PASS
        logger.info(f"Node {node.node_id} passed. A-Score {a_score:.3f}")

    return node
