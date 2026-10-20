from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from .. import models, schemas, storage
from ..config import settings
from ..database import get_db
from ..deps import apply_updates, get_current_portfolio, get_owned

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_media(db: Session, project: models.Project, media_id: int) -> models.ProjectMedia:
    media = db.get(models.ProjectMedia, media_id)
    if media is None or media.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    return media


# --- Projects (R7) -----------------------------------------------------------

@router.get("", response_model=list[schemas.ProjectSearchOut])
def browse_projects(
    search: str | None = Query(None, max_length=100, description="Keywords matched against title, description, category, and technologies"),
    category: str | None = Query(None, max_length=200, description="Exact category (the project's `subject`), case-insensitive"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Public browse/search over stored projects. No login needed.

    Only projects from portfolios whose owner turned sharing on are returned (NFR4).
    Every keyword in `search` must appear somewhere in the project, e.g.
    `/projects?search=robot python` finds projects mentioning both words.
    Newest first.
    """
    query = (
        db.query(models.Project)
        .join(models.Portfolio)
        .join(models.User)
        .filter(models.Portfolio.is_public.is_(True))
    )
    for word in (search or "").split():
        word = word.lower()
        query = query.filter(
            or_(
                func.lower(models.Project.title).contains(word, autoescape=True),
                func.lower(models.Project.description).contains(word, autoescape=True),
                func.lower(models.Project.subject).contains(word, autoescape=True),
                func.lower(cast(models.Project.technologies, String)).contains(word, autoescape=True),
            )
        )
    if category and category.strip():
        query = query.filter(func.lower(models.Project.subject) == category.strip().lower())

    projects = query.order_by(models.Project.id.desc()).offset(offset).limit(limit).all()
    return [
        schemas.ProjectSearchOut(
            **schemas.ProjectOut.model_validate(p).model_dump(),
            owner_name=p.portfolio.user.name,
            share_token=p.portfolio.share_token,
        )
        for p in projects
    ]


@router.get("/mine", response_model=list[schemas.ProjectOut])
def list_my_projects(portfolio: models.Portfolio = Depends(get_current_portfolio)):
    """R7.5: all of the logged-in student's projects, shared or not."""
    return portfolio.projects


@router.post("", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: schemas.ProjectCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R7.1–R7.3: title, description (plain and/or editor blocks), date, subject, technologies."""
    project = models.Project(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    return get_owned(db, models.Project, project_id, portfolio)


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R7.4"""
    project = get_owned(db, models.Project, project_id, portfolio)
    apply_updates(project, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    project = get_owned(db, models.Project, project_id, portfolio)
    stored_files = [m.storage_path for m in project.media]
    if project.model_3d:
        stored_files.append(project.model_3d.storage_path)
    db.delete(project)
    db.commit()
    for path in stored_files:
        storage.remove_file(path)


# --- Images and links (R8) ---------------------------------------------------

@router.post("/{project_id}/images", response_model=schemas.ImageOut, status_code=status.HTTP_201_CREATED)
def upload_image(
    project_id: int,
    file: UploadFile = File(..., description="JPEG, PNG, GIF, or WebP"),
    label: str | None = Form(None, max_length=200, description="Caption / alt text"),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R8.1: upload an image file and attach it to the project."""
    project = get_owned(db, models.Project, project_id, portfolio)
    data = storage.read_upload(file, settings.max_image_mb)
    ext = storage.detect_image_format(data)
    path = storage.new_object_path(f"projects/{project.id}/images", ext)
    url = storage.store_file(path, data, storage.IMAGE_CONTENT_TYPES[ext])

    media = models.ProjectMedia(
        project_id=project.id, media_type="image", url=url, storage_path=path,
        label=(label or "").strip() or None, display_order=len(project.media),
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.post("/{project_id}/images/url", response_model=schemas.ImageOut, status_code=status.HTTP_201_CREATED)
def add_image_url(
    project_id: int,
    payload: schemas.ImageCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R8.1: attach an image that's already hosted elsewhere."""
    project = get_owned(db, models.Project, project_id, portfolio)
    media = models.ProjectMedia(
        project_id=project.id, media_type="image", display_order=len(project.media), **payload.model_dump()
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.post("/{project_id}/links", response_model=schemas.ProjectLinkOut, status_code=status.HTTP_201_CREATED)
def add_project_link(
    project_id: int,
    payload: schemas.LinkMediaCreate,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R8.2: link to a repository, demo video, or related resource."""
    project = get_owned(db, models.Project, project_id, portfolio)
    media = models.ProjectMedia(
        project_id=project.id, media_type="link", display_order=len(project.media), **payload.model_dump()
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.delete("/{project_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_media(
    project_id: int,
    media_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R8.4: remove an image or link (uploaded files are deleted from storage too)."""
    project = get_owned(db, models.Project, project_id, portfolio)
    media = _get_media(db, project, media_id)
    path = media.storage_path
    db.delete(media)
    db.commit()
    storage.remove_file(path)


# --- 3D model (R15) ----------------------------------------------------------

@router.put("/{project_id}/model", response_model=schemas.ModelOut)
def attach_model(
    project_id: int,
    file: UploadFile = File(..., description=f"3D model ({storage.SUPPORTED_MODEL_FORMATS})"),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R15.1–R15.3, R15.5: attach (or replace) the project's 3D model. Only .glb and
    self-contained .gltf files are accepted; anything else returns 400."""
    project = get_owned(db, models.Project, project_id, portfolio)
    data = storage.read_upload(file, settings.max_model_mb)
    ext = storage.detect_model_format(data, file.filename)
    path = storage.new_object_path(f"projects/{project.id}/models", ext)
    url = storage.store_file(path, data, storage.MODEL_CONTENT_TYPES[ext])

    old_path = project.model_3d.storage_path if project.model_3d else None
    if project.model_3d:
        db.delete(project.model_3d)
        db.flush()
    project.model_3d = models.ProjectModel(
        url=url, file_format=ext, storage_path=path,
        original_filename=(file.filename or "")[:255] or None, file_size_bytes=len(data),
    )
    db.commit()
    db.refresh(project)
    storage.remove_file(old_path)
    return project.model_3d


@router.delete("/{project_id}/model", status_code=status.HTTP_204_NO_CONTENT)
def remove_model(
    project_id: int,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    """R15.4"""
    project = get_owned(db, models.Project, project_id, portfolio)
    if project.model_3d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This project has no 3D model")
    path = project.model_3d.storage_path
    db.delete(project.model_3d)
    db.commit()
    storage.remove_file(path)
