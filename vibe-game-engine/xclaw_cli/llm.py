"""LLM provider abstraction. One method: complete(system, user) -> text.

Providers:
- gemini: google-genai (uses GEMINI_API_KEY). JSON-mode response.
- ollama: local HTTP (free), for the cost-conscious / offline path.
- fake:   canned responder, for deterministic wiring tests (no network).
"""
from __future__ import annotations

import os
from typing import Callable


class LLMError(RuntimeError):
    pass


class LLMClient:
    name: str = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class GeminiClient(LLMClient):
    name = "gemini"

    def __init__(self, model: str = "gemini-3.5-flash", api_key: str | None = None, temperature: float = 0.2) -> None:
        try:
            from google import genai
            from google.genai.types import HttpOptions
        except Exception as exc:
            raise LLMError(f"google-genai not installed: {exc}") from exc
        
        key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        
        if key:
            # Gemini Enterprise / AI Studio Mode
            self._client = genai.Client(
                api_key=key,
                http_options=HttpOptions(api_version="v1")
            )
        else:
            # Vertex AI Mode
            project_id = os.environ.get("GCP_PROJECT", "parents-care-453403")
            print(f"[xclaw] Using Gemini via Vertex AI (ADC) - Project: {project_id}")
            self._client = genai.Client(
                vertexai=True, 
                project=project_id, 
                location="us-central1"
            )
            
        self.model = model
        self.temperature = temperature

    def complete(self, system: str, user: str) -> str:
        try:
            prompt_text = f"{system}\n\nUSER REQUEST AND PROJECT CONTEXT:\n{user}"
            
            resp = self._client.models.generate_content(
                model=self.model,
                contents=prompt_text
            )
            return resp.text or ""
        except Exception as exc:
            raise LLMError(f"Gemini/Vertex error: {exc}") from exc


class OllamaClient(LLMClient):
    name = "ollama"

    def __init__(self, model: str = "qwen2.5-coder", host: str = "http://localhost:11434", temperature: float = 0.2) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature

    def complete(self, system: str, user: str) -> str:
        import requests

        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system}\n\n{user}",
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": self.temperature},
                },
                timeout=300,
            )
            resp.raise_for_status()
        except Exception as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc
        return resp.json().get("response", "")


class AnthropicClient(LLMClient):
    """Claude via the official Anthropic SDK.

    Defaults to claude-opus-4-8 with adaptive thinking. Constrains the response to a
    JSON object {summary, writes:[{path, content}]} via structured outputs, and caches
    the (stable) system prompt across the loop's retry attempts. Resolves credentials
    from the environment (ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / `ant auth` profile).
    """

    name = "anthropic"

    # Structured-output schema: every object sets additionalProperties:false (required).
    _SCHEMA = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "writes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "writes"],
        "additionalProperties": False,
    }

    def __init__(self, model: str = "claude-opus-4-8", max_tokens: int = 16000) -> None:
        try:
            import anthropic  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise LLMError(f"anthropic SDK not installed (pip install anthropic): {exc}") from exc
        import anthropic

        self._anthropic = anthropic
        try:
            self._client = anthropic.Anthropic()  # resolves key from env / auth profile
        except Exception as exc:
            raise LLMError(f"Anthropic client init failed (set ANTHROPIC_API_KEY): {exc}") from exc
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": self._SCHEMA}},
        )
        # Structured outputs guarantee the first text block is valid JSON.
        for block in resp.content:
            if block.type == "text":
                return block.text
        raise LLMError("Claude returned no text block")


class FakeClient(LLMClient):
    name = "fake"

    def __init__(self, responder: Callable[[str, str], str]) -> None:
        self._responder = responder

    def complete(self, system: str, user: str) -> str:
        return self._responder(system, user)


def get_client(provider: str = "anthropic", model: str | None = None, **kwargs) -> LLMClient:
    provider = (provider or "anthropic").strip().lower()
    if provider in ("anthropic", "claude"):
        return AnthropicClient(model=model or "claude-opus-4-8", **kwargs)
    if provider == "gemini":
        return GeminiClient(model=model or "gemini-3.5-flash", **kwargs)
    if provider == "ollama":
        return OllamaClient(model=model or "qwen2.5-coder", **kwargs)
    raise LLMError(
        f"Unknown provider '{provider}'. Use anthropic, gemini, or ollama (or construct FakeClient directly)."
    )
