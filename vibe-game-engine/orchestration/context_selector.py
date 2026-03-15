
# Context selection for reducing noise
class ContextSelector:
    def get_relevant_files(self, workspace_files, user_intent):
        return [f for f in workspace_files if not f.endswith(".import")]

