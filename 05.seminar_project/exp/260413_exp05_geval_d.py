"""
Experiment 05 — G-Eval D
Deviation (D) measured via G-Eval: task-specific CoT rubric + probabilistic logprobs scoring.
Graph: SaaS Pricing (same as Exp02 for fair comparison)
State: state_exp05.json
"""
import logging
from src.graphs import saas_pricing_graph
from src.orchestrator import DAGOrchestrator
from src.evaluators.exp_geval_d import process_node

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run():
    print("=" * 60)
    print("  Exp05: G-Eval D — CoT Rubric + Probabilistic Scoring")
    print("=" * 60)

    graph = saas_pricing_graph()
    orchestrator = DAGOrchestrator(graph, store_path="state_exp05.json", process_fn=process_node)

    logger.info("Starting Exp05 graph execution...")
    orchestrator.execute_graph()

    ambiguous = [nid for nid, n in orchestrator.graph.nodes.items() if n.status == "AMBIGUOUS"]
    if ambiguous:
        print("\n[PAUSED] AMBIGUOUS node(s) detected:", ambiguous)
        for nid in ambiguous:
            node = orchestrator.graph.nodes[nid]
            print(f"\nNode: {nid}")
            print(f"A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"G-Eval Feedback:\n{node.evaluation.feedback}")
            print(f"Output:\n{node.output_data}")
            user_input = input("\nEnter corrected output (or 'skip'): ")
            if user_input.lower() != "skip":
                orchestrator.apply_human_intervension(nid, user_input)
                orchestrator.execute_graph()

    print("\n=== Exp05 Final Node Summary ===")
    for nid, node in orchestrator.graph.nodes.items():
        ev = node.evaluation
        if ev:
            print(
                f"  {nid}: status={node.status}  A={ev.ambiguity_index:.3f}  "
                f"S={ev.similarity_score:.3f}  C={ev.confidence_score:.3f}  D(G-Eval)={ev.deviation_score:.3f}"
            )


if __name__ == "__main__":
    run()
