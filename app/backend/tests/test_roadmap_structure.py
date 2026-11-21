"""Competency-based roadmap structure: education is integrated into the goals
it teaches (learn -> apply), career-action goals need no courses, completed
coursework isn't recommended again, and older roadmaps keep working.

OpenAI is the scripted fake; pages come from the mock link check in
test_official_names. No network.
"""

import openai
import pytest
from openai.lib._parsing._responses import type_to_text_format_param
from sqlalchemy import select

from app import models
from app.config import settings
from app.database import SessionLocal
from app.routers import career_chat as cc

from . import openai_fakes
from .openai_fakes import FakeOpenAI, resource, search_call
from .test_official_names import BULLETIN, CERT, EDX, pages  # noqa: F401 - fixture

DB_COURSE = resource("Introduction to Database Systems", BULLETIN, code="CSC 675",
                     topics=["SQL", "normalization"], credential="academic_credit",
                     description="Your Data Engineer goal needs relational design.",
                     outcome="Design a normalized schema.")
AI_COURSE = resource("Artificial Intelligence", BULLETIN, code="CSC 665")
PIPELINES = resource("Introduction to Data Engineering", EDX, provider="IBM via edX",
                     topics=["data pipelines", "ETL"])
ANALYTICS = resource("Google Data Analytics Professional Certificate", CERT, provider="Coursera",
                     kind="certificate", credential="certificate", topics=["SQL", "Data Visualization"])


@pytest.fixture
def fake(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_web_search", True)
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


def _ready(client, headers, coursework=()):
    client.post("/portfolio/me/education", headers=headers, json={
        "school_name": "San Francisco State University", "degree": "B.S. Computer Science",
        "coursework": list(coursework)})
    for name in ("Python", "SQL", "Git"):
        client.post("/portfolio/me/skills", headers=headers, json={"name": name})
    client.post("/portfolio/me/job-preferences", headers=headers, json={"role": "Data Engineer"})
    client.post("/projects", headers=headers, json={"title": "Pipeline"})


def step(title, kind, *resources):
    return {"id": "m", "title": title, "completed": False, "step": kind, "resources": list(resources)}


def goal(title, kind, *milestones):
    """A goal; learning stages serve the test student's goal (Data Engineer)."""
    serves = "" if kind == "career_action" else "Data Engineer"
    return {"id": "g", "title": title, "kind": kind, "serves": serves, "milestones": list(milestones)}


def competency_plan():
    return {"title": "Data engineering roadmap", "goals": [
        goal("Relational databases", "competency",
             step("Take CSC 675 Introduction to Database Systems", "learn", DB_COURSE),
             step("Add a normalized schema to your Pipeline project", "apply")),
        goal("Data pipelines", "competency",
             step("Complete Introduction to Data Engineering", "learn", PIPELINES),
             step("Build a scheduled ETL job that loads 10k rows", "apply")),
        goal("Internship search", "career_action",
             step("Apply to 10 data engineering internships", "action"),
             step("Ask a CS professor for a referral", "action")),
    ]}


def _generate(client, auth, fake, proposal, sources=(BULLETIN, EDX, CERT), coursework=()):
    _ready(client, auth, coursework)
    fake.script = [{"output": [search_call(*sources)], "parsed": {"proposal": proposal}, "citations": {}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"})
    assert r.status_code == 200, r.text
    return r.json()


def _goals(body):
    return body["proposal"]["goals"]


# --- Education integrated into competencies ---------------------------------------

def test_resources_appear_in_multiple_relevant_goals(client, auth, fake, pages):
    body = _generate(client, auth, fake, competency_plan())
    taught = {
        g["title"]: [r["title"] for m in g["milestones"] for r in m.get("resources") or []]
        for g in _goals(body)
    }
    assert taught == {
        "Relational databases": ["Introduction to Database Systems"],
        "Data pipelines": ["Introduction to Data Engineering"],
        "Internship search": [],
    }
    assert "Note:" not in body["reply"]


def test_each_learning_goal_has_learn_knowledge_and_apply(client, auth, fake, pages):
    body = _generate(client, auth, fake, competency_plan())
    for g in _goals(body):
        if g["kind"] != "competency":
            continue
        steps = [m["step"] for m in g["milestones"]]
        assert steps[0] == "learn" and "apply" in steps
        [learned] = g["milestones"][0]["resources"]
        assert learned["topics"]                 # KNOWLEDGE: topics confirmed on the provider page
        assert learned["url"] in (BULLETIN, EDX)  # LEARN: the verified offering


def test_exact_official_titles_and_codes_are_preserved(client, auth, fake, pages):
    plan = competency_plan()
    plan["goals"][1]["milestones"][0] = step(
        "Earn the Google Data Analytics Professional Certificate", "learn", ANALYTICS)
    body = _generate(client, auth, fake, plan)
    db = _goals(body)[0]["milestones"][0]["resources"][0]
    cert = _goals(body)[1]["milestones"][0]["resources"][0]
    assert (db["code"], db["title"], db["credential_detail"]) == ("CSC 675", "Introduction to Database Systems", "3 units")
    assert (cert["title"], cert["kind"]) == ("Google Data Analytics Professional Certificate", "certificate")


def test_practical_application_follows_learning(client, auth, fake, pages):
    plan = competency_plan()
    plan["goals"][0]["milestones"].reverse()   # model put the project first
    plan["goals"][2]["milestones"].reverse()   # career goals keep their order
    body = _generate(client, auth, fake, plan)
    db, _, career = _goals(body)
    assert [m["step"] for m in db["milestones"]] == ["learn", "apply"]
    assert [m["title"] for m in career["milestones"]] == [
        "Ask a CS professor for a referral", "Apply to 10 data engineering internships"]


def test_career_action_goals_stay_resource_free_without_a_note(client, auth, fake, pages):
    body = _generate(client, auth, fake, competency_plan())
    career = _goals(body)[2]
    assert career["kind"] == "career_action"
    assert all("resources" not in m for m in career["milestones"])
    assert "couldn't verify a specific course or certificate for" not in body["reply"]


def test_competency_without_a_verified_course_is_named(client, auth, fake, pages):
    plan = competency_plan()
    plan["goals"][1]["milestones"][0] = step("Find a data engineering course in the SFSU Bulletin", "learn")
    body = _generate(client, auth, fake, plan)
    assert [g["title"] for g in _goals(body)] == ["Relational databases", "Internship search"]
    assert 'left out 1 learning stage ("Data pipelines")' in body["reply"]
    assert '"Internship search"' not in body["reply"]


def test_sfsu_only_roadmap_needs_no_provider_note(client, auth, fake, pages):
    plan = competency_plan()
    plan["goals"][1]["milestones"][0] = step("Take CSC 665 Artificial Intelligence", "learn", AI_COURSE)
    body = _generate(client, auth, fake, plan)
    assert all(r["type"] == "sfsu" for g in _goals(body) for m in g["milestones"] for r in m.get("resources") or [])
    assert "Note:" not in body["reply"]


# --- Personalization -----------------------------------------------------------------

def test_completed_coursework_is_not_recommended_again(client, auth, fake, pages):
    body = _generate(client, auth, fake, competency_plan(),
                     coursework=["CSC 675 Introduction to Database Systems", "CSC 413"])
    # The learn step that only repeated a finished course is gone, which leaves
    # its stage without an educational offering, so the stage is removed too.
    assert [g["title"] for g in _goals(body)] == ["Data pipelines", "Internship search"]
    assert "1 recommendation for coursework or certificates already in your portfolio" in body["reply"]
    assert 'left out 1 learning stage ("Relational databases")' in body["reply"]
    assert "couldn't confirm" not in body["reply"]          # not reported as unverified
    assert _goals(body)[0]["milestones"][0]["resources"][0]["title"] == "Introduction to Data Engineering"


def test_held_certificate_is_not_recommended_again(client, auth, fake, pages):
    _ready(client, auth)
    client.post("/portfolio/me/certificates", headers=auth,
                json={"name": "Google Data Analytics Professional Certificate", "issuer": "Google"})
    fake.script = [{"output": [search_call(CERT)], "citations": {}, "parsed": {"resources": [ANALYTICS]}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Which certificates should I get?"}).json()
    assert body["resources"] == []


def test_prompt_personalizes_instead_of_a_fixed_template(client, auth, fake, pages):
    _generate(client, auth, fake, competency_plan())
    prompt = fake.calls[-1]["instructions"]
    assert "competency THIS student still needs" in prompt
    assert "do not default to a fixed template or tech stack" in prompt
    assert "do not recommend a course or certificate already listed in their portfolio" in prompt
    assert "Coursework and certificates" not in prompt     # the old education-only goal pattern


def test_schema_asks_for_goal_kind_and_milestone_step():
    schema = type_to_text_format_param(cc.AIChatResponse)["schema"]["$defs"]
    assert schema["AIGoal"]["properties"]["kind"]["enum"] == ["competency", "career_action"]
    assert schema["AIMilestone"]["properties"]["step"]["enum"] == ["learn", "apply", "action"]
    assert "kind" in schema["AIGoal"]["required"] and "step" in schema["AIMilestone"]["required"]


def test_structure_is_logged_as_counts(client, auth, fake, pages, caplog):
    with caplog.at_level("INFO", logger="app.routers.career_chat"):
        _generate(client, auth, fake, competency_plan())
    assert "competency_goals=2 taught_goals=2 action_goals=1" in caplog.text


# --- Existing roadmaps ---------------------------------------------------------------

OLD = {"title": "Approved before P3", "goals": [
    {"id": "edu", "title": "Coursework and certificates", "milestones": [
        {"id": "c1", "title": "Take CSC 675", "completed": True,
         "resources": [{"title": "CSC courses", "url": BULLETIN, "type": "sfsu"}]}]},
    {"id": "p", "title": "Projects", "milestones": [
        {"id": "p1", "title": "Build an API", "completed": False}]},
]}


def test_previously_approved_roadmaps_keep_working(client, auth, fake):
    _ready(client, auth)
    with SessionLocal() as db:
        portfolio = db.scalars(select(models.Portfolio)).first()
        db.add(models.CareerRoadmap(portfolio_id=portfolio.id, title=OLD["title"], goals=OLD["goals"]))
        db.commit()

    roadmap = client.get("/career/roadmap", headers=auth).json()
    assert [g["title"] for g in roadmap["goals"]] == ["Coursework and certificates", "Projects"]
    assert "kind" not in roadmap["goals"][0] and "step" not in roadmap["goals"][0]["milestones"][0]

    # Ticking a milestone (owner edit) keeps everything else as it was.
    roadmap["goals"][1]["milestones"][0]["completed"] = True
    r = client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})
    assert r.status_code == 200, r.text
    saved = client.get("/career/roadmap", headers=auth).json()
    assert saved["goals"][0]["milestones"][0]["resources"][0]["title"] == "CSC courses"
    assert saved["goals"][0]["milestones"][0]["completed"] and saved["goals"][1]["milestones"][0]["completed"]


def test_structure_fields_survive_approval_and_owner_edits(client, auth, fake, pages):
    body = _generate(client, auth, fake, competency_plan())
    client.post(f"/career/proposals/{body['proposal_id']}/approve", headers=auth)
    roadmap = client.get("/career/roadmap", headers=auth).json()
    roadmap["goals"][0]["milestones"][0]["completed"] = True
    client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": roadmap["goals"]})
    saved = client.get("/career/roadmap", headers=auth).json()
    assert [g["kind"] for g in saved["goals"]] == ["competency", "competency", "career_action"]
    assert [m["step"] for m in saved["goals"][0]["milestones"]] == ["learn", "apply"]
    assert saved["goals"][0]["milestones"][0]["completed"] is True


def test_unknown_structure_values_are_dropped(client, auth):
    body = cc.RoadmapBody.model_validate({"title": "T", "goals": [
        {"id": "g", "title": "G", "kind": "bogus", "milestones": [{"id": "m", "title": "M", "step": "<script>"}]}]})
    plan = cc.clean_plan(body)
    assert "kind" not in plan["goals"][0] and "step" not in plan["goals"][0]["milestones"][0]


# --- Education-only goals are distributed (server-side, not just the prompt) ---------
#
# The failed manual test: the model put every course and certificate into one
# "Education" goal and left the other goals as generic checklists. Whatever
# the model writes, verified learning steps end up in the goal they teach.

def bucket_plan(*extra_bucket_steps):
    return {"title": "Data engineering roadmap", "goals": [
        goal("Education: confirmed SFSU courses & certificates", "competency",
             step("Take CSC 675 Introduction to Database Systems", "learn", DB_COURSE),
             step("Complete Introduction to Data Engineering", "learn", PIPELINES),
             *extra_bucket_steps),
        goal("Relational databases", "competency",
             step("Add a normalized schema to your Pipeline project", "apply")),
        goal("Data pipelines", "competency",
             step("Build a scheduled ETL job that loads 10k rows", "apply")),
        goal("Data engineering internships", "career_action",
             step("Apply to 10 data pipeline internships", "action")),
    ]}


def _taught(body):
    return {
        g["title"]: [(m["step"], [r["title"] for r in m.get("resources") or []]) for m in g["milestones"]]
        for g in _goals(body)
    }


def test_education_only_goal_is_distributed_into_the_goals_it_teaches(client, auth, fake, pages, caplog):
    with caplog.at_level("INFO", logger="app.routers.career_chat"):
        body = _generate(client, auth, fake, bucket_plan())
    assert _taught(body) == {
        "Relational databases": [("learn", ["Introduction to Database Systems"]), ("apply", [])],
        "Data pipelines": [("learn", ["Introduction to Data Engineering"]), ("apply", [])],
        "Data engineering internships": [("action", [])],
    }
    # Exact official names, codes, and verified details travel with the step.
    db = _goals(body)[0]["milestones"][0]["resources"][0]
    assert (db["code"], db["title"], db["topics"]) == ("CSC 675", "Introduction to Database Systems",
                                                       ["SQL", "normalization"])
    assert "education_only_goals=0 learn_steps_moved=2" in caplog.text


def test_career_action_goal_never_receives_courses(client, auth, fake, pages):
    plan = bucket_plan()
    plan["goals"] = [g for g in plan["goals"] if g["title"] != "Data pipelines"]
    body = _generate(client, auth, fake, plan)
    # "data pipeline internships" shares words with the pipelines course, but a
    # career-action goal is never a destination; the course stays where it was.
    assert _taught(body)["Data engineering internships"] == [("action", [])]
    assert ("learn", ["Introduction to Data Engineering"]) in _taught(body)[
        "Education: confirmed SFSU courses & certificates"]


def test_unmatched_learning_step_stays_rather_than_being_guessed(client, auth, fake, pages):
    body = _generate(client, auth, fake,
                     bucket_plan(step("Take CSC 665 Artificial Intelligence", "learn", AI_COURSE)))
    taught = _taught(body)
    assert taught["Education: confirmed SFSU courses & certificates"] == [("learn", ["Artificial Intelligence"])]
    assert taught["Relational databases"][0] == ("learn", ["Introduction to Database Systems"])


def test_ambiguous_match_is_not_moved():
    course = {"title": "Take Cloud Data Course", "step": "learn",
              "resources": [{"title": "Cloud Data", "url": BULLETIN}]}
    other = {"title": "Take Something Else", "step": "learn",
             "resources": [{"title": "Unrelated Topic", "url": EDX}]}
    plan = {"goals": [
        {"title": "Courses", "kind": "competency", "milestones": [course, other]},
        {"title": "Cloud", "kind": "competency", "milestones": [{"title": "Deploy", "step": "apply"}]},
        {"title": "Data", "kind": "competency", "milestones": [{"title": "Model", "step": "apply"}]},
    ]}
    plan, moved = cc.distribute_education(plan)
    assert moved == 0 and len(plan["goals"]) == 3


def test_without_goal_kinds_nothing_is_moved():
    # The shape of the failed manual-test draft: no kind/step data, so an
    # "Interview & applications" goal could not be told apart from a skill goal.
    plan = bucket_plan()
    for g in plan["goals"]:
        g.pop("kind")
        for m in g["milestones"]:
            m.pop("step")
    plan["goals"].append({"title": "Interview & applications", "milestones": [
        {"title": "Practice SQL exercises and database design questions"}]})
    before = [[m["title"] for m in g["milestones"]] for g in plan["goals"]]
    plan, moved = cc.distribute_education(plan)
    assert moved == 0
    assert [[m["title"] for m in g["milestones"]] for g in plan["goals"]] == before


def test_goals_that_already_apply_their_learning_are_left_alone():
    plan = competency_plan()
    before = [[m["title"] for m in g["milestones"]] for g in plan["goals"]]
    plan, moved = cc.distribute_education(plan)
    assert moved == 0
    assert [[m["title"] for m in g["milestones"]] for g in plan["goals"]] == before


def test_previously_approved_education_goal_is_not_restructured(client, auth, fake):
    # Only new AI proposals are distributed; stored roadmaps render as saved.
    _ready(client, auth)
    old = {"title": "Old", "goals": [
        {"id": "edu", "title": "Coursework and certificates", "milestones": [
            {"id": "a", "title": "Take a database course", "completed": True,
             "resources": [{"title": "Introduction to Database Systems", "url": BULLETIN, "code": "CSC 675"}]},
            {"id": "b", "title": "Take a data engineering course", "completed": False,
             "resources": [{"title": "Introduction to Data Engineering", "url": EDX}]}]},
        {"id": "db", "title": "Databases", "milestones": [
            {"id": "c", "title": "Design a database", "completed": False}]},
    ]}
    client.put("/career/roadmap", headers=auth, json=old)
    saved = client.get("/career/roadmap", headers=auth).json()
    assert [[m["id"] for m in g["milestones"]] for g in saved["goals"]] == [["a", "b"], ["c"]]
    assert saved["goals"][0]["milestones"][0]["completed"] is True


# --- Several courses on one bulletin listing ------------------------------------------

def test_two_courses_on_one_bulletin_listing_are_both_kept(client, auth, fake, pages):
    plan = competency_plan()
    plan["goals"][0]["milestones"][0]["resources"] = [DB_COURSE, AI_COURSE]
    body = _generate(client, auth, fake, plan)
    assert [(r["code"], r["title"]) for r in _goals(body)[0]["milestones"][0]["resources"]] == [
        ("CSC 675", "Introduction to Database Systems"), ("CSC 665", "Artificial Intelligence")]


def test_revision_keeps_each_stored_course_on_its_own_step(client, auth, fake):
    _ready(client, auth)
    stored = {"title": "Approved", "goals": [
        {"id": "g1", "title": "Databases", "kind": "competency", "milestones": [
            {"id": "m1", "title": "Take CSC 675 Introduction to Database Systems", "completed": True,
             "step": "learn", "resources": [{"title": "Introduction to Database Systems", "code": "CSC 675",
                                             "url": BULLETIN, "type": "sfsu", "topics": ["SQL"],
                                             "kind": "course", "description": "Relational design."}]}]},
        {"id": "g2", "title": "AI", "kind": "competency", "milestones": [
            {"id": "m2", "title": "Take CSC 665 Artificial Intelligence", "completed": False,
             "step": "learn", "resources": [{"title": "Artificial Intelligence", "code": "CSC 665",
                                             "url": BULLETIN, "type": "sfsu",
                                             "kind": "course", "description": "Model-based reasoning."}]}]},
    ]}
    client.put("/career/roadmap", headers=auth, json=stored)
    # A revision without research: both steps point at the shared listing URL.
    db_ref = {**AI_COURSE, "code": "CSC 675", "name": "Introduction to Database Systems"}
    revised = {"title": "Approved (shorter)", "goals": [
        goal("Databases", "competency",
             {**step("Take CSC 675 Introduction to Database Systems", "learn", db_ref), "id": "m1", "completed": True}),
        goal("AI", "competency",
             {**step("Take CSC 665 Artificial Intelligence", "learn", AI_COURSE), "id": "m2"}),
    ]}
    fake.script = [{"parsed": {"proposal": revised}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make it shorter please"})
    assert r.status_code == 200, r.text
    goals = r.json()["proposal"]["goals"]
    got = [[(x["code"], x["title"]) for m in g["milestones"] for x in m.get("resources") or []] for g in goals]
    assert got == [[("CSC 675", "Introduction to Database Systems")], [("CSC 665", "Artificial Intelligence")]]
    assert goals[0]["milestones"][0]["resources"][0]["topics"] == ["SQL"]   # exactly as stored
