"""Simulation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import json
import asyncio

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.simulation import Simulation, SimulationResponse as SimRespModel
from app.models.persona import Persona
from app.schemas.simulation import (
    SimulationCreate, SimulationResponse, SimulationResultFull,
    SimResponseItem, SimulationListResponse,
)
from app.engine.simulation_engine import select_persona_sample, run_simulation, run_simulation_stream

router = APIRouter(prefix="/simulations", tags=["Simulations"])


@router.get("", response_model=SimulationListResponse)
async def list_simulations(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all simulations for the current user."""
    query = select(Simulation).where(Simulation.user_id == current_user.id)
    if project_id:
        query = query.where(Simulation.project_id == project_id)
    query = query.order_by(Simulation.created_at.desc())

    result = await db.execute(query)
    sims = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Simulation.id)).where(Simulation.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    return SimulationListResponse(
        simulations=[SimulationResponse.model_validate(s) for s in sims],
        total=total,
    )


@router.post("", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    req: SimulationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and run a new simulation."""
    # Validate simulation type
    valid_types = [
        "market", "election", "product_launch", "pricing",
        "feature_test", "ad_test", "policy", "crisis", "brand", "interview",
    ]
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid simulation type. Must be one of: {valid_types}")

    # Create simulation record
    simulation = Simulation(
        user_id=current_user.id,
        project_id=req.project_id,
        type=req.type,
        title=req.title,
        question=req.question,
        sample_size=req.sample_size,
        config=json.dumps(req.config) if req.config else None,
        status="running",
    )
    db.add(simulation)
    await db.flush()

    # Select personas
    filters = req.config or {}
    personas = await select_persona_sample(
        db, current_user.id, req.sample_size, filters, req.project_id
    )

    if not personas:
        simulation.status = "failed"
        simulation.results_summary = json.dumps({"error": "No personas found matching filters"})
        await db.commit()
        raise HTTPException(status_code=400, detail="No personas found. Please import personas first.")

    # Run simulation
    try:
        await run_simulation(db, simulation, personas)
    except Exception as e:
        simulation.status = "failed"
        simulation.results_summary = json.dumps({"error": str(e)})
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

    await db.refresh(simulation)
    return SimulationResponse.model_validate(simulation)


@router.post("/stream", status_code=201)
async def create_simulation_stream(
    req: SimulationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and run a new simulation with streaming responses."""
    valid_types = [
        "market", "election", "product_launch", "pricing",
        "feature_test", "ad_test", "policy", "crisis", "brand", "interview",
    ]
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid simulation type. Must be one of: {valid_types}")

    simulation = Simulation(
        user_id=current_user.id,
        project_id=req.project_id,
        type=req.type,
        title=req.title,
        question=req.question,
        sample_size=req.sample_size,
        config=json.dumps(req.config) if req.config else None,
        status="running",
    )
    db.add(simulation)
    await db.flush()

    filters = req.config or {}
    personas = await select_persona_sample(
        db, current_user.id, req.sample_size, filters, req.project_id
    )

    if not personas:
        simulation.status = "failed"
        simulation.results_summary = json.dumps({"error": "No personas found matching filters"})
        await db.commit()
        raise HTTPException(status_code=400, detail="No personas found. Please import personas first.")

    async def event_generator():
        # Yield the simulation ID first so the client knows it
        yield f"data: {json.dumps({'simulation_id': simulation.id})}\n\n"
        
        try:
            async for data in run_simulation_stream(db, simulation, personas):
                yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@router.get("/{simulation_id}", response_model=SimulationResultFull)
async def get_simulation(
    simulation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get simulation results with individual responses and analytics."""
    result = await db.execute(
        select(Simulation).where(
            Simulation.id == simulation_id,
            Simulation.user_id == current_user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Get individual responses
    resp_result = await db.execute(
        select(SimRespModel).where(SimRespModel.simulation_id == simulation_id)
    )
    responses = resp_result.scalars().all()

    # Get persona labels for each response
    response_items = []
    for resp in responses:
        persona_result = await db.execute(select(Persona).where(Persona.id == resp.persona_id))
        persona = persona_result.scalar_one_or_none()
        label = f"{persona.persona_id} ({persona.age}{persona.gender[0]}, {persona.city})" if persona else "Unknown"

        response_items.append(SimResponseItem(
            persona_id=resp.persona_id,
            persona_label=label,
            response=resp.response,
            sentiment=resp.sentiment,
            confidence=resp.confidence,
            decision=resp.decision,
        ))

    analytics = json.loads(simulation.results_summary) if simulation.results_summary else {}

    return SimulationResultFull(
        simulation=SimulationResponse.model_validate(simulation),
        responses=response_items,
        analytics=analytics,
    )
