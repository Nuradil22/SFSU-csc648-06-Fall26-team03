import os
import tempfile

# Point the app at a throwaway SQLite DB and upload folder before it's imported.
_tmp = tempfile.mkdtemp(prefix="careergps-test-")
# Set TEST_DATABASE_URL to run against a scratch Postgres instead. Never point it at
# the shared Supabase database: every test drops and recreates all tables.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["AI_PROVIDER"] = "mock"
# Keep a developer's local .env research/limit settings out of the tests.
os.environ["OPENAI_WEB_SEARCH"] = "false"
os.environ["OPENAI_WEB_SEARCH_DOMAINS"] = ""
os.environ["OPENAI_WEB_SEARCH_BLOCKED_DOMAINS"] = "courseleaf.com,reddit.com,youtube.com,quora.com"
# No real network from tests; link-check tests enable it with a mock transport.
os.environ["RESOURCE_LINK_CHECK"] = "false"
os.environ["OPENAI_MAX_WEB_SEARCHES"] = "3"
os.environ["OPENAI_WEB_SEARCH_CONTEXT"] = "low"
os.environ["AI_ROADMAP_GENERATIONS_PER_DAY"] = "5"
os.environ["AI_CHAT_MESSAGES_PER_HOUR"] = "30"
os.environ["OPENAI_REASONING_EFFORT"] = "low"
os.environ["OPENAI_MAX_OUTPUT_TOKENS_CHAT"] = "3000"
os.environ["OPENAI_MAX_OUTPUT_TOKENS_ROADMAP"] = "10000"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def signup(client, email="student@sfsu.edu", name="Sam Student", password="password123"):
    response = client.post("/auth/signup", json={"name": name, "email": email, "password": password})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return signup(client)
