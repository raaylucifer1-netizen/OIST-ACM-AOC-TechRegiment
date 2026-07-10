import asyncio
import os
import sys
from dotenv import load_dotenv

# Add app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load env variables
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

from app.engine.agent import PersonaAgent

async def run_test():
    # Make a dummy persona profile
    dummy_profile = {
        "persona_id": "P-TEST-1",
        "age": 30,
        "gender": "Female",
        "city": "Mumbai",
        "state": "Maharashtra",
        "education": "Master's",
        "occupation": "Software Engineer",
        "income_inr": 1800000,
        "language": "Hindi, English",
        "marital_status": "Single",
        "children": 0,
        "vehicle": "Car",
        "lifestyle": "Active",
        "shopping_frequency": "Weekly",
        "online_shopping_pct": 80,
        "offline_shopping_pct": 20,
        "payment_method": "UPI",
        "technology_adoption": "Early Adopter",
        "health_consciousness": 80,
        "food_preference": "Vegetarian",
        "political_interest": "Medium",
        "social_media_usage": 90,
        "brand_loyalty": 40,
        "price_sensitivity": 50,
        "risk_taking": 70,
        "impulse_buying": 30,
        "discount_preference": 60,
        "premium_preference": 70,
        "preferred_brand": "Apple",
        "communication_style": "Friendly",
        "response_length": "Medium",
        "openness": 80,
        "conscientiousness": 70,
        "extraversion": 75,
        "agreeableness": 85,
        "neuroticism": 30,
        "confidence": 80,
        "optimism": 85,
        "patience": 70,
        "curiosity": 90,
        "practicality": 75,
        "emotional_score": 50
    }

    print("Initializing PersonaAgent with dummy profile and product context...")
    agent = PersonaAgent(
        profile=dummy_profile,
        product_name="EcoCharge Electric Scooter",
        product_description="An electric scooter priced at Rs 1.1 Lakhs, with a 150km range, smart app connectivity, and sleek design."
    )

    print("\n--- SYSTEM PROMPT ---")
    print("\n--- SYSTEM PROMPT CHECK ---")
    
    # Verify that product context is in system prompt
    if "EcoCharge Electric Scooter" in agent.system_prompt:
        print("[SUCCESS] Product context found in agent's system prompt!")
    else:
        print("[FAILURE] Product context missing from system prompt!")
        sys.exit(1)

    print("Test passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_test())
