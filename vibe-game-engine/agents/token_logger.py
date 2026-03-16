import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TokenEconomicsLogger:
    """
    Singleton-style logger that intercepts and records all token usage across the engine.
    This tracks cache hits, prompt sizes, and output bounds to compute the 
    'Cost per successful edit' KPI over long sessions.
    """
    
    # We maintain a session-level ledger
    _session_ledger = []
    
    @classmethod
    def record_usage(cls, 
                     model: str, 
                     cached_tokens: int, 
                     prompt_tokens: int, 
                     output_tokens: int, 
                     context_label: str = "general"):
        """Records a single inference event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": model,
            "context_label": context_label,
            "cached_tokens": cached_tokens,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens
        }
        cls._session_ledger.append(entry)
        logger.debug(f"[TokenEconomics] {context_label} | Cached: {cached_tokens} | Prompt: {prompt_tokens} | Output: {output_tokens}")
        
    @classmethod
    def get_session_summary(cls) -> Dict[str, Any]:
        """Calculates total usage and roughly estimates cost."""
        total_cached = sum(e["cached_tokens"] for e in cls._session_ledger)
        total_prompt = sum(e["prompt_tokens"] for e in cls._session_ledger)
        total_output = sum(e["output_tokens"] for e in cls._session_ledger)
        
        # Rough pricing for Gemini 1.5 Flash (as a baseline for MVP cost modeling)
        # Assuming cached is ~90% cheaper than prompt
        cost_prompt = (total_prompt / 1_000_000) * 0.35
        cost_cached = (total_cached / 1_000_000) * 0.035
        cost_output = (total_output / 1_000_000) * 1.05
        
        return {
            "calls_made": len(cls._session_ledger),
            "tokens": {
                "cached": total_cached,
                "prompt_uncached": total_prompt,
                "output": total_output,
                "total_processed": total_cached + total_prompt + total_output
            },
            "estimated_cost_usd": round(cost_prompt + cost_cached + cost_output, 4)
        }
        
    @classmethod
    def reset_session(cls):
        cls._session_ledger = []

    @classmethod
    def dump_ledger(cls, filepath: str):
        """Dumps the raw token events to disk for offline analysis."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cls._session_ledger, f, indent=2)
