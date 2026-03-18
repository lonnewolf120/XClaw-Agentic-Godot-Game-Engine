from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from typing import Any, Optional, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMProviderError(RuntimeError):
    pass


class LLMProviderClient:
    def __init__(self, provider: str = "gemini", model_name: Optional[str] = None):
        self.provider = (provider or "gemini").strip().lower()
        self.model_name = model_name or os.environ.get("XCLAW_LLM_MODEL") or "gemini-3.1-pro-preview"

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema: Optional[Type[BaseModel]] = None) -> dict[str, Any]:
        if self.provider == "gemini":
            text = self._generate_with_gemini(system_prompt=system_prompt, user_prompt=user_prompt, schema=schema)
        elif self.provider == "gemini_cli":
            text = self._generate_with_cli(system_prompt=system_prompt, user_prompt=user_prompt, env_key="XCLAW_GEMINI_CLI_CMD", default_cmd="gemini")
        elif self.provider == "copilot_cli":
            text = self._generate_with_cli(system_prompt=system_prompt, user_prompt=user_prompt, env_key="XCLAW_COPILOT_CLI_CMD", default_cmd="gh copilot suggest --")
        elif self.provider == "codex_cli":
            text = self._generate_with_cli(system_prompt=system_prompt, user_prompt=user_prompt, env_key="XCLAW_CODEX_CLI_CMD", default_cmd="codex")
        else:
            raise LLMProviderError(f"Unsupported provider '{self.provider}'. Use one of: gemini, gemini_cli, copilot_cli, codex_cli.")

        payload = _extract_json_object(text)
        if not isinstance(payload, dict):
            raise LLMProviderError("Provider output is not a JSON object.")
        return _validate_payload(schema, payload)

    def _generate_with_gemini(self, *, system_prompt: str, user_prompt: str, schema: Optional[Type[BaseModel]] = None) -> str:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise LLMProviderError("GEMINI_API_KEY is required when provider=gemini.")

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise LLMProviderError(f"google-genai package is required for Gemini provider: {exc}") from exc

        client = genai.Client(api_key=api_key)
        merged_prompt = f"{system_prompt}\n\n{user_prompt}"
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=merged_prompt)])]

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "contents": contents,
            # We validate against schema locally because some Gemini endpoints reject
            # pydantic-generated JSON schema fields such as additional_properties.
            "config": types.GenerateContentConfig(response_mime_type="application/json"),
        }

        response = client.models.generate_content(**kwargs)
        return response.text or "{}"

    def _generate_with_cli(self, *, system_prompt: str, user_prompt: str, env_key: str, default_cmd: str) -> str:
        cmd_template = os.environ.get(env_key, default_cmd).strip()
        if not cmd_template:
            raise LLMProviderError(f"No CLI command configured for {env_key}.")

        prompt = (
            f"{system_prompt}\n\n"
            "Return only a valid JSON object and nothing else.\n\n"
            f"{user_prompt}"
        )

        cmd = _build_command(cmd_template, prompt)
        logger.info("Running LLM CLI provider command: %s", cmd[0])

        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(os.environ.get("XCLAW_LLM_CLI_TIMEOUT", "180")),
                shell=False,
            )
        except FileNotFoundError as exc:
            raise LLMProviderError(f"CLI binary not found for command: {cmd[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise LLMProviderError(f"CLI provider timed out after {exc.timeout}s") from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise LLMProviderError(f"CLI provider command failed ({completed.returncode}): {stderr}")

        output = (completed.stdout or "").strip()
        if not output:
            raise LLMProviderError("CLI provider returned empty output.")
        return output


def _build_command(template: str, prompt: str) -> list[str]:
    parts = shlex.split(template, posix=os.name != "nt")
    has_placeholder = any("{prompt}" in part for part in parts)
    command = [part.replace("{prompt}", prompt) for part in parts]
    if not has_placeholder:
        command.append(prompt)
    return command


def _extract_json_object(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMProviderError("No JSON object found in provider output.")

    snippet = raw[start : end + 1]
    try:
        return json.loads(snippet)
    except Exception as exc:
        raise LLMProviderError(f"Failed to parse JSON output: {exc}") from exc


def _validate_payload(schema: Optional[Type[BaseModel]], payload: dict[str, Any]) -> dict[str, Any]:
    if schema is None:
        return payload
    try:
        model = schema.model_validate(payload)
        return model.model_dump()
    except Exception as exc:
        raise LLMProviderError(f"Provider JSON failed schema validation: {exc}") from exc
