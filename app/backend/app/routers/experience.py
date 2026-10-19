from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import apply_updates, check_date_range, get_current_portfolio, get_owned

router = APIRouter(prefix="/portfolio/me/experience", tags=["experience"])


def _normalize(record: models.Experience) -> None:
    check_date_range(record.start_date, record.end_date)
    if record.is_current:
        record.end_date = None


@router.get("", response_model=list[schemas.ExperienceOut])
def list_experience(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """R6.5"""
    return portfolio.experiences


@router.post("", response_model=schemas.ExperienceOut, status_code=status.HTTP_201_CREATED)
def add_experience(
    payload: schemas.ExperienceCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R6.1, R6.2: work / internship / volunteer / academic / research / other."""
    record = models.Experience(portfolio_id=portfolio.id, **payload.model_dump())
    _normalize(record)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{experience_id}", response_model=schemas.ExperienceOut)
def update_experience(
    experience_id: int,
    payload: schemas.ExperienceUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R6.3"""
    record = get_owned(db, models.Experience, experience_id, portfolio)
    apply_updates(record, payload.model_dump(exclude_unset=True))
    _normalize(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R6.4"""
    db.delete(get_owned(db, models.Experience, experience_id, portfolio))
    db.commit()
