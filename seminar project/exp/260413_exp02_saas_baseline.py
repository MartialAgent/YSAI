import logging
from src.models import NodeState, GraphState
from src.orchestrator import DAGOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def define_exp02_graph() -> GraphState:
    """Defines the Complex B2B SaaS Pricing Strategy graph with strict constraints."""
    
    node_a = NodeState(
        node_id="A_Pricing",
        task_description=(
            "Design a B2B SaaS subscription pricing strategy with EXACTLY 3 tiers (Basic, Pro, Enterprise). "
            "STRICT CONSTRAINTS: "
            "1. The price of the Pro tier MUST be exactly 2.5 times the price of the Basic tier. "
            "2. The Enterprise tier MUST include 'Advanced Zero-Trust Security' and explicitly limit data storage to '500GB'. "
            "3. Provide a brief 1-sentence summary for each tier. "
            "If you fail to meet these constraints, the output is invalid."
        )
    )
    
    node_b = NodeState(
        node_id="B_ROI",
        task_description=(
            "Based on the pricing defined in Node A, calculate the 1-year ROI for a company "
            "that purchases 10 Pro tier licenses. Assume the software saves the company $50,000 a year in operational costs. "
            "Show the exact math: (Savings - Cost) / Cost * 100. "
            "Be extremely precise with the numbers from Node A."
        ),
        depends_on=[{"node_id": "A_Pricing", "reliance_R": 0.9}]
    )
    
    node_c = NodeState(
        node_id="C_AdCopy",
        task_description=(
            "Write 3 short LinkedIn ad copies to promote the Pro tier. "
            "You MUST mention the exact 1-year ROI percentage calculated in Node B to attract B2B buyers."
        ),
        depends_on=[{"node_id": "B_ROI", "reliance_R": 0.5}]
    )
    
    return GraphState(nodes={"A_Pricing": node_a, "B_ROI": node_b, "C_AdCopy": node_c})

def run_simulation():
    print("=====================================================")
    print("🚀 Starting AgentDAG Experiment 02: Complex Constraints")
    print("=====================================================\n")
    
    graph = define_exp02_graph()
    # Use a different state file to preserve Exp01
    orchestrator = DAGOrchestrator(graph, store_path="state_exp02.json")
    
    logger.info("Starting Graph Execution...")
    orchestrator.execute_graph()
    
    # Check if graph halted on AMBIGUOUS
    ambiguous_nodes = [nid for nid, node in orchestrator.graph.nodes.items() if node.status == 'AMBIGUOUS']
    
    if ambiguous_nodes:
        print("\n==========================================")
        print("⏸️ GRAPH PAUSED: AMBIGUOUS NODE DETECTED ")
        print("==========================================")
        for nid in ambiguous_nodes:
            logger.warning(f"Node '{nid}' requires Human Intervention.")
            node = orchestrator.graph.nodes[nid]
            if node.evaluation:
                print(f"Current A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"Raw Output:\n{node.output_data}")
            
            # Simulate Human Intervention
            print("\n[Human-In-The-Loop Simulation]")
            user_input = input("Enter corrected output to resolve ambiguity (or type 'skip' to exit simulation): ")
            
            if user_input.lower() != 'skip':
                orchestrator.apply_human_intervension(nid, user_input)
                # Restart execution
                print("\n==========================================")
                print("▶️ RESTARTING GRAPH EXECUTION ")
                print("==========================================\n")
                orchestrator.execute_graph()

if __name__ == "__main__":
    run_simulation()
