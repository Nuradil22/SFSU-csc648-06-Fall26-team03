"""Two-model academic recommendation comparison (POST /career/compare).

Both models receive the same student portfolio payload, the same question,
and the same curated SFSU course records. Each produces a structured list of
recommendations; the server validates every course against the curated
record and reports agreement/disagreement between the two outputs.

Agreement between models is NOT evidence of accuracy. A failed provider is
reported as an error for that model, never replaced by fabricated output.
"""

import json
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import ai, models
from ..academic_catalog import (
    catalog_for_prompt,
    compare_recommendations,
    validate_course,
)
from ..config import settings
from ..database import get_db
from ..deps import get_current_portfolio
from .career_chat import AIResponseError, _require_ready, _usage_event

router = APIRouter(prefix="/career", tags=["two-model comparison"])

logger = logging.getLogger(__name__)

COMPARE_KIND = "chat"

DISCLAIMER = (
    "Recommendations come from AI models and may be wrong. Agreement between "
    "the two models is not proof of accuracy. Always confirm courses, "
    "prerequisites, and schedules in the official SFSU Bulletin before "
    "enrolling."
)

MAX_RECOMMENDATIONS = 6


class CompareRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)


# Strict JSON schema both providers are asked to produce.
class ModelRecommendation(BaseModel):
    course_code: str | None = Field(
        default=None,
        description="Catalog course code such as 'CSC 675', or null for a non-course item.",
    )
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(
        default="course",
        description="course | campus_activity | online_resource | project_idea | other",
    )
    rationale: str = Field(min_length=1, max_length=600)
    prerequisites_claimed: list[str] = Field(
        default_factory=list,
        description="Prerequisite courses the model believes are required.",
    )


class CompareResponse(BaseModel):
    recommendations: list[ModelRecommendation] = Field(max_length=MAX_RECOMMENDATIONS)


COMPARE_SYSTEM_PROMPT = """You are an academic advisor for a student at San Francisco State University.

Answer the student's question with at most {max_recs} concrete recommendations.
For every course you recommend, use only entries from the OFFICIAL SFSU COURSE
RECORDS below — give the exact course code and title from the record, and do
not invent courses, prerequisites, or schedule details. If none of the listed
courses fit the question, recommend a non-course item (category
campus_activity, online_resource, project_idea, or other) instead.

OFFICIAL SFSU COURSE RECORDS (curated subset of the academic bulletin):
{catalog}

STUDENT PORTFOLIO (JSON):
{portfolio}
"""


def compare_pair() -> list[tuple[str, str]]:
    """The two (provider, model) pairs to compare, from configuration."""
    spec = settings.model_compare_pair.strip()
    if spec:
        pair = []
        for entry in spec.split(","):
            provider, _, model = entry.strip().partition(":")
            provider, model = provider.strip().lower(), model.strip()
            if provider and model:
                pair.append((provider, model))
        if len(pair) == 2:
            return pair
        logger.warning("MODEL_COMPARE_PAIR must list two 'provider:model' entries.")

    pair = [("openai", settings.openai_model)]
    if settings.anthropic_api_key:
        pair.append(("anthropic", settings.ai_model))
    else:
        pair.append(("openai", settings.compare_fallback_model))
    return pair


def _supports_reasoning(model: str) -> bool:
    name = model.lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4"))


def _call_openai(question: str, system: str, model: str) -> CompareResponse:
    import openai
    from openai.lib._parsing._responses import type_to_text_format_param

    if not settings.openai_api_key:
        raise AIResponseError(503, "OpenAI is not configured on the server.")

    client = openai.OpenAI(api_key=settings.openai_api_key,
                           timeout=settings.ai_timeout_seconds)

    options = {}
    if _supports_reasoning(model):
        options["reasoning"] = {"effort": settings.openai_reasoning_effort}

    try:
        response = client.responses.create(
            model=model,
            instructions=system,
            input=question,
            text={"format": type_to_text_format_param(CompareResponse)},
            max_output_tokens=3000,
            **options,
        )
    except openai.AuthenticationError as exc:
        raise AIResponseError(503, "OpenAI authentication failed on the server.") from exc
    except openai.RateLimitError as exc:
        raise AIResponseError(503, "OpenAI is temporarily rate-limited or out of credits.") from exc
    except openai.APIError as exc:
        raise AIResponseError(503, "The OpenAI service is unavailable.") from exc

    try:
        return CompareResponse.model_validate_json(response.output_text)
    except (ValueError, TypeError) as exc:
        raise AIResponseError(502, "The OpenAI response could not be parsed.") from exc


def _call_anthropic(question: str, system: str, model: str) -> CompareResponse:
    import anthropic

    if not settings.anthropic_api_key:
        raise AIResponseError(503, "Anthropic is not configured on the server.")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key,
                                 timeout=settings.ai_timeout_seconds)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": question}],
        )
    except anthropic.AuthenticationError as exc:
        raise AIResponseError(503, "Anthropic authentication failed on the server.") from exc
    except anthropic.APIStatusError as exc:
        raise AIResponseError(503, "The Anthropic service is unavailable.") from exc
    except anthropic.APIConnectionError as exc:
        raise AIResponseError(503, "Could not reach the Anthropic service.") from exc

    text = "".join(block.text for block in response.content if block.type == "text")
    try:
        return CompareResponse.model_validate(json.loads(text))
    except (ValueError, TypeError):
        # Some models wrap JSON in prose or code fences; extract the object.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return CompareResponse.model_validate(json.loads(match.group(0)))
            except (ValueError, TypeError):
                pass
        raise AIResponseError(502, "The Anthropic response could not be parsed.")


def _call_provider(provider: str, question: str, system: str, model: str) -> CompareResponse:
    if provider == "openai":
        return _call_openai(question, system, model)
    if provider == "anthropic":
        return _call_anthropic(question, system, model)
    raise AIResponseError(503, f"Unknown comparison provider '{provider}'.")


def _validated(rec: ModelRecommendation) -> dict:
    item = rec.model_dump()
    if rec.course_code:
        item["validation"] = validate_course(
            rec.course_code, rec.title, rec.prerequisites_claimed
        )
    else:
        item["validation"] = {
            "status": "not_applicable",
            "issue": "Not a catalog course; nothing to verify against records.",
        }
    return item


@router.post("/compare")
def compare(
    body: CompareRequest,
    portfolio: models.Portfolio = Depends(get_current_portfolio),
    db: Session = Depends(get_db),
):
    payload = ai.build_portfolio_payload(portfolio)
    _require_ready(payload)

    system = COMPARE_SYSTEM_PROMPT.format(
        max_recs=MAX_RECOMMENDATIONS,
        catalog=json.dumps(catalog_for_prompt(), ensure_ascii=False),
        portfolio=json.dumps(payload, ensure_ascii=False),
    ) + (
        "\nRespond ONLY with a JSON object {\"recommendations\": [...]}. "
        "No text outside the JSON."
    )

    pair = compare_pair()
    results = []

    for provider, model in pair:
        label = f"{provider}:{model}"
        try:
            answer = _call_provider(provider, body.question, system, model)
        except HTTPException as exc:
            logger.warning(
                "Comparison provider failed: %s %s status=%s",
                provider, model, exc.status_code,
            )
            db.add(_usage_event(portfolio.id, COMPARE_KIND, provider, {"status": "failed"}))
            results.append({
                "label": label,
                "provider": provider,
                "model": model,
                "status": "error",
                "error": exc.detail,
                "recommendations": [],
            })
            continue

        db.add(_usage_event(
            portfolio.id, COMPARE_KIND, provider,
            {"status": "completed",
             "input_tokens": None, "output_tokens": None},
        ))
        results.append({
            "label": label,
            "provider": provider,
            "model": model,
            "status": "ok",
            "error": None,
            "recommendations": [_validated(r) for r in answer.recommendations],
        })

    db.commit()

    ok = [r for r in results if r["status"] == "ok"]
    comparison = None
    if len(ok) == 2:
        diff = compare_recommendations(ok[0]["recommendations"], ok[1]["recommendations"])
        comparison = {
            "shared": diff["shared"],
            "shared_titles": diff["shared_titles"],
            "only": {ok[0]["label"]: diff["only_a"], ok[1]["label"]: diff["only_b"]},
        }

    return {
        "question": body.question,
        "models": results,
        "comparison": comparison,
        "disclaimer": DISCLAIMER,
        "compared_at": datetime.now(timezone.utc).isoformat(),
    }
