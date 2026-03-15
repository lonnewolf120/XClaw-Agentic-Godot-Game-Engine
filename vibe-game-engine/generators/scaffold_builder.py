import os
import logging
from pathlib import Path
from typing import Dict

from generators.platformer_template import PLATFORMER_FILES
from generators.runner_template import RUNNER_FILES
from generators.dialogue_template import DIALOGUE_FILES

logger = logging.getLogger(__name__)

# Very basic template registry for Phase 0
TEMPLATES = {
    "platformer": PLATFORMER_FILES,
    "runner": RUNNER_FILES,
    "dialogue": DIALOGUE_FILES
}

class ScaffoldBuilder:
    """Builds a deterministic Phase 0 Godot project into the workspace."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.generated_dir = self.workspace_path / "generated"

    def build_archetype(self, archetype: str) -> Dict[str, str]:
        """
        Writes the template files to the generated directory.
        Returns a dictionary of generated files mappings.
        """
        if archetype not in TEMPLATES:
            logger.warning(f"Archetype {archetype} not strictly supported yet. Falling back to platformer.")
            archetype = "platformer"

        files = TEMPLATES[archetype]
        manifest = {}

        for relative_path, content in files.items():
            full_path = self.generated_dir / relative_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            manifest[relative_path] = str(full_path)
            logger.debug(f"Generated {relative_path} successfully.")

        # Ensure empty asset folders exist as required by project conventions
        (self.generated_dir / "assets").mkdir(parents=True, exist_ok=True)

        return manifest
