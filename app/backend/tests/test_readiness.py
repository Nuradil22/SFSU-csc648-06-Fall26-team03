"""Readiness for a personalized roadmap.

Required: education level, major or field of study ("Undecided" counts), a
career goal, and at least 3 skills. Projects, work experience, and
certificates are optional (zero of each is valid). Ordinary chat is always
available; only roadmaps wait for the required details. OpenAI is the
scripted fake; no network.
"""

import openai
import pytest
from sqlalchemy import select

from app import ai, models
from app.config import settings
from app.database import SessionLocal

from . import openai_fakes
from .openai_fakes import FakeOpenAI


@pytest.fixture
def fake(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_web_search", False)
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


def _post(client, auth, path, json):
    r = client.post(path, headers=auth, json=json)
    assert r.status_code in (200, 201), r.text


def _essentials(client, auth, degree="B.A. Undecided", major=None, skills=("Writing", "Excel", "Spanish"),
                goal="Explore careers in public health"):
    _post(client, auth, "/portfolio/me/education",
          {"school_name": "San Francisco State University", "degree": degree, "major": major})
    for name in skills:
        _post(client, auth, "/portfolio/me/skills", {"name": name, "proficiency": "beginner"})
    if goal:
        _post(client, auth, "/portfolio/me/job-preferences", {"role": goal})


def _readiness(client, auth):
    return client.get("/career/readiness", headers=auth).json()


def _plan(title="First steps"):
    return {"title": title, "goals": [{"id": "g", "title": "Explore", "kind": "competency", "milestones": [
        {"id": "m", "title": "Meet an SFSU advisor", "completed": False, "step": "learn", "resources": []}]}]}


def _usage():
    with SessionLocal() as db:
        return db.scalars(select(models.AIUsageEvent.kind)).all()


# --- What counts --------------------------------------------------------------------

@pytest.mark.parametrize("degree, major, has_field", [
    ("B.A. Undecided", None, True),
    ("B.S.", "Undecided", True),
    ("B.S. Nursing", None, True),
    ("Bachelor of Science in Kinesiology", None, True),
    ("High school diploma", "Biology", True),
    ("B.S.", None, False),
    ("Bachelor of Science", None, False),
    ("Associate of Arts", "", False),
])
def test_major_comes_from_the_major_field_or_the_degree_box(degree, major, has_field):
    assert ai._has_field({"degree": degree, "major": major}) is has_field


def test_zero_projects_experience_and_certificates_is_ready(client, auth):
    _essentials(client, auth)
    body = _readiness(client, auth)
    assert body["ready"] is True and body["missing"] == []
    optional = {item["key"] for item in body["optional_missing"]}
    assert {"projects", "experience", "certificates"} <= optional


@pytest.mark.parametrize("change, missing", [
    ({"degree": "B.S."}, ["major"]),
    ({"skills": ("Writing", "Excel")}, ["skills"]),
    ({"goal": None}, ["career_goal"]),
])
def test_each_missing_essential_is_named(client, auth, change, missing):
    _essentials(client, auth, **change)
    body = _readiness(client, auth)
    assert body["ready"] is False and [item["key"] for item in body["missing"]] == missing


# --- A ready student with nothing optional gets a roadmap ----------------------------

PUBLIC_HEALTH = "https://bulletin.sfsu.edu/courses/hed/"


def _public_health_plan(title="First steps"):
    """A verified, relevant offering for an undecided student exploring public health."""
    course = openai_fakes.resource("Introduction to Public Health", PUBLIC_HEALTH,
                                   description="Lets you test your interest in public health.")
    return openai_fakes.researched({"title": title, "goals": [{
        "id": "g", "title": "Explore public health", "kind": "competency",
        "serves": "Explore careers in public health", "milestones": [
            {"id": "m", "title": "Take Introduction to Public Health", "completed": False, "step": "learn",
             "resources": [course]}]}]})


def test_undecided_beginner_without_projects_gets_a_personalized_roadmap(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _essentials(client, auth)
    fake.script = [_public_health_plan()]
    r = client.post("/career/roadmap/auto", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "generated", r.text

    prompt = fake.calls[-1]["instructions"]
    assert "Undecided" in prompt and "Explore careers in public health" in prompt
    assert "Required for a personalized roadmap but not saved yet: nothing." in prompt
    assert "Projects" in prompt and "never suggest the student needs to make them up" in prompt

    fake.script = [_public_health_plan("Second")]
    r = client.post("/career/chat", headers=auth, json={"message": "Generate a new roadmap for me"})
    assert r.status_code == 200 and r.json()["proposal"]["title"] == "Second"


# --- Missing essentials: chat stays open, roadmaps wait -------------------------------

def test_chat_stays_available_with_an_empty_portfolio(client, auth, fake):
    fake.script = [{"parsed": {"reply": "Here are some majors to explore."}}]
    r = client.post("/career/chat", headers=auth, json={"message": "What can I do with a psychology degree?"})
    assert r.status_code == 200 and r.json()["reply"] == "Here are some majors to explore."

    prompt = fake.calls[-1]["instructions"]
    assert "Your education level" in prompt and "At least 3 skills" in prompt
    assert "do not create or revise a roadmap" in prompt
    assert [m["role"] for m in client.get("/career/chat/history", headers=auth).json()] == ["user", "assistant"]


def test_roadmap_request_names_what_is_missing_without_any_ai_call(client, auth, fake):
    _essentials(client, auth, degree="B.S.", skills=("Writing",))
    for call in (lambda: client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}),
                 lambda: client.post("/career/roadmap/auto", headers=auth)):
        r = call()
        assert r.status_code == 409
        detail = r.json()["detail"]
        assert "major or field of study" in detail and "At least 3 skills" in detail
        assert "Projects, work experience, and certificates are optional" in detail
    assert fake.calls == [] and _usage() == []
    assert client.get("/career/proposals", headers=auth).json() == []


def test_no_roadmap_slips_through_ordinary_chat_when_not_ready(client, auth, fake):
    _essentials(client, auth, goal=None)
    # An approved roadmap from before the student removed their goal.
    client.put("/career/roadmap", headers=auth, json=_plan("Approved"))
    fake.script = [{"parsed": {"reply": "Sure.", "proposal": _plan("Sneaky")}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make it shorter"})
    assert r.status_code == 200
    assert r.json()["proposal"] is None and r.json()["proposal_id"] is None
    assert "ROADMAP CHANGES" not in fake.calls[-1]["instructions"]
    assert client.get("/career/proposals", headers=auth).json() == []
    assert client.get("/career/roadmap", headers=auth).json()["title"] == "Approved"
