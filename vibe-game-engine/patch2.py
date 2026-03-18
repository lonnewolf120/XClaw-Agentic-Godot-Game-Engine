import os
import re

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\api\plugin_bridge.py'
with open(path, 'r') as f:
    text = f.read()

# Add to ProposalRequest options
if 'options: dict = None' not in text:
    text = text.replace('prompt: str\n', 'prompt: str\n    options: dict = None\n')

# Add API Key env var setup inside create_proposal
pattern = r'(async def create_proposal.*?):\n'
replacement = r'\1:\n    if req.options and req.options.get("api_key"):\n        os.environ["GEMINI_API_KEY"] = req.options["api_key"]\n'
text = re.sub(pattern, replacement, text, count=1)

with open(path, 'w') as f:
    f.write(text)
print("Patched plugin_bridge 2")
