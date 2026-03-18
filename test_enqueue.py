import requests
import json
js = {
    "proposal_id": "prop_direct_123",
    "actions": [
        {"type": "create_node", "params": {"node_type": "ColorRect", "node_name": "MagicRect", "parent_path": "."}},
        {"type": "set_property", "params": {"node_path": "MagicRect", "property_name": "color", "value": "ff0000", "value_type": "auto"}},
        {"type": "set_property", "params": {"node_path": "MagicRect", "property_name": "custom_minimum_size", "value": "Vector2(100, 100)", "value_type": "vector2"}}
    ],
    "diff_preview": ["Auto injected rect"]
}
r = requests.post("http://127.0.0.1:8000/plugin/enqueue_proposal", json=js)
print(r.json())
