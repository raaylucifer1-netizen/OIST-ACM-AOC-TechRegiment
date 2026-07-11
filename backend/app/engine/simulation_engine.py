"""Simulation Engine — orchestrates multi-agent simulations with smart sampling."""

import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.persona import Persona
from app.models.simulation import Simulation, SimulationResponse
from app.response_agent.response_agent import ResponseGenerationAgent
from app.response_agent.retry_manager import QuotaExceededError


async def select_persona_sample(
    db: AsyncSession,
    user_id: str,
    sample_size: int,
    filters: dict | None = None,
    project_id: str | None = None,
    exclude_ids: set[str] | None = None,
) -> list[Persona]:
    """Select a representative sample of personas with optional filtering."""
    query = select(Persona).where(Persona.user_id == user_id)
    
    if exclude_ids:
        query = query.where(Persona.id.notin_(exclude_ids))

    if project_id:
        query = query.where(Persona.project_id == project_id)

    if filters:
        if filters.get("gender"):
            query = query.where(Persona.gender == filters["gender"])
        if filters.get("state"):
            query = query.where(Persona.state == filters["state"])
        if filters.get("city"):
            query = query.where(Persona.city == filters["city"])
        if filters.get("age_min"):
            query = query.where(Persona.age >= filters["age_min"])
        if filters.get("age_max"):
            query = query.where(Persona.age <= filters["age_max"])
        if filters.get("income_min"):
            query = query.where(Persona.income_inr >= filters["income_min"])
        if filters.get("income_max"):
            query = query.where(Persona.income_inr <= filters["income_max"])
        if filters.get("education"):
            query = query.where(Persona.education == filters["education"])
        if filters.get("lifestyle"):
            query = query.where(Persona.lifestyle == filters["lifestyle"])
        if filters.get("technology_adoption"):
            query = query.where(Persona.technology_adoption == filters["technology_adoption"])
        if filters.get("food_preference"):
            query = query.where(Persona.food_preference == filters["food_preference"])

    # Get all matching personas, then random sample
    result = await db.execute(query)
    all_personas = list(result.scalars().all())

    if len(all_personas) <= sample_size:
        return all_personas

    return random.sample(all_personas, sample_size)


async def run_simulation_stream(
    db: AsyncSession,
    simulation: Simulation,
    personas: list[Persona],
    batch_size: int = 10,
):
    """Run a simulation and yield responses as they complete (Server-Sent Events)."""
    # Find completed personas to resume
    completed_query = select(SimulationResponse.persona_id).where(SimulationResponse.simulation_id == simulation.id)
    completed_result = await db.execute(completed_query)
    completed_ids = set(completed_result.scalars().all())
    
    pending_personas = [p for p in personas if p.id not in completed_ids]
    
    # Load all existing responses for analytics aggregation later
    existing_resp_query = select(SimulationResponse).where(SimulationResponse.simulation_id == simulation.id)
    existing_resp_result = await db.execute(existing_resp_query)
    all_responses_db = list(existing_resp_result.scalars().all())
    
    all_responses_dicts = [
        {
            "sentiment": r.sentiment,
            "decision": r.decision,
            "confidence": r.confidence,
            "persona_id": r.persona_id
        }
        for r in all_responses_db
    ]

    total = len(pending_personas)
    
    if total == 0 and len(personas) > 0:
        # Already completed
        analytics = aggregate_results_dicts(all_responses_dicts, personas)
        simulation.status = "completed"
        simulation.completed_at = datetime.now(timezone.utc)
        simulation.results_summary = json.dumps(analytics)
        await db.commit()
        yield {"analytics": analytics}
        return

    is_paused = False

    for i in range(0, total, batch_size):
        batch = pending_personas[i:i + batch_size]
        
        async def process_persona(p: Persona):
            agent = ResponseGenerationAgent(db, simulation, p)
            res = await agent.generate_response()
            return p, res
            
        tasks = [process_persona(p) for p in batch]

        try:
            # wait for the batch to finish
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            for persona, response_dict in batch_results:
                sim_response = SimulationResponse(
                    simulation_id=simulation.id,
                    persona_id=persona.id,
                    response=response_dict.get("reason", ""),
                    sentiment=response_dict.get("sentiment", 0.0),
                    confidence=response_dict.get("confidence", 0),
                    decision=response_dict.get("decision", "neutral"),
                    metadata_json=json.dumps(response_dict),
                )
                db.add(sim_response)
                
                # Append for analytics
                all_responses_dicts.append({
                    "sentiment": sim_response.sentiment,
                    "decision": sim_response.decision,
                    "confidence": sim_response.confidence,
                    "persona_id": sim_response.persona_id
                })
                
                await db.flush()
                
                yield {
                    "persona_id": persona.id,
                    "persona_label": f"{persona.persona_id} ({persona.age}{persona.gender[0]}, {persona.city})",
                    "response": sim_response.response,
                    "confidence": sim_response.confidence,
                    "decision": sim_response.decision
                }
                
        except QuotaExceededError as e:
            print(f"[Simulation Paused] Quota exceeded during stream: {e}")
            simulation.status = "paused"
            await db.commit()
            yield {"status": "paused", "error": "Quota Exceeded. Simulation paused and will resume automatically."}
            is_paused = True
            break
        except Exception as e:
            print(f"[Simulation Error]: {e}")
            # If an unexpected error occurs, mark paused to avoid losing progress
            simulation.status = "paused"
            await db.commit()
            yield {"status": "paused", "error": f"Unexpected error: {str(e)}"}
            is_paused = True
            break
            
        if i + batch_size < total:
            await asyncio.sleep(1.0) # Rate limiting pause

    if not is_paused:
        analytics = aggregate_results_dicts(all_responses_dicts, personas)
        simulation.status = "completed"
        simulation.completed_at = datetime.now(timezone.utc)
        simulation.results_summary = json.dumps(analytics)
        await db.commit()
        yield {"analytics": analytics}


async def run_simulation(
    db: AsyncSession,
    simulation: Simulation,
    personas: list[Persona],
    batch_size: int = 10,
) -> dict:
    """Run a simulation across multiple persona agents synchronously."""
    completed_query = select(SimulationResponse.persona_id).where(SimulationResponse.simulation_id == simulation.id)
    completed_result = await db.execute(completed_query)
    completed_ids = set(completed_result.scalars().all())
    
    pending_personas = [p for p in personas if p.id not in completed_ids]
    
    existing_resp_query = select(SimulationResponse).where(SimulationResponse.simulation_id == simulation.id)
    existing_resp_result = await db.execute(existing_resp_query)
    all_responses_db = list(existing_resp_result.scalars().all())
    
    all_responses_dicts = [
        {
            "sentiment": r.sentiment,
            "decision": r.decision,
            "confidence": r.confidence,
            "persona_id": r.persona_id
        }
        for r in all_responses_db
    ]

    total = len(pending_personas)
    if total == 0 and len(personas) > 0:
        return aggregate_results_dicts(all_responses_dicts, personas)

    is_paused = False

    for i in range(0, total, batch_size):
        batch = pending_personas[i:i + batch_size]
        
        async def process_persona(p: Persona):
            agent = ResponseGenerationAgent(db, simulation, p)
            res = await agent.generate_response()
            return p, res

        tasks = [process_persona(p) for p in batch]

        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            for persona, response_dict in batch_results:
                sim_response = SimulationResponse(
                    simulation_id=simulation.id,
                    persona_id=persona.id,
                    response=response_dict.get("reason", ""),
                    sentiment=response_dict.get("sentiment", 0.0),
                    confidence=response_dict.get("confidence", 0),
                    decision=response_dict.get("decision", "neutral"),
                    metadata_json=json.dumps(response_dict),
                )
                db.add(sim_response)
                
                all_responses_dicts.append({
                    "sentiment": sim_response.sentiment,
                    "decision": sim_response.decision,
                    "confidence": sim_response.confidence,
                    "persona_id": sim_response.persona_id
                })
                
            await db.flush()

        except QuotaExceededError as e:
            print(f"[Simulation Paused] Quota exceeded: {e}")
            simulation.status = "paused"
            await db.commit()
            is_paused = True
            return {"status": "paused", "reason": "Quota Exceeded"}
        except Exception as e:
            print(f"[Simulation Error]: {e}")
            simulation.status = "paused"
            await db.commit()
            is_paused = True
            return {"status": "paused", "reason": str(e)}

        if i + batch_size < total:
            await asyncio.sleep(1.0)

    if not is_paused:
        analytics = aggregate_results_dicts(all_responses_dicts, personas)
        simulation.status = "completed"
        simulation.completed_at = datetime.now(timezone.utc)
        simulation.results_summary = json.dumps(analytics)
        await db.commit()
        return analytics
    
    return {"status": "paused"}


def aggregate_results_dicts(responses: list[dict], personas: list[Persona]) -> dict:
    """Aggregate individual dict responses into simulation analytics."""
    if not responses:
        return {"error": "No responses collected"}

    sentiments = [r.get("sentiment", 0.0) for r in responses]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    sentiment_dist = {
        "positive": len([s for s in sentiments if s > 0.2]),
        "neutral": len([s for s in sentiments if -0.2 <= s <= 0.2]),
        "negative": len([s for s in sentiments if s < -0.2]),
    }

    decisions = [r.get("decision", "neutral") for r in responses]
    decision_counts = {}
    for d in decisions:
        decision_counts[d] = decision_counts.get(d, 0) + 1

    confidences = [r.get("confidence", 0) for r in responses]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    persona_map = {p.id: p for p in personas}  # Using ID now, previously was persona_id
    gender_breakdown = {}
    age_breakdown = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56+": 0}
    state_breakdown = {}
    income_breakdown = {"<5L": 0, "5-10L": 0, "10-20L": 0, "20-50L": 0, "50L+": 0}

    for resp in responses:
        # Changed from p.persona_id to p.id indexing
        persona = persona_map.get(resp.get("persona_id"))
        if not persona:
            continue

        gender_breakdown[persona.gender] = gender_breakdown.get(persona.gender, 0) + 1

        if persona.age <= 25:
            age_breakdown["18-25"] += 1
        elif persona.age <= 35:
            age_breakdown["26-35"] += 1
        elif persona.age <= 45:
            age_breakdown["36-45"] += 1
        elif persona.age <= 55:
            age_breakdown["46-55"] += 1
        else:
            age_breakdown["56+"] += 1

        state_breakdown[persona.state] = state_breakdown.get(persona.state, 0) + 1

        income_lakhs = persona.income_inr / 100000
        if income_lakhs < 5:
            income_breakdown["<5L"] += 1
        elif income_lakhs < 10:
            income_breakdown["5-10L"] += 1
        elif income_lakhs < 20:
            income_breakdown["10-20L"] += 1
        elif income_lakhs < 50:
            income_breakdown["20-50L"] += 1
        else:
            income_breakdown["50L+"] += 1

    positive_decisions = sum(1 for d in decisions if d in ("yes", "stay", "persuaded", "support"))
    decision_rate = positive_decisions / len(decisions) if decisions else 0

    return {
        "total_responses": len(responses),
        "avg_sentiment": round(avg_sentiment, 3),
        "sentiment_distribution": sentiment_dist,
        "decision_breakdown": decision_counts,
        "positive_rate": round(decision_rate * 100, 1),
        "avg_confidence": round(avg_confidence, 3),
        "demographics": {
            "gender": gender_breakdown,
            "age_groups": age_breakdown,
            "states": dict(sorted(state_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]),
            "income": income_breakdown,
        },
    }
