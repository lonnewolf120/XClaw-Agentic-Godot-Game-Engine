import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Analyzes the raw prompt to drastically narrow the scope of retrieval and execution.
    By doing a cheap classification step first, we avoid pulling the entire project into context
    for simple script patches, or hitting heavy LLMs when we only need template assets.
    """
    
    def classify(self, prompt: str) -> Dict[str, Any]:
        """
        Returns a classified intent envelope.
        """
        prompt_lower = prompt.lower()
        
        intent = {
            "is_asset_request": False,
            "is_script_patch": False,
            "is_scene_mutation": False,
            "is_new_feature": False,
            "primary_focus": "unknown"
        }
        
        # Simple heuristics for Phase 2 implementation.
        # This will be replaced by a small fast local LLM or fine-tuned classifier later.
        if any(w in prompt_lower for w in ["sprite", "texture", "audio", "sound", "music", "art"]):
            intent["is_asset_request"] = True
            intent["primary_focus"] = "asset"
            
        if any(w in prompt_lower for w in ["function", "logic", "speed", "jump", "math", "variable", "var", "bug", "fix script"]):
            intent["is_script_patch"] = True
            if intent["primary_focus"] == "unknown":
                intent["primary_focus"] = "script"
                
        if any(w in prompt_lower for w in ["node", "scene", "add a", "spawn", "instantiate", "child"]):
            intent["is_scene_mutation"] = True
            if intent["primary_focus"] == "unknown":
                intent["primary_focus"] = "scene"
                
        if any(w in prompt_lower for w in ["system", "mechanic", "inventory", "level", "menu"]):
            intent["is_new_feature"] = True
            intent["primary_focus"] = "feature"
            
        # Default fallback
        if intent["primary_focus"] == "unknown":
            intent["is_new_feature"] = True
            intent["primary_focus"] = "feature"
            
        logger.info(f"Classified intent: {intent['primary_focus']} (Asset: {intent['is_asset_request']}, Script: {intent['is_script_patch']}, Scene: {intent['is_scene_mutation']})")
        return intent
