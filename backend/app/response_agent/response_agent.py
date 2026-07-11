from sqlalchemy.ext.asyncio import AsyncSession
from app.models.persona import Persona
from app.models.simulation import Simulation
from app.response_agent.prompt_builder import build_structured_prompt
from app.response_agent.retry_manager import RetryManager, QuotaExceededError

class ResponseGenerationAgent:
    """The central agent responsible for generating robust, validated responses for a persona."""
    
    def __init__(self, db: AsyncSession, simulation: Simulation, persona: Persona):
        self.db = db
        self.simulation = simulation
        self.persona = persona
        self.retry_manager = RetryManager(db, simulation.id, persona.id)
        
    async def generate_response(self) -> dict:
        """
        Generates a validated response dict containing:
        - decision, confidence, purchase_probability, sentiment, reason, price_opinion, important_factor, improvement_suggestion
        - provider_used, generation_time_ms
        Raises QuotaExceededError if generation completely fails.
        """
        # 1. Build Prompt
        prompt = build_structured_prompt(
            persona_profile=self.persona.to_profile_dict(),
            product_info=self.simulation.title,
            question=self.simulation.question
        )
        
        # We can dynamically set temperature based on persona logic if desired,
        # but for now we use a default of 0.7 for creativity while maintaining structure.
        temperature = 0.7
        
        # 2. Generate with retries
        # This will raise QuotaExceededError if it fails all attempts
        validated_data, provider, gen_time = await self.retry_manager.generate_with_retries(prompt, temperature)
        
        # 3. Attach metadata
        validated_data["provider_used"] = provider
        validated_data["generation_time_ms"] = gen_time
        
        return validated_data
