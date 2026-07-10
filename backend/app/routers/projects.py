"""Project API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.persona import Persona
from app.models.simulation import Simulation
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    result = await db.execute(
        select(Project).where(
            Project.user_id == current_user.id,
            Project.is_deleted == False,
        ).order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()

    responses = []
    for p in projects:
        persona_count = await db.execute(
            select(func.count(Persona.id)).where(Persona.project_id == p.id)
        )
        sim_count = await db.execute(
            select(func.count(Simulation.id)).where(Simulation.project_id == p.id)
        )
        responses.append(ProjectResponse(
            id=p.id, user_id=p.user_id, name=p.name,
            description=p.description, is_archived=p.is_archived,
            is_deleted=p.is_deleted, created_at=p.created_at,
            updated_at=p.updated_at,
            persona_count=persona_count.scalar() or 0,
            simulation_count=sim_count.scalar() or 0,
        ))

    return ProjectListResponse(projects=responses, total=len(responses))


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(user_id=current_user.id, name=req.name, description=req.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id, user_id=project.user_id, name=project.name,
        description=project.description, is_archived=project.is_archived,
        is_deleted=project.is_deleted, created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    req: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if req.name is not None:
        project.name = req.name
    if req.description is not None:
        project.description = req.description

    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id, user_id=project.user_id, name=project.name,
        description=project.description, is_archived=project.is_archived,
        is_deleted=project.is_deleted, created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_deleted = True
    await db.commit()
    return {"message": "Project deleted"}


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive/unarchive a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_archived = not project.is_archived
    await db.commit()
    return {"message": f"Project {'archived' if project.is_archived else 'unarchived'}"}
