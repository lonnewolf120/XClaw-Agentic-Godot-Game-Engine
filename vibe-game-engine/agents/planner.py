import os
import json
import logging
from typing import Optional

from contracts.messages import PlanMessage, PlanTask
from contracts.run_state import RunState

try:
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

logger = logging.getLogger(__name__)

class PlannerAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        # If GOOGLE_APPLICATION_CREDENTIALS is not set, we default to mock.
        has_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None or os.environ.get("VERTEX_STRICT", "false").lower() == "true"
        self.use_mock = not (VERTEX_AVAILABLE and has_credentials)
        if os.environ.get("USE_MOCK_PLANNER", "false").lower() == "true":
            self.use_mock = True

        self.model_name = model_name
        
        if not self.use_mock:
            self.llm = ChatVertexAI(
                model_name=self.model_name,
                temperature=0.0,
                max_output_tokens=1024,
            )
            self.parser = PydanticOutputParser(pydantic_object=PlanMessage)
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are the Planner Agent for a deterministic Godot game engine generator.
Your job is to read the user's game request and output a structured plan.
You MUST choose one of three supported barebones archetypes: 'platformer', 'runner', or 'dialogue'.
Do NOT generate game code. Only generate the structural plan.
"""),
                ("user", "User Request: {user_prompt}\n\n{format_instructions}")
            ])

    def plan(self, user_prompt: str) -> PlanMessage:
        if self.use_mock:
            logger.info("Using MOCK Planner Agent (no Vertex credentials or VERTEX_STRICT enabled).")
            # Deterministic fallback logic
            prompt_lower = user_prompt.lower()
            archetype = "platformer"
            if "runner" in prompt_lower:
                archetype = "runner"
            elif "dialog" in prompt_lower or "narrative" in prompt_lower:
                archetype = "dialogue"
            
            return PlanMessage(
                archetype=archetype,
                goals=["Build base Godot prototype."],
                mechanics=["Standard template mechanics."],
                constraints=["2D only, Phase 0 valid."],
                asset_requirements=["Placeholder sprites"],
                risk_flags=["Requires Godot headless test."],
                tasks=[PlanTask(id="1", role="builder", goal=f"Generate {archetype} scaffold")]
            )

        # Real LLM Call using Vertex
        try:
            logger.info(f"Invoking Vertex AI Planner ({self.model_name})...")
            chain = self.prompt | self.llm | self.parser
            plan = chain.invoke({
                "user_prompt": user_prompt,
                "format_instructions": self.parser.get_format_instructions()
            })
            return plan
        except Exception as e:
            logger.error(f"Planner Vertex LLM failed: {e}")
            raise
