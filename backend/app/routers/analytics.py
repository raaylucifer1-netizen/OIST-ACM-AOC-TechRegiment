"""Analytics API endpoints — dashboard data and simulation analytics."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.persona import Persona
from app.models.simulation import Simulation, SimulationResponse
from app.models.conversation import Conversation
from app.models.report import Report

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview statistics."""
    # Total personas
    persona_count = await db.execute(
        select(func.count(Persona.id)).where(Persona.user_id == current_user.id)
    )
    total_personas = persona_count.scalar() or 0

    # Total simulations
    sim_count = await db.execute(
        select(func.count(Simulation.id)).where(Simulation.user_id == current_user.id)
    )
    total_simulations = sim_count.scalar() or 0

    # Completed simulations
    completed_count = await db.execute(
        select(func.count(Simulation.id)).where(
            Simulation.user_id == current_user.id,
            Simulation.status == "completed",
        )
    )
    completed_simulations = completed_count.scalar() or 0

    # Total conversations
    convo_count = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    )
    total_conversations = convo_count.scalar() or 0

    # Recent simulations
    recent_sims = await db.execute(
        select(Simulation).where(Simulation.user_id == current_user.id)
        .order_by(Simulation.created_at.desc()).limit(5)
    )
    recent = recent_sims.scalars().all()

    # Persona demographic breakdown for dashboard charts
    gender_result = await db.execute(
        select(Persona.gender, func.count(Persona.id))
        .where(Persona.user_id == current_user.id)
        .group_by(Persona.gender)
    )
    gender_dist = [{"name": row[0], "value": row[1]} for row in gender_result.all()]

    # Age distribution
    age_buckets = []
    for label, low, high in [("18-25", 18, 25), ("26-35", 26, 35), ("36-45", 36, 45), ("46-55", 46, 55), ("56+", 56, 999)]:
        r = await db.execute(
            select(func.count(Persona.id)).where(
                Persona.user_id == current_user.id,
                Persona.age >= low,
                Persona.age <= high,
            )
        )
        count = r.scalar() or 0
        if count > 0:
            age_buckets.append({"name": label, "value": count})

    # Top 5 states
    state_result = await db.execute(
        select(Persona.state, func.count(Persona.id))
        .where(Persona.user_id == current_user.id)
        .group_by(Persona.state)
        .order_by(func.count(Persona.id).desc())
        .limit(5)
    )
    top_states = [{"name": row[0], "value": row[1]} for row in state_result.all()]

    # Simulation type distribution
    sim_type_result = await db.execute(
        select(Simulation.type, func.count(Simulation.id))
        .where(Simulation.user_id == current_user.id)
        .group_by(Simulation.type)
    )
    sim_types = [{"name": row[0], "value": row[1]} for row in sim_type_result.all()]

    return {
        "total_personas": total_personas,
        "total_simulations": total_simulations,
        "completed_simulations": completed_simulations,
        "total_conversations": total_conversations,
        "recent_simulations": [
            {
                "id": s.id,
                "title": s.title,
                "type": s.type,
                "status": s.status,
                "sample_size": s.sample_size,
                "created_at": s.created_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in recent
        ],
        "charts": {
            "gender_distribution": gender_dist,
            "age_distribution": age_buckets,
            "top_states": top_states,
            "simulation_types": sim_types,
        },
    }


@router.get("/simulations/{simulation_id}/analytics")
async def get_simulation_analytics(
    simulation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed analytics for a specific simulation."""
    result = await db.execute(
        select(Simulation).where(
            Simulation.id == simulation_id,
            Simulation.user_id == current_user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    analytics = json.loads(simulation.results_summary) if simulation.results_summary else {}

    # Build chart-friendly data structures
    charts = {}

    if analytics:
        # Decision breakdown as bar chart data
        decision_data = analytics.get("decision_breakdown", {})
        charts["decisions"] = [{"name": k.capitalize(), "value": v} for k, v in decision_data.items()]

        # Sentiment pie
        sentiment_data = analytics.get("sentiment_distribution", {})
        charts["sentiment"] = [
            {"name": "Positive", "value": sentiment_data.get("positive", 0), "color": "#22c55e"},
            {"name": "Neutral", "value": sentiment_data.get("neutral", 0), "color": "#94a3b8"},
            {"name": "Negative", "value": sentiment_data.get("negative", 0), "color": "#ef4444"},
        ]

        # Demographics
        demo = analytics.get("demographics", {})
        charts["gender"] = [{"name": k, "value": v} for k, v in demo.get("gender", {}).items()]
        charts["age_groups"] = [{"name": k, "value": v} for k, v in demo.get("age_groups", {}).items()]
        charts["income"] = [{"name": k, "value": v} for k, v in demo.get("income", {}).items()]
        charts["states"] = [{"name": k, "value": v} for k, v in list(demo.get("states", {}).items())[:10]]

    return {
        "simulation_id": simulation_id,
        "title": simulation.title,
        "type": simulation.type,
        "sample_size": simulation.sample_size,
        "status": simulation.status,
        "analytics": analytics,
        "charts": charts,
    }
