import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.simulation import Simulation, SimulationResponse
from app.models.persona import Persona

async def main():
    async with async_session() as session:
        # Get the latest simulation responses
        result = await session.execute(
            select(SimulationResponse, Persona, Simulation)
            .join(Persona, Persona.id == SimulationResponse.persona_id)
            .join(Simulation, Simulation.id == SimulationResponse.simulation_id)
            .order_by(SimulationResponse.created_at.desc())
            .limit(10)
        )
        rows = result.all()
        if not rows:
            print("No simulation responses found.")
            return
        
        for resp, persona, sim in rows:
            print(f"--- Simulation: {sim.title} (Type: {sim.type}) ---")
            print(f"Persona: {persona.persona_id} ({persona.age}, {persona.gender}, {persona.city}, Lang: {persona.language})")
            print(f"Response: {resp.response}")
            print(f"Decision: {resp.decision}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
