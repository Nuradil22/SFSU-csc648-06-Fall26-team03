"""A scripted stand-in for openai.OpenAI used by the career chat tests.

No network calls are made. Each `responses.create` call records its kwargs and
returns the next scripted step (or raises it, if it is an exception). A step
is a dict:

- "parsed": fields merged into {"reply": "ok", "resources": [], "proposal": None}
  and returned as the message's JSON output text
- "text": raw output text instead (e.g. invalid or truncated JSON)
- "refusal": a refusal message instead of output text
- "status": response status (default "completed"); "incomplete" pairs with
  "reason" (default "max_output_tokens")
- "output": extra output items placed before the message (e.g. search_call())
- "usage": token counts (default 100 input / 20 output)
"""

import json
from types import SimpleNamespace


class FakeOpenAI:
    calls: list = []
    clients: list = []
    script: list = []

    def __init__(self, **kwargs):
        FakeOpenAI.clients.append(kwargs)
        self.responses = self

    def create(self, **kwargs):
        FakeOpenAI.calls.append(kwargs)
        step = FakeOpenAI.script.pop(0) if FakeOpenAI.script else {}

        if isinstance(step, Exception):
            raise step

        if "refusal" in step:
            content = [{"type": "refusal", "refusal": step["refusal"]}]
        else:
            text = step.get("text")
            if text is None:
                text = json.dumps({"reply": "ok", "resources": [], "proposal": None, **step.get("parsed", {})})
            content = [{"type": "output_text", "text": text, "annotations": []}]

        status = step.get("status", "completed")
        usage = {"input_tokens": 100, "output_tokens": 20, **step.get("usage", {})}

        return SimpleNamespace(
            model="gpt-5-mini-fake",
            status=status,
            incomplete_details=(
                {"reason": step.get("reason", "max_output_tokens")} if status == "incomplete" else None
            ),
            output=[*step.get("output", []), {"type": "message", "role": "assistant", "content": content}],
            usage=SimpleNamespace(**usage),
        )


def reset():
    FakeOpenAI.calls = []
    FakeOpenAI.clients = []
    FakeOpenAI.script = []


def search_call(*urls, query="courses"):
    """A completed web_search_call output item with these source URLs."""
    return {
        "type": "web_search_call",
        "status": "completed",
        "action": {"type": "search", "query": query, "sources": [{"type": "url", "url": u} for u in urls]},
    }


def resource(name, url, provider="San Francisco State University", description="Fits your goals."):
    return {"name": name, "description": description, "provider": provider, "url": url}


def plan(*milestone_resources, title="Data engineering roadmap"):
    """A proposal with one goal; one milestone per resource list given."""
    milestones = [
        {"id": f"m{i}", "title": f"Milestone {i}", "completed": False, "resources": list(res)}
        for i, res in enumerate(milestone_resources or [[]], start=1)
    ]
    return {"title": title, "goals": [{"id": "g1", "title": "Build skills", "milestones": milestones}]}
