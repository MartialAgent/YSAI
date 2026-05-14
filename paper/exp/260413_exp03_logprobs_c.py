"""
Experiment 03 — Logprobs C
Confidence (C) measured via token log-probabilities instead of self-report.
Graph: SaaS Pricing (same as Exp02 for fair comparison)
State: state_exp03.json
"""
import logging
from src.graphs import saas_pricing_graph
from src.orchestrator import DAGOrchestrator
from src.evaluators.exp_logprobs_c import process_node

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run():
    print("=" * 60)
    print("  Exp03: Logprobs C — Token Probability Confidence")
    print("=" * 60)

    graph = saas_pricing_graph()
    orchestrator = DAGOrchestrator(graph, store_path="state_exp03.json", process_fn=process_node)

    logger.info("Starting Exp03 graph execution...")
    orchestrator.execute_graph()

    ambiguous = [nid for nid, n in orchestrator.graph.nodes.items() if n.status == "AMBIGUOUS"]
    if ambiguous:
        print("\n[PAUSED] AMBIGUOUS node(s) detected:", ambiguous)
        for nid in ambiguous:
            node = orchestrator.graph.nodes[nid]
            print(f"\nNode: {nid}")
            print(f"A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"C (logprobs): {node.evaluation.confidence_score:.3f}")
            print(f"Output:\n{node.output_data}")
            user_input = input("\nEnter corrected output (or 'skip'): ")
            if user_input.lower() != "skip":
                orchestrator.apply_human_intervension(nid, user_input)
                orchestrator.execute_graph()

    print("\n=== Exp03 Final Node Summary ===")
    for nid, node in orchestrator.graph.nodes.items():
        ev = node.evaluation
        if ev:
            print(
                f"  {nid}: status={node.status}  A={ev.ambiguity_index:.3f}  "
                f"S={ev.similarity_score:.3f}  C={ev.confidence_score:.3f}  D={ev.deviation_score:.3f}"
            )


if __name__ == "__main__":
    run()
