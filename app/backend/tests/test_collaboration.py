"""M4 collaboration: project likes/comments and 3D-model revisions.

Covers authentication, authorization, persistence, visibility of private
projects, idempotent likes, comment deletion rules, revision ordering and
change notes, backward compatibility with pre-revision models, and that old
revision files are kept.
"""

from .conftest import signup
from .test_api import make_glb


def _project(client, headers, title="Robot Arm"):
    r = client.post("/projects", headers=headers, json={"title": title})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_public(client, headers):
    r = client.post("/portfolio/me/share", headers=headers)
    assert r.status_code == 200, r.text


def _upload(client, headers, pid, name="scan.glb", note=None, label=None):
    data = {}
    if note is not None:
        data["change_note"] = note
    if label is not None:
        data["version_label"] = label
    r = client.put(
        f"/projects/{pid}/model",
        headers=headers,
        files={"file": (name, make_glb(), "model/gltf-binary")},
        data=data,
    )
    assert r.status_code == 200, r.text
    return r.json()


# --- Likes ------------------------------------------------------------------

def test_like_requires_login(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)
    assert client.put(f"/projects/{pid}/like").status_code == 401
    assert client.delete(f"/projects/{pid}/like").status_code == 401


def test_like_unlike_counts_and_idempotency(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")

    r = client.put(f"/projects/{pid}/like", headers=other)
    assert r.json() == {"like_count": 1, "comment_count": 0, "liked_by_me": True}

    # Owner likes too; liking twice stays one like per student.
    client.put(f"/projects/{pid}/like", headers=auth)
    r = client.put(f"/projects/{pid}/like", headers=other)
    assert r.json()["like_count"] == 2

    r = client.get(f"/projects/{pid}/engagement", headers=other)
    assert r.json() == {"like_count": 2, "comment_count": 0, "liked_by_me": True}
    # Anonymous read on a public project: counts visible, liked_by_me false.
    r = client.get(f"/projects/{pid}/engagement")
    assert r.json() == {"like_count": 2, "comment_count": 0, "liked_by_me": False}

    r = client.delete(f"/projects/{pid}/like", headers=other)
    assert r.json()["like_count"] == 1
    # Unliking twice is harmless.
    assert client.delete(f"/projects/{pid}/like", headers=other).json()["like_count"] == 1


def test_likes_private_project_hidden_from_others(client, auth):
    pid = _project(client, auth)  # portfolio stays private
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")

    assert client.put(f"/projects/{pid}/like", headers=other).status_code == 404
    assert client.get(f"/projects/{pid}/engagement", headers=other).status_code == 404
    assert client.get(f"/projects/{pid}/engagement").status_code == 404
    # Owner can still like their own private project.
    assert client.put(f"/projects/{pid}/like", headers=auth).json()["like_count"] == 1


# --- Comments ---------------------------------------------------------------

def test_comments_crud_and_permissions(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")

    assert client.get(f"/projects/{pid}/comments", headers=other).json() == []
    assert client.post(f"/projects/{pid}/comments", json={"body": "hi"}).status_code == 401

    r = client.post(f"/projects/{pid}/comments", headers=other,
                    json={"body": "  Nice scan!  "})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert r.json()["author_name"] == "Vera Visitor"
    assert r.json()["body"] == "Nice scan!"

    client.post(f"/projects/{pid}/comments", headers=auth, json={"body": "Thanks!"})

    comments = client.get(f"/projects/{pid}/comments", headers=other).json()
    assert [c["body"] for c in comments] == ["Nice scan!", "Thanks!"]
    assert comments[0]["can_delete"] is True   # own comment
    assert comments[1]["can_delete"] is False  # someone else's

    # Anonymous readers see comments but cannot delete anything.
    anon = client.get(f"/projects/{pid}/comments").json()
    assert len(anon) == 2 and all(c["can_delete"] is False for c in anon)

    # Author can delete; the owner's delete permission is checked below.
    assert client.delete(f"/projects/{pid}/comments/{cid}", headers=other).status_code == 204
    assert [c["body"] for c in client.get(f"/projects/{pid}/comments").json()] == ["Thanks!"]


def test_comment_owner_can_delete_others(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")
    cid = client.post(f"/projects/{pid}/comments", headers=other,
                      json={"body": "feedback"}).json()["id"]

    assert client.delete(f"/projects/{pid}/comments/{cid}", headers=auth).status_code == 204
    assert client.get(f"/projects/{pid}/comments").json() == []


def test_comment_author_cannot_delete_others(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")
    third = signup(client, "third@sfsu.edu", "Tess Third")
    cid = client.post(f"/projects/{pid}/comments", headers=other,
                      json={"body": "mine"}).json()["id"]

    assert client.delete(f"/projects/{pid}/comments/{cid}", headers=third).status_code == 404
    assert len(client.get(f"/projects/{pid}/comments").json()) == 1


def test_comment_validation_and_private_project(client, auth):
    pid = _project(client, auth)  # private
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")

    assert client.post(f"/projects/{pid}/comments", headers=auth,
                       json={"body": ""}).status_code == 422
    assert client.post(f"/projects/{pid}/comments", headers=other,
                       json={"body": "sneaky"}).status_code == 404
    assert client.get(f"/projects/{pid}/comments", headers=other).status_code == 404


# --- Model revisions ----------------------------------------------------------

def test_revisions_history_order_notes_and_current(client, auth):
    _make_public(client, auth)
    pid = _project(client, auth)

    _upload(client, auth, pid, "v1.glb", note="First print")
    _upload(client, auth, pid, "v2.glb", note="Fixed the gripper")
    current = _upload(client, auth, pid, "v3.glb", note="Lighter shell", label="final")

    revisions = client.get(f"/projects/{pid}/model/revisions", headers=auth).json()
    assert [r["version_label"] for r in revisions] == ["final", "v2", "v1"]
    assert revisions[0]["is_current"] is True
    assert revisions[0]["url"] == current["url"]
    assert revisions[0]["change_note"] == "Lighter shell"
    assert [r["is_current"] for r in revisions[1:]] == [False, False]
    assert revisions[1]["original_filename"] == "v2.glb"

    # Older revision files are still downloadable.
    for revision in revisions[1:]:
        assert client.get(revision["url"]).status_code == 200


def test_revisions_public_read_and_private_denied(client, auth):
    pid = _project(client, auth)  # private at first
    _upload(client, auth, pid, note="first")
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")

    assert client.get(f"/projects/{pid}/model/revisions", headers=other).status_code == 404

    _make_public(client, auth)
    revisions = client.get(f"/projects/{pid}/model/revisions", headers=other).json()
    assert len(revisions) == 1 and revisions[0]["change_note"] == "first"


def test_revision_upload_is_owner_only(client, auth):
    pid = _project(client, auth)
    other = signup(client, "visitor@sfsu.edu", "Vera Visitor")
    r = client.put(f"/projects/{pid}/model", headers=other,
                   files={"file": ("x.glb", make_glb(), "model/gltf-binary")})
    assert r.status_code == 404


def test_legacy_model_is_backfilled_as_v1(client, auth):
    pid = _project(client, auth)
    _upload(client, auth, pid, "original.glb")  # model with no revision rows? first upload is v1

    # First upload already records revision v1; uploading again yields v1+v2.
    _upload(client, auth, pid, "second.glb", note="iteration")
    revisions = client.get(f"/projects/{pid}/model/revisions", headers=auth).json()
    assert [r["version_label"] for r in revisions] == ["v2", "v1"]
    assert revisions[1]["original_filename"] == "original.glb"
    assert revisions[0]["is_current"] is True


def test_existing_model_gets_implicit_revision_row(client, auth, monkeypatch):
    """A project whose model predates the revisions table still shows it in
    the history (synthesized v1), and a later upload back-fills it."""
    from app import models
    from app.database import SessionLocal

    pid = _project(client, auth)
    _upload(client, auth, pid, "old.glb")

    # Simulate a pre-revision project: drop the recorded revision row.
    db = SessionLocal()
    try:
        db.query(models.ProjectModelRevision).delete()
        db.commit()
    finally:
        db.close()

    revisions = client.get(f"/projects/{pid}/model/revisions", headers=auth).json()
    assert len(revisions) == 1
    assert revisions[0]["version_label"] == "v1"
    assert revisions[0]["is_current"] is True

    _upload(client, auth, pid, "new.glb", note="revision after upgrade")
    revisions = client.get(f"/projects/{pid}/model/revisions", headers=auth).json()
    assert [r["version_label"] for r in revisions] == ["v2", "v1"]
    assert client.get(revisions[1]["url"]).status_code == 200


def test_delete_model_removes_all_revisions(client, auth):
    pid = _project(client, auth)
    _upload(client, auth, pid)
    _upload(client, auth, pid, "v2.glb")

    assert client.delete(f"/projects/{pid}/model", headers=auth).status_code == 204
    assert client.get(f"/projects/{pid}/model/revisions", headers=auth).json() == []
    assert client.get(f"/projects/{pid}", headers=auth).json()["model_3d"] is None
