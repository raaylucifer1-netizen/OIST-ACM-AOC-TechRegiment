import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.generation_log import GenerationLog
from app.response_agent.provider_manager import call_provider
from app.response_agent.cleaner import clean_llm_output
from app.response_agent.validator import AgentResponseSchema
from pydantic import ValidationError

class QuotaExceededError(Exception):
    pass

class RetryManager:
    def __init__(self, db: AsyncSession, survey_id: str, persona_id: str):
        self.db = db
        self.survey_id = survey_id
        self.persona_id = persona_id
        
        # We try Gemini, then Groq, then OpenRouter
        self.providers = ["gemini", "groq", "openrouter"]
        self.retry_delays = [2, 4, 8]  # Attempt 1 -> wait 2, Attempt 2 -> wait 4, Attempt 3 -> wait 8, then fail provider
        
    async def log_attempt(self, provider: str, attempt: int, status: str, error_msg: str = None):
        """Logs the attempt to the GenerationLog table."""
        log_entry = GenerationLog(
            survey_id=self.survey_id,
            persona_id=self.persona_id,
            provider=provider,
            attempt=attempt,
            status=status,
            error_message=error_msg,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log_entry)
        await self.db.flush()

    async def generate_with_retries(self, prompt: str, temperature: float = 0.7) -> tuple[dict, str, int]:
        """
        Attempts to generate and validate a response.
        Returns (validated_data_dict, provider_used, generation_time_ms).
        Raises QuotaExceededError if all providers fail (or all quotas exhausted).
        """
        import time
        
        for provider in self.providers:
            for attempt_idx in range(len(self.retry_delays) + 1):
                attempt_num = attempt_idx + 1
                start_time = time.time()
                
                try:
                    # 1. Call Provider
                    raw_response = await call_provider(provider, prompt, temperature)
                    
                    # 2. Clean
                    cleaned_json_str = clean_llm_output(raw_response)
                    if not cleaned_json_str:
                        raise ValueError("Cleaned response is empty")
                        
                    # 3. Parse JSON
                    data = json.loads(cleaned_json_str)
                    
                    # 4. Validate Schema
                    validated = AgentResponseSchema(**data)
                    
                    # 5. Success
                    generation_time_ms = int((time.time() - start_time) * 1000)
                    await self.log_attempt(provider, attempt_num, "success")
                    return validated.model_dump(), provider, generation_time_ms
                    
                except Exception as e:
                    error_msg = str(e)
                    await self.log_attempt(provider, attempt_num, "failed", error_msg)
                    
                    # Check for fatal errors that shouldn't bother retrying on the SAME provider
                    if "API_KEY not configured" in error_msg:
                        break # Move to next provider immediately
                        
                    if attempt_idx < len(self.retry_delays):
                        await asyncio.sleep(self.retry_delays[attempt_idx])
                    else:
                        # Reached max retries for this provider, moving to next
                        break

        # If we exit the loop, all providers failed
        raise QuotaExceededError("All providers failed or quotas exceeded")
