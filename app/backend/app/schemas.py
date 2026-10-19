"""Request/response shapes for the API.

Naming convention: `XCreate` is a POST body, `XUpdate` is a PATCH body (every field
optional, only the fields sent are changed), `XOut` is what the API returns.
"""

import re
from datetime import date, datetime
from typing import Annotated, Any, ClassVar, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

# ---------------------------------------------------------------------------
# Shared field types
# ---------------------------------------------------------------------------

def _strip(value: str) -> str:
    return value.strip()


def _check_url(value: str) -> str:
    value = value.strip()
    if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", value, re.IGNORECASE):
        raise ValueError("Must be a valid http:// or https:// URL")
    return value


def _clean_str_list(values: list[str]) -> list[str]:
    """Strip, drop blanks, and de-duplicate (case-insensitive) while keeping order."""
    seen: set[str] = set()
    cleaned = []
    for value in values:
        value = value.strip()
        if value and value.lower() not in seen:
            seen.add(value.lower())
            cleaned.append(value)
    return cleaned


Text = Annotated[str, AfterValidator(_strip)]
Url = Annotated[str, Field(max_length=1000), AfterValidator(_check_url)]
TagList = Annotated[
    list[Annotated[str, Field(max_length=100)]], Field(max_length=50), AfterValidator(_clean_str_list)
]

SkillCategory = Literal["technical", "communication", "leadership", "professional", "language", "other"]
ExperienceType = Literal["work", "internship", "volunteer", "academic", "research", "other"]


class PartialUpdate(BaseModel):
    """Base for PATCH bodies: fields listed in `_required` may be omitted, but not set to null."""

    _required: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _reject_null_required(self):
        for field in self._required:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null")
        return self


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Auth (R1, R2)
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    name: Annotated[Text, Field(min_length=1, max_length=100)]
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        # R1.4 minimum security requirements. bcrypt only reads the first 72 bytes,
        # so longer passwords are rejected rather than silently truncated.
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    message: str = "Success"


# ---------------------------------------------------------------------------
# Portfolio personal info + links (R3)
# ---------------------------------------------------------------------------

class PortfolioUpdate(PartialUpdate):
    _required = ("name", "career_interests")

    name: Annotated[Text, Field(min_length=1, max_length=100)] | None = None
    headline: Annotated[Text, Field(max_length=200)] | None = None
    bio: Annotated[Text, Field(max_length=5000)] | None = None
    location: Annotated[Text, Field(max_length=200)] | None = None
    profile_image_url: Url | None = None
    career_interests: TagList | None = None


class LinkCreate(BaseModel):
    label: Annotated[Text, Field(min_length=1, max_length=100)]
    url: Url


class LinkUpdate(PartialUpdate):
    _required = ("label", "url")

    label: Annotated[Text, Field(min_length=1, max_length=100)] | None = None
    url: Url | None = None


class LinkOut(ORMModel):
    id: int
    label: str
    url: str


# ---------------------------------------------------------------------------
# Education (R4)
# ---------------------------------------------------------------------------

class EducationCreate(BaseModel):
    school_name: Annotated[Text, Field(min_length=1, max_length=200)]
    degree: Annotated[Text, Field(max_length=200)] | None = None
    major: Annotated[Text, Field(max_length=200)] | None = None
    start_date: date | None = None
    graduation_date: date | None = None
    gpa: Annotated[Text, Field(max_length=20)] | None = None
    coursework: TagList = []


class EducationUpdate(PartialUpdate):
    _required = ("school_name", "coursework")

    school_name: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    degree: Annotated[Text, Field(max_length=200)] | None = None
    major: Annotated[Text, Field(max_length=200)] | None = None
    start_date: date | None = None
    graduation_date: date | None = None
    gpa: Annotated[Text, Field(max_length=20)] | None = None
    coursework: TagList | None = None


class EducationOut(ORMModel):
    id: int
    school_name: str
    degree: str | None
    major: str | None
    start_date: date | None
    graduation_date: date | None
    gpa: str | None
    coursework: list[str]

    @computed_field
    @property
    def is_expected(self) -> bool:
        return self.graduation_date is not None and self.graduation_date > date.today()


# ---------------------------------------------------------------------------
# Skills (R5)
# ---------------------------------------------------------------------------

class SkillCreate(BaseModel):
    name: Annotated[Text, Field(min_length=1, max_length=100)]
    category: SkillCategory = "other"
    proficiency: Annotated[Text, Field(max_length=30)] | None = None


class SkillUpdate(PartialUpdate):
    _required = ("name", "category")

    name: Annotated[Text, Field(min_length=1, max_length=100)] | None = None
    category: SkillCategory | None = None
    proficiency: Annotated[Text, Field(max_length=30)] | None = None


class SkillOut(ORMModel):
    id: int
    name: str
    category: str
    proficiency: str | None


# ---------------------------------------------------------------------------
# Experience (R6)
# ---------------------------------------------------------------------------

class ExperienceCreate(BaseModel):
    experience_type: ExperienceType = "work"
    organization: Annotated[Text, Field(min_length=1, max_length=200)]
    position: Annotated[Text, Field(min_length=1, max_length=200)]
    location: Annotated[Text, Field(max_length=200)] | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: Annotated[Text, Field(max_length=5000)] | None = None


class ExperienceUpdate(PartialUpdate):
    _required = ("experience_type", "organization", "position", "is_current")

    experience_type: ExperienceType | None = None
    organization: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    position: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    location: Annotated[Text, Field(max_length=200)] | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: Annotated[Text, Field(max_length=5000)] | None = None


class ExperienceOut(ORMModel):
    id: int
    experience_type: str
    organization: str
    position: str
    location: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    description: str | None


# ---------------------------------------------------------------------------
# Projects (R7), media (R8), 3D models (R15)
# ---------------------------------------------------------------------------

ContentBlocks = Annotated[list[dict[str, Any]], Field(max_length=100)]


class ProjectCreate(BaseModel):
    title: Annotated[Text, Field(min_length=1, max_length=200)]
    description: Annotated[Text, Field(max_length=10000)] = ""
    content_blocks: ContentBlocks = []
    project_date: Annotated[Text, Field(max_length=100)] | None = None
    subject: Annotated[Text, Field(max_length=200)] | None = None
    technologies: TagList = []
    display_order: int = 0


class ProjectUpdate(PartialUpdate):
    _required = ("title", "description", "content_blocks", "technologies", "display_order")

    title: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[Text, Field(max_length=10000)] | None = None
    content_blocks: ContentBlocks | None = None
    project_date: Annotated[Text, Field(max_length=100)] | None = None
    subject: Annotated[Text, Field(max_length=200)] | None = None
    technologies: TagList | None = None
    display_order: int | None = None


class ImageCreate(BaseModel):
    """Attach an image that is already hosted somewhere, by URL."""

    url: Url
    label: Annotated[Text, Field(max_length=200)] | None = None


class LinkMediaCreate(BaseModel):
    """External link to a repository, demo, or related resource (R8.2)."""

    url: Url
    label: Annotated[Text, Field(min_length=1, max_length=200)]
    link_type: Annotated[Text, Field(max_length=30)] | None = None

    @field_validator("link_type")
    @classmethod
    def lowercase(cls, value: str | None) -> str | None:
        return value.lower() if value else None


class ImageOut(ORMModel):
    id: int
    url: str
    label: str | None


class ProjectLinkOut(ORMModel):
    id: int
    url: str
    label: str | None
    link_type: str | None


class ModelOut(ORMModel):
    id: int
    url: str
    file_format: str
    original_filename: str | None
    file_size_bytes: int | None
    created_at: datetime


class ProjectOut(ORMModel):
    id: int
    title: str
    description: str
    content_blocks: list[dict[str, Any]]
    project_date: str | None
    subject: str | None
    technologies: list[str]
    display_order: int
    images: list[ImageOut]
    links: list[ProjectLinkOut]
    model_3d: ModelOut | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _split_media(cls, data: Any) -> Any:
        # Images and links share one table; the API returns them as separate lists.
        if hasattr(data, "media"):
            return {
                **{field: getattr(data, field) for field in cls.model_fields if hasattr(data, field)},
                "images": [m for m in data.media if m.media_type == "image"],
                "links": [m for m in data.media if m.media_type == "link"],
            }
        return data


# ---------------------------------------------------------------------------
# Full portfolio views (R9, R17)
# ---------------------------------------------------------------------------

class PortfolioOut(ORMModel):
    """The owner's view of their whole portfolio."""

    id: int
    name: str
    email: EmailStr
    headline: str | None
    bio: str | None
    location: str | None
    profile_image_url: str | None
    career_interests: list[str]
    is_public: bool
    share_url: str | None
    links: list[LinkOut]
    education: list[EducationOut]
    skills: list[SkillOut]
    experiences: list[ExperienceOut]
    projects: list[ProjectOut]
    updated_at: datetime


class PublicPortfolioOut(BaseModel):
    """What visitors see through a share link. No email, ids of owners, or settings."""

    name: str
    headline: str | None
    bio: str | None
    location: str | None
    profile_image_url: str | None
    career_interests: list[str]
    links: list[LinkOut]
    education: list[EducationOut]
    skills: list[SkillOut]
    experiences: list[ExperienceOut]
    projects: list[ProjectOut]


class ShareOut(BaseModel):
    is_public: bool
    share_token: str | None
    share_url: str | None


# ---------------------------------------------------------------------------
# AI career guidance (R10–R14)
#
# These models double as the JSON schema the AI must fill in, so they deliberately
# avoid validation constraints that structured-output schemas do not support.
# ---------------------------------------------------------------------------

class CareerPath(BaseModel):
    title: str = Field(description="Name of the career path or role, e.g. 'Embedded Software Engineer'")
    explanation: str = Field(description="How this path connects to the student's background (R11.3)")


class Strength(BaseModel):
    title: str = Field(description="Short name of the strength")
    explanation: str = Field(description="Which portfolio items show this strength (R12.4)")


class Improvement(BaseModel):
    area: str = Field(description="Area the student could improve")
    explanation: str = Field(description="Why it matters and which career direction it supports (R13.4)")


class NextStep(BaseModel):
    action: str = Field(description="A concrete next step the student can take")
    category: Literal["skills", "projects", "experience", "career_exploration"]
    supports: str = Field(description="How this step supports a possible career direction (R13.4)")


class GuidanceContent(BaseModel):
    summary: str = Field(description="2-4 sentence summary of the student's academic and professional background")
    career_paths: list[CareerPath]
    strengths: list[Strength]
    improvements: list[Improvement]
    next_steps: list[NextStep]


class GuidanceOut(GuidanceContent, ORMModel):
    id: int
    provider: str
    model: str | None
    created_at: datetime
