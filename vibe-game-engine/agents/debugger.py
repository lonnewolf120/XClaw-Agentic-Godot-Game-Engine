import os
import logging
from typing import Optional

from contracts.godot_patch import PatchBatch, GodotFilePatch, PatchOp
from contracts.validation import ValidationReport
from contracts.messages import DebugPatchMessage
from contracts.run_state import RunState

try:
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

logger = logging.getLogger(__name__)

class DebuggerAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        has_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None or os.environ.get("VERTEX_STRICT", "false").lower() == "true"
        self.use_mock = not (VERTEX_AVAILABLE and has_credentials)
        if os.environ.get("USE_MOCK_DEBUGGER", "false").lower() == "true":
            self.use_mock = True

        self.model_name = model_name

        if not self.use_mock:
            self.llm = ChatVertexAI(
                model_name=self.model_name,
                temperature=0.2, # Slight temp for generating fixes
                max_output_tokens=2048,
            )
            self.parser = PydanticOutputParser(pydantic_object=PatchBatch)
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are the Debugger Agent for a deterministic Godot game engine generator.
A validation test failed. Your job is to propose a minimal `PatchBatch` to fix the errors.
Focus on fixing script parse errors, path resolution, or missing nodes. Do not redesign the project.
"""),
                ("user", "Validation Failed:\n{validation_summary}\n\nIssues:\n{issues}\n\n{format_instructions}")
            ])

    def debug(self, run_state: RunState) -> DebugPatchMessage:
        report = run_state.validation_report
        
        if self.use_mock:
            logger.info("Using MOCK Debugger Agent.")
            # For now, deterministic mock just throws a hypothetical fix script
            patch = GodotFilePatch(
                patch_id="mock_fix_0",
                op=PatchOp.UPDATE,
                file_path="scripts/game_manager.gd",
                language="gdscript",
                reason="Mock patch attempting to clear parse error",
                full_content="extends Node\nfunc _ready():\n\tpass"
            )
            batch = PatchBatch(run_id=run_state.run_id, attempt=run_state.retry_count + 1, patches=[patch])
            return DebugPatchMessage(patch=batch)

        # Real LLM call
        try:
            logger.info(f"Invoking Vertex AI Debugger ({self.model_name})...")
            issues_str = "\n".join([f"- [{i.failure_class.value}] {i.message} (Context: {i.context_snippet})" for i in report.issues])
            chain = self.prompt | self.llm | self.parser
            
            patch_batch = chain.invoke({
                "validation_summary": report.summary,
                "issues": issues_str,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Ensure the ID and attempt are matching state
            patch_batch.run_id = run_state.run_id
            patch_batch.attempt = run_state.retry_count + 1
            
            return DebugPatchMessage(patch=patch_batch)
            
        except Exception as e:
            logger.error(f"Debugger Vertex LLM failed: {e}")
            raise
