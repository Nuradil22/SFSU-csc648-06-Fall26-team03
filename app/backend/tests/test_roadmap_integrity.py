"""P2: unique roadmap ids, precise roadmap-request detection, and progress
kept when an updated roadmap is approved. OpenAI is the scripted fake."""

import openai
import pytest
from sqlalchemy import select

from app import models
from app.config import settings
from app.database import SessionLocal
from app.routers import career_chat as cc
from app.routers.career_chat import carry_over_progress, wants_roadmap

from . import openai_fakes
from .openai_fakes import FakeOpenAI


def _ready(client, headers):
    client.post("/portfolio/me/education", headers=headers,
                json={"school_name": "San Francisco State University", "degree": "B.S. Computer Science"})
    for name in ("Python", "SQL", "Git"):
        client.post("/portfolio/me/skills", headers=headers, json={"name": name})
    client.post("/portfolio/me/job-preferences", headers=headers, json={"role": "Data Engineer"})
    client.post("/projects", headers=headers, json={"title": "Pipeline"})


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


def _plan(title, *goals):
    """goals: (goal title, [(milestone title, completed), ...]); ids repeat on
    purpose. A valid educational roadmap: each learning stage serves the
    student's goal and its steps carry a verified course (see _step)."""
    course = openai_fakes.resource("Database Systems", BULLETIN,
                                   description="Relational design for your Data Engineer goal.")
    return {"title": title, "goals": [
        {"id": "g1", "title": goal_title, "kind": "competency", "serves": "Data Engineer", "milestones": [
            {"id": "m1", "title": m, "completed": done, "resources": [course]} for m, done in milestones
        ]}
        for goal_title, milestones in goals
    ]}


def _step(proposal):
    """A scripted roadmap answer whose search returned its course page."""
    return openai_fakes.researched(proposal)


# --- Unique ids -------------------------------------------------------------------

def test_duplicate_ai_ids_are_made_unique(client, auth, research):
    fake = research
    _ready(client, auth)
    fake.script = [_step(_plan(
        "Plan", ("Learn", [("SQL", False), ("Python", False)]), ("Build", [("Pipeline", False)])))]
    goals = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal"]["goals"]

    goal_ids = [g["id"] for g in goals]
    milestone_ids = [m["id"] for g in goals for m in g["milestones"]]
    assert len(set(goal_ids)) == 2 and goal_ids[0] == "g1"
    assert len(set(milestone_ids)) == 3 and milestone_ids[0] == "m1"


def test_ticking_one_milestone_never_ticks_a_former_duplicate(client, auth, research):
    fake = research
    _ready(client, auth)
    fake.script = [_step(_plan(
        "Plan", ("Learn", [("SQL", False)]), ("Build", [("Pipeline", False)])))]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)

    roadmap = client.get("/career/roadmap", headers=auth).json()
    first = roadmap["goals"][0]["milestones"][0]["id"]
    for goal in roadmap["goals"]:  # what the Roadmap page does: tick by id
        for milestone in goal["milestones"]:
            milestone["completed"] = milestone["id"] == first
    saved = client.put("/career/roadmap", headers=auth,
                       json={"title": roadmap["title"], "goals": roadmap["goals"]}).json()
    assert [m["completed"] for g in saved["goals"] for m in g["milestones"]] == [True, False]


def test_owner_edits_keep_existing_unique_ids(client, auth):
    goals = [{"id": "goal-a", "title": "A", "milestones": [{"id": "x1", "title": "one"}, {"id": "x2", "title": "two"}]},
             {"id": "goal-b", "title": "B", "milestones": [{"id": "x3", "title": "three"}]}]
    saved = client.put("/career/roadmap", headers=auth, json={"title": "Mine", "goals": goals}).json()
    assert [g["id"] for g in saved["goals"]] == ["goal-a", "goal-b"]
    assert [m["id"] for g in saved["goals"] for m in g["milestones"]] == ["x1", "x2", "x3"]


# --- Roadmap-request detection ------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Make me a roadmap", "Please regenerate my roadmap", "Update my road map", "Create my roadmap",
    "I need a new career plan", "Can you revise the roadmap for data science?", "Please make me a new roadmap",
    "Please generate an updated roadmap based on my latest portfolio.", "Make that roadmap shorter",
    "new roadmap please", "Give me a roadmap", "I want a data engineering roadmap",
    "Change the plan to focus on AI", "my roadmap needs an update", "Rebuild my study plan",
    "Can you build me a detailed cloud computing roadmap?",
])
def test_explicit_roadmap_requests_are_recognized(text):
    assert wants_roadmap(text)


@pytest.mark.parametrize("text", [
    "Do I need to follow my roadmap in order?", "I want to understand my roadmap",
    "Can you give me feedback on my roadmap?", "What does my roadmap say about internships?",
    "How do I make progress on my roadmap?", "Should I update my portfolio before my roadmap?",
    "What is new in my roadmap?", "Is my roadmap good?", "How long will my roadmap take?",
    "What does a roadmap mean?", "Make a plan to study for my exam", "Which courses should I take?",
])
def test_questions_about_a_roadmap_are_not_requests(text):
    assert not wants_roadmap(text)


def test_question_about_roadmap_keeps_the_draft_and_the_daily_limit(client, auth, research, monkeypatch):
    fake = research
    monkeypatch.setattr(settings, "ai_roadmap_generations_per_day", 1)
    _ready(client, auth)
    fake.script = [_step(_plan("Draft", ("Learn", [("SQL", False)])))]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]

    r = client.post("/career/chat", headers=auth, json={"message": "Do I need to follow my roadmap in order?"})
    assert r.status_code == 200 and r.json()["proposal_id"] is None
    assert "ROADMAP REQUEST" not in fake.calls[-1]["instructions"]
    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [pid]
    with SessionLocal() as db:
        kinds = [e.kind for e in db.scalars(select(models.AIUsageEvent)).all()]
    assert kinds == ["chat_roadmap", "chat"]


# --- Progress kept on approval ---------------------------------------------------------

def test_carry_over_progress_matches_titles_and_never_uncompletes():
    old = [{"milestones": [{"title": "Meet your CS advisor", "completed": True},
                           {"title": "Learn SQL", "completed": False}]}]
    new = [{"milestones": [{"title": "meet your CS advisor.", "completed": False},
                           {"title": "Learn SQL", "completed": False},
                           {"title": "Already done", "completed": True}]}]
    result = carry_over_progress(old, new)
    assert [m["completed"] for m in result[0]["milestones"]] == [True, False, True]
    assert new[0]["milestones"][0]["completed"] is False  # input untouched


def test_approving_an_updated_roadmap_keeps_finished_milestones(client, auth, research):
    fake = research
    _ready(client, auth)
    fake.script = [_step(_plan(
        "Original", ("Start", [("Meet your CS advisor", False), ("Learn SQL", False)])))]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)

    roadmap = client.get("/career/roadmap", headers=auth).json()
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})

    # The AI's update repeats the finished milestone but forgets its progress.
    fake.script = [_step(_plan(
        "Updated", ("Start", [("Meet your CS advisor", False), ("Take an upper-division database course", False)])))]
    new = client.post("/career/chat", headers=auth, json={"message": "Update my roadmap"}).json()

    # Rejecting changes nothing.
    assert client.get("/career/roadmap", headers=auth).json()["title"] == "Original"

    client.post(f"/career/proposals/{new['proposal_id']}/approve", headers=auth)
    replaced = client.get("/career/roadmap", headers=auth).json()
    assert replaced["title"] == "Updated"
    assert [(m["title"], m["completed"]) for m in replaced["goals"][0]["milestones"]] == [
        ("Meet your CS advisor", True), ("Take an upper-division database course", False)]


def test_rejecting_an_update_leaves_progress_alone(client, auth, research):
    fake = research
    _ready(client, auth)
    fake.script = [_step(_plan("Original", ("Start", [("Learn SQL", False)])))]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)
    roadmap = client.get("/career/roadmap", headers=auth).json()
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})

    fake.script = [_step(_plan("Other", ("Start", [("Learn Spark", False)])))]
    new = client.post("/career/chat", headers=auth, json={"message": "Update my roadmap"}).json()
    client.post(f"/career/proposals/{new['proposal_id']}/reject", headers=auth)

    kept = client.get("/career/roadmap", headers=auth).json()
    assert kept["title"] == "Original" and kept["goals"][0]["milestones"][0]["completed"] is True


# --- Revising a long pending roadmap (output cap) ---------------------------------------

BULLETIN = "https://bulletin.sfsu.edu/courses/csc/"
COURSERA = "https://www.coursera.org/professional-certificates/google-data-analytics"


def _big_plan(title, goals=6, milestones=5, with_links=True):
    links = [openai_fakes.resource("Database Systems", BULLETIN),
             openai_fakes.resource("Data Analytics", COURSERA, provider="Coursera")] if with_links else []
    return {"title": title, "goals": [
        {"id": f"g{i}", "title": f"Goal {i}", "kind": "competency", "serves": "Data Engineer", "milestones": [
            {"id": f"m{i}-{j}", "title": f"Milestone {i}-{j}", "completed": False, "resources": links}
            for j in range(milestones)]}
        for i in range(goals)]}


def _pending_big_draft(client, auth, fake, monkeypatch):
    """A full-size researched draft (6 goals x 5 milestones, 2 links each)."""
    monkeypatch.setattr(settings, "openai_web_search", True)
    fake.script = [{"output": [openai_fakes.search_call(BULLETIN, COURSERA)],
                    "parsed": {"proposal": _big_plan("Full draft")}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert body["proposal_id"]
    return body["proposal_id"]


def test_ordinary_chat_without_a_roadmap_keeps_the_chat_cap(client, auth, fake):
    _ready(client, auth)
    client.post("/career/chat", headers=auth, json={"message": "How do I prepare for interviews?"})
    call = fake.calls[-1]
    assert call["max_output_tokens"] == 3000
    assert "ROADMAP CHANGES" not in call["instructions"]


def test_long_pending_draft_revision_uses_roadmap_cap_without_research(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "ai_roadmap_generations_per_day", 1)
    _ready(client, auth)
    first = _pending_big_draft(client, auth, fake, monkeypatch)

    # The revision repeats the whole draft, links included (large output).
    fake.script = [{"parsed": {"reply": "Shorter version.", "proposal": _big_plan("Shorter draft", goals=5)},
                    "usage": {"output_tokens": 6200}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make it shorter"})
    assert r.status_code == 200, r.text

    call = fake.calls[-1]
    assert call["max_output_tokens"] == 10000
    assert "ROADMAP CHANGES" in call["instructions"] and "LENGTH LIMITS" in call["instructions"]
    assert "ROADMAP REQUEST" not in call["instructions"]
    assert "tools" not in call  # no fresh research for a revision

    body = r.json()
    goals = body["proposal"]["goals"]
    assert len(goals) == 5 and all(len(g["milestones"]) == 5 for g in goals)
    # Links already on the draft are kept (verified when the draft was made).
    assert [x["url"] for x in goals[0]["milestones"][0]["resources"]] == [BULLETIN, COURSERA]
    ids = [g["id"] for g in goals] + [m["id"] for g in goals for m in g["milestones"]]
    assert len(set(ids)) == len(ids)

    # The old draft is replaced; the daily roadmap allowance was not used.
    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [body["proposal_id"]]
    assert body["proposal_id"] != first
    with SessionLocal() as db:
        events = db.scalars(select(models.AIUsageEvent)).all()
    assert [(e.kind, e.status) for e in events] == [("chat_roadmap", "completed"), ("chat", "completed")]


def test_revising_an_approved_roadmap_uses_roadmap_cap_and_keeps_progress(client, auth, fake, monkeypatch):
    _ready(client, auth)
    pid = _pending_big_draft(client, auth, fake, monkeypatch)
    client.post(f"/career/proposals/{pid}/approve", headers=auth)
    roadmap = client.get("/career/roadmap", headers=auth).json()
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})

    fake.script = [{"parsed": {"proposal": _big_plan("Simpler", goals=3)}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Simplify it"}).json()
    assert fake.calls[-1]["max_output_tokens"] == 10000
    # Not applied until approved; then the finished milestone stays finished.
    assert client.get("/career/roadmap", headers=auth).json()["title"] == "Full draft"
    client.post(f"/career/proposals/{body['proposal_id']}/approve", headers=auth)
    assert client.get("/career/roadmap", headers=auth).json()["goals"][0]["milestones"][0]["completed"] is True


def test_cut_off_revision_keeps_the_pending_draft_and_says_why(client, auth, fake, monkeypatch):
    _ready(client, auth)
    first = _pending_big_draft(client, auth, fake, monkeypatch)

    fake.script = [{"status": "incomplete", "reason": "max_output_tokens", "text": '{"reply": "Short',
                    "usage": {"output_tokens": 10000}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make it shorter"})
    assert r.status_code == 502
    assert "cut off" in r.json()["detail"] and "shorter roadmap" in r.json()["detail"]

    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [first]
    history = client.get("/career/chat/history", headers=auth).json()
    assert [m["content"] for m in history if m["role"] == "user"] == ["Make me a roadmap"]
    with SessionLocal() as db:
        last = db.scalars(select(models.AIUsageEvent).order_by(models.AIUsageEvent.id.desc())).first()
    assert (last.kind, last.status, last.output_tokens) == ("chat", "incomplete", 10000)


def test_normal_message_with_a_draft_still_answers_normally(client, auth, fake, monkeypatch):
    _ready(client, auth)
    first = _pending_big_draft(client, auth, fake, monkeypatch)
    fake.script = [{"parsed": {"reply": "Practice behavioral questions."}}]
    r = client.post("/career/chat", headers=auth, json={"message": "How do I prepare for interviews?"})
    assert r.status_code == 200 and r.json()["proposal_id"] is None
    assert r.json()["reply"] == "Practice behavioral questions."
    assert [p["id"] for p in client.get("/career/proposals", headers=auth).json()] == [first]


# --- Proactive educational roadmaps (generic-roadmap fix) ---------------------------------

@pytest.mark.parametrize("text", [
    "okay provide me with a roadmap", "Generate a new career roadmap for me", "okay create me a career guide",
    "Can you suggest a roadmap for me?", "Recommend a learning roadmap", "Design a study plan for me",
    "Outline a roadmap to become a backend developer", "Put together a roadmap for me", "Come up with a career plan",
    "redo the roadmap",
])
def test_more_ways_of_asking_for_a_roadmap(text):
    assert wants_roadmap(text)


@pytest.mark.parametrize("text", [
    "Show me my roadmap", "Recommend courses for my roadmap", "What courses do you recommend for my roadmap?",
    "Can you suggest improvements to my roadmap?", "Can you help me with my roadmap?",
    "What career guide books exist?",
])
def test_requests_about_an_existing_roadmap_still_do_not_regenerate(text):
    assert not wants_roadmap(text)


def test_roadmap_prompt_requires_specific_education(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _ready(client, auth)
    fake.script = [_step(_plan("P", ("Learn", [("SQL", False)]))), {}]
    client.post("/career/chat", headers=auth, json={"message": "okay provide me with a roadmap"})
    client.post("/career/chat", headers=auth, json={"message": "How do I prepare for interviews?"})
    roadmap_call, chat_call = fake.calls

    prompt = roadmap_call["instructions"]
    assert "ROADMAP REQUEST" in prompt and "STRUCTURE:" in prompt
    assert "Never make a goal that only lists courses or certificates" in prompt
    assert "sfsu.edu, then other .edu sites" in prompt and "Coursera or edX" in prompt
    assert "never to fill a provider quota" in prompt  # no forced providers
    assert "Plan your searches around the competencies" in prompt
    assert roadmap_call["tools"][0]["type"] == "web_search"
    assert "STRUCTURE:" not in chat_call["instructions"]


def test_without_research_the_roadmap_points_to_the_bulletin_without_links(client, auth, fake):
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": _plan("P", ("Learn", [("SQL", False)]))}}]
    client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"})
    call = fake.calls[0]
    assert "tools" not in call
    assert "STRUCTURE:" in call["instructions"]
    assert "refers the student to the SFSU Bulletin" in call["instructions"]
    assert "Web research is not available" in call["instructions"]


def test_provide_me_with_a_roadmap_researches_and_keeps_the_approved_one(client, auth, research, monkeypatch):
    """The manual-test scenario: approved roadmap exists, student asks again."""
    fake = research
    _ready(client, auth)
    fake.script = [_step(_plan("Approved one", ("Start", [("Meet your CS advisor", False)])))]
    pid = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()["proposal_id"]
    client.post(f"/career/proposals/{pid}/approve", headers=auth)

    monkeypatch.setattr(settings, "openai_web_search", True)
    education = {"title": "Data engineering roadmap", "goals": [
        {"id": "edu", "title": "Coursework and certificates", "kind": "competency", "serves": "Data Engineer",
         "milestones": [
            {"id": "c1", "title": "Take CSC 675 Introduction to Database Systems", "completed": False,
             "resources": [openai_fakes.resource("CSC 675 Introduction to Database Systems", BULLETIN,
                                                 description="Relational design and SQL for backend roles.")]},
            {"id": "c2", "title": "Complete a data engineering certificate", "completed": False,
             "resources": [openai_fakes.resource("Data Engineering Certificate", COURSERA, provider="Coursera",
                                                 description="Pipelines and warehousing for your Data Engineer goal.")]},
        ]},
        {"id": "proj", "title": "Portfolio", "kind": "career_action", "milestones": [
            {"id": "p1", "title": "Add tests to the AI Assistant project", "completed": False, "resources": []}]},
    ]}
    fake.script = [{"output": [openai_fakes.search_call(BULLETIN), openai_fakes.search_call(COURSERA)],
                    "parsed": {"proposal": education}}]
    body = client.post("/career/chat", headers=auth, json={"message": "okay provide me with a roadmap"}).json()

    assert "ROADMAP REQUEST" in fake.calls[-1]["instructions"]
    assert body["web_search"] is True
    milestones = body["proposal"]["goals"][0]["milestones"]
    assert [(m["resources"][0]["title"], m["resources"][0]["provider"], m["resources"][0]["type"]) for m in milestones] == [
        ("Introduction to Database Systems", "San Francisco State University", "sfsu"),
        ("Data Engineering Certificate", "Coursera", "external"),
    ]
    # The course code is its own field; a "... Certificate" is never a course.
    assert milestones[0]["resources"][0]["code"] == "CSC 675"
    assert milestones[1]["resources"][0]["kind"] == "certificate"
    assert milestones[0]["resources"][0]["description"] == "Relational design and SQL for backend roles."
    # Pending until approved; the approved roadmap is untouched.
    assert client.get("/career/roadmap", headers=auth).json()["title"] == "Approved one"
    with SessionLocal() as db:
        assert [e.kind for e in db.scalars(select(models.AIUsageEvent)).all()][-1] == "chat_roadmap"


def test_resource_counts_are_logged(client, auth, fake, monkeypatch, caplog):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _ready(client, auth)
    fake.script = [{"output": [openai_fakes.search_call(BULLETIN)],
                    "parsed": {"proposal": {"title": "P", "goals": [{"id": "g", "title": "Edu",
                                                                     "serves": "Data Engineer", "milestones": [
                        {"id": "m", "title": "Course", "completed": False, "resources": [
                            openai_fakes.resource("Database Systems", BULLETIN),
                            openai_fakes.resource("Invented", "https://www.edx.org/invented", provider="edX")]}]}]}}}]
    with caplog.at_level("INFO", logger="app.routers.career_chat"):
        client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"})
    assert "Resources: recommended=2 kept=1" in caplog.text
    assert "edx.org" not in caplog.text  # counts only, no URLs


# --- Link precision and external providers -------------------------------------------------

DEPT = "https://bulletin.sfsu.edu/colleges/science-engineering/computer-science/"
EXTERNAL_CERT = "https://www.coursera.org/professional-certificates/ibm-backend-development"


def _edu_plan(*resources):
    return {"title": "Data roadmap", "goals": [{"id": "edu", "title": "Coursework and certificates",
                                                "kind": "competency", "serves": "Data Engineer", "milestones": [
        {"id": f"c{i}", "title": f"Education step {i}", "completed": False, "resources": [r]}
        for i, r in enumerate(resources)]}]}


def _roadmap(client, auth, fake, monkeypatch, sources, *resources, message="Generate a new career roadmap for me"):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _ready(client, auth)
    fake.script = [{"output": [openai_fakes.search_call(*sources)], "parsed": {"proposal": _edu_plan(*resources)}}]
    body = client.post("/career/chat", headers=auth, json={"message": message}).json()
    milestones = body["proposal"]["goals"][0]["milestones"]
    return body, [(m.get("resources") or [None])[0] for m in milestones]


def test_named_sfsu_course_links_to_the_course_listing(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _ready(client, auth)
    fake.script = [{
        "output": [openai_fakes.search_call(DEPT, BULLETIN, EXTERNAL_CERT)],
        "parsed": {"proposal": _edu_plan(
            openai_fakes.resource("CSC 675: Introduction to Database Systems", DEPT),
            openai_fakes.resource("Data Engineering Foundations", EXTERNAL_CERT, provider="Coursera"))},
        # The course listing shows the course, so the link moves there.
        "citations": {BULLETIN: "CSC 675 Introduction to Database Systems",
                      EXTERNAL_CERT: "Data Engineering Foundations | Coursera"},
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"}).json()
    links = [m["resources"][0] for m in body["proposal"]["goals"][0]["milestones"]]
    assert links[0]["url"] == BULLETIN and links[0]["type"] == "sfsu"
    assert (links[0]["code"], links[0]["title"]) == ("CSC 675", "Introduction to Database Systems")
    assert links[1]["url"] == EXTERNAL_CERT and links[1]["type"] == "external"


def test_course_link_is_not_switched_to_a_page_the_search_did_not_return(client, auth, fake, monkeypatch):
    _, links = _roadmap(client, auth, fake, monkeypatch, [DEPT, EXTERNAL_CERT],
                        openai_fakes.resource("CSC 675: Introduction to Database Systems", DEPT),
                        openai_fakes.resource("Data Engineering Foundations", EXTERNAL_CERT, provider="Coursera"))
    assert links[0]["url"] == DEPT


@pytest.mark.parametrize("url", [
    "https://www.coursera.org/",                                 # provider homepage
    "https://www.edx.org/search?q=backend",                      # search results
    "https://www.coursera.org/courses?query=sql",                # search query
    "https://www.coursera.org/browse/computer-science",          # browse page
    "https://bulletin.sfsu.edu/search/?P=CSC%20675",             # catalog search
])
def test_generic_pages_are_never_recommended(client, auth, fake, monkeypatch, url):
    _, links = _roadmap(client, auth, fake, monkeypatch, [url, BULLETIN],
                        openai_fakes.resource("Some course", url, provider="Provider"),
                        openai_fakes.resource("Database Systems", BULLETIN))
    assert links[0] is None and links[1]["url"] == BULLETIN


def test_link_check_covers_the_more_specific_course_listing(client, auth, fake, monkeypatch):
    import httpx

    from app.routers import career_chat as cc

    checked = []
    monkeypatch.setattr(settings, "resource_link_check", True)
    monkeypatch.setattr(cc, "_public_host", lambda host: True)
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(
        lambda r: checked.append(str(r.url)) or httpx.Response(404 if str(r.url) == BULLETIN else 200)))
    _, links = _roadmap(client, auth, fake, monkeypatch, [DEPT, BULLETIN],
                        openai_fakes.resource("CSC 675: Introduction to Database Systems", DEPT))
    assert BULLETIN in checked
    # The course listing failed the check, so the verified department page is used.
    assert links[0]["url"] == DEPT


def test_roadmap_research_asks_for_universities_first_without_forcing(client, auth, fake, monkeypatch):
    _roadmap(client, auth, fake, monkeypatch, [BULLETIN, EXTERNAL_CERT],
             openai_fakes.resource("Database Systems", BULLETIN),
             openai_fakes.resource("Data Engineering Foundations", EXTERNAL_CERT, provider="Coursera"))
    prompt = fake.calls[-1]["instructions"]
    assert "only where no university offering fits, search Coursera or edX" in prompt
    assert "Recommend a resource only if a page you retrieved shows it fits" in prompt
    assert "Never link a provider homepage" in prompt
    assert fake.calls[-1]["max_tool_calls"] == 3  # search limit unchanged


def test_verified_sfsu_and_external_resources_need_no_note(client, auth, fake, monkeypatch):
    body, _ = _roadmap(client, auth, fake, monkeypatch, [BULLETIN, EXTERNAL_CERT],
                       openai_fakes.resource("Database Systems", BULLETIN),
                       openai_fakes.resource("Data Engineering Foundations", EXTERNAL_CERT, provider="Coursera"))
    assert "Note:" not in body["reply"]


def test_unverified_external_resource_is_dropped_without_a_provider_quota_note(client, auth, fake, monkeypatch):
    body, links = _roadmap(client, auth, fake, monkeypatch, [BULLETIN],
                           openai_fakes.resource("Database Systems", BULLETIN),
                           openai_fakes.resource("Invented edX course", "https://www.edx.org/learn/invented", provider="edX"))
    assert links[0]["url"] == BULLETIN and links[1] is None
    # SFSU-only resources are fine: relevance, not provider variety, matters.
    assert "external course" not in body["reply"]


def test_no_verified_resources_at_all_means_no_roadmap(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", True)
    _ready(client, auth)
    fake.script = [{"output": [openai_fakes.search_call()], "parsed": {"proposal": _edu_plan(
        openai_fakes.resource("Invented", "https://www.edx.org/learn/invented", provider="edX"))}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"}).json()
    assert body["proposal"] is None and body["proposal_id"] is None and body["roadmap_unverified"] is True
    assert body["reply"] == cc.NOTE_NO_ROADMAP
    assert client.get("/career/proposals", headers=auth).json() == []


def test_no_note_without_research_or_for_ordinary_chat(client, auth, fake, monkeypatch):
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": _edu_plan(openai_fakes.resource("Database Systems", BULLETIN))}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    assert "Note:" not in body["reply"]  # research off: no searches, no note
    monkeypatch.setattr(settings, "openai_web_search", True)
    fake.script = [{"output": [openai_fakes.search_call()], "parsed": {"reply": "Try CSC electives."}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Which courses should I take?"}).json()
    assert body["reply"] == "Try CSC electives."
