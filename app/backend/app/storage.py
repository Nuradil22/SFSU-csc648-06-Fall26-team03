"""File storage for project images and 3D models.

Two backends, picked with STORAGE_BACKEND:
- "local": files go in UPLOAD_DIR and are served by this app at /uploads. Fine for
  local dev; NOT for Render, whose disk is wiped on every deploy.
- "supabase": files go in a public Supabase Storage bucket (created on first upload
  if it doesn't exist). Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""

import json
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile, status

from .config import settings


class StorageError(Exception):
    pass


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

IMAGE_SIGNATURES = {
    "jpg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "gif": (b"GIF87a", b"GIF89a"),
}
IMAGE_CONTENT_TYPES = {"jpg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}

MODEL_CONTENT_TYPES = {"glb": "model/gltf-binary", "gltf": "model/gltf+json"}
SUPPORTED_MODEL_FORMATS = ", ".join(f".{ext}" for ext in MODEL_CONTENT_TYPES)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def read_upload(upload: UploadFile, max_mb: int) -> bytes:
    limit = max_mb * 1024 * 1024
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File is larger than {max_mb} MB")
    if not data:
        raise _bad_request("Uploaded file is empty")
    return data


def detect_image_format(data: bytes) -> str:
    """Return the image extension based on file contents, or raise 400 (R8.1)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    for ext, signatures in IMAGE_SIGNATURES.items():
        if any(data.startswith(sig) for sig in signatures):
            return ext
    raise _bad_request("Unsupported image. Upload a JPEG, PNG, GIF, or WebP file.")


def detect_model_format(data: bytes, filename: str | None) -> str:
    """Return "glb" or "gltf" if the file is a model the Three.js viewer can load
    from a single URL, otherwise raise 400 (R15.2, R15.5)."""
    if data[:4] == b"glTF":
        return "glb"

    if (filename or "").lower().endswith(".gltf"):
        try:
            doc = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise _bad_request("This .gltf file is not valid JSON.")
        if not isinstance(doc, dict) or "asset" not in doc:
            raise _bad_request("This .gltf file is missing its 'asset' section.")
        # A .gltf that points at separate .bin / texture files would break once
        # uploaded on its own, so only self-contained (embedded) ones are accepted.
        uris = [item.get("uri", "") for key in ("buffers", "images") for item in doc.get(key, []) or []]
        if any(uri and not uri.startswith("data:") for uri in uris):
            raise _bad_request(
                "This .gltf file references external files. Export it as a single .glb file instead."
            )
        return "gltf"

    raise _bad_request(f"Unsupported 3D model. Supported formats: {SUPPORTED_MODEL_FORMATS}.")


def new_object_path(folder: str, ext: str) -> str:
    return f"{folder}/{uuid.uuid4().hex}.{ext}"


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

class LocalStorage:
    def __init__(self, root: str, base_url: str):
        self.root = Path(root)
        self.base_url = base_url.rstrip("/")

    def save(self, path: str, data: bytes, content_type: str) -> str:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"{self.base_url}/uploads/{path}"

    def delete(self, path: str) -> None:
        (self.root / path).unlink(missing_ok=True)


class SupabaseStorage:
    def __init__(self, url: str, service_key: str, bucket: str):
        if not url or not service_key:
            raise StorageError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for Supabase storage")
        self.api = f"{url.rstrip('/')}/storage/v1"
        self.bucket = bucket
        self.headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    def _upload(self, client: httpx.Client, path: str, data: bytes, content_type: str) -> httpx.Response:
        return client.post(
            f"{self.api}/object/{self.bucket}/{path}",
            content=data,
            headers={**self.headers, "Content-Type": content_type, "x-upsert": "true"},
        )

    def save(self, path: str, data: bytes, content_type: str) -> str:
        with httpx.Client(timeout=60) as client:
            response = self._upload(client, path, data, content_type)
            if response.status_code in (400, 404) and "not found" in response.text.lower():
                client.post(
                    f"{self.api}/bucket",
                    json={"id": self.bucket, "name": self.bucket, "public": True},
                    headers=self.headers,
                )
                response = self._upload(client, path, data, content_type)
        if response.is_error:
            raise StorageError(f"Supabase upload failed ({response.status_code}): {response.text[:200]}")
        return f"{self.api}/object/public/{self.bucket}/{path}"

    def delete(self, path: str) -> None:
        with httpx.Client(timeout=30) as client:
            client.request(
                "DELETE", f"{self.api}/object/{self.bucket}", json={"prefixes": [path]}, headers=self.headers
            )


def get_storage() -> LocalStorage | SupabaseStorage:
    if settings.storage_backend == "supabase":
        return SupabaseStorage(settings.supabase_url, settings.supabase_service_role_key, settings.supabase_bucket)
    return LocalStorage(settings.upload_dir, settings.public_api_url)


def store_file(path: str, data: bytes, content_type: str) -> str:
    try:
        return get_storage().save(path, data, content_type)
    except (StorageError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="File storage is unavailable. Try again later."
        ) from exc


def remove_file(path: str | None) -> None:
    """Best-effort delete: a leftover file shouldn't block removing the DB record."""
    if not path:
        return
    try:
        get_storage().delete(path)
    except (StorageError, httpx.HTTPError, OSError):
        pass
