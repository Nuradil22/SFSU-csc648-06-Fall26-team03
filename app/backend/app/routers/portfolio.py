import secrets

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..deps import apply_updates, get_current_portfolio, get_owned

router = APIRouter(prefix="/portfolio/me", tags=["portfolio"])


def share_url(portfolio: models.Portfolio) -> str | None:
    if not portfolio.is_public or not portfolio.share_token:
        return None
    return f"{settings.frontend_url.rstrip('/')}/p/{portfolio.share_token}"


def portfolio_out(portfolio: models.Portfolio) -> schemas.PortfolioOut:
    return schemas.PortfolioOut.model_validate(
        {
            **{field: getattr(portfolio, field) for field in schemas.PortfolioOut.model_fields
               if hasattr(portfolio, field)},
            "name": portfolio.user.name,
            "email": portfolio.user.email,
            "share_url": share_url(portfolio),
        }
    )


@router.get("", response_model=schemas.PortfolioOut)
def get_my_portfolio(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """R3.2, R9: the full portfolio (personal info, education, skills, experience, projects)."""
    return portfolio_out(portfolio)


@router.patch("", response_model=schemas.PortfolioOut)
def update_my_portfolio(
    payload: schemas.PortfolioUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R3.1, R3.3, R3.4: edit name, headline, bio, location, photo, career interests."""
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        portfolio.user.name = updates.pop("name")
    apply_updates(portfolio, updates)
    db.commit()
    db.refresh(portfolio)
    return portfolio_out(portfolio)


# --- External profile links (R3.5) -----------------------------------------

@router.get("/links", response_model=list[schemas.LinkOut])
def list_links(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    return portfolio.links


@router.post("/links", response_model=schemas.LinkOut, status_code=status.HTTP_201_CREATED)
def add_link(
    payload: schemas.LinkCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    link = models.PortfolioLink(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.patch("/links/{link_id}", response_model=schemas.LinkOut)
def update_link(
    link_id: int,
    payload: schemas.LinkUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    link = get_owned(db, models.PortfolioLink, link_id, portfolio)
    apply_updates(link, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(link)
    return link


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    link_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    db.delete(get_owned(db, models.PortfolioLink, link_id, portfolio))
    db.commit()


# --- Sharing (R17.1) ---------------------------------------------------------

def _share_out(portfolio: models.Portfolio) -> schemas.ShareOut:
    return schemas.ShareOut(
        is_public=portfolio.is_public,
        share_token=portfolio.share_token if portfolio.is_public else None,
        share_url=share_url(portfolio),
    )


@router.get("/share", response_model=schemas.ShareOut)
def get_share_link(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    return _share_out(portfolio)


@router.post("/share", response_model=schemas.ShareOut)
def enable_sharing(
    regenerate: bool = False,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """Make the portfolio viewable by link. The same link is reused unless
    `?regenerate=true` is passed, which invalidates the old link."""
    if regenerate or not portfolio.share_token:
        portfolio.share_token = secrets.token_urlsafe(16)
    portfolio.is_public = True
    db.commit()
    db.refresh(portfolio)
    return _share_out(portfolio)


@router.delete("/share", response_model=schemas.ShareOut)
def disable_sharing(portfolio: models.Portfolio = Depends(get_current_portfolio), db: Session = Depends(get_db)):
    """Turn the share link off. Turning it back on restores the same link."""
    portfolio.is_public = False
    db.commit()
    db.refresh(portfolio)
    return _share_out(portfolio)
