"""Memory Engine — manages short-term and long-term persona memory."""

from typing import Optional


class MemoryEngine:
    """In-memory implementation for persona memory management.
    
    Short-term: Recent conversation context (dict-based, per session).
    Long-term: Persistent memories stored in database (future: ChromaDB for vector search).
    """

    def __init__(self):
        # Short-term memory: {persona_id: [last N messages]}
        self._short_term: dict[str, list[dict]] = {}
        self._max_short_term = 20  # Keep last 20 exchanges per persona

    def get_short_term(self, persona_id: str) -> list[dict]:
        """Get recent conversation context for a persona."""
        return self._short_term.get(persona_id, [])

    def add_short_term(self, persona_id: str, role: str, content: str) -> None:
        """Add a message to short-term memory."""
        if persona_id not in self._short_term:
            self._short_term[persona_id] = []

        self._short_term[persona_id].append({"role": role, "content": content})

        # Trim to max size
        if len(self._short_term[persona_id]) > self._max_short_term:
            self._short_term[persona_id] = self._short_term[persona_id][-self._max_short_term:]

    def clear_short_term(self, persona_id: str) -> None:
        """Clear short-term memory for a persona."""
        self._short_term.pop(persona_id, None)

    def get_conversation_history_for_gemini(self, persona_id: str) -> list[dict]:
        """Format short-term memory as Gemini chat history format."""
        history = []
        for msg in self.get_short_term(persona_id):
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        return history

    def get_conversation_history_for_groq(self, persona_id: str) -> list[dict]:
        """Format short-term memory as Groq chat history format."""
        history = []
        for msg in self.get_short_term(persona_id):
            role = "user" if msg["role"] == "user" else "assistant"
            history.append({"role": role, "content": msg["content"]})
        return history


# Singleton
memory_engine = MemoryEngine()
