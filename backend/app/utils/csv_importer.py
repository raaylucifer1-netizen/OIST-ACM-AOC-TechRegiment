"""CSV/Excel import pipeline for persona data."""

import csv
import io
import openpyxl
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.persona import Persona
from typing import BinaryIO


EXPECTED_COLUMNS = [
    "persona_id", "age", "gender", "city", "state", "education", "occupation",
    "income_inr", "language", "marital_status", "children", "lifestyle",
    "shopping_frequency", "online_shopping_pct", "offline_shopping_pct",
    "payment_method", "vehicle", "technology_adoption", "health_consciousness",
    "food_preference", "political_interest", "social_media_usage", "brand_loyalty",
    "price_sensitivity", "risk_taking", "impulse_buying", "discount_preference",
    "premium_preference", "preferred_brand", "communication_style", "response_length",
    "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
    "confidence", "optimism", "patience", "curiosity", "practicality", "emotional_score",
]

INT_COLUMNS = [
    "age", "income_inr", "children", "online_shopping_pct", "offline_shopping_pct",
    "health_consciousness", "social_media_usage", "brand_loyalty", "price_sensitivity",
    "risk_taking", "impulse_buying", "discount_preference", "premium_preference",
    "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
    "confidence", "optimism", "patience", "curiosity", "practicality", "emotional_score",
]


async def import_csv(
    db: AsyncSession,
    file_content: bytes,
    filename: str,
    user_id: str,
    project_id: str | None = None,
) -> dict:
    """Import personas from a CSV or Excel file.
    
    Returns: {imported: int, failed: int, errors: list[str]}
    """
    errors = []
    imported = 0
    failed = 0

    try:
        rows = []
        headers = []

        # Read file
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            wb = openpyxl.load_workbook(filename=BytesIO(file_content), read_only=True, data_only=True)
            sheet = wb.active
            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(cell).strip().lower() if cell else "" for cell in row]
                else:
                    rows.append(row)
        else:
            # Assuming CSV
            try:
                text_content = file_content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text_content = file_content.decode("cp1252", errors="replace")
            reader = csv.reader(io.StringIO(text_content))
            for i, row in enumerate(reader):
                if i == 0:
                    headers = [str(cell).strip().lower() if cell else "" for cell in row]
                else:
                    rows.append(row)

        # Validate columns
        missing_cols = set(EXPECTED_COLUMNS) - set(headers)
        if missing_cols:
            return {
                "imported": 0,
                "failed": len(rows),
                "total": len(rows),
                "errors": [f"Missing columns: {', '.join(missing_cols)}"],
                "status": "failed",
            }

        # Find indices for expected columns
        col_indices = {col: headers.index(col) for col in EXPECTED_COLUMNS if col in headers}

        # Process rows
        batch = []
        for idx, row in enumerate(rows):
            try:
                persona_data = {}
                for col in EXPECTED_COLUMNS:
                    val = row[col_indices[col]] if col in col_indices and col_indices[col] < len(row) else None
                    if col in INT_COLUMNS:
                        try:
                            persona_data[col] = int(float(val)) if val and str(val).strip() != "" else 0
                        except ValueError:
                            persona_data[col] = 0
                    else:
                        persona_data[col] = str(val).strip() if val is not None and str(val).strip() != "" else ""

                persona = Persona(
                    user_id=user_id,
                    project_id=project_id,
                    **persona_data,
                )
                batch.append(persona)
                imported += 1

                # Batch insert every 500 rows
                if len(batch) >= 500:
                    db.add_all(batch)
                    await db.flush()
                    batch = []

            except Exception as e:
                failed += 1
                if len(errors) < 10:  # Cap error messages
                    errors.append(f"Row {idx + 2}: {str(e)}")

        # Insert remaining batch
        if batch:
            db.add_all(batch)
            await db.flush()

        await db.commit()

    except Exception as e:
        errors.append(f"File processing error: {str(e)}")
        return {
            "imported": 0,
            "failed": 0,
            "total": 0,
            "errors": errors,
            "status": "failed",
        }

    return {
        "imported": imported,
        "failed": failed,
        "total": imported + failed,
        "errors": errors,
        "status": "completed" if failed == 0 else "completed_with_errors",
    }


async def import_from_path(
    db: AsyncSession,
    filepath: str,
    user_id: str,
    project_id: str | None = None,
) -> dict:
    """Import personas from a file path (for initial seeding)."""
    with open(filepath, "rb") as f:
        content = f.read()
    filename = filepath.split("\\")[-1].split("/")[-1]
    return await import_csv(db, content, filename, user_id, project_id)
