"""Database tables for CareerGPS.

Every portfolio record hangs off a Portfolio, and every Portfolio belongs to exactly
one User. Deleting a user cascades down to everything they own.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base

# JSONB on Postgres (Supabase), plain JSON on SQLite for local dev and tests.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["Portfolio"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class Portfolio(TimestampMixin, Base):
    """Personal information (R3) plus sharing settings (R17)."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    headline: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    profile_image_url: Mapped[str | None] = mapped_column(String(1000))
    career_interests: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)

    user: Mapped[User] = relationship(back_populates="portfolio")
    links: Mapped[list["PortfolioLink"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="PortfolioLink.id",
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Education.graduation_date.desc(), Education.id",
    )
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Skill.category, Skill.name",
    )
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Experience.start_date.desc(), Experience.id",
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Project.display_order, Project.id.desc()",
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Certificate.issue_year.desc(), Certificate.id",
    )
    job_preferences: Mapped[list["JobPreference"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="JobPreference.id",
    )
    guidance: Mapped[list["CareerGuidance"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="CareerGuidance.id.desc()",
    )


class PortfolioLink(Base):
    """External professional profiles / personal websites (R3.5)."""

    __tablename__ = "portfolio_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="links")


class Education(TimestampMixin, Base):
    """Education records (R4)."""

    __tablename__ = "education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(200))
    major: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    graduation_date: Mapped[date | None] = mapped_column(Date)
    gpa: Mapped[str | None] = mapped_column(String(20))
    coursework: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="education")


class Skill(TimestampMixin, Base):
    """Skills (R5). `category` groups them, e.g. technical / communication (R5.5)."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(30), default="other", nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(30))

    portfolio: Mapped[Portfolio] = relationship(back_populates="skills")


class Experience(TimestampMixin, Base):
    """Work, internship, volunteer, academic, or other experience (R6)."""

    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    experience_type: Mapped[str] = mapped_column(String(30), default="work", nullable=False)
    organization: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    portfolio: Mapped[Portfolio] = relationship(back_populates="experiences")


class Certificate(TimestampMixin, Base):
    """Certifications and licenses (Account Setup page). Shown on shared portfolios."""

    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(200))
    issue_year: Mapped[int | None] = mapped_column(Integer)
    credential_url: Mapped[str | None] = mapped_column(String(1000))

    portfolio: Mapped[Portfolio] = relationship(back_populates="certificates")


class JobPreference(TimestampMixin, Base):
    """The kinds of jobs a student is looking for (Account Setup page).

    Private: only the owner sees these. Never included in shared portfolios, and
    salary/location are not sent to the AI service.
    """

    __tablename__ = "job_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[str | None] = mapped_column(String(30))
    min_salary: Mapped[int | None] = mapped_column(Integer)

    portfolio: Mapped[Portfolio] = relationship(back_populates="job_preferences")


class Project(TimestampMixin, Base):
    """Portfolio projects (R7).

    `description` is the plain-text summary. `content_blocks` holds the frontend's
    rich description editor output (headings / paragraphs / lists) as-is.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content_blocks: Mapped[list[dict]] = mapped_column(JSONType, default=list, nullable=False)
    project_date: Mapped[str | None] = mapped_column(String(100))
    subject: Mapped[str | None] = mapped_column(String(200))
    technologies: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="projects")
    media: Mapped[list["ProjectMedia"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True,
        order_by="ProjectMedia.display_order, ProjectMedia.id",
    )
    model_3d: Mapped["ProjectModel | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class ProjectMedia(Base):
    """Images and external links attached to a project (R8).

    `media_type` is "image" or "link". `storage_path` is set only for files we host,
    so we know to delete the stored object when the media is removed.
    """

    __tablename__ = "project_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200))
    link_type: Mapped[str | None] = mapped_column(String(30))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="media")


class ProjectModel(Base):
    """The interactive 3D model attached to a project (R15). At most one per project."""

    __tablename__ = "project_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="model_3d")


class CareerGuidance(Base):
    """One saved AI career analysis (R10–R14). Refreshing creates a new row, so
    the history of analyses is kept and the newest one is "current"."""

    __tablename__ = "career_guidance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    career_paths: Mapped[list[dict]] = mapped_column(JSONType, default=list, nullable=False)
    strengths: Mapped[list[dict]] = mapped_column(JSONType, default=list, nullable=False)
    improvements: Mapped[list[dict]] = mapped_column(JSONType, default=list, nullable=False)
    next_steps: Mapped[list[dict]] = mapped_column(JSONType, default=list, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped[Portfolio] = relationship(back_populates="guidance")


class CareerChatMessage(Base):
    __tablename__ = "career_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Verified learning resources shown with an assistant reply (P1).
    resources: Mapped[list[dict] | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class CareerRoadmap(Base):
    __tablename__ = "career_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    goals: Mapped[list[dict]] = mapped_column(
        JSONType,
        default=list,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    # Fingerprint of the portfolio the approved proposal was generated from;
    # NULL for roadmaps approved before P1 or written by the owner (unknown).
    portfolio_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RoadmapProposal(Base):
    __tablename__ = "roadmap_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    goals: Mapped[list[dict]] = mapped_column(
        JSONType,
        default=list,
        nullable=False
    )
    # pending | approved | rejected | superseded (a newer draft replaced it)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )
    # "auto" (generated when the Roadmap page opened) or "chat"; NULL before P1.
    origin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    portfolio_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class AIUsageEvent(Base):
    """One billed AI call: used for per-student rate limits and cost review.

    Stores counts only, never prompts, messages, or portfolio content.
    """

    __tablename__ = "ai_usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # chat | roadmap
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    web_searches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # completed | incomplete (cut off) | invalid (unusable output) | failed
    # (no response, e.g. API error); NULL for rows written before it existed.
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

