"""Reports API endpoints — generate and retrieve simulation reports."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.simulation import Simulation, SimulationResponse as SimRespModel
from app.models.persona import Persona
from app.models.report import Report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports for the current user."""
    result = await db.execute(
        select(Report).where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return {
        "reports": [
            {
                "id": r.id,
                "title": r.title,
                "simulation_id": r.simulation_id,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        "total": len(reports),
    }


@router.post("/generate/{simulation_id}")
async def generate_report(
    simulation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a structured report for a completed simulation."""
    # Get simulation
    result = await db.execute(
        select(Simulation).where(
            Simulation.id == simulation_id,
            Simulation.user_id == current_user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if simulation.status != "completed":
        raise HTTPException(status_code=400, detail="Simulation must be completed before generating a report")

    # Get all responses
    resp_result = await db.execute(
        select(SimRespModel).where(SimRespModel.simulation_id == simulation_id)
    )
    responses = resp_result.scalars().all()

    analytics = json.loads(simulation.results_summary) if simulation.results_summary else {}

    # Build executive summary
    total = analytics.get("total_responses", len(responses))
    positive_rate = analytics.get("positive_rate", 0)
    avg_confidence = analytics.get("avg_confidence", 0)
    avg_sentiment = analytics.get("avg_sentiment", 0)

    sentiment_label = "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "neutral"
    decision_breakdown = analytics.get("decision_breakdown", {})
    top_decision = max(decision_breakdown, key=decision_breakdown.get) if decision_breakdown else "neutral"

    exec_summary = (
        f"This {simulation.type} simulation surveyed {total} synthetic Indian personas about: "
        f'"{simulation.question}". '
        f"Overall sentiment was {sentiment_label} with an average confidence of {avg_confidence:.0%}. "
        f"{positive_rate}% of respondents gave a positive/accepting response. "
        f"The most common response decision was '{top_decision}'."
    )

    # Collect sample responses (top 10 by confidence)
    sample_responses = []
    sorted_resps = sorted(responses, key=lambda r: r.confidence or 0, reverse=True)[:10]
    for resp in sorted_resps:
        persona_result = await db.execute(select(Persona).where(Persona.id == resp.persona_id))
        persona = persona_result.scalar_one_or_none()
        label = f"{persona.persona_id} ({persona.age}{persona.gender[0]}, {persona.city})" if persona else "Unknown"
        sample_responses.append({
            "persona_label": label,
            "response": resp.response,
            "sentiment": resp.sentiment,
            "confidence": resp.confidence,
            "decision": resp.decision,
        })

    # Build key insights
    insights = []
    demo = analytics.get("demographics", {})
    gender_data = demo.get("gender", {})
    if gender_data:
        top_gender = max(gender_data, key=gender_data.get)
        insights.append(f"Most respondents were {top_gender} ({gender_data[top_gender]} of {total})")

    age_data = demo.get("age_groups", {})
    if age_data:
        top_age = max(age_data, key=age_data.get)
        insights.append(f"Dominant age group: {top_age} ({age_data[top_age]} respondents)")

    income_data = demo.get("income", {})
    if income_data:
        top_income = max(income_data, key=income_data.get)
        insights.append(f"Most common income bracket: ₹{top_income}")

    sentiment_dist = analytics.get("sentiment_distribution", {})
    if sentiment_dist:
        positive = sentiment_dist.get("positive", 0)
        negative = sentiment_dist.get("negative", 0)
        if positive > negative:
            insights.append(f"Sentiment skews positive ({positive} vs {negative} negative responses)")
        elif negative > positive:
            insights.append(f"Sentiment skews negative ({negative} vs {positive} positive responses)")
        else:
            insights.append("Sentiment is evenly split between positive and negative")

    # Build recommendations
    recommendations = []
    if positive_rate >= 70:
        recommendations.append("Strong positive reception — consider moving forward with this scenario")
    elif positive_rate >= 50:
        recommendations.append("Mixed reception — refine the offering based on key objections identified")
    else:
        recommendations.append("Low acceptance rate — significant rethinking or repositioning may be needed")

    if avg_confidence < 0.4:
        recommendations.append("Low confidence scores indicate uncertainty — more research or clearer messaging may help")

    # Assemble full report content
    report_content = {
        "executive_summary": exec_summary,
        "key_metrics": {
            "total_responses": total,
            "positive_rate": positive_rate,
            "avg_confidence": round(avg_confidence, 3),
            "avg_sentiment": round(avg_sentiment, 3),
            "top_decision": top_decision,
        },
        "analytics": analytics,
        "key_insights": insights,
        "recommendations": recommendations,
        "sample_responses": sample_responses,
    }

    # Check if a report already exists for this simulation, update it
    existing_result = await db.execute(
        select(Report).where(
            Report.simulation_id == simulation_id,
            Report.user_id == current_user.id,
        )
    )
    existing_report = existing_result.scalar_one_or_none()

    if existing_report:
        existing_report.title = f"Report: {simulation.title}"
        existing_report.content = json.dumps(report_content)
        await db.commit()
        await db.refresh(existing_report)
        report = existing_report
    else:
        report = Report(
            user_id=current_user.id,
            simulation_id=simulation_id,
            title=f"Report: {simulation.title}",
            content=json.dumps(report_content),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

    return {
        "id": report.id,
        "title": report.title,
        "simulation_id": simulation_id,
        "created_at": report.created_at.isoformat(),
        "content": report_content,
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific report."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = json.loads(report.content) if report.content else {}

    return {
        "id": report.id,
        "title": report.title,
        "simulation_id": report.simulation_id,
        "created_at": report.created_at.isoformat(),
        "content": content,
    }


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    await db.commit()
    return {"message": "Report deleted"}
