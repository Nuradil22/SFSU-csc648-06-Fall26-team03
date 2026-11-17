"""Two-model comparison (/career/compare): catalog validation, agreement
diff, provider failure surfacing, and no fabricated output. No live calls —
provider functions are stubbed."""

from fastapi import HTTPException

from app import academic_catalog
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
