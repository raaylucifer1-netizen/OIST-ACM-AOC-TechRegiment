"""Groq API client wrapper with async support."""

from groq import AsyncGroq
from app.config import settings
import asyncio

import time

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.calls = [t for t in self.calls if time.time() - t < self.period]
                
            self.calls.append(time.time())


class GroqClient:
    """Wrapper around Groq SDK for PersonaX."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        # Gemini free tier is 15 RPM, so we limit to 14 requests per 60 seconds
        self.rate_limiter = RateLimiter(max_calls=14, period=60.0)

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response using Groq with system prompt and user message."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        max_retries = 3
        base_delay = 2.0
        for attempt in range(max_retries):
            try:
                await self.rate_limiter.acquire()
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                return "Neutral. I don't have a strong opinion."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "rate limit" in err_msg.lower() or "quota" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Groq Error] Rate limit exceeded on final retry: {e}")
                        return "Neutral. I'm currently overwhelmed with information."
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Groq Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Groq Error] {e}")
                    return "Neutral. I'm unable to process this right now."
        return "Neutral. I don't have a strong opinion."

    async def generate_with_history(
        self,
        system_prompt: str,
        messages: list[dict],  # [{"role": "user"|"assistant", "content": "text"}]
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response with conversation history."""
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        max_retries = 3
        base_delay = 2.0
        for attempt in range(max_retries):
            try:
                await self.rate_limiter.acquire()
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                return "Neutral. I don't have a strong opinion."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "rate limit" in err_msg.lower() or "quota" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Groq Error] Rate limit exceeded on final retry: {e}")
                        return "Neutral. I'm currently overwhelmed with information."
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Groq Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Groq Error] {e}")
                    return "Neutral. I'm unable to process this right now."
        return "Neutral. I don't have a strong opinion."


# Singleton instance
groq_client = GroqClient()
