"""Groq API client wrapper with async support."""

from groq import AsyncGroq
from app.config import settings
import asyncio


class GroqClient:
    """Wrapper around Groq SDK for PersonaX."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

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

        max_retries = 5
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                return "I'm not sure how to respond to that."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "rate limit" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Groq Error] Rate limit exceeded on final retry: {e}")
                        return f"[Error generating response: {str(e)}]"
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Groq Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Groq Error] {e}")
                    return f"[Error generating response: {str(e)}]"
        return "I'm not sure how to respond to that."

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

        max_retries = 5
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                return "I'm not sure how to respond to that."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "rate limit" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Groq Error] Rate limit exceeded on final retry: {e}")
                        return f"[Error generating response: {str(e)}]"
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Groq Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Groq Error] {e}")
                    return f"[Error generating response: {str(e)}]"
        return "I'm not sure how to respond to that."


# Singleton instance
groq_client = GroqClient()
