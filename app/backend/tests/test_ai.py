"""Unit tests for app/ai.py: portfolio payload flattening, the rule-based
mock provider's branches, and provider failure handling. No live AI calls —
SDK clients are faked where the provider would otherwise reach the network."""

from types import SimpleNamespace

import anthropic
import openai
import pytest

from app import ai
from app.config import settings


def _payload(**overrides):
    payload = {
        "headline": "",
        "bio": "",
        "career_interests": [],
        "education": [],
        "skills": [],
        "experience": [],
        "certificates": [],
        "job_preferences": [],
        "projects": [],
    }
    payload.update(overrides)
    return payload


def _experience(n=1):
    return [
        {"type": "internship", "organization": f"Org{i}", "position": "Intern",
         "start_date": "2024-01-01", "end_date": None, "description": ""}
        for i in range(n)
    ]


def _project(technologies=("Python",), title="Demo"):
    return {"title": title, "subject": "", "date": "2025",
            "description": "", "technologies": list(technologies),
            "has_3d_model": False}


# --- Content-block flattening -------------------------------------------------

def test_blocks_to_text_flattens_editor_blocks():
    blocks = [
        {"type": "heading", "content": "Overview"},
        {"type": "paragraph", "content": "  Details here.  "},
        {"type": "list", "items": ["first", " ", "second"]},
        {"type": "list", "content": ["also-a-list", 42, None]},
        {"type": "unknown"},
    ]
    assert ai._blocks_to_text(blocks) == "Overview\nDetails here.\n- first\n- second\n- also-a-list"


def test_blocks_to_text_handles_none_and_empty():
    assert ai._blocks_to_text(None) == ""
    assert ai._blocks_to_text([]) == ""


# --- Mock provider ------------------------------------------------------------

def test_mock_guidance_grammar_and_empty_portfolio():
    content, name = ai._mock_guidance(_payload())
    assert name == "mock"
    assert "just getting started" in content.summary

    one = ai._mock_guidance(_payload(experience=_experience(1)))[0]
    assert "1 experience entry" in one.summary
    two = ai._mock_guidance(_payload(experience=_experience(2)))[0]
    assert "2 experience entries" in two.summary


def test_mock_guidance_projects_without_technologies_improvement():
    content, _ = ai._mock_guidance(_payload(projects=[_project(technologies=())]))
    assert any("technologies" in i.explanation for i in content.improvements)


def test_mock_guidance_fuller_profile_avoids_skill_and_project_nudges():
    skills = [{"name": f"s{i}", "category": "technical", "proficiency": "advanced"}
              for i in range(5)]
    content, _ = ai._mock_guidance(_payload(
        skills=skills,
        projects=[_project()],
        experience=_experience(1),
        career_interests=["Backend Engineer"],
    ))
    areas = [i.area for i in content.improvements]
    assert "Skills" not in areas and "Projects" not in areas and "Experience" not in areas
    assert content.career_paths[0].title == "Backend Engineer"
    # With nothing missing, the fallback next step researches the target role.
    assert "job postings" in content.next_steps[0].action


def test_mock_guidance_without_interests_suggests_adding_them():
    content, _ = ai._mock_guidance(_payload(
        projects=[_project()], experience=_experience(1),
        skills=[{"name": f"s{i}", "category": "technical", "proficiency": "x"}
                for i in range(5)],
    ))
    assert any("career interests" in s.action for s in content.next_steps)


# --- Provider failure handling -------------------------------------------------

def test_openai_guidance_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(ai.AIServiceError) as exc:
        ai._openai_guidance(_payload())
    assert exc.value.unavailable


def test_anthropic_guidance_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with pytest.raises(ai.AIServiceError) as exc:
        ai._anthropic_guidance(_payload())
    assert exc.value.unavailable


def test_openai_guidance_null_output_is_an_error(monkeypatch):
    class FakeClient:
        def __init__(self, **kw):
            self.responses = self

        def parse(self, **kw):
            return SimpleNamespace(output_parsed=None, model="fake")

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    monkeypatch.setattr(settings, "openai_api_key", "k")
    with pytest.raises(ai.AIServiceError):
        ai._openai_guidance(_payload())


def test_anthropic_guidance_refusal_and_incomplete_are_errors(monkeypatch):
    class FakeClient:
        response = None

        def __init__(self, **kw):
            self.beta = self
            self.messages = self

        def parse(self, **kw):
            return FakeClient.response

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    monkeypatch.setattr(settings, "anthropic_api_key", "k")

    FakeClient.response = SimpleNamespace(
        stop_reason="refusal", stop_details=None, parsed_output=None, model="m")
    with pytest.raises(ai.AIServiceError) as refusal:
        ai._anthropic_guidance(_payload())
    assert "could not analyze" in refusal.value.message

    FakeClient.response = SimpleNamespace(
        stop_reason="max_tokens", stop_details=None, parsed_output=None, model="m")
    with pytest.raises(ai.AIServiceError) as incomplete:
        ai._anthropic_guidance(_payload())
    assert "incomplete" in incomplete.value.message


def test_generate_guidance_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    with pytest.raises(ai.AIServiceError) as exc:
        ai.generate_guidance(_payload())
    assert exc.value.unavailable
