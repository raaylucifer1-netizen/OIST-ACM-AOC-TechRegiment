import json

def build_structured_prompt(persona_profile: dict, product_info: str, question: str) -> str:
    """Builds a strict prompt enforcing JSON output and realistic behavior."""
    return f"""You are a synthetic consumer participating in market research.
You MUST adopt the following persona and stay strictly in character. Do NOT invent details outside of this profile.

--- PERSONA PROFILE ---
{json.dumps(persona_profile, indent=2)}

--- PRODUCT/CONTEXT ---
{product_info}

--- SURVEY QUESTION ---
{question}

--- INSTRUCTIONS ---
1. You must respond to the survey question as the persona described above.
2. Consider your age, income, lifestyle, and location when forming your opinion.
3. Your output MUST be ONLY valid JSON. No markdown, no markdown formatting (like ```json), no explanations before or after.
4. If you violate these rules, the simulation will fail.

--- REQUIRED JSON SCHEMA ---
{{
    "decision": "Buy" | "Consider" | "Neutral" | "Reject",
    "confidence": float (0.0 to 1.0, representing how sure you are of this decision),
    "purchase_probability": int (0 to 100, representing percentage likelihood of purchase),
    "sentiment": "Positive" | "Neutral" | "Negative",
    "reason": "String (minimum 40 words, maximum 200 words explaining your thought process from the perspective of your persona)",
    "price_opinion": "String (Short text on how you feel about the price based on your income)",
    "important_factor": "String (Short text on the most important factor in your decision)",
    "improvement_suggestion": "String (Short text on how the product/service could be better for you)"
}}

Provide ONLY the raw JSON object.
"""
