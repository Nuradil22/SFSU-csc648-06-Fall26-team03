from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import apply_updates, get_current_portfolio, get_owned

router = APIRouter(prefix="/portfolio/me/skills", tags=["skills"])


def _ensure_unique(db: Session, portfolio: models.Portfolio, name: str, exclude_id: int | None = None) -> None:
    query = db.query(models.Skill).filter(
        models.Skill.portfolio_id == portfolio.id, func.lower(models.Skill.name) == name.lower()
    )
    if exclude_id is not None:
        query = query.filter(models.Skill.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Skill '{name}' is already in your portfolio")


@router.get("", response_model=list[schemas.SkillOut])
def list_skills(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """R5.4"""
    return portfolio.skills


@router.post("", response_model=schemas.SkillOut, status_code=status.HTTP_201_CREATED)
def add_skill(
    payload: schemas.SkillCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R5.1, R5.5: add a skill, optionally in a category (technical, communication, ...)."""
    _ensure_unique(db, portfolio, payload.name)
    skill = models.Skill(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.patch("/{skill_id}", response_model=schemas.SkillOut)
def update_skill(
    skill_id: int,
    payload: schemas.SkillUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R5.2"""
    skill = get_owned(db, models.Skill, skill_id, portfolio)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        _ensure_unique(db, portfolio, updates["name"], exclude_id=skill.id)
    apply_updates(skill, updates)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R5.3"""
    db.delete(get_owned(db, models.Skill, skill_id, portfolio))
    db.commit()
