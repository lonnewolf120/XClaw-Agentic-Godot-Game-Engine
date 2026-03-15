import logging

logger = logging.getLogger(__name__)

class AssetAgent:
    """
    Stub for Phase 2 2D Asset generation.
    Currently disabled per ADR to force constraint on core deterministic orchestration.
    """
    def __init__(self):
        self.active = False
        
    def generate_asset(self, prompt: str, asset_type: str = "2d_sprite"):
        logger.info(f"Asset Agent stub called for {asset_type}. Returning deterministic placeholder info instead of AI gen.")
        return {
            "path": "assets/placeholder.png",
            "type": asset_type,
            "status": "stubbed"
        }