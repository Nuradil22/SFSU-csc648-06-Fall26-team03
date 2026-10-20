import json
import struct

from app import ai
from app.schemas import GuidanceContent

from .conftest import signup

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def make_glb() -> bytes:
    body = json.dumps({"asset": {"version": "2.0"}}).encode()
    body += b" " * (-len(body) % 4)
    return b"glTF" + struct.pack("<II", 2, 12 + 8 + len(body)) + struct.pack("<I4s", len(body), b"JSON") + body


# --- R1 / R2: registration, login, logout -----------------------------------

def test_signup_validation(client):
    ok = client.post("/auth/signup", json={"name": "A", "email": "a@x.com", "password": "password123"})
    assert ok.status_code == 201
    assert ok.json()["message"] == "Account created successfully"

    dup = client.post("/auth/signup", json={"name": "A", "email": "A@X.com", "password": "password123"})
    assert dup.status_code == 409

    for bad in ({"name": "", "email": "b@x.com", "password": "password123"},
                {"name": "B", "email": "b@x.com", "password": "short1"},
                {"name": "B", "email": "b@x.com", "password": "nodigitshere"},
                {"name": "B", "email": "not-an-email", "password": "password123"},
                {"email": "b@x.com", "password": "password123"}):
        assert client.post("/auth/signup", json=bad).status_code == 422, bad


def test_login_logout(client, auth):
    assert client.post("/auth/login", json={"email": "student@sfsu.edu", "password": "wrong"}).status_code == 401
    ok = client.post("/auth/login", json={"email": "STUDENT@sfsu.edu", "password": "password123"})
    assert ok.status_code == 200
    form = client.post("/auth/token", data={"username": "student@sfsu.edu", "password": "password123"})
    assert form.status_code == 200
    assert client.post("/auth/logout", headers=auth).status_code == 204
    assert client.get("/portfolio/me").status_code == 401


# --- R3 / R9: personal info and full portfolio ------------------------------

def test_personal_info(client, auth):
    r = client.patch("/portfolio/me", headers=auth, json={
        "name": "Sam S.", "bio": "CS junior.", "career_interests": ["Embedded Systems", " robotics ", "ROBOTICS", ""],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Sam S."
    assert body["career_interests"] == ["Embedded Systems", "robotics"]
    assert client.patch("/portfolio/me", headers=auth, json={"name": None}).status_code == 422

    link = client.post("/portfolio/me/links", headers=auth, json={"label": "GitHub", "url": "https://github.com/sam"})
    assert link.status_code == 201
    assert client.post("/portfolio/me/links", headers=auth, json={"label": "x", "url": "javascript:alert(1)"}).status_code == 422
    assert client.get("/portfolio/me", headers=auth).json()["links"][0]["label"] == "GitHub"


# --- R4 / R5 / R6: education, skills, experience ----------------------------

def test_sections_crud(client, auth):
    edu = client.post("/portfolio/me/education", headers=auth, json={
        "school_name": "SFSU", "degree": "B.S.", "major": "Computer Science",
        "graduation_date": "2099-05-20", "coursework": ["CSC 648", "CSC 615"],
    })
    assert edu.status_code == 201 and edu.json()["is_expected"] is True
    edu_id = edu.json()["id"]
    assert client.patch(f"/portfolio/me/education/{edu_id}", headers=auth, json={"major": "CE"}).json()["major"] == "CE"
    bad_dates = {"start_date": "2099-06-01"}
    assert client.patch(f"/portfolio/me/education/{edu_id}", headers=auth, json=bad_dates).status_code == 422

    skill = client.post("/portfolio/me/skills", headers=auth, json={"name": "Python", "category": "technical"})
    assert skill.status_code == 201
    assert client.post("/portfolio/me/skills", headers=auth, json={"name": "python"}).status_code == 409
    assert client.post("/portfolio/me/skills", headers=auth, json={"name": "X", "category": "bogus"}).status_code == 422

    exp = client.post("/portfolio/me/experience", headers=auth, json={
        "experience_type": "internship", "organization": "Acme", "position": "Intern",
        "start_date": "2025-06-01", "end_date": "2025-08-01", "is_current": True,
    })
    assert exp.status_code == 201 and exp.json()["end_date"] is None

    portfolio = client.get("/portfolio/me", headers=auth).json()
    assert len(portfolio["education"]) == len(portfolio["skills"]) == len(portfolio["experiences"]) == 1

    assert client.delete(f"/portfolio/me/education/{edu_id}", headers=auth).status_code == 204
    assert client.delete(f"/portfolio/me/skills/{skill.json()['id']}", headers=auth).status_code == 204
    assert client.delete(f"/portfolio/me/experience/{exp.json()['id']}", headers=auth).status_code == 204


# --- R2.5: students can't touch each other's data ----------------------------

def test_ownership(client, auth):
    other = signup(client, email="other@sfsu.edu")
    skill_id = client.post("/portfolio/me/skills", headers=auth, json={"name": "C"}).json()["id"]
    project_id = client.post("/projects", headers=auth, json={"title": "Mine"}).json()["id"]

    assert client.patch(f"/portfolio/me/skills/{skill_id}", headers=other, json={"name": "Hacked"}).status_code == 404
    assert client.delete(f"/portfolio/me/skills/{skill_id}", headers=other).status_code == 404
    assert client.patch(f"/projects/{project_id}", headers=other, json={"title": "Hacked"}).status_code == 404
    assert client.get(f"/projects/{project_id}", headers=other).status_code == 404
    assert client.delete(f"/projects/{project_id}").status_code == 401


# --- R7 / R8 / R15: projects, media, 3D models -------------------------------

def test_projects_media_and_models(client, auth):
    blocks = [{"id": "a", "type": "paragraph", "content": "Line follower robot"}]
    r = client.post("/projects", headers=auth, json={
        "title": "Robot", "content_blocks": blocks, "technologies": ["C", "Raspberry Pi"], "project_date": "Spring 2026",
    })
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.patch(f"/projects/{pid}", headers=auth, json={"description": "Autonomous car"}).json()["description"] == "Autonomous car"

    img = client.post(f"/projects/{pid}/images", headers=auth, files={"file": ("a.png", PNG, "image/png")}, data={"label": "Circuit"})
    assert img.status_code == 201, img.text
    assert client.get(img.json()["url"].replace("http://localhost:8000", "")).status_code == 200
    assert client.post(f"/projects/{pid}/images", headers=auth, files={"file": ("a.png", b"not an image", "image/png")}).status_code == 400

    link = client.post(f"/projects/{pid}/links", headers=auth, json={"label": "Repo", "url": "https://github.com/x/y", "link_type": "GitHub"})
    assert link.status_code == 201 and link.json()["link_type"] == "github"

    project = client.get(f"/projects/{pid}", headers=auth).json()
    assert len(project["images"]) == 1 and len(project["links"]) == 1

    model = client.put(f"/projects/{pid}/model", headers=auth, files={"file": ("robot.glb", make_glb(), "model/gltf-binary")})
    assert model.status_code == 200, model.text
    assert model.json()["file_format"] == "glb"
    assert client.put(f"/projects/{pid}/model", headers=auth, files={"file": ("robot.obj", b"v 0 0 0", "text/plain")}).status_code == 400
    external = json.dumps({"asset": {"version": "2.0"}, "buffers": [{"uri": "robot.bin"}]}).encode()
    assert client.put(f"/projects/{pid}/model", headers=auth, files={"file": ("robot.gltf", external, "model/gltf+json")}).status_code == 400
    # Replacing keeps exactly one model
    assert client.put(f"/projects/{pid}/model", headers=auth, files={"file": ("v2.glb", make_glb(), "model/gltf-binary")}).status_code == 200
    assert client.get(f"/projects/{pid}", headers=auth).json()["model_3d"]["original_filename"] == "v2.glb"

    assert client.delete(f"/projects/{pid}/media/{img.json()['id']}", headers=auth).status_code == 204
    assert client.delete(f"/projects/{pid}/model", headers=auth).status_code == 204
    assert client.get(f"/projects/{pid}", headers=auth).json()["model_3d"] is None
    assert client.delete(f"/projects/{pid}", headers=auth).status_code == 204
    assert client.get("/projects/mine", headers=auth).json() == []


# --- R17: sharing ------------------------------------------------------------

def test_sharing(client, auth):
    client.post("/projects", headers=auth, json={"title": "Shared project"})
    assert client.get("/portfolio/me/share", headers=auth).json()["share_url"] is None

    share = client.post("/portfolio/me/share", headers=auth).json()
    token = share["share_token"]
    assert share["share_url"].endswith(f"/p/{token}")

    public = client.get(f"/public/portfolios/{token}")
    assert public.status_code == 200
    assert "email" not in public.json()
    assert public.json()["projects"][0]["title"] == "Shared project"
    pid = public.json()["projects"][0]["id"]
    assert client.get(f"/public/portfolios/{token}/projects/{pid}").status_code == 200
    assert client.delete(f"/public/portfolios/{token}").status_code == 405

    client.delete("/portfolio/me/share", headers=auth)
    assert client.get(f"/public/portfolios/{token}").status_code == 404
    assert client.post("/portfolio/me/share", headers=auth).json()["share_token"] == token
    new_token = client.post("/portfolio/me/share?regenerate=true", headers=auth).json()["share_token"]
    assert new_token != token
    assert client.get(f"/public/portfolios/{token}").status_code == 404


# --- R10–R14: AI career guidance ---------------------------------------------

def test_guidance_mock(client, auth):
    assert client.post("/guidance", headers=auth).status_code == 400
    assert client.get("/guidance/latest", headers=auth).status_code == 404

    client.patch("/portfolio/me", headers=auth, json={"career_interests": ["Robotics Engineer"]})
    client.post("/portfolio/me/skills", headers=auth, json={"name": "C", "category": "technical"})
    client.post("/projects", headers=auth, json={"title": "Robot", "technologies": ["C"]})

    first = client.post("/guidance", headers=auth)
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["summary"] and body["career_paths"][0]["title"] == "Robotics Engineer"
    assert body["strengths"] and body["next_steps"]

    second = client.post("/guidance", headers=auth).json()
    assert client.get("/guidance/latest", headers=auth).json()["id"] == second["id"]
    assert len(client.get("/guidance", headers=auth).json()) == 2


def test_guidance_failure_keeps_previous(client, auth, monkeypatch):
    client.post("/portfolio/me/skills", headers=auth, json={"name": "C"})
    first_id = client.post("/guidance", headers=auth).json()["id"]

    def boom(payload):
        raise ai.AIServiceError("Could not reach the AI service.", unavailable=True)

    monkeypatch.setitem(ai.PROVIDERS, "mock", boom)
    failed = client.post("/guidance", headers=auth)
    assert failed.status_code == 503
    assert "could not be completed" in failed.json()["detail"]
    assert client.get("/guidance/latest", headers=auth).json()["id"] == first_id


def test_payload_excludes_private_fields(client, auth):
    client.patch("/portfolio/me", headers=auth, json={"location": "SF"})
    client.post("/portfolio/me/links", headers=auth, json={"label": "Site", "url": "https://sam.dev"})
    from app.database import SessionLocal
    from app import models
    with SessionLocal() as db:
        payload = ai.build_portfolio_payload(db.query(models.Portfolio).one())
    text = json.dumps(payload)
    assert "student@sfsu.edu" not in text and "Sam" not in text and "sam.dev" not in text and "SF" not in text


def test_guidance_schema_is_strict_json_schema_compatible():
    # Structured outputs need every object to list its properties as required.
    schema = GuidanceContent.model_json_schema()
    for definition in [schema, *schema.get("$defs", {}).values()]:
        assert set(definition["required"]) == set(definition["properties"])


# --- Public browse / search --------------------------------------------------

def test_search_projects(client, auth):
    other = signup(client, email="other@sfsu.edu", name="Riley")
    client.post("/projects", headers=auth, json={
        "title": "Line Following Robot", "subject": "Embedded Systems", "technologies": ["C", "Raspberry Pi"],
        "description": "Autonomous car that follows a line.",
    })
    client.post("/projects", headers=auth, json={"title": "Budget App", "subject": "Web Development",
                                                 "technologies": ["React", "Python"]})
    client.post("/projects", headers=other, json={"title": "Secret robot", "technologies": ["C"]})

    # Nothing is public until the owner turns sharing on.
    assert client.get("/projects").json() == []
    client.post("/portfolio/me/share", headers=auth)

    everything = client.get("/projects").json()
    assert [p["title"] for p in everything] == ["Budget App", "Line Following Robot"]
    assert everything[0]["owner_name"] == "Sam Student" and everything[0]["share_token"]

    def titles(**params):
        return [p["title"] for p in client.get("/projects", params=params).json()]

    assert titles(search="robot") == ["Line Following Robot"]          # title, and Riley's isn't shared
    assert titles(search="raspberry") == ["Line Following Robot"]      # technologies
    assert titles(search="autonomous") == ["Line Following Robot"]     # description
    assert titles(search="python react") == ["Budget App"]             # every word must match
    assert titles(search="robot react") == []
    assert titles(search="100%") == []                                 # wildcards are escaped
    assert titles(category="web development") == ["Budget App"]
    assert titles(limit=1, offset=1) == ["Line Following Robot"]


def test_update_three_fields_persists(client, auth):
    pid = client.post("/projects", headers=auth, json={"title": "Old", "description": "Old desc", "subject": "Old cat"}).json()["id"]
    r = client.patch(f"/projects/{pid}", headers=auth, json={"title": "New", "description": "New desc", "subject": "Robotics"})
    assert r.status_code == 200
    saved = client.get(f"/projects/{pid}", headers=auth).json()
    assert (saved["title"], saved["description"], saved["subject"]) == ("New", "New desc", "Robotics")


# --- CORS ---------------------------------------------------------------------

def test_cors_allows_local_frontends(client):
    def preflight(origin):
        return client.options("/projects", headers={
            "Origin": origin, "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        })

    for origin in ("http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"):
        r = preflight(origin)
        assert r.status_code == 200, origin
        assert r.headers["access-control-allow-origin"] == origin
        assert client.get("/projects", headers={"Origin": origin}).headers["access-control-allow-origin"] == origin

    for origin in ("https://evil.example.com", "http://localhost.evil.com", "http://localhost:5173.evil.com"):
        assert preflight(origin).status_code == 400, origin
        assert "access-control-allow-origin" not in client.get("/projects", headers={"Origin": origin}).headers


# --- Certificates and job preferences ---------------------------------------------

def test_certificates_and_job_preferences(client, auth):
    cert = client.post("/portfolio/me/certificates", headers=auth, json={
        "name": "AWS Cloud Practitioner", "issuer": "Amazon Web Services", "issue_year": 2025,
        "credential_url": "https://aws.amazon.com/verify/abc",
    })
    assert cert.status_code == 201, cert.text
    cid = cert.json()["id"]
    assert client.patch(f"/portfolio/me/certificates/{cid}", headers=auth, json={"issue_year": 2026}).json()["issue_year"] == 2026
    assert client.post("/portfolio/me/certificates", headers=auth, json={"name": ""}).status_code == 422
    assert client.post("/portfolio/me/certificates", headers=auth, json={"name": "X", "issue_year": 1800}).status_code == 422
    assert client.patch(f"/portfolio/me/certificates/{cid}", headers=auth, json={"name": None}).status_code == 422

    job = client.post("/portfolio/me/job-preferences", headers=auth, json={
        "role": "Frontend Developer", "location": "Remote", "employment_type": "Internship", "min_salary": 70000,
    })
    assert job.status_code == 201, job.text
    jid = job.json()["id"]
    assert client.patch(f"/portfolio/me/job-preferences/{jid}", headers=auth, json={"employment_type": "Full-time"}).json()["employment_type"] == "Full-time"
    assert client.post("/portfolio/me/job-preferences", headers=auth, json={"role": "X", "employment_type": "Gig"}).status_code == 422
    assert client.post("/portfolio/me/job-preferences", headers=auth, json={"role": "X", "min_salary": -5}).status_code == 422

    mine = client.get("/portfolio/me", headers=auth).json()
    assert [c["name"] for c in mine["certificates"]] == ["AWS Cloud Practitioner"]
    assert mine["job_preferences"][0]["min_salary"] == 70000

    # Shared portfolio shows certificates but never job preferences (salary is private).
    token = client.post("/portfolio/me/share", headers=auth).json()["share_token"]
    public = client.get(f"/public/portfolios/{token}").json()
    assert public["certificates"][0]["issuer"] == "Amazon Web Services"
    assert "job_preferences" not in public

    # Other students can't touch them.
    other = signup(client, email="other@sfsu.edu")
    assert client.delete(f"/portfolio/me/certificates/{cid}", headers=other).status_code == 404
    assert client.patch(f"/portfolio/me/job-preferences/{jid}", headers=other, json={"role": "Hacked"}).status_code == 404

    assert client.delete(f"/portfolio/me/certificates/{cid}", headers=auth).status_code == 204
    assert client.delete(f"/portfolio/me/job-preferences/{jid}", headers=auth).status_code == 204
    assert client.get("/portfolio/me", headers=auth).json()["certificates"] == []


def test_ai_payload_includes_certificates_not_salary(client, auth):
    client.post("/portfolio/me/certificates", headers=auth, json={"name": "CompTIA Security+"})
    client.post("/portfolio/me/job-preferences", headers=auth, json={
        "role": "Security Analyst", "location": "Oakland, CA", "min_salary": 98765,
    })
    from app.database import SessionLocal
    from app import models
    with SessionLocal() as db:
        payload = ai.build_portfolio_payload(db.query(models.Portfolio).one())
    text = json.dumps(payload)
    assert "CompTIA Security+" in text and "Security Analyst" in text
    assert "98765" not in text and "Oakland" not in text

    # A certificate alone is enough to request guidance, and the role shows up as a path.
    r = client.post("/guidance", headers=auth)
    assert r.status_code == 201, r.text
    assert "Security Analyst" in [p["title"] for p in r.json()["career_paths"]]
