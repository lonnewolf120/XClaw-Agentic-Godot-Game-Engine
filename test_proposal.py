import sys
sys.path.insert(0, 'E:/Projects/GAMEDEV/XClaw Agentic Godot Game Engine/vibe-game-engine')
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app, raise_server_exceptions=False)

response = client.post("/plugin/proposal", json={
    "prompt": "hello",
    "selection": [],
    "mode": "scene_mutation",
    "options": {}
})

import traceback
if response.status_code == 500:
    print('Failed:', response.text)
else:
    print('Success:', response.json())
