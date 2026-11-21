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
- "citations": {url: page title} url_citation annotations on the message. By
  default every recommended resource whose URL one of the step's searches
  returned is cited with its own name as the page title (the evidence of an
  official name when the link check, off in tests, can't read the page);
  pass {} for none
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
            citations = step.get("citations")
            if citations is None:
                citations = _default_citations(step)
            annotations = [{"type": "url_citation", "url": u, "title": t} for u, t in citations.items()]
            content = [{"type": "output_text", "text": text, "annotations": annotations}]

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


def _default_citations(step) -> dict:
    searched = {
        source["url"]
        for item in step.get("output", [])
        if isinstance(item, dict) and item.get("type") == "web_search_call"
        for source in item["action"].get("sources", [])
    }
    parsed = step.get("parsed", {})
    items = list(parsed.get("resources") or [])
    for goal in (parsed.get("proposal") or {}).get("goals", []):
        for milestone in goal.get("milestones", []):
            items += milestone.get("resources") or []
    return {item["url"]: item["name"] for item in items if item.get("url") in searched}


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


def resource(name, url, provider="San Francisco State University", description="Fits your goals.", **details):
    """An AI resource; `details` sets code, kind, topics, credential, or outcome."""
    return {
        "name": name, "code": "", "kind": "course", "provider": provider, "topics": [],
        "credential": "none_stated", "url": url, "description": description, "outcome": "",
        **details,
    }


def plan(*milestone_resources, title="Data engineering roadmap", serves="Data Engineer"):
    """A proposal with one learning stage serving `serves`; one milestone per
    resource list given. Without a verified offering the educational gate
    rejects it (no roadmap)."""
    milestones = [
        {"id": f"m{i}", "title": f"Milestone {i}", "completed": False, "resources": list(res)}
        for i, res in enumerate(milestone_resources or [[]], start=1)
    ]
    return {"title": title, "goals": [{"id": "g1", "title": "Build skills", "kind": "competency",
                                       "serves": serves, "milestones": milestones}]}


# --- A verifiable educational roadmap -------------------------------------------
# One learning stage centered on one course from an official SFSU page (its
# name is confirmed by the search title the fake cites by default), serving
# the student's own goal. Use with web search enabled.

EDU_URL = "https://bulletin.sfsu.edu/courses/csc/"


def educational_plan(title="Data engineering roadmap", serves="Data Engineer",
                     name="Introduction to Database Systems", url=EDU_URL, stage="Relational databases"):
    offering = resource(name, url, description="Your goal needs relational data design.")
    return {"title": title, "goals": [{
        "id": "g1", "title": stage, "kind": "competency", "serves": serves,
        "milestones": [
            {"id": "m1", "title": f"Take {name}", "completed": False, "step": "learn",
             "resources": [offering]},
            {"id": "m2", "title": "Use it in one of your projects", "completed": False,
             "step": "apply", "resources": []},
        ],
    }]}


def researched(proposal, reply="ok"):
    """A scripted step: one search that returned every resource URL in
    `proposal`, then the proposal."""
    urls = [r["url"] for g in proposal["goals"] for m in g["milestones"] for r in m.get("resources") or []]
    return {"output": [search_call(*dict.fromkeys(urls))], "parsed": {"reply": reply, "proposal": proposal}}
