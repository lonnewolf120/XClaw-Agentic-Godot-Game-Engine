import os, re
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\planner.py'
with open(path, 'r') as f:
    text = f.read()

replacement = '''class PlannerAgent:
    def __init__(self, model_name: str = "gemini-3.1-pro-preview"):
        self.use_mock = os.environ.get("USE_MOCK_PLANNER", "false").lower() == "true"\n
    def plan(self, initial_prompt: str):
        if self.use_mock:
            return "Mock plan"
            
        import os
        from google import genai
        from google.genai import types
        
        api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyATsGuoPOPqIekC-7N2lwK2VwP52qWjLjg")
        client = genai.Client(api_key=api_key)
        
        system = "You are the Planner. Break the user prompt into logical Godot steps."
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=system + "\\n\\n" + initial_prompt)])]
        
        res = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=contents
        )
        # Using string for now, but signature may require PlanMessage
        from contracts.messages import PlanMessage
        return PlanMessage(overall_strategy=res.text)
'''

text = re.sub(r'class PlannerAgent:.*', replacement, text, flags=re.DOTALL)
with open(path, 'w') as f:
    f.write(text)
print('Patched planner')
