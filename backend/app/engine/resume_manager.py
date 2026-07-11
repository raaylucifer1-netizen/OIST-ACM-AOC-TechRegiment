"""Background worker for automatically resuming paused simulations."""

import asyncio
from sqlalchemy import select, func
from app.database import async_session
from app.models.simulation import Simulation, SimulationResponse
from app.engine.simulation_engine import select_persona_sample, run_simulation
import json

async def resume_paused_simulations():
    """Background task that runs periodically to resume paused simulations."""
    print("[Resume Worker] Started background task loop.")
    while True:
        try:
            # Wait for 1 minute between checks to give APIs a chance to reset quota
            await asyncio.sleep(60)
            
            async with async_session() as db:
                # Find all paused simulations
                paused_sims_query = select(Simulation).where(Simulation.status == "paused")
                result = await db.execute(paused_sims_query)
                paused_sims = result.scalars().all()
                
                if not paused_sims:
                    continue
                    
                print(f"[Resume Worker] Found {len(paused_sims)} paused simulation(s). Attempting to resume...")
                
                for sim in paused_sims:
                    try:
                        # Find how many responses have already been generated
                        completed_query = select(SimulationResponse.persona_id).where(SimulationResponse.simulation_id == sim.id)
                        completed_result = await db.execute(completed_query)
                        completed_ids = set(completed_result.scalars().all())
                        
                        completed_count = len(completed_ids)
                        needed_count = sim.sample_size - completed_count
                        
                        if needed_count <= 0:
                            # Edge case: It was paused but actually finished all required?
                            sim.status = "completed"
                            await db.commit()
                            continue
                            
                        print(f"[Resume Worker] Resuming sim {sim.id}. Needed: {needed_count} / {sim.sample_size}")
                        
                        # Parse config to get filters
                        filters = json.loads(sim.config) if sim.config else {}
                        
                        # Fetch the required number of new personas, excluding already completed ones
                        personas = await select_persona_sample(
                            db=db,
                            user_id=sim.user_id,
                            sample_size=needed_count,
                            filters=filters,
                            project_id=sim.project_id,
                            exclude_ids=completed_ids
                        )
                        
                        if not personas:
                            print(f"[Resume Worker] No more matching personas found for sim {sim.id}.")
                            sim.status = "failed"
                            sim.results_summary = json.dumps({"error": "No more matching personas found to complete the simulation."})
                            await db.commit()
                            continue
                            
                        # Update status back to running
                        sim.status = "running"
                        await db.commit()
                        
                        # Run simulation block
                        # We await here so we don't spam APIs concurrently for multiple simulations
                        result_dict = await run_simulation(db, sim, personas)
                        
                        if result_dict.get("status") == "paused":
                            print(f"[Resume Worker] Sim {sim.id} paused again due to quota.")
                        else:
                            print(f"[Resume Worker] Sim {sim.id} completed successfully!")
                            
                    except Exception as e:
                        print(f"[Resume Worker] Error resuming sim {sim.id}: {e}")
                        
        except asyncio.CancelledError:
            print("[Resume Worker] Task cancelled. Shutting down gracefully.")
            break
        except Exception as e:
            print(f"[Resume Worker] Unexpected error in worker loop: {e}")
            await asyncio.sleep(60) # Sleep on error to prevent tight crash loop
