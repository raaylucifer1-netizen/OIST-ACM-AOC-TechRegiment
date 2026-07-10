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
from app.engine.agent import PersonaAgent, AgentResponse


async def select_persona_sample(
    db: AsyncSession,
    user_id: str,
    sample_size: int,
    filters: dict | None = None,
    project_id: str | None = None,
) -> list[Persona]:
    """Select a representative sample of personas with optional filtering."""
    query = select(Persona).where(Persona.user_id == user_id)

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
    batch_size: int = 20,
):
    """Run a simulation and yield responses as they complete (Server-Sent Events)."""
    all_responses: list[AgentResponse] = []
    total = len(personas)

    for i in range(0, total, batch_size):
        batch = personas[i:i + batch_size]
        
        # We need a wrapper to attach persona info to the result
        async def process_persona(p: Persona):
            agent = PersonaAgent(profile=p.to_profile_dict())
            res = await agent.respond(simulation.question, simulation.type)
            return p, res
            
        tasks = [process_persona(p) for p in batch]

        for coro in asyncio.as_completed(tasks):
            try:
                persona, response = await coro
                
                sim_response = SimulationResponse(
                    simulation_id=simulation.id,
                    persona_id=persona.id,
                    response=response.response,
                    sentiment=response.sentiment,
                    confidence=response.confidence,
                    decision=response.decision,
                    metadata_json=json.dumps(response.metadata),
                )
                db.add(sim_response)
                all_responses.append(response)
                
                # Flush individually to get it in DB, though optional if we just want to send SSE
                await db.flush()
                
                # Yield the JSON data for SSE
                yield {
                    "persona_id": persona.id,
                    "persona_label": f"{persona.persona_id} ({persona.age}{persona.gender[0]}, {persona.city})",
                    "response": response.response,
                    "confidence": response.confidence,
                    "decision": response.decision
                }
                
            except Exception as e:
                print(f"[Simulation Error]: {e}")
                
        # Optional small delay between batches
        if i + batch_size < total:
            await asyncio.sleep(0.5)

    analytics = aggregate_results(all_responses, personas)
    simulation.status = "completed"
    simulation.completed_at = datetime.now(timezone.utc)
    simulation.results_summary = json.dumps(analytics)
    await db.commit()
    
    # Yield final analytics
    yield {"analytics": analytics}


async def run_simulation(
    db: AsyncSession,
    simulation: Simulation,
    personas: list[Persona],
    batch_size: int = 20,
) -> dict:
    """Run a simulation across multiple persona agents.
    
    Processes personas in batches concurrently to manage API rate limits.
    Returns aggregated results.
    """
    all_responses: list[AgentResponse] = []
    total = len(personas)

    # Process in batches
    for i in range(0, total, batch_size):
        batch = personas[i:i + batch_size]
        
        # Create coroutines for this batch
        tasks = []
        for persona in batch:
            agent = PersonaAgent(profile=persona.to_profile_dict())
            tasks.append(agent.respond(simulation.question, simulation.type))

        # Run all agents in the batch concurrently
        batch_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process and save responses
        for persona, response in zip(batch, batch_responses):
            if isinstance(response, Exception):
                print(f"[Simulation Error] Persona {persona.persona_id}: {response}")
                continue
            
            # Save individual response
            sim_response = SimulationResponse(
                simulation_id=simulation.id,
                persona_id=persona.id,
                response=response.response,
                sentiment=response.sentiment,
                confidence=response.confidence,
                decision=response.decision,
                metadata_json=json.dumps(response.metadata),
            )
            db.add(sim_response)
            all_responses.append(response)

        # Flush to DB after each batch to persist progress incrementally
        await db.flush()

        # Small delay between batches to respect rate limits
        if i + batch_size < total:
            await asyncio.sleep(0.5)

    # Aggregate results
    analytics = aggregate_results(all_responses, personas)

    # Update simulation
    simulation.status = "completed"
    simulation.completed_at = datetime.now(timezone.utc)
    simulation.results_summary = json.dumps(analytics)

    await db.commit()

    return analytics


def aggregate_results(responses: list[AgentResponse], personas: list[Persona]) -> dict:
    """Aggregate individual responses into simulation analytics."""
    if not responses:
        return {"error": "No responses collected"}

    # Sentiment analysis
    sentiments = [r.sentiment for r in responses]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    sentiment_dist = {
        "positive": len([s for s in sentiments if s > 0.2]),
        "neutral": len([s for s in sentiments if -0.2 <= s <= 0.2]),
        "negative": len([s for s in sentiments if s < -0.2]),
    }

    # Decision breakdown
    decisions = [r.decision for r in responses]
    decision_counts = {}
    for d in decisions:
        decision_counts[d] = decision_counts.get(d, 0) + 1

    # Confidence
    confidences = [r.confidence for r in responses]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Demographic breakdown
    persona_map = {p.persona_id: p for p in personas}
    gender_breakdown = {}
    age_breakdown = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56+": 0}
    state_breakdown = {}
    income_breakdown = {"<5L": 0, "5-10L": 0, "10-20L": 0, "20-50L": 0, "50L+": 0}

    for resp in responses:
        persona = persona_map.get(resp.persona_id)
        if not persona:
            continue

        # Gender
        gender_breakdown[persona.gender] = gender_breakdown.get(persona.gender, 0) + 1

        # Age groups
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

        # State
        state_breakdown[persona.state] = state_breakdown.get(persona.state, 0) + 1

        # Income
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

    # Positive decision rate (for market simulations)
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
