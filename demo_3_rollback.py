import requests
import json
js = {
    "proposal_id": "prop_demo3_rollback",
    "actions": [
        {"type": "create_node", "params": {"node_type": "Node2D", "node_name": "TemporaryNode", "parent_path": "."}},
        {"type": "create_node", "params": {"node_type": "Sprite2D", "node_name": "CrashSprite", "parent_path": "./FakePathThatDoesNotExist"}}
    ],
    "diff_preview": ["Attempting auto-rollback demo"]
}
r = requests.post("http://127.0.0.1:8000/plugin/enqueue_proposal", json=js)
print(r.json())
