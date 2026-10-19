from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import apply_updates, check_date_range, get_current_portfolio, get_owned

router = APIRouter(prefix="/portfolio/me/education", tags=["education"])


@router.get("", response_model=list[schemas.EducationOut])
def list_education(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    return portfolio.education


@router.post("", response_model=schemas.EducationOut, status_code=status.HTTP_201_CREATED)
def add_education(
    payload: schemas.EducationCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R4.1, R4.2, R4.5: school, degree, major, graduation date, coursework."""
    check_date_range(payload.start_date, payload.graduation_date, "Graduation date")
    record = models.Education(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{education_id}", response_model=schemas.EducationOut)
def update_education(
    education_id: int,
    payload: schemas.EducationUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R4.3"""
    record = get_owned(db, models.Education, education_id, portfolio)
    apply_updates(record, payload.model_dump(exclude_unset=True))
    check_date_range(record.start_date, record.graduation_date, "Graduation date")
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education(
    education_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R4.4"""
    db.delete(get_owned(db, models.Education, education_id, portfolio))
    db.commit()
