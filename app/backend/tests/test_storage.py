"""Unit tests for app/storage.py: upload validation, format detection, both
storage backends, and the HTTP error mapping for storage failures."""

import io
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException, UploadFile

from app import storage


def _upload(data: bytes) -> UploadFile:
    return UploadFile(file=io.BytesIO(data), filename="f.bin")


# --- Upload reading ------------------------------------------------------------

def test_read_upload_enforces_size_limit():
    with pytest.raises(HTTPException) as exc:
        storage.read_upload(_upload(b"x" * (1024 * 1024 + 1)), max_mb=1)
    assert exc.value.status_code == 413


def test_read_upload_rejects_empty_file():
    with pytest.raises(HTTPException) as exc:
        storage.read_upload(_upload(b""), max_mb=1)
    assert exc.value.status_code == 400


# --- Format detection ------------------------------------------------------------

def test_detect_image_format_accepts_webp():
    assert storage.detect_image_format(b"RIFF\x00\x00\x00\x00WEBP" + b"x" * 8) == "webp"


def test_detect_image_format_rejects_unknown_bytes():
    with pytest.raises(HTTPException) as exc:
        storage.detect_image_format(b"not-an-image")
    assert exc.value.status_code == 400


def test_detect_model_format_accepts_glb_magic():
    assert storage.detect_model_format(b"glTF\x02\x00\x00\x00rest", "model.bin") == "glb"


def test_detect_model_format_rejects_invalid_gltf_json():
    with pytest.raises(HTTPException) as exc:
        storage.detect_model_format(b"{not json", "scene.gltf")
    assert "not valid JSON" in exc.value.detail


def test_detect_model_format_requires_asset_section():
    with pytest.raises(HTTPException) as exc:
        storage.detect_model_format(b"{}", "scene.gltf")
    assert "'asset'" in exc.value.detail


def test_detect_model_format_rejects_external_references():
    doc = {"asset": {"version": "2.0"}, "buffers": [{"uri": "buffer.bin"}]}
    with pytest.raises(HTTPException) as exc:
        storage.detect_model_format(json.dumps(doc).encode(), "scene.gltf")
    assert "external files" in exc.value.detail


def test_detect_model_format_accepts_embedded_gltf():
    doc = {"asset": {"version": "2.0"},
           "buffers": [{"uri": "data:application/octet-stream;base64,AA=="}],
           "images": [{"uri": "data:image/png;base64,AA=="}]}
    assert storage.detect_model_format(json.dumps(doc).encode(), "scene.gltf") == "gltf"


def test_detect_model_format_rejects_other_files():
    with pytest.raises(HTTPException) as exc:
        storage.detect_model_format(b"MZ...", "prog.exe")
    assert "Supported formats" in exc.value.detail


# --- Local backend ---------------------------------------------------------------

def test_local_storage_roundtrip(tmp_path):
    local = storage.LocalStorage(str(tmp_path), "http://localhost:8000")
    url = local.save("models/abc.glb", b"glTFdata", "model/gltf-binary")
    assert url == "http://localhost:8000/uploads/models/abc.glb"
    assert (tmp_path / "models" / "abc.glb").read_bytes() == b"glTFdata"

    local.delete("models/abc.glb")
    assert not (tmp_path / "models" / "abc.glb").exists()
    local.delete("models/gone.glb")  # missing files are ignored


# --- Supabase backend ------------------------------------------------------------

def test_supabase_storage_requires_url_and_key():
    with pytest.raises(storage.StorageError):
        storage.SupabaseStorage("", "key", "bucket")
    with pytest.raises(storage.StorageError):
        storage.SupabaseStorage("https://x.supabase.co", "", "bucket")


def test_supabase_storage_headers_by_key_type():
    jwt = storage.SupabaseStorage("https://x.supabase.co", "eyJhbGciOi...", "b")
    assert jwt.headers["Authorization"] == "Bearer eyJhbGciOi..."
    secret = storage.SupabaseStorage("https://x.supabase.co", "sb_secret_abc", "b")
    assert "Authorization" not in secret.headers
    assert secret.headers["apikey"] == "sb_secret_abc"


class _FakeHTTP:
    """Replaces httpx.Client inside storage; queues scripted responses."""
    responses: list = []
    posts: list = []
    deleted: list = []

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @staticmethod
    def _next():
        item = _FakeHTTP.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def post(self, url, **kwargs):
        _FakeHTTP.posts.append((url, kwargs))
        return self._next()

    def request(self, method, url, **kwargs):
        _FakeHTTP.deleted.append((method, url, kwargs))
        return SimpleNamespace(is_error=False)


def _resp(code, text=""):
    return SimpleNamespace(status_code=code, text=text, is_error=code >= 400)


@pytest.fixture
def fake_http(monkeypatch):
    _FakeHTTP.responses = []
    _FakeHTTP.posts = []
    _FakeHTTP.deleted = []
    monkeypatch.setattr(storage.httpx, "Client", _FakeHTTP)
    return _FakeHTTP


def test_supabase_save_creates_missing_bucket_and_retries(fake_http):
    _FakeHTTP.responses = [
        _resp(404, "bucket not found"),
        _resp(200),            # bucket creation
        _resp(200),            # retried upload
    ]
    supa = storage.SupabaseStorage("https://x.supabase.co", "sb_secret_abc", "models")
    url = supa.save("models/a.glb", b"data", "model/gltf-binary")
    assert url == "https://x.supabase.co/storage/v1/object/public/models/models/a.glb"
    assert len(_FakeHTTP.posts) == 3
    assert _FakeHTTP.posts[1][0].endswith("/bucket")
    assert _FakeHTTP.posts[1][1]["json"]["public"] is True


def test_supabase_save_raises_on_unrecoverable_error(fake_http):
    _FakeHTTP.responses = [_resp(500, "server on fire")]
    supa = storage.SupabaseStorage("https://x.supabase.co", "sb_secret_abc", "models")
    with pytest.raises(storage.StorageError):
        supa.save("models/a.glb", b"data", "model/gltf-binary")


def test_supabase_delete_uses_prefix_endpoint(fake_http):
    supa = storage.SupabaseStorage("https://x.supabase.co", "sb_secret_abc", "models")
    supa.delete("models/a.glb")
    method, url, kwargs = _FakeHTTP.deleted[0]
    assert method == "DELETE"
    assert kwargs["json"] == {"prefixes": ["models/a.glb"]}


# --- HTTP mapping / cleanup --------------------------------------------------------

def test_store_file_maps_storage_failure_to_503(monkeypatch):
    class Broken:
        def save(self, *args):
            raise storage.StorageError("down")

    monkeypatch.setattr(storage, "get_storage", lambda: Broken())
    with pytest.raises(HTTPException) as exc:
        storage.store_file("p", b"d", "text/plain")
    assert exc.value.status_code == 503


def test_remove_file_swallows_errors_and_skips_none(monkeypatch):
    class Broken:
        def delete(self, *args):
            raise storage.StorageError("down")

    monkeypatch.setattr(storage, "get_storage", lambda: Broken())
    storage.remove_file("models/a.glb")  # does not raise
    storage.remove_file(None)            # no-op, does not raise
