"""M4 integration test runner — executes the seven P1-category scenarios
end-to-end through FastAPI's TestClient (routing -> dependencies -> DB).

Run from app/backend:

    env -u TEST_DATABASE_URL .venv/bin/python scripts/m4_integration.py

Uses a throwaway SQLite DB and upload dir (same setup as tests/conftest.py).
AI runs on the deterministic mock provider; no network calls are made.
Prints a dated transcript; exits nonzero if any case fails.
"""

import os
import sys
import tempfile
from datetime import datetime, timezone

_tmp = tempfile.mkdtemp(prefix="careergps-m4-it-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/it.db")
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["AI_PROVIDER"] = "mock"
os.environ["OPENAI_WEB_SEARCH"] = "false"
os.environ["RESOURCE_LINK_CHECK"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
results = []


def record(case_id, step, detail, ok):
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {step}: {detail}")
    if not ok:
        results.append((case_id, step, detail))
    return ok


def check(case_id, step, response, expected, *fields):
    detail = f"{response.status_code} (expected {expected})"
    ok = response.status_code == expected
    if ok and fields:
        try:
            for name, test in fields:
                assert test(response.json()), f"{name} check failed"
            detail += " + field checks"
        except AssertionError as exc:
            ok, detail = False, f"{response.status_code} but {exc}"
    return record(case_id, step, detail, ok)


def signup(email, name):
    r = client.post("/auth/signup", json={"name": name, "email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def ready_portfolio(headers):
    client.post("/portfolio/me/education", headers=headers, json={
        "school_name": "San Francisco State University", "degree": "B.S. Computer Science"})
    for skill in ("Python", "SQL", "Git"):
        client.post("/portfolio/me/skills", headers=headers, json={"name": skill})
    client.post("/portfolio/me/job-preferences", headers=headers, json={"role": "Data Engineer"})
    client.post("/projects", headers=headers, json={"title": "Python ETL pipeline"})


def glb_file(name="model.glb", data=b"glTF\x02\x00\x00\x00integration"):
    return ("file", (name, data, "model/gltf-binary"))


def main():
    print(f"M4 integration run — {datetime.now(timezone.utc).isoformat()} "
          f"(TestClient, disposable DB: {_tmp})")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # ---- IT-01 Account authentication and authorization --------------------
    cid = "IT-01"
    print(f"\n{cid} Account authentication and authorization")
    check(cid, "signup valid student", client.post("/auth/signup",
          json={"name": "Sam Student", "email": "sam@sfsu.edu", "password": "password123"}), 201)
    check(cid, "signup duplicate email rejected", client.post("/auth/signup",
          json={"name": "Sam", "email": "sam@sfsu.edu", "password": "password123"}), 409)
    check(cid, "login correct credentials", client.post("/auth/login",
          json={"email": "sam@sfsu.edu", "password": "password123"}), 200,
          ("access_token", lambda j: bool(j.get("access_token"))))
    check(cid, "login wrong password", client.post("/auth/login",
          json={"email": "sam@sfsu.edu", "password": "wrongpass1"}), 401)
    check(cid, "protected route without token", client.get("/portfolio/me"), 401)

    owner = signup("owner@sfsu.edu", "Owner One")
    peer = signup("peer@sfsu.edu", "Peer Two")

    # ---- IT-02 Student profile and education history -----------------------
    cid = "IT-02"
    print(f"\n{cid} Student profile and education history")
    check(cid, "add education", client.post("/portfolio/me/education", headers=owner,
          json={"school_name": "SFSU", "degree": "B.S. CS", "major": "Computer Science"}), 201)
    check(cid, "add skill", client.post("/portfolio/me/skills", headers=owner,
          json={"name": "Python", "category": "technical"}), 201)
    check(cid, "add experience", client.post("/portfolio/me/experience", headers=owner,
          json={"experience_type": "internship", "organization": "Acme",
                "position": "Intern", "start_date": "2024-06-01"}), 201)
    check(cid, "add certificate", client.post("/portfolio/me/certificates", headers=owner,
          json={"name": "AWS CCP", "issuer": "Amazon", "issue_year": 2025}), 201)
    check(cid, "portfolio shows saved sections", client.get("/portfolio/me", headers=owner), 200,
          ("education", lambda j: len(j["education"]) == 1),
          ("skills", lambda j: len(j["skills"]) == 1),
          ("experiences", lambda j: len(j["experiences"]) == 1),
          ("certificates", lambda j: len(j["certificates"]) == 1))
    check(cid, "cannot edit another student's portfolio", client.patch("/portfolio/me",
          headers=peer, json={"bio": "hijack"}), 200)  # edits peer's own, never owner's
    check(cid, "owner bio unaffected", client.get("/portfolio/me", headers=owner), 200,
          ("bio", lambda j: j.get("bio") != "hijack"))

    # ---- IT-03 Portfolio and project management ----------------------------
    cid = "IT-03"
    print(f"\n{cid} Portfolio and project management")
    r = client.post("/projects", headers=owner, json={
        "title": "Rover Chassis", "description": "3D printed rover", "technologies": ["CAD"]})
    check(cid, "create project", r, 201, ("id", lambda j: bool(j.get("id"))))
    project_id = r.json()["id"]
    check(cid, "owner lists project", client.get("/projects/mine", headers=owner), 200,
          ("listed", lambda j: any(p["id"] == project_id for p in j)))
    check(cid, "peer cannot see private project", client.get(f"/projects/{project_id}",
          headers=peer), 404)
    r = client.post("/portfolio/me/share", headers=owner, json={})
    check(cid, "enable sharing", r, 200,
          ("share_token", lambda j: bool(j.get("share_token") or j.get("is_public"))))
    share_token = r.json()["share_token"]
    check(cid, "peer views shared project by link",
          client.get(f"/public/portfolios/{share_token}/projects/{project_id}", headers=peer), 200,
          ("title", lambda j: j["title"] == "Rover Chassis"))
    check(cid, "peer hits viewable engagement endpoint", client.get(
          f"/projects/{project_id}/engagement", headers=peer), 200)
    check(cid, "public browse lists project", client.get("/projects"), 200,
          ("discoverable", lambda j: any(p["id"] == project_id for p in j)))
    check(cid, "peer cannot edit owner's project", client.patch(f"/projects/{project_id}",
          headers=peer, json={"title": "vandalized"}), 404)

    # ---- IT-04 Focused AI academic guidance --------------------------------
    cid = "IT-04"
    print(f"\n{cid} Focused AI academic guidance")
    check(cid, "readiness blocks incomplete portfolio", client.get("/career/readiness",
          headers=peer), 200, ("not_ready", lambda j: j["ready"] is False))
    ready_portfolio(owner)
    r = client.post("/career/chat", headers=owner, json={"message": "What should I learn next?"})
    check(cid, "chat returns personalized reply", r, 200,
          ("reply", lambda j: bool(j.get("reply"))))
    r = client.post("/career/chat", headers=owner, json={"message": "Make me a roadmap"})
    check(cid, "roadmap proposal offered", r, 200,
          ("proposal_id", lambda j: bool(j.get("proposal_id"))))
    pid = r.json()["proposal_id"]
    check(cid, "roadmap not active before approval", client.get("/career/roadmap",
          headers=owner), 200, ("none", lambda j: j is None))
    check(cid, "approve proposal", client.post(f"/career/proposals/{pid}/approve",
          headers=owner), 200, ("status", lambda j: j["status"] == "approved"))
    check(cid, "approved roadmap served", client.get("/career/roadmap", headers=owner), 200,
          ("goals", lambda j: bool(j and j.get("goals"))))

    # ---- IT-05 Recommendation results ---------------------------------------
    cid = "IT-05"
    print(f"\n{cid} Recommendation results")
    r = client.post("/guidance", headers=owner, json={})
    check(cid, "guidance generated", r, 201,
          ("summary", lambda j: bool(j["summary"])),
          ("career_paths", lambda j: len(j["career_paths"]) >= 1),
          ("strengths", lambda j: len(j["strengths"]) >= 1),
          ("next_steps", lambda j: len(j["next_steps"]) >= 1))
    check(cid, "latest guidance retrievable", client.get("/guidance/latest",
          headers=owner), 200)

    # ---- IT-06 Basic collaborative project feedback -------------------------
    cid = "IT-06"
    print(f"\n{cid} Basic collaborative project feedback")
    check(cid, "peer likes shared project", client.put(f"/projects/{project_id}/like",
          headers=peer), 200,
          ("count", lambda j: j["like_count"] == 1), ("liked", lambda j: j["liked_by_me"]))
    check(cid, "second like is idempotent", client.put(f"/projects/{project_id}/like",
          headers=peer), 200, ("count", lambda j: j["like_count"] == 1))
    r = client.post(f"/projects/{project_id}/comments", headers=peer,
                    json={"body": "Nice chassis tolerances!"})
    check(cid, "peer comments", r, 201, ("author", lambda j: j["author_name"] == "Peer Two"))
    comment_id = r.json()["id"]
    check(cid, "anonymous like rejected", client.put(f"/projects/{project_id}/like"), 401)
    check(cid, "owner sees engagement", client.get(f"/projects/{project_id}/engagement",
          headers=owner), 200, ("count", lambda j: j["like_count"] == 1))
    check(cid, "owner deletes peer comment", client.delete(
          f"/projects/{project_id}/comments/{comment_id}", headers=owner), 204)
    check(cid, "unlike", client.delete(f"/projects/{project_id}/like", headers=peer), 200,
          ("count", lambda j: j["like_count"] == 0))

    # ---- IT-07 Project/model revision history --------------------------------
    cid = "IT-07"
    print(f"\n{cid} Project/model revision history")
    check(cid, "upload v1 model", client.put(f"/projects/{project_id}/model",
          headers=owner, files=[glb_file("chassis_v1.glb")],
          data={"version_label": "v1", "change_note": "Initial chassis"}), 200,
          ("format", lambda j: j["file_format"] == "glb"))
    check(cid, "upload v2 with change note", client.put(f"/projects/{project_id}/model",
          headers=owner, files=[glb_file("chassis_v2.glb", b"glTF\x02\x00\x00\x00revised")],
          data={"version_label": "v2", "change_note": "Widened wheelbase"}), 200)
    r = client.get(f"/projects/{project_id}/model/revisions", headers=peer)
    check(cid, "revision history lists both versions", r, 200,
          ("two", lambda j: len(j) == 2),
          ("labels", lambda j: {x["version_label"] for x in j} == {"v1", "v2"}),
          ("note", lambda j: any(x["change_note"] == "Widened wheelbase" for x in j)),
          ("current", lambda j: sum(1 for x in j if x["is_current"]) == 1))
    check(cid, "peer cannot upload a revision", client.put(
          f"/projects/{project_id}/model", headers=peer,
          files=[glb_file("evil.glb")]), 404)
    check(cid, "invalid model rejected", client.put(f"/projects/{project_id}/model",
          headers=owner, files=[("file", ("notamodel.txt", b"MZ", "text/plain"))]), 400)

    print("\n" + "=" * 60)
    if results:
        print(f"{len(results)} FAILED step(s):")
        for case_id, step, detail in results:
            print(f"  {case_id} {step}: {detail}")
        sys.exit(1)
    print("All integration steps passed.")


if __name__ == "__main__":
    main()
