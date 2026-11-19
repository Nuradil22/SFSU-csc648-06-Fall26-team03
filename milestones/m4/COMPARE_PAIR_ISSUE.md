# DRAFT GitHub Issue — do not publish without team approval

**Suggested title:** `compare_pair` leaks whitespace into provider names — 503 "Unknown comparison provider"

**Suggested labels:** `bug`, `status: resolved`
**Suggested severity:** Low (requires unusual spacing in `MODEL_COMPARE_PAIR` env var)
**Suggested assignee:** Nuradil (backend)
**Status:** Closed on creation — fix already committed

## Summary

`compare_pair()` in `app/routers/model_compare.py` split each
`MODEL_COMPARE_PAIR` entry on `:` but did not strip whitespace around the
provider or model. A config value like `" OpenAI : gpt-5.1 , anthropic : x "`
produced provider `"openai "` (trailing space), which then failed provider
dispatch at request time with `503 Unknown comparison provider 'openai '`.

## Reproduction

```python
settings.model_compare_pair = " OpenAI : gpt-5.1 , Anthropic : claude-sonnet-4 "
compare_pair()  # -> [("openai ", " gpt-5.1"), ("anthropic ", " claude-sonnet-4")]
```

Calling `POST /career/compare` with that config returns a per-model
`status: "error"` result instead of recommendations.

## Expected

Entries are normalized; whitespace inside the env value is ignored.

## Fix

Commit `0081429` (`feature/m4-integration`): strip both sides of the
`provider:model` partition in `compare_pair`. Regression test:
`tests/test_model_compare.py::test_compare_pair_parses_explicit_spec`.

## Evidence

Found by the new unit test `test_compare_pair_parses_explicit_spec` during
M4 test-authoring — an example of the test suite catching a real defect.
