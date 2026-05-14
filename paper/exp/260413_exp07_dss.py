"""
Experiment 07 — DSS (Dependency Sensitivity Score)
Baseline evaluator + additional DSS diagnostic per node.
High DSS nodes are flagged as high-risk upstream dependencies.
Graph: SaaS Pricing (same as Exp02 for fair comparison)
State: state_exp07.json
"""
import logging
from src.graphs import saas_pricing_graph
from src.orchestrator import DAGOrchestrator
from src.evaluators.exp_dss import process_node, DSS_HIGH_RISK_THRESHOLD

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run():
    print("=" * 60)
    print(f"  Exp07: DSS — Dependency Sensitivity Score")
    print(f"  High-risk threshold: DSS > {DSS_HIGH_RISK_THRESHOLD}")
    print("=" * 60)

    graph = saas_pricing_graph()
    orchestrator = DAGOrchestrator(graph, store_path="state_exp07.json", process_fn=process_node)

    logger.info("Starting Exp07 graph execution...")
    orchestrator.execute_graph()

    ambiguous = [nid for nid, n in orchestrator.graph.nodes.items() if n.status == "AMBIGUOUS"]
    if ambiguous:
        print("\n[PAUSED] AMBIGUOUS node(s) detected:", ambiguous)
        for nid in ambiguous:
            node = orchestrator.graph.nodes[nid]
            print(f"\nNode: {nid}")
            print(f"A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"DSS Feedback:\n{node.evaluation.feedback}")
            print(f"Output:\n{node.output_data}")
            user_input = input("\nEnter corrected output (or 'skip'): ")
            if user_input.lower() != "skip":
                orchestrator.apply_human_intervension(nid, user_input)
                orchestrator.execute_graph()

    print("\n=== Exp07 Final Node Summary (with DSS) ===")
    for nid, node in orchestrator.graph.nodes.items():
        ev = node.evaluation
        if ev:
            # Extract DSS value from feedback string
            dss_str = ""
            for line in ev.feedback.split("\n"):
                if "DSS" in line:
                    dss_str = f"  [{line.strip()}]"
                    break
            print(
                f"  {nid}: status={node.status}  A={ev.ambiguity_index:.3f}  "
                f"S={ev.similarity_score:.3f}  C={ev.confidence_score:.3f}  "
                f"D={ev.deviation_score:.3f}{dss_str}"
            )


if __name__ == "__main__":
    run()
