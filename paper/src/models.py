from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NodeStatus(str, Enum):
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'
    PASS = 'PASS'
    FAIL = 'FAIL'
    AMBIGUOUS = 'AMBIGUOUS'

class EvaluationResult(BaseModel):
    similarity_score: float = 0.0     # S
    confidence_score: float = 0.0     # C
    deviation_score: float = 0.0      # D
    ambiguity_index: float = 0.0      # A-Score
    feedback: str = ""

class NodeState(BaseModel):
    node_id: str
    task_description: str
    input_data: Any = None
    output_data: Any = None
    status: NodeStatus = NodeStatus.IDLE
    evaluation: Optional[EvaluationResult] = None
    retry_count: int = 0
    
    # dependencies: -> [{"node_id": "A", "reliance_R": 0.9}]
    depends_on: List[Dict[str, Any]] = Field(default_factory=list)

class GraphState(BaseModel):
    nodes: Dict[str, NodeState]
