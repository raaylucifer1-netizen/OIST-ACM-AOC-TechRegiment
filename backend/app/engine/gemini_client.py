"""Google Gemini API client wrapper with async support."""

import google.generativeai as genai
from app.config import settings
import asyncio
from typing import Optional


class GeminiClient:
    """Wrapper around Google Generative AI SDK for PersonaX."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self._embedding_model = settings.GEMINI_EMBEDDING_MODEL

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response using Gemini with system prompt and user message."""
        # Build the full prompt with system instruction
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        max_retries = 5
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                # Run in thread pool since the SDK is synchronous
                response = await asyncio.to_thread(
                    model.generate_content, user_message
                )

                if response.text:
                    return response.text.strip()
                return "I'm not sure how to respond to that."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower() or "resource" in err_msg.lower() or "exhausted" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Gemini Error] Quota exceeded on final retry: {e}")
                        return f"[Error generating response: {str(e)}]"
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Gemini Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Gemini Error] {e}")
                    return f"[Error generating response: {str(e)}]"
        return "I'm not sure how to respond to that."

    async def generate_with_history(
        self,
        system_prompt: str,
        messages: list[dict],  # [{"role": "user"|"model", "parts": ["text"]}]
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response with conversation history."""
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])
        last_message = messages[-1]["parts"][0] if messages else ""

        max_retries = 5
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(chat.send_message, last_message)

                if response.text:
                    return response.text.strip()
                return "I'm not sure how to respond to that."

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower() or "resource" in err_msg.lower() or "exhausted" in err_msg.lower():
                    if attempt == max_retries - 1:
                        print(f"[Gemini Error] Quota exceeded on final retry: {e}")
                        return f"[Error generating response: {str(e)}]"
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"[Gemini Client] Rate limit hit. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    print(f"[Gemini Error] {e}")
                    return f"[Error generating response: {str(e)}]"
        return "I'm not sure how to respond to that."

    async def get_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model=f"models/{self._embedding_model}",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            print(f"[Embedding Error] {e}")
            return []

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        # Process in batches of 100
        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]
            try:
                result = await asyncio.to_thread(
                    genai.embed_content,
                    model=f"models/{self._embedding_model}",
                    content=batch,
                    task_type="retrieval_document",
                )
                embeddings.extend(result["embedding"])
            except Exception as e:
                print(f"[Batch Embedding Error] {e}")
                embeddings.extend([[] for _ in batch])
        return embeddings


# Singleton instance
gemini_client = GeminiClient()
