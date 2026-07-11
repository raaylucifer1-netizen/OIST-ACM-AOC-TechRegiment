import google.generativeai as genai
from groq import AsyncGroq
import httpx
from app.config import settings

# Initialize SDKs if keys are available
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

groq_client = None
if settings.GROQ_API_KEY:
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)


async def call_provider(provider: str, prompt: str, temperature: float = 0.7) -> str:
    """Calls the specified LLM provider and returns the raw string response."""
    if provider == "gemini":
        return await _call_gemini(prompt, temperature)
    elif provider == "groq":
        return await _call_groq(prompt, temperature)
    elif provider == "openrouter":
        return await _call_openrouter(prompt, temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")

async def _call_gemini(prompt: str, temperature: float) -> str:
    import asyncio
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
        
    model = genai.GenerativeModel(
        settings.GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
        ),
    )
    # Gemini SDK is synchronous, run in thread
    response = await asyncio.to_thread(model.generate_content, prompt)
    if response.text:
        return response.text
    raise ValueError("Empty response from Gemini")

async def _call_groq(prompt: str, temperature: float) -> str:
    if not groq_client:
        raise ValueError("GROQ_API_KEY not configured")
        
    response = await groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    if response.choices and response.choices[0].message.content:
        return response.choices[0].message.content
    raise ValueError("Empty response from Groq")

async def _call_openrouter(prompt: str, temperature: float) -> str:
    # Requires OPENROUTER_API_KEY in config
    api_key = getattr(settings, "OPENROUTER_API_KEY", None)
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000", # Modify for production
        "X-Title": "Aaru India Synthetic Personas",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free", # Using a free fallback model by default
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        raise ValueError("Empty response from OpenRouter")
