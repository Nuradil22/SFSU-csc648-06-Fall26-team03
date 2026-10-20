from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import apply_updates, get_current_portfolio, get_owned

router = APIRouter(prefix="/portfolio/me/certificates", tags=["certificates"])


@router.get("", response_model=list[schemas.CertificateOut])
def list_certificates(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    return portfolio.certificates


@router.post("", response_model=schemas.CertificateOut, status_code=status.HTTP_201_CREATED)
def add_certificate(
    payload: schemas.CertificateCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    certificate = models.Certificate(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate


@router.patch("/{certificate_id}", response_model=schemas.CertificateOut)
def update_certificate(
    certificate_id: int,
    payload: schemas.CertificateUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    certificate = get_owned(db, models.Certificate, certificate_id, portfolio)
    apply_updates(certificate, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(certificate)
    return certificate


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    certificate_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    db.delete(get_owned(db, models.Certificate, certificate_id, portfolio))
    db.commit()
