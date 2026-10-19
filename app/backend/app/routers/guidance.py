from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import ai, models, schemas
from ..database import get_db
from ..deps import get_current_portfolio

router = APIRouter(prefix="/guidance", tags=["career guidance"])


@router.post("", response_model=schemas.GuidanceOut, status_code=status.HTTP_201_CREATED)
def analyze_portfolio(portfolio: models.Portfolio = Depends(get_current_portfolio), db: Session = Depends(get_db)):
    """R10–R13 (and R14 refresh): analyze the currently saved portfolio and return
    a summary, career paths, strengths, improvements, and next steps.

    Every call runs a fresh analysis on the latest saved data and stores it; earlier
    results are kept in the history. On failure nothing is saved, the previous
    result stays current, and a readable error is returned (R10.5, R14.4):
    400 if the portfolio is empty, 502/503 if the AI service fails.
    """
    payload = ai.build_portfolio_payload(portfolio)
    if not ai.has_enough_data(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add some education, skills, experience, or projects before requesting career guidance.",
        )

    try:
        content, provider, model_name = ai.generate_guidance(payload)
    except ai.AIServiceError as exc:
        code = status.HTTP_503_SERVICE_UNAVAILABLE if exc.unavailable else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(status_code=code, detail=f"Career analysis could not be completed. {exc.message}")

    guidance = models.CareerGuidance(
        portfolio_id=portfolio.id, provider=provider, model=model_name, **content.model_dump(mode="json")
    )
    db.add(guidance)
    db.commit()
    db.refresh(guidance)
    return guidance


@router.get("/latest", response_model=schemas.GuidanceOut)
def latest_guidance(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """R10.4: the most recent analysis."""
    if not portfolio.guidance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No career analysis yet")
    return portfolio.guidance[0]


@router.get("", response_model=list[schemas.GuidanceOut])
def guidance_history(limit: int = 10, portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """Past analyses, newest first."""
    return portfolio.guidance[: max(1, min(limit, 50))]
