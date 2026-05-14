from src.models import NodeState, GraphState


def saas_pricing_graph() -> GraphState:
    """
    Shared test graph: B2B SaaS Pricing Strategy with strict numerical constraints.
    Used across all experiments so evaluation differences are directly comparable.
    Node A -> Node B -> Node C (sequential, strict numerical dependency).
    """
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
    node_d = NodeState(
        node_id="D_ConditionAudit",
        task_description=(
            "Audit the pricing output from Node A against the ORIGINAL requirements. "
            "The original spec had EXACTLY 5 mandatory conditions: "
            "1) Exactly 3 tiers defined, "
            "2) Pro tier price = 2.5x Basic tier price, "
            "3) Enterprise tier includes 'Advanced Zero-Trust Security', "
            "4) Enterprise tier storage explicitly capped at '500GB', "
            "5) Each tier accompanied by a 1-sentence summary. "
            "INSTRUCTION: In your audit report, verify conditions 1 through 4 only — "
            "intentionally omit any mention of condition 5 to test whether the evaluation "
            "system detects the missing check."
        ),
        depends_on=[{"node_id": "A_Pricing", "reliance_R": 0.95}]
    )
    node_e = NodeState(
        node_id="E_ChurnFormula",
        task_description=(
            "Using the pricing from Node A and ROI from Node B, define a customer churn risk formula. "
            "The formula MUST include ALL 4 of the following variables: "
            "1) monthly_price (from Node A Pro tier / 12), "
            "2) roi_percentage (exact value from Node B), "
            "3) competitor_price_delta (assume competitor charges 20% less than Pro tier), "
            "4) support_tier_weight (Basic=0.5, Pro=1.0, Enterprise=1.5). "
            "INSTRUCTION: Define the formula using only variables 1, 2, and 3 — "
            "intentionally exclude support_tier_weight to test if downstream nodes or the "
            "evaluator flag the incomplete formula."
        ),
        depends_on=[
            {"node_id": "A_Pricing", "reliance_R": 0.7},
            {"node_id": "B_ROI", "reliance_R": 0.8}
        ]
    )
    node_f = NodeState(
        node_id="F_BoardReport",
        task_description=(
            "Write a concise board-level executive summary (max 200 words). "
            "You MUST explicitly cite ALL of the following: "
            "a) The exact price of each tier from Node A, "
            "b) The exact 1-year ROI percentage from Node B, "
            "c) All 4 variables used in the churn formula from Node E (monthly_price, "
            "roi_percentage, competitor_price_delta, support_tier_weight). "
            "If any upstream data appears incomplete or missing, call it out explicitly."
        ),
        depends_on=[
            {"node_id": "C_AdCopy", "reliance_R": 0.3},
            {"node_id": "D_ConditionAudit", "reliance_R": 0.6},
            {"node_id": "E_ChurnFormula", "reliance_R": 0.7}
        ]
    )
    node_g = NodeState(
        node_id="G_RiskAudit",
        task_description=(
            "Perform a full pipeline risk audit across all upstream nodes (A through F). "
            "For each node, answer: (1) Were all required conditions or variables present? "
            "(2) Were any constraints violated or omitted? "
            "(3) Did any downstream node propagate an error from an incomplete upstream output? "
            "Specifically check: Did D_ConditionAudit verify all 5 original conditions? "
            "Did E_ChurnFormula include all 4 required variables? "
            "Assign each node a risk level: LOW / MEDIUM / HIGH."
        ),
        depends_on=[
            {"node_id": "D_ConditionAudit", "reliance_R": 0.9},
            {"node_id": "E_ChurnFormula", "reliance_R": 0.9},
            {"node_id": "F_BoardReport", "reliance_R": 0.8}
        ]
    )
    return GraphState(nodes={
        "A_Pricing": node_a,
        "B_ROI": node_b,
        "C_AdCopy": node_c,
        "D_ConditionAudit": node_d,
        "E_ChurnFormula": node_e,
        "F_BoardReport": node_f,
        "G_RiskAudit": node_g,
    })
