import os
import logging
from typing import Optional
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from contracts.messages import PlanMessage
from contracts.actions import ActionBatch

logger = logging.getLogger(__name__)

class ActionBuilderAgent:
    """
    Consumes a PlanMessage and current Local Project Context,
    Returns a strict Pydantic ActionBatch (Structured JSON) schema for local execution.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.use_mock = os.environ.get("USE_MOCK_BUILDER", "false").lower() == "true"
        
        if not self.use_mock:
            self.llm = ChatVertexAI(
                model_name=self.model_name,
                temperature=0.0, # ZERO temperature for strict deterministic tool payload
                max_output_tokens=4096
            ).with_structured_output(ActionBatch)

    def generate_action_batch(self, prompt: str, plan: PlanMessage, context_summary: str) -> ActionBatch:
        if self.use_mock:
            logger.info("Using mock Builder (no Vertex AI call)")
            return ActionBatch(
                description="Mock adding a jump feature",
                actions=[
                    {
                        "action_type": "patch_script",
                        "script_path": "res://player.gd",
                        "search_string": "# Add jump here",
                        "replace_string": "velocity.y = JUMP_VELOCITY"
                    }
                ]
            )
            
        system_prompt = """You are an expert Godot Game Engine Builder Agent.
Your job is to read the Project Context and the Execution Plan, then output a STRCIT ActionBatch JSON that executes the plan.

Constraints:
- Treat `patch_script` as your primary way to modify behavior. Ensure your `search_string` is an EXACT literal match of code that exists in the files.
- ALWAYS return the requested JSON schema.
"""
        
        human_prompt = f"""
USER PROMPT: {prompt}

EXECUTION PLAN:
{plan.model_dump_json(indent=2)}

LOCAL PROJECT CONTEXT:
{context_summary}

Generate the ActionBatch to fulfill the plan.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        logger.info("Calling Vertex AI Builder Agent (Structured Output mode)...")
        action_batch = self.llm.invoke(messages)
        return action_batch
