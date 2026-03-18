import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\api\server.py'
with open(path, 'r') as f:
    text = f.read()

text = text.replace(
    'app = FastAPI(title="GENESIS ENGINE API", version="0.1.0")',
    'app = FastAPI(title="GENESIS ENGINE API", version="0.1.0")\nfrom api.plugin_bridge import router as plugin_router\napp.include_router(plugin_router)'
)

with open(path, 'w') as f:
    f.write(text)
print('Fixed server.py!')
