"""
Experiment 06 — Multi-LLM Judge (GPT-4o + Claude Sonnet + Gemini Pro)
Deviation (D) averaged across 3 LLM families to remove same-model bias.
Graph: SaaS Pricing (same as Exp02 for fair comparison)
State: state_exp06.json
"""
import logging
from src.graphs import saas_pricing_graph
from src.orchestrator import DAGOrchestrator
from src.evaluators.exp_multi_llm import process_node, JUDGE_CONFIGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run():
    judges = [f"{c['provider']}/{c['model']}" for c in JUDGE_CONFIGS]
    print("=" * 60)
    print("  Exp06: Multi-LLM Judge (3-family cross-model evaluation)")
    print(f"  Judges: {judges}")
    print("=" * 60)

    graph = saas_pricing_graph()
    orchestrator = DAGOrchestrator(graph, store_path="state_exp06.json", process_fn=process_node)

    logger.info("Starting Exp06 graph execution...")
    orchestrator.execute_graph()

    ambiguous = [nid for nid, n in orchestrator.graph.nodes.items() if n.status == "AMBIGUOUS"]
    if ambiguous:
        print("\n[PAUSED] AMBIGUOUS node(s) detected:", ambiguous)
        for nid in ambiguous:
            node = orchestrator.graph.nodes[nid]
            print(f"\nNode: {nid}")
            print(f"A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"Multi-LLM Feedback:\n{node.evaluation.feedback}")
            print(f"Output:\n{node.output_data}")
            user_input = input("\nEnter corrected output (or 'skip'): ")
            if user_input.lower() != "skip":
                orchestrator.apply_human_intervension(nid, user_input)
                orchestrator.execute_graph()

    print("\n=== Exp06 Final Node Summary ===")
    for nid, node in orchestrator.graph.nodes.items():
        ev = node.evaluation
        if ev:
            print(
                f"  {nid}: status={node.status}  A={ev.ambiguity_index:.3f}  "
                f"S={ev.similarity_score:.3f}  C={ev.confidence_score:.3f}  D(avg3)={ev.deviation_score:.3f}"
            )
            # Print per-judge breakdown from feedback header
            for line in ev.feedback.split("\n")[:4]:
                print(f"    {line}")


if __name__ == "__main__":
    run()
