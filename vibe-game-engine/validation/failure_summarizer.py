from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)

class FailureSummarizer:
    """
    Analyzes Godot headless execution logs to find implicated files
    and extract a tight context window to avoid flooding the Debugger with giant logs.
    """
    
    def __init__(self, context_limit: int = 800):
        self.context_limit = context_limit

    def summarize(self, full_log: str, validation_issues: List[Any]) -> Dict[str, Any]:
        """
        Takes the raw log string and the Pydantic issues from HeadlessValidator.
        Returns:
          - A compressed text snippet.
          - A list of implicated file paths for the RetrievalOrchestrator to target.
        """
        implicated_files = set()
        snippet_lines = []
        
        # 1. Parse log for explicit file paths mentioned near errors
        # Godot errors often look like:
        # SCRIPT ERROR: Parse Error: ... at: res://scripts/player.gd:42
        # ERROR: ... at: (res://scenes/main.tscn:10)
        
        res_regex = re.compile(r'res://([a-zA-Z0-9_/\.\-]+)')
        
        # 2. Find the core error block
        error_keywords = ["Parse Error:", "SCRIPT ERROR:", "USER ERROR:", "ERROR:"]
        
        lines = full_log.split('\n')
        error_line_indices = []
        
        for i, line in enumerate(lines):
            if any(k in line for k in error_keywords):
                error_line_indices.append(i)
                # find files in this line
                for match in res_regex.finditer(line):
                    implicated_files.add(f"res://{match.group(1)}")
                    
        # If no explicit error keyword found, just tail the log
        if not error_line_indices:
            tail = "\n".join(lines[-15:])
            for match in res_regex.finditer(tail):
                implicated_files.add(f"res://{match.group(1)}")
            return {
                "summary": f"Godot exited with failure. Log tail:\n...\n{tail}",
                "implicated_files": list(implicated_files)
            }
            
        # Build bounded snippet around the first major error
        primary_idx = error_line_indices[0]
        start_idx = max(0, primary_idx - 3)
        end_idx = min(len(lines), primary_idx + 8)
        
        snippet = "\n".join(lines[start_idx:end_idx])
        
        # Truncate if insanely long
        if len(snippet) > self.context_limit:
            snippet = snippet[:self.context_limit] + "\n...[truncated]"
            
        # Also grab any files mentioned in the provided ValidationIssues
        for issue in validation_issues:
            if hasattr(issue, 'context_snippet') and issue.context_snippet:
                for match in res_regex.finditer(issue.context_snippet):
                    implicated_files.add(f"res://{match.group(1)}")
            if hasattr(issue, 'message') and issue.message:
                 for match in res_regex.finditer(issue.message):
                    implicated_files.add(f"res://{match.group(1)}")

        return {
            "summary": f"Detected Engine Error:\n{snippet}",
            "implicated_files": list(implicated_files)
        }
