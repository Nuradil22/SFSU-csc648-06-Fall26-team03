"""Exact official names for every educational recommendation.

Each recommended course, certificate, specialization, or degree program is
checked against the page the link check reads (an httpx.MockTransport here)
or the search's own page title. OpenAI is the scripted fake; no network.
"""

import httpx
import openai
import pytest

from app.config import settings
from app.routers import career_chat as cc

from . import openai_fakes
from .openai_fakes import FakeOpenAI, resource, search_call

BULLETIN = "https://bulletin.sfsu.edu/courses/csc/"
CERT = "https://www.coursera.org/professional-certificates/google-data-analytics"
EDX = "https://www.edx.org/learn/data-engineering/ibm-introduction-to-data-engineering"
BLOCKED = "https://www.comptia.org/certifications/data"
# A page on an accepted course platform that refuses automated checks.
BLOCKED_EDU = "https://www.edx.org/certificates/professional-certificate/test-data-analysis"

PAGES = {
    BULLETIN: """<html><head><title>Computer Science (CSC) &lt; San Francisco State University</title></head>
        <body><h1>Computer Science (CSC)</h1>
        <div class="courseblock"><p><strong>CSC 675 Introduction to Database Systems (Units: 3)</strong></p>
        <p>Prerequisite: CSC 340. Relational data model, SQL, normalization, and transaction processing.</p></div>
        <div class="courseblock"><p><strong>CSC 665 Artificial Intelligence (Units: 3)</strong></p></div>
        <script>var fake = "CSC 999 Invented Course";</script>
        </body></html>""",
    CERT: """<html><head><title>Google Data Analytics Professional Certificate | Coursera</title>
        <meta property="og:title" content="Google Data Analytics Professional Certificate"></head>
        <body><h1>Google Data Analytics Professional Certificate</h1>
        <p>Earn a career certificate. Skills you'll gain: Data Cleansing, SQL, Data Visualization, R Programming.</p>
        </body></html>""",
    EDX: """<html><head><title>IBM: Introduction to Data Engineering | edX</title></head>
        <body><h1>IBM: Introduction to Data Engineering</h1><p>Learn data pipelines and ETL.</p></body></html>""",
}


def _routes(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url in (BLOCKED, BLOCKED_EDU):
        return httpx.Response(403)
    if url in PAGES:
        return httpx.Response(200, html=PAGES[url])
    return httpx.Response(404)


@pytest.fixture
def pages(monkeypatch):
    monkeypatch.setattr(settings, "resource_link_check", True)
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(_routes))
    monkeypatch.setattr(cc, "_public_host", lambda host: True)


@pytest.fixture
def fake(monkeypatch):
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
    client.post("/projects", headers=headers, json={"title": "Pipeline"})


def _plan(*goals):
    """goals: (goal title, [(milestone title, [resources])][, kind]); learning
    stages serve the test student's goal."""
    return {"title": "Data roadmap", "goals": [
        {"id": f"g{g}", "title": goal[0], "kind": goal[2] if len(goal) > 2 else "competency",
         "serves": "Data Engineer", "milestones": [
            {"id": f"m{g}{m}", "title": m_title, "completed": False, "resources": res}
            for m, (m_title, res) in enumerate(goal[1])]}
        for g, goal in enumerate(goals)]}


def _roadmap(client, auth, fake, sources, proposal, citations=None):
    _ready(client, auth)
    step = {"output": [search_call(*sources)], "parsed": {"proposal": proposal}}
    if citations is not None:
        step["citations"] = citations
    fake.script = [step]
    r = client.post("/career/chat", headers=auth, json={"message": "Generate a new career roadmap for me"})
    assert r.status_code == 200, r.text
    return r.json()


def _resources(body):
    return {
        milestone["title"]: milestone.get("resources") or []
        for goal in body["proposal"]["goals"] for milestone in goal["milestones"]
    }


# --- Verified against the page ------------------------------------------------------

def test_sfsu_course_shows_every_verified_detail(client, auth, fake, pages):
    course = resource(
        "Introduction to Database Systems", BULLETIN, code="CSC 675",
        topics=["SQL", "normalization", "query optimization"],  # the last isn't on the page
        credential="academic_credit",
        description="Database design is central to data engineering.",
        outcome="Design a normalized schema and write SQL queries.",
    )
    body = _roadmap(client, auth, fake, [BULLETIN],
                    _plan(("Coursework", [("Take CSC 675 Introduction to Database Systems", [course])])),
                    citations={})
    [item] = _resources(body)["Take CSC 675 Introduction to Database Systems"]
    assert item == {
        "title": "Introduction to Database Systems",
        "url": BULLETIN,
        "provider": "San Francisco State University",
        "type": "sfsu",
        "description": "Database design is central to data engineering.",
        "code": "CSC 675",
        "kind": "course",
        "credential": "academic_credit",
        "credential_detail": "3 units",
        "outcome": "Design a normalized schema and write SQL queries.",
        "topics": ["SQL", "normalization"],
    }


def test_certificate_name_must_be_the_exact_official_title(client, auth, fake, pages):
    exact = resource("Google Data Analytics Professional Certificate", CERT, provider="Coursera",
                     kind="course", credential="certificate", topics=["SQL", "Tableau"])
    shortened = resource("Google Data Analytics", CERT, provider="Coursera")
    body = _roadmap(client, auth, fake, [CERT], _plan(
        ("Certificates", [("Earn a data analytics certificate", [exact]),
                          ("Study data analytics", [shortened])])), citations={})
    found = _resources(body)
    [item] = found["Earn a data analytics certificate"]
    assert item["title"] == "Google Data Analytics Professional Certificate"
    assert item["kind"] == "certificate"          # a certificate is never shown as a course
    assert item["credential"] == "certificate"
    assert item["topics"] == ["SQL"]              # "Tableau" isn't on the page
    assert found["Study data analytics"] == []    # a shortened name is not the official one


def test_provider_prefix_in_the_headline_is_allowed(client, auth, fake, pages):
    body = _roadmap(client, auth, fake, [EDX], _plan(
        ("Data engineering", [("Learn data pipelines", [
            resource("Introduction to Data Engineering", EDX, provider="IBM via edX")])])), citations={})
    [item] = _resources(body)["Learn data pipelines"]
    assert item["title"] == "Introduction to Data Engineering"


@pytest.mark.parametrize("bad", [
    resource("Machine learning courses", BULLETIN),                        # a subject, not a title
    resource("Introduction to Database Systems", BULLETIN, code="CSC 999"),  # code not on the page
    resource("Advanced Database Systems", BULLETIN, code="CSC 675"),       # wrong title for the code
    resource("Invented Course", BULLETIN, code="CSC 999"),                 # only in a script
])
def test_unverifiable_names_are_never_shown(client, auth, fake, pages, bad):
    body = _roadmap(client, auth, fake, [BULLETIN],
                    _plan(("Coursework", [("Pick a database elective", [bad])])), citations={})
    # Its only stage has no verified offering left, so there is no roadmap.
    assert body["proposal"] is None and body["roadmap_unverified"] is True
    assert body["reply"] == cc.NOTE_NO_ROADMAP


def test_unstated_credential_is_marked_unverified(client, auth, fake, pages):
    claim = resource("Introduction to Data Engineering", EDX, provider="edX",
                     credential="professional_certification")
    body = _roadmap(client, auth, fake, [EDX], _plan(("Skills", [("Learn ETL", [claim])])), citations={})
    [item] = _resources(body)["Learn ETL"]
    assert item["credential"] == "unverified"


NAME = "Data Analysis Professional Certificate"


def test_blocked_page_needs_the_search_title_as_evidence(client, auth, fake, pages):
    cert = resource(NAME, BLOCKED_EDU, provider="edX", kind="certificate",
                    credential="professional_certification", topics=["data mining"])
    plan = _plan(("Certification", [("Earn the data analysis certificate", [cert])]))

    body = _roadmap(client, auth, fake, [BLOCKED_EDU], plan, citations={BLOCKED_EDU: f"{NAME} | edX"})
    [item] = _resources(body)["Earn the data analysis certificate"]
    assert item["title"] == NAME
    assert item["provider"] == "edX"              # shown in the search title
    assert "topics" not in item                   # the page couldn't be read: no topics claimed
    assert item["credential"] == "unverified"     # nor a credential


def test_blocked_page_without_a_matching_title_is_dropped(client, auth, fake, pages):
    cert = resource(NAME, BLOCKED_EDU, provider="edX")
    body = _roadmap(client, auth, fake, [BLOCKED_EDU], _plan(("Certification", [("Get certified", [cert])])),
                    citations={})
    assert body["proposal"] is None and body["roadmap_unverified"] is True


def test_certification_body_page_is_not_an_educational_source(client, auth, fake, pages):
    """Even with its official name confirmed by the search title, a page
    outside academic institutions and accepted course platforms is never
    presented as an educational offering."""
    cert = resource("CompTIA Data+", BLOCKED, provider="CompTIA", kind="professional_certification")
    body = _roadmap(client, auth, fake, [BLOCKED], _plan(("Certification", [("Earn CompTIA Data+", [cert])])),
                    citations={BLOCKED: "CompTIA Data+ | CompTIA"})
    assert body["proposal"] is None and body["roadmap_unverified"] is True


# --- Every goal, not just education -------------------------------------------------

def test_steps_naming_unverified_courses_are_removed_in_any_goal(client, auth, fake, pages):
    good = resource("Introduction to Database Systems", BULLETIN, code="CSC 675")
    invented = resource("Advanced Data Pipelines Professional Certificate", CERT, provider="Coursera")
    body = _roadmap(client, auth, fake, [BULLETIN, CERT], _plan(
        ("Coursework", [("Take CSC 675 Introduction to Database Systems", [good])]),
        ("Projects", [("Build a pipeline project", []),
                      ("Apply CSC 680 concepts to your project", [])], "career_action"),  # code, no resource
        ("Certificates", [("Complete the Advanced Data Pipelines Professional Certificate", [invented])]),
    ), citations={})
    titles = list(_resources(body))
    assert titles == ["Take CSC 675 Introduction to Database Systems", "Build a pipeline project"]
    assert [g["title"] for g in body["proposal"]["goals"]] == ["Coursework", "Projects"]
    assert "left out 2 roadmap steps" in body["reply"]


def test_generic_steps_are_kept(client, auth, fake, pages):
    good = resource("Introduction to Database Systems", BULLETIN, code="CSC 675")
    body = _roadmap(client, auth, fake, [BULLETIN], _plan(
        ("Coursework", [("Take CSC 675 Introduction to Database Systems", [good]),
                        ("Find an upper-division database elective in the SFSU Bulletin", [])])),
        citations={})
    assert list(_resources(body)) == ["Take CSC 675 Introduction to Database Systems",
                                      "Find an upper-division database elective in the SFSU Bulletin"]
    assert "left out" not in body["reply"]


def test_without_research_named_course_steps_are_removed(client, auth, fake, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search", False)
    _ready(client, auth)
    fake.script = [{"parsed": {"proposal": _plan(
        ("Coursework", [("Take CSC 675", []), ("Meet your advisor", [])]))}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Make me a roadmap"}).json()
    # No research, so no verified offering: no roadmap, nothing stored.
    assert body["proposal"] is None and body["roadmap_unverified"] is True
    assert client.get("/career/proposals", headers=auth).json() == []


def test_revision_keeps_stored_resources_and_existing_steps(client, auth, fake, pages):
    course = resource("Introduction to Database Systems", BULLETIN, code="CSC 675")
    body = _roadmap(client, auth, fake, [BULLETIN],
                    _plan(("Coursework", [("Take CSC 675 Introduction to Database Systems", [course])])),
                    citations={})
    client.post(f"/career/proposals/{body['proposal_id']}/approve", headers=auth)
    stored = client.get("/career/roadmap", headers=auth).json()["goals"][0]["milestones"][0]["resources"]

    # No search this time; the model renames the kept resource.
    fake.script = [{"parsed": {"proposal": _plan(("Coursework", [
        ("Take CSC 675 Introduction to Database Systems",
         [resource("Databases 101", BULLETIN, code="CSC 675", credential="degree")])]))}}]
    revised = client.post("/career/chat", headers=auth, json={"message": "Make it shorter"}).json()
    [kept] = _resources(revised)["Take CSC 675 Introduction to Database Systems"]
    assert [kept] == stored and kept["title"] == "Introduction to Database Systems"


def test_chat_resources_are_verified_too(client, auth, fake, pages):
    _ready(client, auth)
    fake.script = [{"output": [search_call(BULLETIN, CERT)], "citations": {}, "parsed": {"resources": [
        resource("Introduction to Database Systems", BULLETIN, code="CSC 675"),
        resource("Data Analytics Certificate", CERT, provider="Coursera"),
    ]}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Which courses should I take?"}).json()
    assert [(x["code"], x["title"]) for x in body["resources"]] == [("CSC 675", "Introduction to Database Systems")]


# --- Units ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("CSC675", "csc 675"),
    ("Data Science &amp; AI", "data science and ai"),
    ("Introduction to Database Systems (Units: 3)", "introduction to database systems units 3"),
    ("IBM: Introduction", "ibm introduction"),
])
def test_normalize_text(raw, expected):
    assert cc.normalize_text(raw) == expected


def test_page_text_is_never_sent_to_the_ai(client, auth, fake, pages):
    _roadmap(client, auth, fake, [BULLETIN], _plan(("Coursework", [("Take a course", [
        resource("Introduction to Database Systems", BULLETIN, code="CSC 675")])])), citations={})
    assert len(fake.calls) == 1  # one AI call; the page check happens after it
    assert "Relational data model" not in str(fake.calls[0])
