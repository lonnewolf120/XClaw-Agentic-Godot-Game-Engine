import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/plugin", tags=["Godot Plugin Bridge"])

class NodeContext(BaseModel):
    name: str
    class_name: str = Field(alias="class", default="")
    path: str

class ProposalRequest(BaseModel):
    prompt: str
    selection: List[NodeContext] = []
    current_scene_path: Optional[str] = None
    project_path: Optional[str] = None
    mode: Optional[str] = "scene_mutation"

class ApplyRequest(BaseModel):
    proposal_id: str
    approved_actions: List[Dict[str, Any]] = []

@router.post("/proposal")
async def create_proposal(req: ProposalRequest):
    proposal_id = str(uuid.uuid4())

    # Simulate generating actual Wave 1 action payload
    test_node_name = "AgentGeneratedNode"
    actions = []
    
    if req.selection and len(req.selection) > 0:
        parent_path = req.selection[0].path
        
        # 1. create_node
        actions.append({
            "type": "create_node",
            "params": {
                "parent_path": parent_path,
                "node_type": "Node3D",
                "node_name": test_node_name
            }
        })
        
        # 2. set_property (We'll just set it on the parent for mock safety since new node paths are tricky dynamically)
        actions.append({
            "type": "set_property",
            "params": {
                "node_path": parent_path,
                "property_name": "visible",
                "new_value": True
            }
        })
    else:
        # Default to scene root if no selection
        actions.append({
            "type": "create_node",
            "params": {
                "parent_path": ".",
                "node_type": "Node3D",
                "node_name": "GlobalAgentNode"
            }
        })

    mock_diff = [f"Expected change based on prompt: '{req.prompt}'\nWill generate {len(actions)} node mutations."]

    return {
        "proposal_id": proposal_id,
        "selection": [node.dict() for node in req.selection],
        "intent": req.mode,
        "actions": actions,
        "diff_preview": mock_diff,
        "risk_flags": ["low_risk_semantic"]
@router.post("/apply")
async def apply_proposal(req: ApplyRequest):
    # In reality, this applies the actions to Python's internal representation
    # or just delegates to the local orchestrator to execute the transaction
    run_id = str(uuid.uuid4())
    
    return {
        "run_id": run_id,
        "status": "success",
        "validation_result": "passed",
        "touched_files": [],
        "touched_nodes": []
    }
