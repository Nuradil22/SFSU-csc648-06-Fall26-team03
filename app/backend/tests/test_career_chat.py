"""Career chatbot (/career/*): chat, AI roadmap proposals, approve/reject,
owner edits, and per-account isolation. Ordinary chat runs with
AI_PROVIDER=mock; roadmaps come from the scripted OpenAI fake with a verified
educational offering (the mock provider never creates a roadmap)."""

import openai
import pytest

from app.config import settings

from . import openai_fakes
from .conftest import signup


def _add(client, headers, path, json):
    r = client.post(path, headers=headers, json=json)
    assert r.status_code == 201, r.text


def _with_portfolio(client, headers, skills=("Python", "SQL", "Git"), role="Data Engineer"):
    """A portfolio that meets the assistant's minimum, built the way the
    dashboard saves it (degree and major in one field, job preference role)."""
    _add(client, headers, "/portfolio/me/education",
         {"school_name": "San Francisco State University", "degree": "B.S. Computer Science"})
    for name in skills:
        _add(client, headers, "/portfolio/me/skills", {"name": name})
    _add(client, headers, "/portfolio/me/job-preferences", {"role": role})
    _add(client, headers, "/projects", {"title": f"{skills[0]} pipeline"})


@pytest.fixture
def edu_ai(monkeypatch):
    """OpenAI fake with research on; each roadmap request gets a verified
    educational roadmap."""
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_web_search", True)
    monkeypatch.setattr(openai, "OpenAI", openai_fakes.FakeOpenAI)
    return openai_fakes.FakeOpenAI


def _roadmap_proposal(client, headers):
    openai_fakes.FakeOpenAI.script.append(openai_fakes.researched(openai_fakes.educational_plan()))
    r = client.post("/career/chat", headers=headers, json={"message": "Make me a roadmap"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["proposal_id"] and body["proposal"]["goals"]
    return body


def test_chat_requires_login(client):
    assert client.post("/career/chat", json={"message": "hi"}).status_code == 401
    assert client.get("/career/roadmap").status_code == 401
    assert client.get("/career/proposals").status_code == 401
    assert client.get("/career/readiness").status_code == 401


def test_chat_is_personalized_and_saved(client, auth):
    _with_portfolio(client, auth)
    r = client.post("/career/chat", headers=auth, json={"message": "What should I learn?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "mock"
    assert "Data Engineer" in body["reply"] and "Python" in body["reply"]
    assert body["proposal_id"] is None
    history = client.get("/career/chat/history", headers=auth).json()
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_chat_rejects_empty_and_oversized_messages(client, auth):
    assert client.post("/career/chat", headers=auth, json={"message": ""}).status_code == 422
    assert client.post("/career/chat", headers=auth, json={"message": "x" * 3001}).status_code == 422


def test_roadmap_proposal_approve_flow(client, auth, edu_ai):
    _with_portfolio(client, auth)
    assert client.get("/career/roadmap", headers=auth).json() is None

    body = _roadmap_proposal(client, auth)
    pid = body["proposal_id"]
    # Not official until approved.
    assert client.get("/career/roadmap", headers=auth).json() is None
    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [pid]

    r = client.post(f"/career/proposals/{pid}/approve", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    roadmap = client.get("/career/roadmap", headers=auth).json()
    assert roadmap["title"] == body["proposal"]["title"]
    assert roadmap["goals"] == body["proposal"]["goals"]
    assert roadmap["educational"] is True and roadmap["offerings"] == 1
    assert client.get("/career/proposals", headers=auth).json() == []
    # Cannot be decided twice.
    assert client.post(f"/career/proposals/{pid}/reject", headers=auth).status_code == 409

    # Owner edit: tick a milestone (what the Roadmap page does).
    goals = roadmap["goals"]
    goals[0]["milestones"][0]["completed"] = True
    r = client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": goals})
    assert r.status_code == 200
    assert client.get("/career/roadmap", headers=auth).json()["goals"][0]["milestones"][0]["completed"] is True


def test_roadmap_proposal_reject_flow(client, auth, edu_ai):
    _with_portfolio(client, auth)
    pid = _roadmap_proposal(client, auth)["proposal_id"]
    r = client.post(f"/career/proposals/{pid}/reject", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert client.get("/career/roadmap", headers=auth).json() is None
    assert client.get("/career/proposals", headers=auth).json() == []
    assert client.post(f"/career/proposals/{pid}/maybe", headers=auth).status_code == 400


def test_roadmaps_are_separated_by_account(client, auth, edu_ai):
    other = signup(client, email="other-career@sfsu.edu")
    _with_portfolio(client, auth)
    _with_portfolio(client, other)

    pid = _roadmap_proposal(client, auth)["proposal_id"]
    # Another account can't see, approve, or reject it.
    assert client.get("/career/proposals", headers=other).json() == []
    assert client.post(f"/career/proposals/{pid}/approve", headers=other).status_code == 404
    assert client.post(f"/career/proposals/{pid}/reject", headers=other).status_code == 404

    client.post(f"/career/proposals/{pid}/approve", headers=auth)
    assert client.get("/career/roadmap", headers=auth).json() is not None
    assert client.get("/career/roadmap", headers=other).json() is None
    assert client.get("/career/chat/history", headers=other).json() == []

    # Editing my roadmap doesn't touch theirs and vice versa.
    client.put("/career/roadmap", headers=other, json={
        "title": "Theirs", "goals": [{"id": "g", "title": "G", "milestones": [{"title": "m"}]}],
    })
    assert client.get("/career/roadmap", headers=auth).json()["title"] != "Theirs"
    assert client.get("/career/roadmap", headers=other).json()["title"] == "Theirs"


# --- Portfolio readiness (roadmaps need the essentials; chat is always open) ----

def _missing(client, headers):
    body = client.get("/career/readiness", headers=headers).json()
    return body["ready"], [item["key"] for item in body["missing"]]


def test_empty_portfolio_blocks_roadmaps_for_every_provider(client, auth, monkeypatch):
    assert _missing(client, auth) == (False, ["education", "major", "career_goal", "skills"])

    for provider in ("mock", "openai", "anthropic"):
        monkeypatch.setattr(settings, "ai_provider", provider)
        r = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"})
        assert r.status_code == 409, provider
        assert "To create your personalized roadmap, I still need" in r.json()["detail"]

    # Nothing is stored for a blocked request.
    assert client.get("/career/chat/history", headers=auth).json() == []
    assert client.get("/career/proposals", headers=auth).json() == []


def test_partial_portfolio_lists_only_what_is_missing_then_unlocks(client, auth):
    _add(client, auth, "/portfolio/me/education",
         {"school_name": "San Francisco State University", "degree": "B.S. Biology"})
    _add(client, auth, "/portfolio/me/skills", {"name": "Lab safety"})
    assert _missing(client, auth) == (False, ["career_goal", "skills"])

    # Saving the rest from the dashboard is picked up with no other step;
    # no project, experience, or certificate is needed.
    for name in ("Microscopy", "R"):
        _add(client, auth, "/portfolio/me/skills", {"name": name})
    _add(client, auth, "/portfolio/me/job-preferences", {"role": "Research Associate"})

    body = client.get("/career/readiness", headers=auth).json()
    assert body["ready"] is True and body["missing"] == []
    optional = [item["key"] for item in body["optional_missing"]]
    assert {"graduation_date", "projects", "experience", "certificates"} <= set(optional)
    assert client.post("/career/chat", headers=auth, json={"message": "Hi"}).status_code == 200


def test_school_alone_needs_an_education_level_and_a_major(client, auth):
    _add(client, auth, "/portfolio/me/education", {"school_name": "SFSU"})
    for name in ("Python", "SQL", "Git"):
        _add(client, auth, "/portfolio/me/skills", {"name": name})
    _add(client, auth, "/portfolio/me/job-preferences", {"role": "Data Analyst"})
    _add(client, auth, "/portfolio/me/experience",
         {"experience_type": "internship", "organization": "Acme", "position": "Intern"})
    assert _missing(client, auth) == (False, ["education", "major"])


# --- OpenAI path: the prompt is built from the caller's own saved data --------

@pytest.fixture
def fake_openai(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(openai, "OpenAI", openai_fakes.FakeOpenAI)
    return openai_fakes.FakeOpenAI.calls


def test_openai_prompt_uses_only_the_callers_portfolio(client, auth, fake_openai):
    other = signup(client, email="other-advisor@sfsu.edu")
    _with_portfolio(client, auth, skills=("Python", "SQL", "Git"), role="Data Engineer")
    _with_portfolio(client, other, skills=("Figma", "Illustrator", "Sketch"), role="UX Designer")

    assert client.post("/career/chat", headers=auth, json={"message": "Advice?"}).status_code == 200
    assert client.post("/career/chat", headers=other, json={"message": "Advice?"}).status_code == 200

    mine, theirs = (call["instructions"] for call in fake_openai)
    assert "Data Engineer" in mine and "Python" in mine
    assert "UX Designer" not in mine and "Figma" not in mine
    assert "UX Designer" in theirs and "Python" not in theirs
    # SFSU-scoped advisor that knows the date and what's missing,
    # and is told not to ask for saved information again.
    assert "San Francisco State University" in mine
    assert "Today's date is" in mine
    assert "Expected graduation year" in mine
    assert "Never ask the student to re-enter" in mine
    # The student's own email/name never reach the AI.
    assert "student@sfsu.edu" not in mine and "Sam Student" not in mine


def test_openai_prompt_includes_pending_draft_for_follow_ups(client, auth, edu_ai, monkeypatch):
    _with_portfolio(client, auth)
    proposal = _roadmap_proposal(client, auth)["proposal"]

    fake_openai = edu_ai.calls
    edu_ai.script = [openai_fakes.researched(openai_fakes.educational_plan(title="Shorter"))]
    r = client.post("/career/chat", headers=auth, json={"message": "Make that roadmap shorter"})
    assert r.status_code == 200, r.text
    assert r.json()["proposal"]["title"] == "Shorter"
    prompt = fake_openai[-1]["instructions"]
    assert proposal["title"] in prompt
    assert prompt.split("DRAFT AWAITING APPROVAL")[1].strip() != "none"
    # Prior turns are sent as conversation history.
    assert fake_openai[-1]["input"][0] == {"role": "user", "content": "Make me a roadmap"}


# --- Milestone resources survive owner edits ----------------------------------

def test_roadmap_resources_are_kept_and_sanitized(client, auth):
    good = {"title": "SFSU Bulletin", "url": "https://bulletin.sfsu.edu/", "provider": "SFSU", "extra": "x"}
    goals = [{"id": "g", "title": "Plan courses", "milestones": [{
        "id": "m", "title": "Pick electives", "completed": False,
        "resources": [
            good,
            {"title": "Bad", "url": "javascript:alert(1)"},
            {"title": "Plain http", "url": "http://example.com"},
            {"title": "", "url": "https://example.com"},
            "not-a-dict",
        ],
    }]}]
    r = client.put("/career/roadmap", headers=auth, json={"title": "Plan", "goals": goals})
    assert r.status_code == 200
    saved = r.json()["goals"][0]["milestones"][0]["resources"]
    assert saved == [{"title": "SFSU Bulletin", "url": "https://bulletin.sfsu.edu/", "provider": "SFSU"}]

    # Ticking the milestone (what the Roadmap page sends back) keeps its links.
    goals = r.json()["goals"]
    goals[0]["milestones"][0]["completed"] = True
    again = client.put("/career/roadmap", headers=auth, json={"title": "Plan", "goals": goals}).json()
    assert again["goals"][0]["milestones"][0]["resources"] == saved


# --- The mock provider never invents a roadmap --------------------------------

def test_mock_provider_never_creates_a_generic_roadmap(client, auth):
    """Without research there is no verified offering, so a roadmap request
    is answered with an explanation; nothing is stored or approvable."""
    _with_portfolio(client, auth)
    r = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["proposal"] is None and body["proposal_id"] is None
    assert body["roadmap_unverified"] is True
    assert "verified" in body["reply"] and "no roadmap was created" in body["reply"]
    assert client.get("/career/proposals", headers=auth).json() == []

    # Ordinary chat mentioning a plan or goal doesn't create one either.
    r = client.post("/career/chat", headers=auth, json={"message": "What goal should I plan for?"})
    assert r.json()["proposal"] is None

    auto = client.post("/career/roadmap/auto", headers=auth).json()
    assert auto["status"] == "unverified" and "proposal" not in auto
