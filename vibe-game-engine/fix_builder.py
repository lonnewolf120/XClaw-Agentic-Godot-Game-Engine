import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\builder.py'
with open(path, 'r') as f:
    text = f.read()

import re

# Swap the instructor patching if needed or just use raw genai client
replacement = '''class ActionBuilderAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyATsGuoPOPqIekC-7N2lwK2VwP52qWjLjg")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3.1-pro-preview"

    def generate_action_batch(self, prompt: str, plan_summary: str, retrieved_context: str) -> ActionBatch:
        system_prompt = \"\"\"You are Godot Builder AI. You mutate the Godot editor state...\"\"\"
        user_prompt = f"Plan: {plan_summary}\\nContext: {retrieved_context}\\nUser: {prompt}\\nBuild the JSON ActionBatch."
        
        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=system_prompt + "\\n\\n" + user_prompt)])
        ]
        
        # Pydantic schemas via GenerateContentConfig
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActionBatch
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        
        try:
            import json
            data = json.loads(response.text)
            return ActionBatch(**data)
        except Exception as e:
            print("Fallback or error parsing json:", e)
            return ActionBatch(actions=[], description="Error parsing Gemini output")
'''

# Use regex to completely rewrite ActionBuilderAgent class
text = re.sub(r'class ActionBuilderAgent:.*', replacement, text, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(text)

print('Rewrote ActionBuilderAgent for raw Gemini GenAI SDK')
