import requests

res = requests.post("http://127.0.0.1:8000/plugin/proposal", json={
    "prompt": "Create a Label under selected node and set text/visibility",
    "selection": [{"name": "Root", "class": "Node3D", "path": "."}],
    "current_scene_path": "res://main.tscn"
})
print("STATUS:", res.status_code)
print(res.json())