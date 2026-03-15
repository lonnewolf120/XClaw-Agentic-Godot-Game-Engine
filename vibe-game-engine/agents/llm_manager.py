from __future__ import annotations

import os
from typing import Any, Dict, Optional
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate

# Model configs with Vertex AI
DEFAULT_MODEL = "gemini-1.5-pro-preview-0409"
FALLBACK_MODEL = "gemini-1.5-flash-preview-0409"

class VertexAIManager:
    """Manages GCP Vertex AI connections for LLM inference."""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1") -> None:
        # Relies on GOOGLE_APPLICATION_CREDENTIALS for auth in environment
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", location)
        
    def get_chat_model(self, model_name: str = DEFAULT_MODEL, temperature: float = 0.2, **kwargs: Any) -> ChatVertexAI:
        """Initialize and return a ChatVertexAI instance."""
        return ChatVertexAI(
            project=self.project_id,
            location=self.location,
            model_name=model_name,
            temperature=temperature,
            **kwargs,
        )

    def invoke_with_json_schema(self, 
                                prompt: str, 
                                schema: Any, 
                                model_name: str = DEFAULT_MODEL,
                                **kwargs: Any) -> Any:
        """Call the model and ask it to conform to a Pydantic schema."""
        model = self.get_chat_model(model_name=model_name, **kwargs)
        # We can use WithStructuredOutput if LangChain supports it out of the box for Vertex
        structured_llm = model.with_structured_output(schema)
        return structured_llm.invoke(prompt)

# Singleton helper
_manager = None

def get_llm_manager() -> VertexAIManager:
    global _manager
    if _manager is None:
        _manager = VertexAIManager()
    return _manager