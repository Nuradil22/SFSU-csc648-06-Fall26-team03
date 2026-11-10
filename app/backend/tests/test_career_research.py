"""P1: automatic roadmaps, explicit roadmap requests, portfolio-change
detection, verified web-research resources, rate limits, and usage logging.

OpenAI is always the scripted fake in tests/openai_fakes.py; no network calls.
"""

import httpx
import openai
import pytest
from sqlalchemy import select

from app import models
from app.config import settings
from app.database import SessionLocal
from app.routers.career_chat import wants_research, wants_roadmap

from . import openai_fakes
from .conftest import signup
from .openai_fakes import FakeOpenAI, plan, resource, search_call

BULLETIN = "https://bulletin.sfsu.edu/courses/csc/"
COURSERA = "https://www.coursera.org/professional-certificates/google-data-analytics"


def _add(client, headers, path, json):
    r = client.post(path, headers=headers, json=json)
    assert r.status_code == 201, r.text


def _ready(client, headers, skills=("Python", "SQL", "Git"), role="Data Engineer"):
    _add(client, headers, "/portfolio/me/education",
         {"school_name": "San Francisco State University", "degree": "B.S. Computer Science"})
    for name in skills:
        _add(client, headers, "/portfolio/me/skills", {"name": name})
    _add(client, headers, "/portfolio/me/job-preferences", {"role": role})
    _add(client, headers, "/projects", {"title": f"{skills[0]} pipeline"})


def _usage():
    with SessionLocal() as db:
        return db.scalars(select(models.AIUsageEvent).order_by(models.AIUsageEvent.id)).all()


@pytest.fixture
def fake(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


@pytest.fixture
def research(fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", True)
    return fake


# --- Request classification ---------------------------------------------------

def test_roadmap_and_research_intent_detection():
    for text in ("Make me a roadmap", "Please regenerate my roadmap", "Update my road map",
                 "I need a new career plan", "Can you revise the roadmap for data science?"):
        assert wants_roadmap(text), text
    for text in ("What does a roadmap mean?", "How do I write a resume?", "Hi"):
        assert not wants_roadmap(text), text

    for text in ("Which courses should I take?", "Is CSC 648 hard?", "Any good certificates?",
                 "Recommend learning resources"):
        assert wants_research(text), text
    for text in ("How do I prepare for interviews?", "Hello", "Top 100 companies"):
        assert not wants_research(text), text


# --- Automatic generation -------------------------------------------------------

def test_auto_generates_once_and_refresh_returns_the_same_draft(client, auth):
    _ready(client, auth)

    first = client.post("/career/roadmap/auto", headers=auth)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "generated" and body["generated"] is True
    assert body["proposal"]["goals"]

    again = client.post("/career/roadmap/auto", headers=auth).json()
    assert again == {
        "status": "pending", "generated": False,
        "proposal_id": body["proposal_id"],
        "proposal": {"id": body["proposal_id"], **body["proposal"]},
    }

    proposals = client.get("/career/proposals", headers=auth).json()
    assert [(p["id"], p["origin"]) for p in proposals] == [(body["proposal_id"], "auto")]
    # The analysis is in the conversation; the hidden prompt is not.
    assert [m["role"] for m in client.get("/career/chat/history", headers=auth).json()] == ["assistant"]
    assert [e.kind for e in _usage()] == ["auto_roadmap"]


def test_auto_never_replaces_an_approved_roadmap_and_flags_portfolio_changes(client, auth):
    _ready(client, auth)
    pid = client.post("/career/roadmap/auto", headers=auth).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)
    approved = client.get("/career/roadmap", headers=auth).json()
    assert approved["portfolio_changed"] is False

    r = client.post("/career/roadmap/auto", headers=auth).json()
    assert r == {"status": "approved", "generated": False, "portfolio_changed": False}

    # A dashboard change is recognized, but nothing is regenerated or replaced.
    _add(client, auth, "/portfolio/me/skills", {"name": "Docker"})
    r = client.post("/career/roadmap/auto", headers=auth).json()
    assert r == {"status": "approved", "generated": False, "portfolio_changed": True}
    now = client.get("/career/roadmap", headers=auth).json()
    assert now["portfolio_changed"] is True
    assert (now["title"], now["goals"]) == (approved["title"], approved["goals"])
    assert client.get("/career/proposals", headers=auth).json() == []


def test_rejected_auto_draft_is_not_regenerated_until_the_portfolio_changes(client, auth):
    _ready(client, auth)
    pid = client.post("/career/roadmap/auto", headers=auth).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/reject", headers=auth)

    assert client.post("/career/roadmap/auto", headers=auth).json() == {
        "status": "up_to_date", "generated": False}

    _add(client, auth, "/portfolio/me/skills", {"name": "Airflow"})
    r = client.post("/career/roadmap/auto", headers=auth).json()
    assert r["status"] == "generated" and r["proposal_id"] != pid


def test_incomplete_portfolio_blocks_auto_and_chat_without_any_ai_call(client, auth, research):
    assert client.post("/career/roadmap/auto", headers=auth).status_code == 409
    r = client.post("/career/chat", headers=auth, json={"message": "Make me a new roadmap"})
    assert r.status_code == 409
    assert "complete your Projectory portfolio" in r.json()["detail"]

    assert research.calls == []
    assert _usage() == []
    assert client.get("/career/proposals", headers=auth).json() == []
    assert client.get("/career/chat/history", headers=auth).json() == []


def test_auto_drafts_are_per_student(client, auth):
    other = signup(client, email="other-p1@sfsu.edu")
    _ready(client, auth)
    _ready(client, other, skills=("Figma", "Sketch", "UX research"), role="UX Designer")

    mine = client.post("/career/roadmap/auto", headers=auth).json()["proposal_id"]
    theirs = client.post("/career/roadmap/auto", headers=other).json()
    assert theirs["status"] == "generated" and theirs["proposal_id"] != mine

    assert client.post(f"/career/proposals/{mine}/approve", headers=other).status_code == 404
    assert [p["id"] for p in client.get("/career/proposals", headers=other).json()] == [theirs["proposal_id"]]


# --- Explicit requests ------------------------------------------------------------

def test_explicit_request_uses_latest_portfolio_and_supersedes_older_drafts(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": plan(title="First")}},
                   {"parsed": {"proposal": plan(title="Second")}}]

    first = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert "Docker" not in fake.calls[0]["instructions"]
    assert "ROADMAP REQUEST" in fake.calls[0]["instructions"]

    # The student saves a new skill on the dashboard, then asks again.
    _add(client, auth, "/portfolio/me/skills", {"name": "Docker"})
    second = client.post("/career/chat", headers=auth,
                         json={"message": "Please regenerate my roadmap"}).json()
    assert "Docker" in fake.calls[1]["instructions"]
    assert second["proposal"]["title"] == "Second"

    # Only the newest draft can be approved.
    r = client.post(f"/career/proposals/{first['proposal_id']}/approve", headers=auth)
    assert r.status_code == 409 and "newer" in r.json()["detail"]
    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [second["proposal_id"]]


def test_explicit_request_keeps_approved_roadmap_until_replacement_is_approved(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": plan(title="Original")}}]
    pid = client.post("/career/chat", headers=auth, json={"message": "Create my roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)

    # Progress on the approved roadmap.
    roadmap = client.get("/career/roadmap", headers=auth).json()
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})

    _add(client, auth, "/portfolio/me/skills", {"name": "Spark"})
    assert client.get("/career/roadmap", headers=auth).json()["portfolio_changed"] is True

    fake.script = [{"parsed": {"proposal": plan(title="Updated")}}]
    new = client.post("/career/chat", headers=auth, json={"message": "Update my roadmap"}).json()
    assert "portfolio has changed since their approved roadmap" in fake.calls[-1]["instructions"]

    kept = client.get("/career/roadmap", headers=auth).json()
    assert kept["title"] == "Original"
    assert kept["goals"][0]["milestones"][0]["completed"] is True

    client.post(f"/career/proposals/{new['proposal_id']}/approve", headers=auth)
    replaced = client.get("/career/roadmap", headers=auth).json()
    assert replaced["title"] == "Updated" and replaced["portfolio_changed"] is False


def test_explicit_request_without_a_proposal_fails_and_stores_nothing(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"parsed": {"reply": "Sure!"}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"})
    assert r.status_code == 502
    assert client.get("/career/chat/history", headers=auth).json() == []
    assert client.get("/career/proposals", headers=auth).json() == []
    assert [e.kind for e in _usage()] == ["chat_roadmap"]


# --- Web search requests -------------------------------------------------------------

def test_roadmap_generation_searches_the_open_web_within_budget(client, auth, research):
    _ready(client, auth)
    research.script = [{"parsed": {"proposal": plan()}}]
    assert client.post("/career/roadmap/auto", headers=auth).status_code == 200

    call = research.calls[0]
    assert call["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert call["max_tool_calls"] == 3
    assert call["include"] == ["web_search_call.action.sources"]
    assert "WEB RESEARCH" in call["instructions"] and "Coursera" in call["instructions"]
    assert research.clients[0]["max_retries"] == 1


def test_domain_allowlist_is_sent_and_enforced(client, auth, research, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search_domains", "sfsu.edu, coursera.org")
    monkeypatch.setattr(settings, "openai_max_web_searches", 2)
    _ready(client, auth)
    research.script = [{
        "output": [search_call(BULLETIN, COURSERA, "https://www.udemy.com/course/sql/")],
        "parsed": {"resources": [
            resource("CSC courses", BULLETIN),
            resource("SQL course", "https://www.udemy.com/course/sql/", provider="Udemy"),
        ]},
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Which courses fit me?"}).json()

    tool = research.calls[0]["tools"][0]
    assert tool["filters"] == {"allowed_domains": ["sfsu.edu", "coursera.org"]}
    assert research.calls[0]["max_tool_calls"] == 2
    assert [r["url"] for r in body["resources"]] == [BULLETIN]


def test_ordinary_chat_does_not_search(client, auth, research):
    _ready(client, auth)
    client.post("/career/chat", headers=auth, json={"message": "How do I prepare for interviews?"})
    client.post("/career/chat", headers=auth, json={"message": "Which certificates should I get?"})
    assert "tools" not in research.calls[0]
    assert "Web research is not available" in research.calls[0]["instructions"]
    assert research.calls[1]["tools"][0]["type"] == "web_search"


def test_disabled_search_sends_no_tools_and_shows_no_links(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"parsed": {
        "reply": "Try https://bulletin.sfsu.edu/courses/csc/ soon.",
        "resources": [resource("CSC courses", BULLETIN)],
        "proposal": plan([resource("CSC courses", BULLETIN)]),
    }}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap with courses"}).json()

    assert "tools" not in fake.calls[0]
    assert body["resources"] == [] and body["web_search"] is False
    assert "resources" not in body["proposal"]["goals"][0]["milestones"][0]
    assert body["reply"] == "Try [unverified link removed] soon."


# --- Resource verification ----------------------------------------------------------

def test_only_urls_returned_by_the_search_are_kept(client, auth, research):
    _ready(client, auth)
    research.script = [{
        "output": [search_call(BULLETIN, COURSERA, "http://insecure.example.edu/page")],
        "parsed": {
            "reply": f"See {BULLETIN} and https://www.edx.org/made-up-course.",
            "resources": [
                resource("CSC courses", "https://www.bulletin.sfsu.edu/courses/csc"),  # same page
                resource("Google Data Analytics", COURSERA, provider="Coursera"),
                resource("Invented edX course", "https://www.edx.org/made-up-course", provider="edX"),
                resource("Insecure", "http://insecure.example.edu/page"),
                resource("Duplicate", BULLETIN),
            ],
            "proposal": plan(
                [resource("CSC courses", BULLETIN), resource("Fake", "https://example.com/fake")],
                [resource("Google Data Analytics", COURSERA, provider="Coursera")],
            ),
        },
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()

    assert body["web_search"] is True
    assert [(r["title"], r["url"], r["type"]) for r in body["resources"]] == [
        ("CSC courses", BULLETIN, "sfsu"),  # the source's own URL is used
        ("Google Data Analytics", COURSERA, "external"),
    ]
    assert body["resources"][1]["provider"] == "Coursera"
    assert body["resources"][1]["description"] == "Fits your goals."
    assert body["reply"] == f"See {BULLETIN} and [unverified link removed]."

    milestones = body["proposal"]["goals"][0]["milestones"]
    assert [r["url"] for r in milestones[0]["resources"]] == [BULLETIN]
    assert [r["url"] for r in milestones[1]["resources"]] == [COURSERA]

    # Stored with the reply and with the draft.
    history = client.get("/career/chat/history", headers=auth).json()
    assert history[-1]["resources"] == body["resources"]
    stored = client.get("/career/proposals", headers=auth).json()[0]
    assert stored["goals"][0]["milestones"][0]["resources"][0]["url"] == BULLETIN


def test_empty_search_results_give_no_resources(client, auth, research):
    _ready(client, auth)
    research.script = [{
        "output": [search_call()],
        "parsed": {"resources": [resource("Guess", BULLETIN)]},
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Any SFSU programs for me?"}).json()
    assert body["web_search"] is True and body["resources"] == []
    assert _usage()[0].web_searches == 1


def test_revision_without_search_keeps_only_links_already_on_the_roadmap(client, auth, research, monkeypatch):
    _ready(client, auth)
    research.script = [{
        "output": [search_call(BULLETIN)],
        "parsed": {"proposal": plan([resource("CSC courses", BULLETIN)])},
    }]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)

    monkeypatch.setattr(settings, "openai_web_search", False)
    research.script = [{"parsed": {"proposal": plan(
        [resource("CSC courses", BULLETIN), resource("New guess", "https://www.edx.org/guess")]
    )}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Revise my roadmap"}).json()
    assert [r["url"] for r in body["proposal"]["goals"][0]["milestones"][0]["resources"]] == [BULLETIN]


# --- Failures, limits, usage ---------------------------------------------------------

def test_api_failure_returns_503_and_stores_no_conversation(client, auth, fake):
    _ready(client, auth)
    fake.script = [openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))]
    r = client.post("/career/roadmap/auto", headers=auth)
    assert r.status_code == 503
    assert client.get("/career/chat/history", headers=auth).json() == []
    assert client.get("/career/proposals", headers=auth).json() == []
    # The attempt still counts toward the limits.
    assert [(e.kind, e.provider, e.status, e.input_tokens) for e in _usage()] == [
        ("auto_roadmap", "openai", "failed", None)]


def test_unparseable_response_returns_502(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"text": "not json"}]
    r = client.post("/career/chat", headers=auth, json={"message": "Hello"})
    assert r.status_code == 502
    assert client.get("/career/chat/history", headers=auth).json() == []
    assert [(e.status, e.input_tokens) for e in _usage()] == [("invalid", 100)]


def test_chat_rate_limit_blocks_before_calling_the_ai(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "ai_chat_messages_per_hour", 2)
    _ready(client, auth)
    assert client.post("/career/chat", headers=auth, json={"message": "Hi"}).status_code == 200
    assert client.post("/career/chat", headers=auth, json={"message": "Hi again"}).status_code == 200
    r = client.post("/career/chat", headers=auth, json={"message": "One more"})
    assert r.status_code == 429 and "per hour" in r.json()["detail"]
    assert len(fake.calls) == 2


def test_roadmap_generation_limit_is_per_day_and_per_student(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "ai_roadmap_generations_per_day", 1)
    other = signup(client, email="other-limit@sfsu.edu")
    _ready(client, auth)
    _ready(client, other)

    assert client.post("/career/roadmap/auto", headers=auth).status_code == 200
    r = client.post("/career/chat", headers=auth, json={"message": "Make me a new roadmap"})
    assert r.status_code == 429 and "per day" in r.json()["detail"]
    # Ordinary chat is still allowed, and other students are unaffected.
    assert client.post("/career/chat", headers=auth, json={"message": "Hi"}).status_code == 200
    assert client.post("/career/chat", headers=other, json={"message": "Make me a roadmap"}).status_code == 200


def test_usage_events_store_counts_only(client, auth, research):
    _ready(client, auth)
    research.script = [{"output": [search_call(BULLETIN), search_call(COURSERA)],
                        "parsed": {"proposal": plan()}}]
    client.post("/career/roadmap/auto", headers=auth)

    (event,) = _usage()
    assert (event.kind, event.provider, event.web_searches, event.status) == (
        "auto_roadmap", "openai", 2, "completed")
    assert (event.input_tokens, event.output_tokens) == (100, 20)
    columns = set(models.AIUsageEvent.__table__.columns.keys())
    assert columns == {"id", "portfolio_id", "kind", "provider", "web_searches", "status",
                       "input_tokens", "output_tokens", "created_at"}


# --- Response handling after the incomplete live test -----------------------------

def test_requests_use_strict_schema_low_reasoning_and_output_caps(client, auth, fake):
    _ready(client, auth)
    fake.script = [{}, {"parsed": {"proposal": plan()}}]
    client.post("/career/chat", headers=auth, json={"message": "Hello"})
    client.post("/career/roadmap/auto", headers=auth)
    chat, roadmap = fake.calls

    for call in (chat, roadmap):
        fmt = call["text"]["format"]
        assert (fmt["type"], fmt["strict"], fmt["name"]) == ("json_schema", True, "AIChatResponse")
        assert call["reasoning"] == {"effort": "low"}
        assert "text_format" not in call
    assert chat["max_output_tokens"] == 3000
    assert roadmap["max_output_tokens"] == 10000
    # Roadmap answers are told how long they may be.
    assert "LENGTH LIMITS" in roadmap["instructions"]
    assert "at most 6 goals with at most 5 short milestones" in roadmap["instructions"]
    assert "at most 2 resources per milestone" in roadmap["instructions"]
    assert "LENGTH LIMITS" not in chat["instructions"]


def test_reasoning_and_output_caps_are_configurable(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_reasoning_effort", "minimal")
    monkeypatch.setattr(settings, "openai_max_output_tokens_roadmap", 8000)
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": plan()}}]
    client.post("/career/roadmap/auto", headers=auth)
    assert fake.calls[0]["reasoning"] == {"effort": "minimal"}
    assert fake.calls[0]["max_output_tokens"] == 8000


def test_cut_off_roadmap_gets_a_clear_error_and_its_usage_is_logged(client, auth, research):
    _ready(client, auth)
    research.script = [{
        "status": "incomplete", "reason": "max_output_tokens",
        "output": [search_call(BULLETIN), search_call(COURSERA)],
        "text": '{"reply": "Below is a personalized roadmap for students with alumni and',
        "usage": {"input_tokens": 21000, "output_tokens": 10000},
    }]
    r = client.post("/career/roadmap/auto", headers=auth)
    assert r.status_code == 502
    assert "too long and was cut off" in r.json()["detail"]
    assert "shorter roadmap" in r.json()["detail"]

    assert client.get("/career/proposals", headers=auth).json() == []
    assert client.get("/career/chat/history", headers=auth).json() == []
    (event,) = _usage()
    assert (event.status, event.web_searches, event.input_tokens, event.output_tokens) == (
        "incomplete", 2, 21000, 10000)

    # The failed attempt counts, so a retry is allowed but not unbounded.
    research.script = [{"parsed": {"proposal": plan()}}]
    assert client.post("/career/roadmap/auto", headers=auth).json()["status"] == "generated"
    assert [e.status for e in _usage()] == ["incomplete", "completed"]


def test_cut_off_chat_reply_and_content_filter_errors(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"status": "incomplete", "text": '{"reply": "Long'},
                   {"status": "incomplete", "reason": "content_filter", "text": ""}]
    r = client.post("/career/chat", headers=auth, json={"message": "Tell me everything"})
    assert r.status_code == 502 and "shorter question" in r.json()["detail"]
    r = client.post("/career/chat", headers=auth, json={"message": "Something"})
    assert r.status_code == 502 and "content filter" in r.json()["detail"]
    assert [e.status for e in _usage()] == ["incomplete", "incomplete"]
    assert client.get("/career/chat/history", headers=auth).json() == []


def test_truncated_json_with_completed_status_is_invalid(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"text": '{"reply": "Below is a per', "usage": {"output_tokens": 5}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"})
    assert r.status_code == 502 and "could not be processed" in r.json()["detail"]
    assert [(e.status, e.output_tokens) for e in _usage()] == [("invalid", 5)]


def test_refusal_is_reported_and_logged(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"refusal": "I can't help with that."}]
    r = client.post("/career/chat", headers=auth, json={"message": "Hello"})
    assert r.status_code == 502 and "declined" in r.json()["detail"]
    assert [e.status for e in _usage()] == ["invalid"]


def test_other_response_statuses_are_errors(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"status": "failed"}]
    r = client.post("/career/chat", headers=auth, json={"message": "Hello"})
    assert r.status_code == 502
    assert [e.status for e in _usage()] == ["failed"]
