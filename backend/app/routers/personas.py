"""Persona API endpoints — CRUD, import, export, search, filter, stats."""

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import json

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.persona import Persona
from app.schemas.persona import (
    PersonaCreate, PersonaResponse, PersonaListResponse, PersonaStats, ImportProgress,
)
from app.utils.csv_importer import import_csv

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.get("", response_model=PersonaListResponse)
async def list_personas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    gender: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    income_min: Optional[int] = None,
    income_max: Optional[int] = None,
    education: Optional[str] = None,
    lifestyle: Optional[str] = None,
    technology_adoption: Optional[str] = None,
    food_preference: Optional[str] = None,
    political_interest: Optional[str] = None,
    search: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List personas with pagination and filtering."""
    query = select(Persona).where(Persona.user_id == current_user.id)
    count_query = select(func.count(Persona.id)).where(Persona.user_id == current_user.id)

    # Apply filters
    if project_id:
        query = query.where(Persona.project_id == project_id)
        count_query = count_query.where(Persona.project_id == project_id)
    if gender:
        query = query.where(Persona.gender == gender)
        count_query = count_query.where(Persona.gender == gender)
    if state:
        query = query.where(Persona.state == state)
        count_query = count_query.where(Persona.state == state)
    if city:
        query = query.where(Persona.city.ilike(f"%{city}%"))
        count_query = count_query.where(Persona.city.ilike(f"%{city}%"))
    if age_min:
        query = query.where(Persona.age >= age_min)
        count_query = count_query.where(Persona.age >= age_min)
    if age_max:
        query = query.where(Persona.age <= age_max)
        count_query = count_query.where(Persona.age <= age_max)
    if income_min:
        query = query.where(Persona.income_inr >= income_min)
        count_query = count_query.where(Persona.income_inr >= income_min)
    if income_max:
        query = query.where(Persona.income_inr <= income_max)
        count_query = count_query.where(Persona.income_inr <= income_max)
    if education:
        query = query.where(Persona.education == education)
        count_query = count_query.where(Persona.education == education)
    if lifestyle:
        query = query.where(Persona.lifestyle == lifestyle)
        count_query = count_query.where(Persona.lifestyle == lifestyle)
    if technology_adoption:
        query = query.where(Persona.technology_adoption == technology_adoption)
        count_query = count_query.where(Persona.technology_adoption == technology_adoption)
    if food_preference:
        query = query.where(Persona.food_preference == food_preference)
        count_query = count_query.where(Persona.food_preference == food_preference)
    if political_interest:
        query = query.where(Persona.political_interest == political_interest)
        count_query = count_query.where(Persona.political_interest == political_interest)
    if search:
        search_filter = or_(
            Persona.persona_id.ilike(f"%{search}%"),
            Persona.city.ilike(f"%{search}%"),
            Persona.occupation.ilike(f"%{search}%"),
            Persona.preferred_brand.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Persona.persona_id).offset(offset).limit(page_size)
    result = await db.execute(query)
    personas = result.scalars().all()

    return PersonaListResponse(
        personas=[PersonaResponse.model_validate(p) for p in personas],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", response_model=PersonaStats)
async def persona_stats(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate statistics for personas."""
    base_filter = Persona.user_id == current_user.id
    if project_id:
        base_filter = base_filter & (Persona.project_id == project_id)

    # Total count
    count_result = await db.execute(select(func.count(Persona.id)).where(base_filter))
    total = count_result.scalar() or 0

    if total == 0:
        return PersonaStats(
            total_personas=0, avg_age=0, gender_distribution={},
            state_distribution={}, income_distribution={},
            top_occupations=[], lifestyle_distribution={}, avg_big_five={},
        )

    # Average age
    avg_age_result = await db.execute(select(func.avg(Persona.age)).where(base_filter))
    avg_age = round(avg_age_result.scalar() or 0, 1)

    # Gender distribution
    gender_result = await db.execute(
        select(Persona.gender, func.count(Persona.id)).where(base_filter).group_by(Persona.gender)
    )
    gender_dist = {row[0]: row[1] for row in gender_result.all()}

    # State distribution (top 10)
    state_result = await db.execute(
        select(Persona.state, func.count(Persona.id)).where(base_filter)
        .group_by(Persona.state).order_by(func.count(Persona.id).desc()).limit(10)
    )
    state_dist = {row[0]: row[1] for row in state_result.all()}

    # Income distribution
    income_dist = {}
    for label, low, high in [("<5L", 0, 500000), ("5-10L", 500000, 1000000),
                              ("10-20L", 1000000, 2000000), ("20-50L", 2000000, 5000000),
                              ("50L+", 5000000, 100000000)]:
        r = await db.execute(
            select(func.count(Persona.id)).where(
                base_filter, Persona.income_inr >= low, Persona.income_inr < high
            )
        )
        income_dist[label] = r.scalar() or 0

    # Top occupations
    occ_result = await db.execute(
        select(Persona.occupation, func.count(Persona.id)).where(base_filter)
        .group_by(Persona.occupation).order_by(func.count(Persona.id).desc()).limit(10)
    )
    top_occs = [{"occupation": row[0], "count": row[1]} for row in occ_result.all()]

    # Lifestyle distribution
    life_result = await db.execute(
        select(Persona.lifestyle, func.count(Persona.id)).where(base_filter)
        .group_by(Persona.lifestyle)
    )
    lifestyle_dist = {row[0]: row[1] for row in life_result.all()}

    # Average Big Five
    avg_big_five = {}
    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        r = await db.execute(select(func.avg(getattr(Persona, trait))).where(base_filter))
        avg_big_five[trait] = round(r.scalar() or 0, 1)

    return PersonaStats(
        total_personas=total,
        avg_age=avg_age,
        gender_distribution=gender_dist,
        state_distribution=state_dist,
        income_distribution=income_dist,
        top_occupations=top_occs,
        lifestyle_distribution=lifestyle_dist,
        avg_big_five=avg_big_five,
    )


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single persona by ID."""
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == current_user.id)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaResponse.model_validate(persona)


@router.post("/import")
async def import_personas(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import personas from a CSV or Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    valid_extensions = (".csv", ".xlsx", ".xls")
    if not any(file.filename.endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel")

    content = await file.read()
    result = await import_csv(db, content, file.filename, current_user.id, project_id)
    return result


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a persona."""
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == current_user.id)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    await db.delete(persona)
    await db.commit()
    return {"message": "Persona deleted"}


@router.get("/filter-options/values")
async def get_filter_options(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get distinct values for filter dropdowns."""
    options = {}
    for field_name, col in [
        ("genders", Persona.gender),
        ("states", Persona.state),
        ("cities", Persona.city),
        ("educations", Persona.education),
        ("occupations", Persona.occupation),
        ("lifestyles", Persona.lifestyle),
        ("technology_adoptions", Persona.technology_adoption),
        ("food_preferences", Persona.food_preference),
        ("political_interests", Persona.political_interest),
        ("preferred_brands", Persona.preferred_brand),
    ]:
        result = await db.execute(
            select(col).where(Persona.user_id == current_user.id).distinct().order_by(col)
        )
        options[field_name] = [row[0] for row in result.all()]

    return options


@router.get("/{persona_id}/adjacent")
async def get_adjacent_personas(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get next and previous persona IDs relative to a given persona."""
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == current_user.id)
    )
    current_persona = result.scalar_one_or_none()
    if not current_persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Find previous persona (largest persona_id smaller than current)
    prev_result = await db.execute(
        select(Persona.id)
        .where(Persona.user_id == current_user.id, Persona.persona_id < current_persona.persona_id)
        .order_by(Persona.persona_id.desc())
        .limit(1)
    )
    prev_id = prev_result.scalar_one_or_none()

    # Find next persona (smallest persona_id larger than current)
    next_result = await db.execute(
        select(Persona.id)
        .where(Persona.user_id == current_user.id, Persona.persona_id > current_persona.persona_id)
        .order_by(Persona.persona_id.asc())
        .limit(1)
    )
    next_id = next_result.scalar_one_or_none()

    return {"prev_id": prev_id, "next_id": next_id}


@router.post("/import/from-server")
async def import_from_server_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import personas from the pre-loaded server CSV (D:\\AARU\\backend\\data\\personas_20000.csv)."""
    import os
    from app.utils.csv_importer import import_from_path

    # Try multiple known paths
    candidate_paths = [
        "./data/personas_20000.csv",
        "../data/personas_20000.csv",
    ]

    filepath = None
    for path in candidate_paths:
        if os.path.exists(path):
            filepath = path
            break

    if not filepath:
        raise HTTPException(
            status_code=404,
            detail="Server CSV not found. Please upload a CSV file instead.",
        )

    try:
        result = await import_from_path(db, filepath, current_user.id)
        return result
    except Exception as e:
        import traceback
        error_msg = f"Import failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete("/bulk/all")
async def delete_all_personas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete ALL personas for the current user (use with caution)."""
    from sqlalchemy import delete as sa_delete
    await db.execute(sa_delete(Persona).where(Persona.user_id == current_user.id))
    await db.commit()
    return {"message": "All personas deleted"}
