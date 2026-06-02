import logging
from src.models import NodeState, GraphState
from src.orchestrator import DAGOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def define_test_graph() -> GraphState:
    """Defines the 2026 Autonomous Driving Market Strategy MVP test graph."""
    node_a = NodeState(
        node_id="A_Trend",
        task_description="Analyze the 3 major trends in the global autonomous driving market in 2026. Be specific and give futuristic predictions."
    )
    
    node_b = NodeState(
        node_id="B_Model",
        task_description="Based on the 3 trends provided from Node A, design a subscription-based revenue model for an autonomous driving service.",
        depends_on=[{"node_id": "A_Trend", "reliance_R": 0.9}]
    )
    
    node_c = NodeState(
        node_id="C_PricingFormula",
        task_description="Based on Node B, create a specific pricing formula. The required conditions are: 1) Base tier ($50), 2) Premium tier ($100), 3) Enterprise tier ($200). Intentionally omit the 'Premium tier' in your output to test if the evaluation system recognizes the missing condition.",
        depends_on=[{"node_id": "B_Model", "reliance_R": 0.8}]
    )

    node_d = NodeState(
        node_id="D_ConditionCheck",
        task_description="Review the pricing formula from Node C. The original requirement was to include 3 tiers (Base, Premium, Enterprise). Identify exactly which condition or tier was omitted and explain the commercial impact of this missing condition.",
        depends_on=[{"node_id": "C_PricingFormula", "reliance_R": 0.9}]
    )
    
    node_e = NodeState(
        node_id="E_Copy",
        task_description="Write 5 marketing email subject lines to promote the finalized business model and pricing structure.",
        depends_on=[{"node_id": "D_ConditionCheck", "reliance_R": 0.5}]
    )
    
    return GraphState(nodes={"A_Trend": node_a, "B_Model": node_b, "C_PricingFormula": node_c, "D_ConditionCheck": node_d, "E_Copy": node_e})

def run_simulation():
    print("==========================================")
    print("🚀 Starting AgentDAG Execution Simulation ")
    print("==========================================\n")
    
    graph = define_test_graph()
    orchestrator = DAGOrchestrator(graph, store_path="state.json")
    
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
            print(f"Current A-Score: {node.evaluation.ambiguity_index:.3f}")
            print(f"Raw Output:\n{node.output_data}")
            
            # Simulate Human Intervention
            print("\n[Human-In-The-Loop Simulation]")
            user_input = input("Enter corrected output to resolve ambiguity (or 'skip' to exit simulation): ")
            
            if user_input.lower() != 'skip':
                orchestrator.apply_human_intervension(nid, user_input)
                # Restart execution
                print("\n==========================================")
                print("▶️ RESTARTING GRAPH EXECUTION ")
                print("==========================================\n")
                orchestrator.execute_graph()

if __name__ == "__main__":
    run_simulation()
