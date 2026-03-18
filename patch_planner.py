import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\planner.py'
with open(path, 'r') as f:
    text = f.read()
text = text.replace('return self.plan(initial_prompt) if not self.use_mock else PlanMessage() # Basic fallback or retry could go here, for now it will just fail. Actually just fallback to mock', 'return PlanMessage(archetype="platformer", goals=["Fail Build"], mechanics=[], constraints=[], asset_requirements=[], risk_flags=[], tasks=[PlanTask(id="1", role="builder", goal="Fallback")])')
with open(path, 'w') as f:
    f.write(text)
