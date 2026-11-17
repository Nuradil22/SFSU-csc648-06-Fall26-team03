"""The advisor works for any student, not just computer science.

Mocked students from different fields and levels (nursing sophomore, design
senior, accounting student with work experience, CS student). For each:
their own portfolio reaches the model with no built-in tech template, their
field's offerings pass verification and land in that field's learning
stages, completed coursework isn't recommended again, and a fresh roadmap is
built from the portfolio rather than from earlier AI plans.

The pages below are test fixtures served by an httpx.MockTransport (their
course listings are made up for the test); OpenAI is the scripted fake. No
network. Whether a live model writes good roadmaps for each field can only
be judged with a live run.
"""

import httpx
import openai
import pytest

from app.config import settings
from app.routers import career_chat as cc

from . import openai_fakes
from .openai_fakes import FakeOpenAI, resource, search_call

NURS = "https://bulletin.sfsu.edu/courses/nurs/"
DES = "https://bulletin.sfsu.edu/courses/des/"
ACCT = "https://bulletin.sfsu.edu/courses/acct/"
UX_CERT = "https://www.coursera.org/professional-certificates/google-ux-design"
CPA_PREP = "https://www.edx.org/learn/accounting/test-university-financial-reporting"

PAGES = {
    NURS: """<html><head><title>Nursing (NURS) &lt; San Francisco State University</title></head><body>
        <p><strong>NURS 312 Pathophysiology (Units: 3)</strong> Cellular injury, inflammation, and fluid and electrolyte imbalance.</p>
        <p><strong>NURS 316 Pharmacology (Units: 3)</strong> Drug classes, dosage calculation, and medication safety.</p>
        </body></html>""",
    DES: """<html><head><title>Design (DES) &lt; San Francisco State University</title></head><body>
        <p><strong>DES 400 Interaction Design (Units: 3)</strong> User research, prototyping, and usability testing.</p>
        </body></html>""",
    ACCT: """<html><head><title>Accounting (ACCT) &lt; San Francisco State University</title></head><body>
        <p><strong>ACCT 301 Intermediate Accounting I (Units: 3)</strong> Financial reporting, revenue recognition, and the conceptual framework.</p>
        <p><strong>ACCT 300 Accounting Principles (Units: 3)</strong> Journal entries and financial statements.</p>
        </body></html>""",
    UX_CERT: """<html><head><title>Google UX Design Professional Certificate | Coursera</title></head><body>
        <h1>Google UX Design Professional Certificate</h1>
        <p>Earn a career certificate. Skills you'll gain: Wireframing, Prototyping, Usability Testing, Figma.</p></body></html>""",
}

TEMPLATE_WORDS = ("Docker", "PostgreSQL", "Redis", "backend", "Backend", "interview", "algorithm")


def _routes(request):
    url = str(request.url)
    return httpx.Response(200, html=PAGES[url]) if url in PAGES else httpx.Response(404)


@pytest.fixture
def fake(monkeypatch):
    openai_fakes.reset()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_web_search", True)
    monkeypatch.setattr(settings, "resource_link_check", True)
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(_routes))
    monkeypatch.setattr(cc, "_public_host", lambda host: True)
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


PROFILES = {
    "nursing_sophomore": {
        "education": {"school_name": "San Francisco State University", "degree": "B.S. Nursing",
                      "coursework": ["BIOL 220 General Microbiology", "CHEM 115"]},
        "skills": ["Patient communication", "CPR", "Medical terminology"],
        "role": "Registered Nurse",
        "experience": {"experience_type": "volunteer", "organization": "Community clinic",
                       "position": "Front desk volunteer"},
    },
    "design_senior": {
        "education": {"school_name": "San Francisco State University", "degree": "B.A. Design"},
        "skills": ["Adobe Illustrator", "Typography", "Figma"],
        "role": "UX Designer",
        "project": "Brand identity for a neighborhood cafe",
    },
    "accounting_with_work": {
        "education": {"school_name": "San Francisco State University", "degree": "B.S. Business Administration",
                      "coursework": ["ACCT 300 Accounting Principles"]},
        "skills": ["Excel", "Bookkeeping", "QuickBooks"],
        "role": "Staff Accountant",
        "experience": {"experience_type": "work", "organization": "Family restaurant",
                       "position": "Part-time bookkeeper"},
    },
    "cs_junior": {
        "education": {"school_name": "San Francisco State University", "degree": "B.S. Computer Science"},
        "skills": ["Python", "Java", "Git"],
        "role": "Software Engineer",
        "project": "Campus events app",
    },
}


def _make(client, auth, name):
    p = PROFILES[name]
    client.post("/portfolio/me/education", headers=auth, json=p["education"])
    for skill in p["skills"]:
        client.post("/portfolio/me/skills", headers=auth, json={"name": skill})
    client.post("/portfolio/me/job-preferences", headers=auth, json={"role": p["role"]})
    if "experience" in p:
        client.post("/portfolio/me/experience", headers=auth, json=p["experience"])
    if "project" in p:
        client.post("/projects", headers=auth, json={"title": p["project"]})
    assert client.get("/career/readiness", headers=auth).json()["ready"]


def stage(title, learn, resources, apply, serves=""):
    return {"id": "g", "title": title, "kind": "competency", "serves": serves, "milestones": [
        {"id": "m", "title": learn, "completed": False, "step": "learn", "resources": resources},
        {"id": "m", "title": apply, "completed": False, "step": "apply", "resources": []}]}


def _roadmap(client, auth, fake, proposal, sources):
    fake.script = [{"output": [search_call(*sources)], "parsed": {"proposal": proposal}, "citations": {}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"})
    assert r.status_code == 200, r.text
    return r.json(), fake.calls[-1]


def _taught(body):
    return {g["title"]: [(r.get("code", ""), r["title"]) for m in g["milestones"] for r in m.get("resources") or []]
            for g in body["proposal"]["goals"]}


# --- Each student's own portfolio, no built-in template -------------------------------

@pytest.mark.parametrize("name", list(PROFILES))
def test_each_students_portfolio_reaches_the_model_without_a_template(client, auth, fake, name):
    _make(client, auth, name)
    _, call = _roadmap(client, auth, fake, {"title": "R", "goals": [stage("S", "Find a course", [], "Practice")]}, [])
    prompt = call["instructions"]
    p = PROFILES[name]
    assert p["education"]["degree"] in prompt and p["role"] in prompt
    assert all(skill in prompt for skill in p["skills"])
    assert "do not assume a major or career" in prompt
    if name != "cs_junior":
        # Nothing in Projectory's own instructions pushes a tech or job-search template.
        assert [w for w in TEMPLATE_WORDS if w in prompt] == []


def test_prompts_differ_by_student(client, fake):
    from .conftest import signup
    prompts = {}
    for i, name in enumerate(PROFILES):
        headers = signup(client, email=f"s{i}@sfsu.edu")
        _make(client, headers, name)
        prompts[name] = _roadmap(client, headers, fake, {"title": "R", "goals": [
            stage("S", "Find a course", [], "Practice")]}, [])[1]["instructions"]
    assert len(set(prompts.values())) == len(PROFILES)
    assert "Registered Nurse" in prompts["nursing_sophomore"] and "Registered Nurse" not in prompts["design_senior"]


def test_missing_details_are_acknowledged_not_invented(client, auth, fake):
    _make(client, auth, "design_senior")   # no coursework, experience, or certificates saved
    _, call = _roadmap(client, auth, fake, {"title": "R", "goals": [stage("S", "Find a course", [], "Practice")]}, [])
    prompt = call["instructions"]
    assert "Completed coursework" in prompt                     # listed as not in the portfolio
    assert "say what you assumed instead of inventing it" in prompt


# --- Field-specific offerings are verified and integrated -----------------------------

def test_nursing_student_gets_nursing_courses_in_their_stages(client, auth, fake):
    _make(client, auth, "nursing_sophomore")
    patho = resource("Pathophysiology", NURS, code="NURS 312", topics=["inflammation"], credential="academic_credit")
    pharm = resource("Pharmacology", NURS, code="NURS 316", topics=["dosage calculation"], credential="academic_credit")
    micro = resource("General Microbiology", "https://bulletin.sfsu.edu/courses/biol/", code="BIOL 220")
    body, _ = _roadmap(client, auth, fake, {"title": "Path to RN", "goals": [
        stage("Disease processes", "Take NURS 312 Pathophysiology", [patho, micro],
              "Write care-plan rationales for three clinic cases", serves="Registered Nurse"),
        stage("Medication safety", "Take NURS 316 Pharmacology", [pharm],
              "Pass a 20-question dosage calculation self-test", serves="Registered Nurse"),
    ]}, [NURS, "https://bulletin.sfsu.edu/courses/biol/"])
    assert _taught(body) == {"Disease processes": [("NURS 312", "Pathophysiology")],
                             "Medication safety": [("NURS 316", "Pharmacology")]}
    first = body["proposal"]["goals"][0]["milestones"][0]["resources"][0]
    assert (first["credential_detail"], first["topics"], first["type"]) == ("3 units", ["inflammation"], "sfsu")
    assert [m["step"] for m in body["proposal"]["goals"][1]["milestones"]] == ["learn", "apply"]


def test_design_student_gets_sfsu_and_external_offerings(client, auth, fake):
    _make(client, auth, "design_senior")
    ixd = resource("Interaction Design", DES, code="DES 400", topics=["usability testing"])
    ux = resource("Google UX Design Professional Certificate", UX_CERT, provider="Coursera",
                  kind="certificate", credential="certificate", topics=["Wireframing", "Figma"])
    body, _ = _roadmap(client, auth, fake, {"title": "Into UX", "goals": [
        stage("User research and prototyping", "Take DES 400 Interaction Design", [ixd],
              "Run a usability test on your cafe brand's ordering flow", serves="UX Designer"),
        stage("UX portfolio", "Earn the Google UX Design Professional Certificate", [ux],
              "Publish two case studies", serves="UX Designer"),
    ]}, [DES, UX_CERT])
    assert _taught(body) == {"User research and prototyping": [("DES 400", "Interaction Design")],
                             "UX portfolio": [("", "Google UX Design Professional Certificate")]}
    cert = body["proposal"]["goals"][1]["milestones"][0]["resources"][0]
    assert (cert["provider"], cert["credential"], cert["type"]) == ("Coursera", "certificate", "external")


def test_completed_coursework_in_any_field_is_not_recommended_again(client, auth, fake):
    _make(client, auth, "accounting_with_work")
    done = resource("Accounting Principles", ACCT, code="ACCT 300")
    nxt = resource("Intermediate Accounting I", ACCT, code="ACCT 301", topics=["revenue recognition"])
    body, _ = _roadmap(client, auth, fake, {"title": "Toward CPA", "goals": [
        stage("Financial reporting", "Take ACCT 301 Intermediate Accounting I", [done, nxt],
              "Prepare a revenue schedule for the restaurant's catering sales", serves="Staff Accountant"),
    ]}, [ACCT])
    assert _taught(body) == {"Financial reporting": [("ACCT 301", "Intermediate Accounting I")]}
    assert "already in your portfolio" in body["reply"]


# --- Fresh roadmaps are built from the portfolio, not earlier AI plans ----------------

def test_fresh_roadmap_sees_progress_but_not_old_plans(client, auth, fake):
    _make(client, auth, "accounting_with_work")
    old = {"title": "Old backend plan", "goals": [{"id": "g", "title": "Old goal", "milestones": [
        {"id": "a", "title": "Finished the Excel modeling workshop", "completed": True},
        {"id": "b", "title": "Integrate Redis caching for one endpoint", "completed": False}]}]}
    client.put("/career/roadmap", headers=auth, json=old)
    # A pending draft and an AI reply describing it.
    fake.script = [{"reply": "x", "parsed": {"reply": "Your plan: practice 1-2 algorithm problems/week.",
                                             "proposal": {"title": "Pending draft title", "goals": [
                                                 stage("Docker deployment", "Dockerize", [], "Deploy")]}}}]
    client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap focused on audit"})

    _, call = _roadmap(client, auth, fake, {"title": "R", "goals": [stage("S", "Find a course", [], "Practice")]}, [])
    prompt = call["instructions"]
    assert "Finished the Excel modeling workshop" in prompt          # progress is kept
    for stale in ("Integrate Redis caching", "Pending draft title", "Docker deployment", "Old backend plan"):
        assert stale not in prompt
    # The student's own earlier request is still there; the AI's old answer is not.
    assert {"role": "user", "content": "Make me a roadmap focused on audit"} in call["input"]
    assert all(turn["role"] == "user" for turn in call["input"])


@pytest.mark.parametrize("message, fresh", [
    ("Generate a new career roadmap for me", True),
    ("Please regenerate my roadmap", True),
    ("Create my roadmap", True),
    ("Give me a different roadmap", True),
    ("Make that roadmap shorter", False),
    ("Update my roadmap to add a statistics course", False),
    ("Change the plan to focus on pediatrics", False),
])
def test_new_roadmap_versus_edit(message, fresh):
    assert cc.wants_roadmap(message)
    assert cc.is_fresh("chat", message) is fresh


def _nursing_draft(title):
    patho = resource("Pathophysiology", NURS, code="NURS 312")
    return {"title": title, "goals": [stage("Disease processes", "Take NURS 312 Pathophysiology", [patho],
                                            "Practice care plans", serves="Registered Nurse")]}


def test_roadmap_edit_request_sees_the_draft_it_changes(client, auth, fake):
    _make(client, auth, "nursing_sophomore")
    body, _ = _roadmap(client, auth, fake, _nursing_draft("Draft to shorten"), [NURS])
    assert body["proposal_id"]
    fake.script = [{"output": [search_call(NURS)], "citations": {},
                    "parsed": {"proposal": _nursing_draft("Shorter")}}]
    r = client.post("/career/chat", headers=auth, json={"message": "Make that roadmap shorter"})
    assert r.status_code == 200, r.text
    prompt = fake.calls[-1]["instructions"]
    assert "Draft to shorten" in prompt and "Return the complete revised roadmap" in prompt
    assert "Create a fresh one" not in prompt


def test_revisions_still_see_the_draft_they_change(client, auth, fake):
    _make(client, auth, "nursing_sophomore")
    body, _ = _roadmap(client, auth, fake, _nursing_draft("Draft to shorten"), [NURS])
    assert body["proposal_id"]
    fake.script = [{"parsed": {"proposal": {"title": "Shorter", "goals": [stage("S", "Find a course", [], "Practice")]}}}]
    client.post("/career/chat", headers=auth, json={"message": "Make it shorter"})
    assert "Draft to shorten" in fake.calls[-1]["instructions"]
    assert any(turn["role"] == "assistant" for turn in fake.calls[-1]["input"])
