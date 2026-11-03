"""Career chatbot (/career/*): chat, AI roadmap proposals, approve/reject,
owner edits, and per-account isolation. Runs with AI_PROVIDER=mock."""

from .conftest import signup


def _with_portfolio(client, headers):
    client.patch("/portfolio/me", headers=headers, json={"career_interests": ["Data Engineer"]})
    client.post("/portfolio/me/skills", headers=headers, json={"name": "Python"})


def _roadmap_proposal(client, headers):
    r = client.post("/career/chat", headers=headers, json={"message": "Make me a roadmap"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["proposal_id"] and body["proposal"]["goals"]
    return body


def test_chat_requires_login(client):
    assert client.post("/career/chat", json={"message": "hi"}).status_code == 401
    assert client.get("/career/roadmap").status_code == 401
    assert client.get("/career/proposals").status_code == 401


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


def test_roadmap_proposal_approve_flow(client, auth):
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
    assert client.get("/career/proposals", headers=auth).json() == []
    # Cannot be decided twice.
    assert client.post(f"/career/proposals/{pid}/reject", headers=auth).status_code == 409

    # Owner edit: tick a milestone (what the Roadmap page does).
    goals = roadmap["goals"]
    goals[0]["milestones"][0]["completed"] = True
    r = client.put("/career/roadmap", headers=auth, json={"title": roadmap["title"], "goals": goals})
    assert r.status_code == 200
    assert client.get("/career/roadmap", headers=auth).json()["goals"][0]["milestones"][0]["completed"] is True


def test_roadmap_proposal_reject_flow(client, auth):
    _with_portfolio(client, auth)
    pid = _roadmap_proposal(client, auth)["proposal_id"]
    r = client.post(f"/career/proposals/{pid}/reject", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert client.get("/career/roadmap", headers=auth).json() is None
    assert client.get("/career/proposals", headers=auth).json() == []
    assert client.post(f"/career/proposals/{pid}/maybe", headers=auth).status_code == 400


def test_roadmaps_are_separated_by_account(client, auth):
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
