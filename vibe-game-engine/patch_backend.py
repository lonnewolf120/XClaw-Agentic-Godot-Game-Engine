import os

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\api\plugin_bridge.py'
with open(path, 'r') as f:
    text = f.read()

# Add to ProposalRequest
if 'options: dict = None' not in text and 'options: Optional[dict]' not in text:
    text = text.replace('prompt: str', 'prompt: str\n    options: dict = None')
    
# Update PlannerAgent and ActionBuilderAgent calling code
text = text.replace('PlannerAgent()', 'PlannerAgent()') # We will pass it in via kwargs later? Actually, we can just export it in environ if we receive it.

# Update create_proposal method
if 'api_key_override' not in text:
    import re
    # find def create_proposal(req: ProposalRequest):
    code = '''
@router.post("/plugin/proposal", response_model=ProposalResponse)
async def create_proposal(req: ProposalRequest):
    if req.options and req.options.get("api_key"):
        os.environ["GEMINI_API_KEY"] = req.options["api_key"]
'''
    text = re.sub(r'@router.post\("/plugin/proposal".*?async def create_proposal\(req: ProposalRequest\):', code.strip(), text, flags=re.DOTALL)
    with open(path, 'w') as f:
        f.write(text)
    print("Patched plugin_bridge")
