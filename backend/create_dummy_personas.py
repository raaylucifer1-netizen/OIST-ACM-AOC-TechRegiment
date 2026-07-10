import asyncio
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.user import User
from app.models.persona import Persona

async def seed_personas():
    async with async_session() as db:
        # Get first user
        result = await db.execute(select(User))
        user = result.scalars().first()
        
        if not user:
            print("No users found. Please register an account first.")
            return

        print(f"Creating sample personas for user: {user.email}")
        
        occupations = ["Software Engineer", "Teacher", "Doctor", "Retail Manager", "Student", "Artist", "Plumber", "Data Analyst", "Chef", "Lawyer"]
        cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
        lifestyles = ["Active", "Sedentary", "Balanced", "Health-conscious"]
        
        for i in range(15):
            p = Persona(
                user_id=user.id,
                persona_id=f"P-TEST-{i+1}",
                age=random.randint(18, 65),
                gender=random.choice(["Male", "Female", "Non-binary"]),
                state="State",
                city=random.choice(cities),
                occupation=random.choice(occupations),
                income_inr=random.randint(300000, 5000000),
                education=random.choice(["High School", "Bachelor's", "Master's", "PhD"]),
                lifestyle=random.choice(lifestyles),
                technology_adoption=random.choice(["Early Adopter", "Majority", "Laggard"]),
                food_preference=random.choice(["Vegetarian", "Non-Vegetarian", "Vegan"]),
                political_interest=random.choice(["High", "Medium", "Low"]),
                preferred_brand="Generic",
                openness=random.uniform(0.1, 1.0),
                conscientiousness=random.uniform(0.1, 1.0),
                extraversion=random.uniform(0.1, 1.0),
                agreeableness=random.uniform(0.1, 1.0),
                neuroticism=random.uniform(0.1, 1.0)
            )
            db.add(p)
        
        await db.commit()
        print("Successfully added 15 sample personas to your account!")

if __name__ == "__main__":
    asyncio.run(seed_personas())
