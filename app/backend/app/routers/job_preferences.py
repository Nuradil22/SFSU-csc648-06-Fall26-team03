from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import apply_updates, get_current_portfolio, get_owned

# Private to the owner: never part of the public/shared portfolio.
router = APIRouter(prefix="/portfolio/me/job-preferences", tags=["job preferences"])


@router.get("", response_model=list[schemas.JobPreferenceOut])
def list_job_preferences(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    return portfolio.job_preferences


@router.post("", response_model=schemas.JobPreferenceOut, status_code=status.HTTP_201_CREATED)
def add_job_preference(
    payload: schemas.JobPreferenceCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    preference = models.JobPreference(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.patch("/{preference_id}", response_model=schemas.JobPreferenceOut)
def update_job_preference(
    preference_id: int,
    payload: schemas.JobPreferenceUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    preference = get_owned(db, models.JobPreference, preference_id, portfolio)
    apply_updates(preference, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(preference)
    return preference


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_preference(
    preference_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    db.delete(get_owned(db, models.JobPreference, preference_id, portfolio))
    db.commit()
