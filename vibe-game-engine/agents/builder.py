import os
import logging
from typing import Optional
import json

from contracts.messages import PlanMessage
from contracts.actions import ActionBatch
from agents.llm_provider import LLMProviderClient, LLMProviderError

logger = logging.getLogger(__name__)

class ActionBuilderAgent:
    def __init__(self, provider: str = "gemini", model_name: Optional[str] = None):
        self.provider = provider
        self.model = model_name or os.environ.get("XCLAW_LLM_MODEL") or "gemini-3.1-pro-preview"

    def generate_action_batch(self, prompt: str, plan_summary: str, retrieved_context: str) -> ActionBatch:
        system_prompt = '''You are Godot Builder AI. You mutate the Godot editor state...'''
        user_prompt = f'''Plan: {plan_summary}\nContext: {retrieved_context}\nUser: {prompt}\nBuild the JSON ActionBatch.'''

        try:
            client = LLMProviderClient(provider=self.provider, model_name=self.model)
            data = client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=ActionBatch,
            )
            valid_keys = ActionBatch.model_fields.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return ActionBatch(**filtered_data)
        except (LLMProviderError, json.JSONDecodeError, ValueError) as e:
            logger.error('Provider call failed or returned invalid action batch: %s', e)
            return ActionBatch(actions=[], description='API Error: ' + str(e))
