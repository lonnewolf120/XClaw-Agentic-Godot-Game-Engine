from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, List
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview.caching import CachedContent
import datetime
from agents.token_logger import TokenEconomicsLogger

# Model configs with Vertex AI
DEFAULT_MODEL = "gemini-1.5-pro-preview-0409"
FALLBACK_MODEL = "gemini-1.5-flash-preview-0409"

class VertexAIManager:
    """Manages GCP Vertex AI connections for LLM inference, including Explicit Caching."""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1") -> None:
        # Relies on GOOGLE_APPLICATION_CREDENTIALS for auth in environment
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", location)
        if self.project_id:
            vertexai.init(project=self.project_id, location=self.location)
        self.active_caches: Dict[str, str] = {} # Mapping of context hash/name to cache resource name
        
    def get_chat_model(self, model_name: str = DEFAULT_MODEL, temperature: float = 0.0, **kwargs: Any) -> ChatVertexAI:
        """Initialize and return a ChatVertexAI instance. Uses low temperature for deterministic tool payloads."""
        return ChatVertexAI(
            project=self.project_id,
            location=self.location,
            model_name=model_name,
            temperature=temperature, # Low temperature for reliable function calls and JSON schema
            **kwargs,
        )

    def invoke_with_json_schema(self, 
                                prompt: str, 
                                schema: Any, 
                                model_name: str = DEFAULT_MODEL,
                                context_label: str = "json_schema_call",
                                **kwargs: Any) -> Any:
        """Call the model and ask it to conform to a Pydantic schema."""
        model = self.get_chat_model(model_name=model_name, **kwargs)
        structured_llm = model.with_structured_output(schema)
        response = structured_llm.invoke(prompt)
        
        # Log basic un-cached usage. 
        # (LangChain structured output doesn't trivially expose raw usage metadata yet in all wrappers, 
        # but we can estimate or attach a callback if needed. For now we record an invocation event).
        TokenEconomicsLogger.record_usage(
            model=model_name,
            cached_tokens=0,
            prompt_tokens=len(prompt) // 4, # Very rough estimate if raw usage missing
            output_tokens=500, # Rough estimate for JSON payloads
            context_label=context_label
        )
        return response

    def _generate_cache_key(self, system_instruction: str, contents: List[Any]) -> str:
        """Generates a stable fingerprint/hash for the cache content."""
        import hashlib
        import json
        
        # Simple stable hash based on content string forms
        content_str = str(contents) + system_instruction
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def create_or_get_cached_context(self, context_name: str, system_instruction: str, contents: List[Any], ttl_minutes: int = 60) -> str:
        """
        Creates a CachedContent resource for large, stable contexts (like Engine API or Project Index).
        Default TTL is 60 minutes to control token-hour storage costs.
        Uses SHA-256 fingerprinting to avoid duplicating caches for the same content.
        Returns the cached content name.
        """
        cache_key = self._generate_cache_key(system_instruction, contents)
        
        if cache_key in self.active_caches:
            return self.active_caches[cache_key]
            
        try:
            # Create a new cache
            cached_content = CachedContent.create(
                model_name=DEFAULT_MODEL,
                system_instruction=system_instruction,
                contents=contents,
                ttl=datetime.timedelta(minutes=ttl_minutes),
                display_name=f"{context_name}_{cache_key[:8]}"
            )
            self.active_caches[cache_key] = cached_content.name
            return cached_content.name
        except Exception as e:
            print(f"Failed to create cache: {e}")
            return ""

    def invoke_with_cached_context(self, prompt: str, cache_name: str, schema: Any = None) -> Any:
        """
        Invokes the model using an explicitly cached context.
        Logs telemetry for cached tokens to quantify savings.
        """
        if not cache_name:
            # Fallback to standard if no cache is available
            if schema:
                return self.invoke_with_json_schema(prompt, schema)
            else:
                model = self.get_chat_model()
                return model.invoke(prompt)
                
        # Use Vertex SDK directly for cached content as Langchain ChatVertexAI might not fully support it yet
        model = GenerativeModel.from_cached_content(cached_content=cache_name)
        
        # If schema is needed, we construct response_schema
        generation_config = {"temperature": 0.0}
        if schema:
            generation_config["response_mime_type"] = "application/json"
            # Note: full pydantic to dict schema translation needed for native SDK, 
            # or fallback to string prompt engineering
            
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Telemetry: Log token savings
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            cached_tokens = getattr(usage, "cached_content_token_count", 0)
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            output_tokens = getattr(usage, "candidates_token_count", 0)
            
            TokenEconomicsLogger.record_usage(
                model=DEFAULT_MODEL,
                cached_tokens=cached_tokens,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                context_label=f"cached_{cache_name}"
            )
            
        return response.text

# Singleton helper
_manager = None

def get_llm_manager() -> VertexAIManager:
    global _manager
    if _manager is None:
        _manager = VertexAIManager()
    return _manager
