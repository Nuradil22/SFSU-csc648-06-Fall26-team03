"""Read-only portfolio views for visitors with a share link (R17).

No login is required (R17.2), and this router only exposes GET endpoints, so
visitors cannot change anything (R17.5).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/public/portfolios", tags=["public"])

NOT_AVAILABLE = "This portfolio is not available. The link may be wrong or sharing may have been turned off."


def _shared_portfolio(db: Session, share_token: str) -> models.Portfolio:
    portfolio = db.query(models.Portfolio).filter(models.Portfolio.share_token == share_token).first()
    if portfolio is None or not portfolio.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_AVAILABLE)
    return portfolio


@router.get("/{share_token}", response_model=schemas.PublicPortfolioOut)
def view_shared_portfolio(share_token: str, db: Session = Depends(get_db)):
    """R17.3, R17.4: background, education, skills, experience, and projects
    (with images, links, and 3D models). The owner's email is never included."""
    portfolio = _shared_portfolio(db, share_token)
    return schemas.PublicPortfolioOut.model_validate(
        {
            **{field: getattr(portfolio, field) for field in schemas.PublicPortfolioOut.model_fields
               if hasattr(portfolio, field)},
            "name": portfolio.user.name,
        },
        from_attributes=True,
    )


@router.get("/{share_token}/projects/{project_id}", response_model=schemas.ProjectOut)
def view_shared_project(share_token: str, project_id: int, db: Session = Depends(get_db)):
    """A single project page (R16.1), e.g. to load its 3D model."""
    portfolio = _shared_portfolio(db, share_token)
    project = db.get(models.Project, project_id)
    if project is None or project.portfolio_id != portfolio.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
