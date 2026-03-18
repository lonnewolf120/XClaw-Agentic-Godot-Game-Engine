import json
import logging
from typing import Optional

from contracts.messages import PlanMessage, PlanTask
from agents.llm_provider import LLMProviderClient, LLMProviderError

logger = logging.getLogger(__name__)

class PlannerAgent:
    def __init__(self, model_name: str = "gemini-3.1-pro-preview", provider: str = "gemini", use_mock: bool = False):
        self.model_name = model_name
        self.provider = provider
        self.use_mock = use_mock
        
    def plan(self, initial_prompt: str) -> PlanMessage:
        if self.use_mock:
            return PlanMessage(
                archetype="platformer",
                goals=["Mock Build"],
                mechanics=["Mock"],
                constraints=["Mock"],
                asset_requirements=["Mock"],
                risk_flags=["Mock"],
                tasks=[PlanTask(id="1", role="builder", goal="Generate scaffold")]
            )

        system = "You are the Planner. Break the user prompt into a structured PlanMessage for a deterministic Godot game engine generator. You MUST choose one of three supported barebones archetypes: 'platformer', 'runner', or 'dialogue'."
        user_prompt = "User: " + initial_prompt

        try:
            client = LLMProviderClient(provider=self.provider, model_name=self.model_name)
            data = client.generate_json(
                system_prompt=system,
                user_prompt=user_prompt,
                schema=PlanMessage,
            )
            # Filter out extra keys that StrictModel would reject
            valid_keys = PlanMessage.model_fields.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return PlanMessage(**filtered_data)
        except (LLMProviderError, json.JSONDecodeError, ValueError) as e:
            logger.error("Planner generation failed: %s", e)
            return PlanMessage(
                archetype="platformer", 
                goals=["Failed: " + str(e)], 
                mechanics=[], 
                constraints=[], 
                asset_requirements=[], 
                risk_flags=[], 
                tasks=[PlanTask(id="1", role="builder", goal="Fallback")]
            )
