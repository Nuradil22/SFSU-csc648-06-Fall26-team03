"""Blocked-site and link-check handling for researched resources.

All network traffic goes to an httpx.MockTransport; DNS is stubbed. OpenAI is
the scripted fake from tests/openai_fakes.py.
"""

import httpx
import openai
import pytest

from app.config import settings
from app.routers import career_chat as cc

from . import openai_fakes
from .openai_fakes import FakeOpenAI, plan, resource, search_call

OK = "https://bulletin.sfsu.edu/courses/csc/"
GONE = "https://www.edx.org/course/removed-course"
BAD_TLS = "https://catalog-mirror.example.edu/csc/"
REFUSES = "https://www.sfsu.edu/departments/academic-technology/students/technology-certificates-students"
MOVED = "https://www.coursera.org/old-certificate"
MOVED_TO = "https://www.coursera.org/professional-certificates/google-data-analytics"


def _routes(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url == OK or url == MOVED_TO:
        return httpx.Response(200)
    if url == GONE:
        return httpx.Response(404)
    if url == REFUSES:
        return httpx.Response(403)
    if url == MOVED:
        return httpx.Response(301, headers={"location": "/professional-certificates/google-data-analytics"})
    if url == BAD_TLS:
        raise httpx.ConnectError("certificate verify failed: Hostname mismatch", request=request)
    if url.endswith("/timeout"):
        raise httpx.ReadTimeout("timed out", request=request)
    if url.endswith("/server-error"):
        return httpx.Response(503)
    if url.endswith("/to-http"):
        return httpx.Response(302, headers={"location": "http://insecure.example.org/page"})
    if url.endswith("/loop"):
        return httpx.Response(302, headers={"location": url})
    raise AssertionError(f"unexpected request {url}")


@pytest.fixture
def links(monkeypatch):
    """Link checks on, against the mock transport; every host looks public."""
    requested = []

    def handler(request):
        requested.append(str(request.url))
        return _routes(request)

    monkeypatch.setattr(settings, "resource_link_check", True)
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(handler))
    monkeypatch.setattr(cc, "_public_host", lambda host: True)
    return requested


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
    client.post("/projects", headers=headers, json={"title": "Pipeline"})


# --- check_link outcomes ------------------------------------------------------------

@pytest.mark.parametrize("url, expected", [
    (OK, "ok"),
    (MOVED, "ok"),                                           # relative redirect followed
    (GONE, "missing"),
    (REFUSES, "blocked"),
    (BAD_TLS, "unavailable"),                                # certificate error
    ("https://slow.example.org/timeout", "unavailable"),
    ("https://down.example.org/server-error", "unavailable"),
    ("https://redir.example.org/to-http", "unavailable"),    # redirect to plain http
    ("https://redir.example.org/loop", "unavailable"),       # too many redirects
    ("http://bulletin.sfsu.edu/", "unavailable"),            # not https
])
def test_check_link_outcomes(links, url, expected):
    assert cc.check_links([url]) == {url: expected}


def test_non_public_addresses_are_never_contacted(monkeypatch):
    monkeypatch.setattr(settings, "resource_link_check", True)
    calls = []
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200)))
    # Real resolution: these are loopback / private, so no request is made.
    assert cc.check_links(["https://localhost/admin", "https://127.0.0.1/", "https://10.0.0.5/"]) == {
        "https://localhost/admin": "unavailable",
        "https://127.0.0.1/": "unavailable",
        "https://10.0.0.5/": "unavailable",
    }
    assert calls == []


def test_a_crashing_check_counts_as_unavailable(links, monkeypatch):
    def boom(client, url):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(cc, "check_link", boom)
    assert cc.check_links([OK]) == {OK: "unavailable"}


# --- In roadmap generation ----------------------------------------------------------

def test_unreachable_links_are_dropped_and_good_ones_kept(client, auth, research, links):
    _ready(client, auth)
    research.script = [{
        "output": [search_call(OK, GONE, BAD_TLS, REFUSES, MOVED)],
        "parsed": {"proposal": plan(
            [resource("CSC courses", OK), resource("Removed edX course", GONE, provider="edX")],
            [resource("Catalog mirror", BAD_TLS)],
            [resource("AT certificates", REFUSES), resource("Data Analytics", MOVED, provider="Coursera")],
        )},
    }]
    r = client.post("/career/roadmap/auto", headers=auth)
    assert r.status_code == 200, r.text  # link problems never fail generation

    milestones = r.json()["proposal"]["goals"][0]["milestones"]
    assert [x["url"] for x in milestones[0]["resources"]] == [OK]
    assert "resources" not in milestones[1]                    # TLS failure dropped
    # A site refusing automated checks is kept only because the search
    # returned it; a redirect keeps the search's own URL.
    assert [x["url"] for x in milestones[2]["resources"]] == [REFUSES, MOVED]
    assert sorted(set(links)) == sorted({OK, GONE, BAD_TLS, REFUSES, MOVED, MOVED_TO})


def test_links_not_in_the_search_are_never_checked_or_shown(client, auth, research, links):
    _ready(client, auth)
    research.script = [{
        "output": [search_call(OK)],
        "parsed": {"resources": [resource("Invented", "https://www.edx.org/invented")]},
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Any courses?"}).json()
    assert body["resources"] == []
    assert links == []  # nothing to check: the only recommendation wasn't a source


def test_blocked_domains_are_never_sources(client, auth, research, links):
    _ready(client, auth)
    mirror = "https://sfsu-public.courseleaf.com/colleges/science-engineering/computer-science/"
    forum = "https://www.reddit.com/r/dataengineering/comments/o46wci"
    video = "https://www.youtube.com/watch?v=abc"
    research.script = [{
        "output": [search_call(OK, mirror, forum, video)],
        "parsed": {"resources": [resource("CSC courses", OK), resource("Mirror", mirror),
                                 resource("Forum thread", forum), resource("Video", video)]},
    }]
    body = client.post("/career/chat", headers=auth, json={"message": "Which courses fit me?"}).json()
    assert [(x["url"], x["type"]) for x in body["resources"]] == [(OK, "sfsu")]
    assert links == [OK]  # blocked sites aren't even contacted
    assert "never forums, social media" in research.calls[0]["instructions"]


def test_blocked_domains_are_configurable(client, auth, research, monkeypatch):
    monkeypatch.setattr(settings, "openai_web_search_blocked_domains", "")
    _ready(client, auth)
    forum = "https://www.reddit.com/r/SFSU/comments/x"
    research.script = [{"output": [search_call(forum)],
                        "parsed": {"resources": [resource("Thread", forum, provider="Reddit")]}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Any courses?"}).json()
    assert [x["url"] for x in body["resources"]] == [forum]


def test_link_check_can_be_turned_off(client, auth, research, monkeypatch):
    monkeypatch.setattr(settings, "resource_link_check", False)
    monkeypatch.setattr(cc, "_link_transport", httpx.MockTransport(
        lambda r: (_ for _ in ()).throw(AssertionError("no network expected"))))
    _ready(client, auth)
    research.script = [{"output": [search_call(GONE)],
                        "parsed": {"resources": [resource("Course", GONE, provider="edX")]}}]
    body = client.post("/career/chat", headers=auth, json={"message": "Any courses?"}).json()
    assert [x["url"] for x in body["resources"]] == [GONE]


def test_every_link_failing_still_returns_the_roadmap(client, auth, research, links):
    _ready(client, auth)
    research.script = [{
        "output": [search_call(GONE, BAD_TLS)],
        "parsed": {"proposal": plan([resource("Gone", GONE), resource("Mirror", BAD_TLS)])},
    }]
    r = client.post("/career/roadmap/auto", headers=auth)
    assert r.status_code == 200
    assert r.json()["proposal"]["goals"][0]["milestones"][0].get("resources") is None
