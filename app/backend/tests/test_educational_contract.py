"""The educational-roadmap contract, enforced server-side for every provider.

A roadmap is presented as successful only when each learning stage centers on
a verified, named course, program, or certificate from an academic
institution or an accepted course platform, relevant to the student. Generic
career checklists are never stored or approved, whatever the model returns.
Records stored before the contract are flagged, never changed or deleted.

OpenAI is the scripted fake (tests/openai_fakes.py); no network.
"""

import openai
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app import models
from app.config import settings
from app.database import SessionLocal
from app.routers import career_chat as cc

from . import openai_fakes
from .openai_fakes import FakeOpenAI, educational_plan, researched, resource, search_call

BULLETIN = openai_fakes.EDU_URL
NURS = "https://bulletin.sfsu.edu/courses/nurs/"


@pytest.fixture
def research(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_web_search", True)
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


def _ready(client, headers):
    client.post("/portfolio/me/education", headers=headers,
                json={"school_name": "San Francisco State University", "degree": "B.S. Computer Science"})
    for name in ("Python", "SQL", "Git"):
        client.post("/portfolio/me/skills", headers=headers, json={"name": name})
    client.post("/portfolio/me/job-preferences", headers=headers, json={"role": "Data Engineer"})


def _portfolio_id():
    with SessionLocal() as db:
        return db.scalars(select(models.Portfolio.id)).first()


def _checklist_goal(title, *steps, kind="competency"):
    return {"id": "g", "title": title, "kind": kind, "serves": "Data Engineer", "milestones": [
        {"id": "m", "title": s, "completed": False, "step": "apply", "resources": []} for s in steps]}


# The shape of the rejected live output (pending proposal #7): eight goals of
# technical and career tasks, no named course, program, or certificate.
GENERIC = {"title": "Career Guide: Backend Engineering (Personalized)", "goals": [
    _checklist_goal("Master server-side programming & API design", "Choose FastAPI and build a CRUD API"),
    _checklist_goal("Become strong with databases", "Install PostgreSQL", "Write SQL joins"),
    _checklist_goal("Adopt testing and code quality", "Write unit tests with pytest"),
    _checklist_goal("Containerize, CI, and deployment", "Create a Dockerfile", "Add a GitHub Actions workflow"),
    _checklist_goal("Reliability and caching", "Integrate Redis caching"),
    _checklist_goal("Portfolio demos", "Publish the repo with a README", kind="career_action"),
    _checklist_goal("Interviews", "Practice algorithm problems", kind="career_action"),
    _checklist_goal("Networking", "Reach out to 5 alumni", kind="career_action"),
]}


# --- Rejected ---------------------------------------------------------------------

def test_generic_career_checklist_is_never_a_roadmap(client, auth, research):
    _ready(client, auth)
    research.script = [{"output": [search_call(BULLETIN)], "parsed": {"proposal": GENERIC}}]
    body = client.post("/career/chat", headers=auth, json={"message": "generate my specialized personal roadmap"}).json()
    assert body["proposal"] is None and body["proposal_id"] is None
    assert body["roadmap_unverified"] is True and body["reply"] == cc.NOTE_NO_ROADMAP
    assert client.get("/career/proposals", headers=auth).json() == []


def test_misspelled_request_takes_the_researched_roadmap_path(client, auth, research):
    """The live failure: "roadmpa" was treated as ordinary chat (no research,
    no gate). It is now a researched roadmap request."""
    _ready(client, auth)
    research.script = [{"output": [search_call(BULLETIN)], "parsed": {"proposal": GENERIC}}]
    client.post("/career/chat", headers=auth, json={"message": "generate my specialized personal roadmpa"})
    call = research.calls[-1]
    assert "ROADMAP REQUEST" in call["instructions"] and call["tools"][0]["type"] == "web_search"


def test_generic_checklist_revision_in_ordinary_chat_is_rejected(client, auth, research):
    """Ordinary chat may revise an existing roadmap; a revision without a
    verified offering is never stored either."""
    _ready(client, auth)
    client.put("/career/roadmap", headers=auth, json={"title": "Old", "goals": GENERIC["goals"][:2]})
    research.script = [{"parsed": {"reply": "Here you go.", "proposal": GENERIC}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make it shorter"}).json()
    assert body["proposal"] is None and body["roadmap_unverified"] is True
    assert client.get("/career/proposals", headers=auth).json() == []


def test_course_unrelated_to_the_student_is_dropped(client, auth, research):
    """A real, verified nursing course attached to a data engineering stage."""
    _ready(client, auth)
    patho = resource("Pathophysiology", NURS, code="NURS 312", description="Fits your goals.")
    plan = educational_plan()
    plan["goals"].append({"id": "g2", "title": "Data modeling", "kind": "competency", "serves": "Data Engineer",
                          "milestones": [{"id": "m3", "title": "Take NURS 312 Pathophysiology", "completed": False,
                                          "step": "learn", "resources": [patho]}]})
    research.script = [{"output": [search_call(BULLETIN, NURS)], "parsed": {"proposal": plan},
                        "citations": {BULLETIN: "Introduction to Database Systems",
                                      NURS: "NURS 312 Pathophysiology | Nursing (NURS)"}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert [g["title"] for g in body["proposal"]["goals"]] == ["Relational databases"]
    assert "unrelated to that stage" in body["reply"]


def test_the_same_course_is_kept_for_a_student_in_that_field(client, auth, research):
    client.post("/portfolio/me/education", headers=auth,
                json={"school_name": "San Francisco State University", "degree": "B.S. Nursing"})
    for name in ("CPR", "Patient communication", "Medical terminology"):
        client.post("/portfolio/me/skills", headers=auth, json={"name": name})
    client.post("/portfolio/me/job-preferences", headers=auth, json={"role": "Registered Nurse"})
    patho = resource("Pathophysiology", NURS, code="NURS 312", description="Core to clinical reasoning.")
    plan = {"title": "Path to RN", "goals": [{
        "id": "g", "title": "Disease processes", "kind": "competency", "serves": "Registered Nurse",
        "milestones": [{"id": "m", "title": "Take NURS 312 Pathophysiology", "completed": False, "step": "learn",
                        "resources": [patho]}]}]}
    research.script = [{"output": [search_call(NURS)], "parsed": {"proposal": plan},
                        "citations": {NURS: "NURS 312 Pathophysiology | Nursing (NURS)"}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    [item] = body["proposal"]["goals"][0]["milestones"][0]["resources"]
    assert (item["code"], item["title"], item["url"]) == ("NURS 312", "Pathophysiology", NURS)


@pytest.mark.parametrize("url", [
    "https://fastapi.tiangolo.com/tutorial/",          # documentation
    "https://github.com/example/backend-course",       # code host
    "https://medium.com/@someone/learn-sql-in-a-week",  # blog
    "https://www.coursera.org/",                       # provider homepage
    "https://www.sfsu.edu/",                           # institution homepage
])
def test_non_educational_or_generic_pages_never_count(client, auth, research, url):
    _ready(client, auth)
    plan = educational_plan(url=url, name="Learn Data Engineering")
    research.script = [researched(plan)]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert body["proposal"] is None and body["roadmap_unverified"] is True


def test_invented_course_title_is_never_shown(client, auth, research):
    _ready(client, auth)
    plan = educational_plan(name="Advanced Quantum Data Engineering")
    research.script = [{**researched(plan), "citations": {BULLETIN: "Computer Science (CSC)"}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert body["proposal"] is None and body["roadmap_unverified"] is True


def test_store_proposal_refuses_a_plan_without_offerings(client, auth):
    _ready(client, auth)
    with SessionLocal() as db, pytest.raises(HTTPException) as err:
        cc.store_proposal(db, _portfolio_id(), {"title": "T", "goals": GENERIC["goals"]}, "chat", "fp")
    assert err.value.status_code == 502
    with SessionLocal() as db:
        assert db.scalars(select(models.RoadmapProposal)).all() == []


# --- Accepted -----------------------------------------------------------------------

def test_valid_educational_roadmap_keeps_exact_verified_details(client, auth, research):
    _ready(client, auth)
    research.script = [researched(educational_plan())]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert body["proposal"]["educational"] is True and body["proposal"]["offerings"] == 1
    [item] = body["proposal"]["goals"][0]["milestones"][0]["resources"]
    assert (item["title"], item["provider"], item["url"], item["kind"], item["description"]) == (
        "Introduction to Database Systems", "San Francisco State University", BULLETIN, "course",
        "Your goal needs relational data design.")
    r = client.post(f"/career/proposals/{body['proposal_id']}/approve", headers=auth)
    assert r.status_code == 200


# --- Records stored before the contract: flagged, never changed ---------------------

def test_legacy_generic_draft_is_flagged_and_cannot_be_approved(client, auth):
    _ready(client, auth)
    with SessionLocal() as db:
        draft = models.RoadmapProposal(portfolio_id=_portfolio_id(), origin="chat", status="pending",
                                       title=GENERIC["title"], goals=GENERIC["goals"])
        db.add(draft)
        db.commit()
        pid = draft.id

    [listed] = client.get("/career/proposals", headers=auth).json()
    assert listed["id"] == pid and listed["educational"] is False and listed["offerings"] == 0
    auto = client.post("/career/roadmap/auto", headers=auth).json()
    assert auto["status"] == "pending" and auto["proposal"]["educational"] is False

    r = client.post(f"/career/proposals/{pid}/approve", headers=auth)
    assert r.status_code == 409 and "verified courses" in r.json()["detail"]
    # Kept exactly as it was; the student may still reject it.
    [still] = client.get("/career/proposals", headers=auth).json()
    assert still["goals"] == GENERIC["goals"]
    assert client.post(f"/career/proposals/{pid}/reject", headers=auth).json()["status"] == "rejected"


def test_legacy_approved_roadmap_and_progress_are_preserved(client, auth, research):
    _ready(client, auth)
    old = {"title": "Old plan", "goals": [_checklist_goal("Databases", "Write SQL joins", "Take a database course")]}
    old["goals"][0]["milestones"][1]["title"] = "Take Introduction to Database Systems"
    old["goals"][0]["milestones"][1]["completed"] = True
    client.put("/career/roadmap", headers=auth, json=old)

    roadmap = client.get("/career/roadmap", headers=auth).json()
    assert roadmap["educational"] is False and roadmap["title"] == "Old plan"
    assert roadmap["goals"][0]["milestones"][1]["completed"] is True
    auto = client.post("/career/roadmap/auto", headers=auth).json()
    assert auto["status"] == "approved" and auto["educational"] is False and research.calls == []

    # Ticking a step (what the Roadmap page does) still works, keeps earlier
    # progress, and the saved roadmap keeps its flag; it never becomes a draft.
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    saved = client.put("/career/roadmap", headers=auth,
                       json={"title": roadmap["title"], "goals": roadmap["goals"]}).json()
    assert [m["completed"] for m in saved["goals"][0]["milestones"]] == [True, True]
    assert saved["educational"] is False
    assert client.get("/career/proposals", headers=auth).json() == []

    # A new verified roadmap replaces it only on approval, keeping finished steps.
    research.script = [researched(educational_plan())]
    body = client.post("/career/chat", headers=auth, json={"message": "Generate a new roadmap"}).json()
    assert client.get("/career/roadmap", headers=auth).json()["title"] == "Old plan"
    client.post(f"/career/proposals/{body['proposal_id']}/approve", headers=auth)
    new = client.get("/career/roadmap", headers=auth).json()
    assert new["educational"] is True
    learn = new["goals"][0]["milestones"][0]
    assert learn["title"] == "Take Introduction to Database Systems" and learn["completed"] is True
