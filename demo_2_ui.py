import requests
import json
js = {
    "proposal_id": "prop_demo2_ui",
    "actions": [
        {"type": "create_node", "params": {"node_type": "Label", "node_name": "DemoTitle", "parent_path": "."}},
        {"type": "set_property", "params": {"node_path": "DemoTitle", "property_name": "text", "value": "XClaw Agent Active!", "value_type": "auto"}},
        {"type": "set_property", "params": {"node_path": "DemoTitle", "property_name": "position", "value": "Vector2(120, 120)", "value_type": "vector2"}},
        {"type": "set_property", "params": {"node_path": "DemoTitle", "property_name": "modulate", "value": "88c0d0", "value_type": "auto"}}
    ],
    "diff_preview": ["Auto injected label"]
}
r = requests.post("http://127.0.0.1:8000/plugin/enqueue_proposal", json=js)
print(r.json())
