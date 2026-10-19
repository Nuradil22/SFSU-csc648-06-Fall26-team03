"""Shared FastAPI dependencies: who is calling, and which portfolio they own."""

from typing import TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.orm import Session

from . import models, security
from .database import Base, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

ModelT = TypeVar("ModelT", bound=Base)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = db.get(models.User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def ensure_portfolio(db: Session, user: models.User) -> models.Portfolio:
    """Every user has exactly one portfolio. Accounts created before portfolios
    existed get theirs created the first time they need it."""
    if user.portfolio is None:
        user.portfolio = models.Portfolio(career_interests=[])
        db.commit()
        db.refresh(user)
    return user.portfolio


def get_current_portfolio(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> models.Portfolio:
    return ensure_portfolio(db, user)


def get_owned(db: Session, model: type[ModelT], item_id: int, portfolio: models.Portfolio) -> ModelT:
    """Fetch a portfolio record by id, but only if it belongs to the caller (R2.5).

    Records owned by someone else return 404, not 403, so ids of other students'
    records can't be probed.
    """
    item = db.get(model, item_id)
    if item is None or getattr(item, "portfolio_id", None) != portfolio.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return item


def apply_updates(item: Base, updates: dict) -> None:
    for field, value in updates.items():
        setattr(item, field, value)


def check_date_range(start, end, end_label: str = "End date") -> None:
    if start and end and end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{end_label} cannot be before the start date"
        )
