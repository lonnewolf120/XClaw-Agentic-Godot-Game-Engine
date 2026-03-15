
# Context compactification threshold logic
class ContextCompactifier:
    def __init__(self, token_threshold=4000, turn_threshold=10):
        self.token_threshold = token_threshold
        self.turn_threshold = turn_threshold

    def compactify(self, conversation_history):
        # Keeps last few turns, summarizes older history
        if len(conversation_history) > self.turn_threshold:
            return conversation_history[-self.turn_threshold:]
        return conversation_history

