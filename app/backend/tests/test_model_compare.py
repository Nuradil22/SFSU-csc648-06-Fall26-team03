"""Two-model comparison (/career/compare): catalog validation, agreement
diff, provider failure surfacing, and no fabricated output. No live calls —
provider functions are stubbed or SDK clients are faked."""

import json
from types import SimpleNamespace

import anthropic
import httpx
import openai
import pytest
from fastapi import HTTPException

from app import academic_catalog
from app.config import settings
from app.routers import model_compare
from app.routers.model_compare import (
    CompareResponse,
    ModelRecommendation,
    compare_pair,
    validate_course,
)

from .test_career_chat import _with_portfolio


# --- Curated record validation ----------------------------------------------

def test_normalize_code_variants():
    assert academic_catalog.normalize_code("csc648") == "CSC 648"
    assert academic_catalog.normalize_code("CSC-675") == "CSC 675"
    assert academic_catalog.normalize_code("CSC 300") == "CSC 300GW"  # alias
    assert academic_catalog.normalize_code("nope") is None


def test_validate_known_course_is_verified():
    result = validate_course("CSC 317", "Introduction to Web Software Development")
    assert result["status"] == "verified"
    assert result["catalog_title"] == "Introduction to Web Software Development"
    assert result["issue"] is None


def test_validate_unknown_code_is_unverified_not_fabricated():
    result = validate_course("CSC 999", "Underwater Basket Weaving")
    assert result["status"] == "unverified"
    assert "not in the curated" in result["issue"]


def test_validate_title_mismatch_is_flagged():
    result = validate_course("CSC 675", "Basket Weaving 101")
    assert result["status"] == "title_mismatch"
    assert "Introduction to Database Systems" in result["issue"]


def test_validate_unconfirmed_prerequisite_claim_is_flagged():
    result = validate_course("CSC 675", "Introduction to Database Systems",
                             ["CSC 999 required first"])
    assert "CSC 999" in result["issue"]
    # A correct claim is not flagged.
    ok = validate_course("CSC 675", "Introduction to Database Systems",
                         ["CSC 413 with a grade of C or better"])
    assert ok["issue"] is None


# --- Agreement diff ----------------------------------------------------------

def test_compare_recommendations_finds_agreement_and_differences():
    a = [
        {"course_code": "CSC 675", "title": "Introduction to Database Systems"},
        {"course_code": "CSC 667", "title": "Internet Application Design and Development"},
    ]
    b = [
        {"course_code": "csc675", "title": "Introduction to Database Systems"},
        {"course_code": "CSC 645", "title": "Computer Networks"},
    ]
    diff = academic_catalog.compare_recommendations(a, b)
    assert diff["shared"] == ["CSC 675"]
    assert diff["only_a"] == ["CSC 667"]
    assert diff["only_b"] == ["CSC 645"]


def test_compare_recommendations_matches_non_course_items_by_title():
    a = [{"course_code": None, "title": "SFSU Hackathon"}]
    b = [{"course_code": None, "title": "SFSU Hackathon"}]
    diff = academic_catalog.compare_recommendations(a, b)
    assert "sfsuhackathon" in diff["shared_titles"]


# --- Endpoint ----------------------------------------------------------------

def test_compare_requires_login(client):
    assert client.post("/career/compare", json={"question": "Which CSC courses?"}).status_code == 401


def test_compare_requires_ready_portfolio(client, auth):
    r = client.post("/career/compare", headers=auth, json={"question": "Which CSC courses?"})
    assert r.status_code == 409


def _fake_response(*codes):
    return CompareResponse(recommendations=[
        ModelRecommendation(course_code=c[0], title=c[1], rationale="fits goals")
        for c in codes
    ])


def test_compare_both_models_validated_and_diffed(client, auth, monkeypatch):
    _with_portfolio(client, auth)

    calls = []

    def fake(provider, question, system, model):
        calls.append((provider, model))
        if model == "fake-a":
            return _fake_response(("CSC 675", "Introduction to Database Systems"),
                                  ("CSC 999", "Invented Course"))
        return _fake_response(("CSC 675", "Introduction to Database Systems"),
                              ("CSC 667", "Internet Application Design and Development"))

    monkeypatch.setattr(model_compare, "_call_provider", fake)
    monkeypatch.setattr(model_compare, "compare_pair",
                        lambda: [("openai", "fake-a"), ("anthropic", "fake-b")])

    r = client.post("/career/compare", headers=auth,
                    json={"question": "Which CSC courses should I take?"})
    assert r.status_code == 200, r.text
    body = r.json()

    assert calls == [("openai", "fake-a"), ("anthropic", "fake-b")]
    assert [m["label"] for m in body["models"]] == ["openai:fake-a", "anthropic:fake-b"]
    assert all(m["status"] == "ok" for m in body["models"])

    recs = body["models"][0]["recommendations"]
    assert recs[0]["validation"]["status"] == "verified"
    assert recs[1]["validation"]["status"] == "unverified"  # invented course flagged

    comparison = body["comparison"]
    assert comparison["shared"] == ["CSC 675"]
    assert comparison["only"]["openai:fake-a"] == ["CSC 999"]
    assert comparison["only"]["anthropic:fake-b"] == ["CSC 667"]
    assert "not proof of accuracy" in body["disclaimer"]


def test_compare_provider_failure_is_reported_not_fabricated(client, auth, monkeypatch):
    _with_portfolio(client, auth)

    def fake(provider, question, system, model):
        if provider == "anthropic":
            raise HTTPException(status_code=503, detail="Anthropic is not configured on the server.")
        return _fake_response(("CSC 675", "Introduction to Database Systems"))

    monkeypatch.setattr(model_compare, "_call_provider", fake)
    monkeypatch.setattr(model_compare, "compare_pair",
                        lambda: [("openai", "fake-a"), ("anthropic", "fake-b")])

    r = client.post("/career/compare", headers=auth,
                    json={"question": "Which CSC courses should I take?"})
    assert r.status_code == 200, r.text
    body = r.json()

    statuses = {m["provider"]: m["status"] for m in body["models"]}
    assert statuses == {"openai": "ok", "anthropic": "error"}
    assert "not configured" in body["models"][1]["error"]
    assert body["comparison"] is None  # no diff without both answers


def test_compare_pair_defaults_to_fallback_without_anthropic_key(monkeypatch):
    monkeypatch.setattr("app.routers.model_compare.settings.anthropic_api_key", "")
    monkeypatch.setattr("app.routers.model_compare.settings.model_compare_pair", "")
    assert compare_pair() == [("openai", model_compare.settings.openai_model),
                              ("openai", model_compare.settings.compare_fallback_model)]


def test_compare_pair_uses_anthropic_when_key_set(monkeypatch):
    monkeypatch.setattr("app.routers.model_compare.settings.anthropic_api_key", "x")
    monkeypatch.setattr("app.routers.model_compare.settings.model_compare_pair", "")
    assert compare_pair() == [("openai", model_compare.settings.openai_model),
                              ("anthropic", model_compare.settings.ai_model)]


# --- Provider pair configuration --------------------------------------------

def test_compare_pair_parses_explicit_spec(monkeypatch):
    monkeypatch.setattr(settings, "model_compare_pair",
                        " OpenAI : gpt-5.1 , Anthropic : claude-sonnet-4 ")
    assert compare_pair() == [("openai", "gpt-5.1"), ("anthropic", "claude-sonnet-4")]


def test_compare_pair_rejects_malformed_spec_and_falls_back(monkeypatch, caplog):
    monkeypatch.setattr(settings, "model_compare_pair", "only-one-entry")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with caplog.at_level("WARNING"):
        pair = compare_pair()
    assert pair == [("openai", settings.openai_model),
                    ("openai", settings.compare_fallback_model)]
    assert "provider:model" in caplog.text


def test_supports_reasoning_flag():
    assert model_compare._supports_reasoning("gpt-5.1")
    assert model_compare._supports_reasoning("o3-mini")
    assert not model_compare._supports_reasoning("gpt-4o-mini")
    assert not model_compare._supports_reasoning("claude-sonnet-4")


# --- OpenAI provider call ----------------------------------------------------

class _FakeOpenAIClient:
    """Stands in for openai.OpenAI; responses.create returns scripted text or raises."""
    calls: list = []
    outcome: object = None

    def __init__(self, **kwargs):
        self.responses = self

    def create(self, **kwargs):
        _FakeOpenAIClient.calls.append(kwargs)
        if isinstance(_FakeOpenAIClient.outcome, Exception):
            raise _FakeOpenAIClient.outcome
        return SimpleNamespace(output_text=_FakeOpenAIClient.outcome)


@pytest.fixture
def fake_openai_sdk(monkeypatch):
    _FakeOpenAIClient.calls = []
    monkeypatch.setattr(openai, "OpenAI", _FakeOpenAIClient)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    return _FakeOpenAIClient


def _openai_status_error(cls, code=503):
    req = httpx.Request("POST", "https://api.openai.test/v1/responses")
    return cls("boom", response=httpx.Response(code, request=req), body=None)


def _compare_json(*codes):
    return json.dumps({"recommendations": [
        {"course_code": c, "title": "T", "rationale": "r"} for c in codes
    ]})


def test_call_openai_parses_output_and_sends_reasoning_only_for_gpt5(fake_openai_sdk):
    _FakeOpenAIClient.outcome = _compare_json("CSC 675")
    result = model_compare._call_openai("q?", "system", "gpt-5.1")
    assert isinstance(result, CompareResponse)
    assert result.recommendations[0].course_code == "CSC 675"
    assert _FakeOpenAIClient.calls[0]["max_output_tokens"] == 3000
    assert _FakeOpenAIClient.calls[0]["reasoning"] == {"effort": settings.openai_reasoning_effort}

    _FakeOpenAIClient.calls = []
    model_compare._call_openai("q?", "system", "gpt-4o-mini")
    assert "reasoning" not in _FakeOpenAIClient.calls[0]


def test_call_openai_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(HTTPException) as exc:
        model_compare._call_openai("q?", "system", "gpt-5.1")
    assert exc.value.status_code == 503


@pytest.mark.parametrize("exc", [
    _openai_status_error(openai.AuthenticationError, 401),
    _openai_status_error(openai.RateLimitError, 429),
    _openai_status_error(openai.APIStatusError, 500),
    openai.APIError("down", request=httpx.Request("POST", "https://api.openai.test"), body=None),
])
def test_call_openai_maps_sdk_errors_to_503(fake_openai_sdk, exc):
    _FakeOpenAIClient.outcome = exc
    with pytest.raises(HTTPException) as raised:
        model_compare._call_openai("q?", "system", "gpt-5.1")
    assert raised.value.status_code == 503


def test_call_openai_unparseable_output_is_502(fake_openai_sdk):
    _FakeOpenAIClient.outcome = "not json at all"
    with pytest.raises(HTTPException) as exc:
        model_compare._call_openai("q?", "system", "gpt-5.1")
    assert exc.value.status_code == 502


# --- Anthropic provider call -------------------------------------------------

class _FakeAnthropicClient:
    calls: list = []
    outcome: object = ""

    def __init__(self, **kwargs):
        self.messages = self

    def create(self, **kwargs):
        _FakeAnthropicClient.calls.append(kwargs)
        if isinstance(_FakeAnthropicClient.outcome, Exception):
            raise _FakeAnthropicClient.outcome
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=_FakeAnthropicClient.outcome)]
        )


@pytest.fixture
def fake_anthropic_sdk(monkeypatch):
    _FakeAnthropicClient.calls = []
    monkeypatch.setattr(anthropic, "Anthropic", _FakeAnthropicClient)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    return _FakeAnthropicClient


def _anthropic_status_error(cls, code=503):
    req = httpx.Request("POST", "https://api.anthropic.test/v1/messages")
    return cls("boom", response=httpx.Response(code, request=req), body=None)


def test_call_anthropic_parses_json_text(fake_anthropic_sdk):
    _FakeAnthropicClient.outcome = _compare_json("CSC 317")
    result = model_compare._call_anthropic("q?", "system", "claude-sonnet-4")
    assert result.recommendations[0].course_code == "CSC 317"
    assert _FakeAnthropicClient.calls[0]["max_tokens"] == 2000


def test_call_anthropic_extracts_json_wrapped_in_prose(fake_anthropic_sdk):
    _FakeAnthropicClient.outcome = (
        'Here are my picks:\n```json\n' + _compare_json("CSC 648") + '\n```'
    )
    result = model_compare._call_anthropic("q?", "system", "claude-sonnet-4")
    assert result.recommendations[0].course_code == "CSC 648"


def test_call_anthropic_unparseable_output_is_502(fake_anthropic_sdk):
    _FakeAnthropicClient.outcome = "no JSON here"
    with pytest.raises(HTTPException) as exc:
        model_compare._call_anthropic("q?", "system", "claude-sonnet-4")
    assert exc.value.status_code == 502


@pytest.mark.parametrize("exc", [
    _anthropic_status_error(anthropic.AuthenticationError, 401),
    _anthropic_status_error(anthropic.APIStatusError, 500),
    anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.test")),
])
def test_call_anthropic_maps_sdk_errors_to_503(fake_anthropic_sdk, exc):
    _FakeAnthropicClient.outcome = exc
    with pytest.raises(HTTPException) as raised:
        model_compare._call_anthropic("q?", "system", "claude-sonnet-4")
    assert raised.value.status_code == 503


def test_call_anthropic_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with pytest.raises(HTTPException) as exc:
        model_compare._call_anthropic("q?", "system", "claude-sonnet-4")
    assert exc.value.status_code == 503


# --- Dispatch and validation -------------------------------------------------

def test_call_provider_rejects_unknown_provider():
    with pytest.raises(HTTPException) as exc:
        model_compare._call_provider("gemini", "q?", "system", "gemini-pro")
    assert exc.value.status_code == 503
    assert "gemini" in exc.value.detail


def test_validated_non_course_item_is_not_applicable():
    rec = ModelRecommendation(course_code=None, title="SFSU Hackathon", rationale="fun")
    item = model_compare._validated(rec)
    assert item["validation"]["status"] == "not_applicable"
    assert "nothing to verify" in item["validation"]["issue"]


def test_validated_course_runs_catalog_check():
    rec = ModelRecommendation(
        course_code="CSC 999", title="Invented", rationale="r",
        prerequisites_claimed=["CSC 000"])
    item = model_compare._validated(rec)
    assert item["validation"]["status"] == "unverified"
