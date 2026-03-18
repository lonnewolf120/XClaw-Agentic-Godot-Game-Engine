import os
import re

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\api\server.py'
with open(path, 'r') as f:
    text = f.read()

if 'logging.basicConfig' not in text:
    text = text.replace('import logging\n', 'import logging\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")\n')

# Deduplicate includes just in case:
text = text.replace('from api.plugin_bridge import router as plugin_router\napp.include_router(plugin_router)\nfrom api.plugin_bridge import router as plugin_router\napp.include_router(plugin_router)', 'from api.plugin_bridge import router as plugin_router\napp.include_router(plugin_router)')

with open(path, 'w') as f:
    f.write(text)
print("Updated server logging")
