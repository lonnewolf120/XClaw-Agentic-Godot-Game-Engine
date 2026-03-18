import requests
import json
js = {
    "proposal_id": "prop_demo1_visual",
    "actions": [
        {"type": "create_node", "params": {"node_type": "ColorRect", "node_name": "DemoBackground", "parent_path": "."}},
        {"type": "set_property", "params": {"node_path": "DemoBackground", "property_name": "color", "value": "2e3440", "value_type": "auto"}},
        {"type": "set_property", "params": {"node_path": "DemoBackground", "property_name": "custom_minimum_size", "value": "Vector2(400, 300)", "value_type": "vector2"}},
        {"type": "set_property", "params": {"node_path": "DemoBackground", "property_name": "position", "value": "Vector2(100, 100)", "value_type": "vector2"}}
    ],
    "diff_preview": ["Auto injected background"]
}
r = requests.post("http://127.0.0.1:8000/plugin/enqueue_proposal", json=js)
print(r.json())
