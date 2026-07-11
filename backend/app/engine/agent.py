"""PersonaAgent — the core agentic AI unit. Each persona becomes an autonomous agent."""

from app.engine.groq_client import groq_client
from app.engine.prompt_engine import build_persona_system_prompt, build_simulation_prompt
from app.engine.decision_engine import calculate_temperature, process_response
from app.engine.memory_engine import memory_engine
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """Structured response from a PersonaAgent."""
    persona_id: str
    persona_label: str
    response: str
    sentiment: float
    confidence: float
    decision: str
    metadata: dict = field(default_factory=dict)


class PersonaAgent:
    """An autonomous AI agent that embodies a specific persona profile.
    
    Each PersonaAgent has:
    - Identity (full persona profile)
    - Memory (short-term conversation + long-term persistent)
    - Decision logic (personality-weighted)
    - Communication style
    """

    def __init__(
        self, 
        profile: dict, 
        memories: list[str] | None = None,
        product_name: str | None = None,
        product_description: str | None = None,
    ):
        self.profile = profile
        self.persona_id = profile["persona_id"]
        self.label = f"{self.persona_id} ({profile['age']}{profile['gender'][0]}, {profile['city']})"
        self.system_prompt = build_persona_system_prompt(
            profile, memories, product_name, product_description
        )
        self.temperature = calculate_temperature(profile)

    async def respond(self, question: str, simulation_type: str | None = None) -> AgentResponse:
        """Generate a response to a question, staying in character."""
        # Build the user message
        if simulation_type:
            user_message = build_simulation_prompt(simulation_type, question)
        else:
            user_message = question

        # Generate response via Groq
        response_text = await groq_client.generate(
            system_prompt=self.system_prompt,
            user_message=user_message,
            temperature=self.temperature,
        )

        # Process response for structured data
        processed = process_response(response_text, self.profile)

        return AgentResponse(
            persona_id=self.persona_id,
            persona_label=self.label,
            response=response_text,
            sentiment=processed["sentiment"],
            confidence=processed["confidence"],
            decision=processed["decision"],
            metadata={
                "temperature": self.temperature,
                "simulation_type": simulation_type,
            },
        )

    async def chat(self, user_message: str, conversation_key: str) -> str:
        """Have a conversation with this persona, maintaining context."""
        # Add user message to memory
        memory_engine.add_short_term(conversation_key, "user", user_message)

        # Get conversation history
        history = memory_engine.get_conversation_history_for_groq(conversation_key)

        # Generate response with history
        response_text = await groq_client.generate_with_history(
            system_prompt=self.system_prompt,
            messages=history,
            temperature=self.temperature,
        )

        # Add response to memory
        memory_engine.add_short_term(conversation_key, "model", response_text)

        return response_text
