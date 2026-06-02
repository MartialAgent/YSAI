import json
import logging
import os
from collections import deque
from src.config import I_FACTOR_THRESHOLD, MAX_FAIL_RETRIES
from src.models import NodeState, NodeStatus, GraphState
from src.evaluator import process_node as _default_process_node

logger = logging.getLogger(__name__)

class DAGOrchestrator:
    def __init__(self, graph_state: GraphState, store_path="graph_state.json", process_fn=None):
        self.graph = graph_state
        self.store_path = store_path
        self.process_fn = process_fn or _default_process_node

    def save_state(self):
        with open(self.store_path, "w", encoding="utf-8") as f:
            f.write(self.graph.model_dump_json(indent=2))
        logger.info(f"💾 State saved to {self.store_path}")

    @classmethod
    def load_state(cls, store_path="graph_state.json"):
        if os.path.exists(store_path):
            with open(store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(GraphState(**data), store_path)
        return None

    def _get_topological_order(self) -> list[str]:
        in_degree = {nid: 0 for nid in self.graph.nodes}
        for node in self.graph.nodes.values():
            for dep in node.depends_on:
                in_degree[node.node_id] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        order = []
        while queue:
            curr = queue.popleft()
            order.append(curr)
            for node in self.graph.nodes.values():
                for dep in node.depends_on:
                    if dep["node_id"] == curr:
                        in_degree[node.node_id] -= 1
                        if in_degree[node.node_id] == 0:
                            queue.append(node.node_id)
        return order
        
    def resolve_inputs(self, node_id: str) -> dict:
        """Fetch outputs from dependent parent nodes as input to this node."""
        inputs = {}
        node = self.graph.nodes[node_id]
        for dep in node.depends_on:
            parent_id = dep["node_id"]
            if self.graph.nodes[parent_id].status == NodeStatus.PASS:
               inputs[parent_id] = self.graph.nodes[parent_id].output_data
        return inputs

    def execute_graph(self):
        order = self._get_topological_order()
        logger.info(f"Execution Order: {order}")

        for node_id in order:
            node = self.graph.nodes[node_id]
            
            if node.status == NodeStatus.PASS:
                logger.info(f"⏩ Skipping {node_id} (Already PASS)")
                continue
                
            if node.status == NodeStatus.AMBIGUOUS:
                logger.warning(f"🛑 Node {node_id} is AMBIGUOUS. Waiting for human intervention.")
                break # Pause execution

            while True:
                # Prepare inputs
                node.input_data = self.resolve_inputs(node_id)
                
                # Execute node logic
                node = self.process_fn(node)
                self.graph.nodes[node_id] = node
                self.save_state()

                if node.status == NodeStatus.PASS:
                    break
                elif node.status == NodeStatus.FAIL:
                    node.retry_count += 1
                    if node.retry_count > MAX_FAIL_RETRIES:
                        logger.error(f"❌ Max retries reached for {node_id}. Escalating to AMBIGUOUS.")
                        node.status = NodeStatus.AMBIGUOUS
                        self.save_state()
                        break
                    logger.info(f"♻️ Retrying {node_id} (Attempt {node.retry_count}/{MAX_FAIL_RETRIES})")
                elif node.status == NodeStatus.AMBIGUOUS:
                    break

            if node.status == NodeStatus.AMBIGUOUS:
                break # Pause overall graph execution

    def calculate_impact_factor(self, modified_node_id: str) -> list[str]:
        """Calculates cumulative partial back-prop effect (I-Factor) down the graph"""
        logger.info(f"🔍 Calculating Impact Factor from {modified_node_id}")
        impact_scores = {nid: 0.0 for nid in self.graph.nodes}
        # Start distance propagation
        
        # A simple BFS or topological propagation of I-Factor
        order = self._get_topological_order()
        
        # We prime the modified node explicitly as having an impact of 1.0 at distance 0
        nodes_to_traverse = {modified_node_id: {"impact_sent": 1.0, "distance": 0}}
        
        for curr_id in order:
            if curr_id not in nodes_to_traverse:
                continue
            
            current_dist = nodes_to_traverse[curr_id]["distance"]
            current_impact = nodes_to_traverse[curr_id]["impact_sent"]
            
            # Find children
            for child_id, child_node in self.graph.nodes.items():
                for dep in child_node.depends_on:
                    if dep["node_id"] == curr_id:
                        reliance = dep["reliance_R"]
                        path_impact = reliance / ((current_dist + 1) + 1) # Eq: R / (dist + 1) 
                        
                        impact_scores[child_id] += path_impact
                        
                        if child_id not in nodes_to_traverse:
                           nodes_to_traverse[child_id] = {"impact_sent": path_impact, "distance": current_dist + 1}
                        else:
                           nodes_to_traverse[child_id]["impact_sent"] += path_impact

        # Filter nodes to rerun
        rerun_queue = []
        for nid, i_score in impact_scores.items():
            if nid == modified_node_id:
                continue
            logger.info(f"Node {nid} Cumulative I-Factor: {i_score:.3f}")
            if i_score > I_FACTOR_THRESHOLD:
                rerun_queue.append(nid)
                
        return rerun_queue

    def apply_human_intervension(self, node_id: str, new_output: str):
         logger.info(f"👤 Human modified data for {node_id}")
         node = self.graph.nodes[node_id]
         node.output_data = new_output
         node.status = NodeStatus.PASS
         node.retry_count = 0
         self.graph.nodes[node_id] = node
         
         rerun_list = self.calculate_impact_factor(node_id)
         logger.info(f"🔄 Nodes scheduled for Rerun due to Impact: {rerun_list}")
         
         for r_id in rerun_list:
             self.graph.nodes[r_id].status = NodeStatus.IDLE
             self.graph.nodes[r_id].output_data = None
             self.graph.nodes[r_id].retry_count = 0
             logger.info(f"  - Resetting {r_id} to IDLE")
             
         self.save_state()
