from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Re-exported so existing imports of `routers.auth.get_current_user` keep working.
__all__ = ["router", "get_current_user"]


def _issue_token(user: models.User, message: str) -> schemas.Token:
    access_token = security.create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=access_token, user=user, message=message)


def _authenticate(db: Session, email: str, password: str) -> models.User:
    user = db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


@router.post("/signup", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """R1: register with name, email, password. Creates the user's empty portfolio too."""
    email = payload.email.lower()
    if db.query(models.User).filter(func.lower(models.User.email) == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=email,
        hashed_password=security.hash_password(payload.password),
    )
    user.portfolio = models.Portfolio(career_interests=[])
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(user, "Account created successfully")


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """R2.1–R2.3: log in with email and password (JSON body, used by the frontend)."""
    return _issue_token(_authenticate(db, payload.email, payload.password), "Logged in successfully")


@router.post("/token", response_model=schemas.Token, include_in_schema=True)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Same as /auth/login but takes form data, so the Swagger UI "Authorize" button
    works. Put the email in the "username" field."""
    return _issue_token(_authenticate(db, form.username, form.password), "Logged in successfully")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: models.User = Depends(get_current_user)):
    """R2.4. Tokens are stateless JWTs, so logging out means the client deletes its
    stored token. This endpoint exists so the frontend has one call to make and
    so an expired/invalid token is reported consistently."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user
