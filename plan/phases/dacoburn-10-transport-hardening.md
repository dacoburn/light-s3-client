# Phase dacoburn-10: Transport hardening — timeouts + retry with backoff in do_request

> **Status:** planned — ready to implement
> **Depends on:** —
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** `do_request` currently calls `requests.request` with **no timeout** (a hung
connection blocks forever) and gives up on the first transient failure. Add a default timeout
and bounded retries with exponential backoff for transient errors only.

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-10: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

All in `light_s3_client/__init__.py` (the module-level `do_request`):

- [ ] `do_request` signature gains `timeout: int = 60, max_retries: int = 3,
      backoff_factor: float = 0.5` (keyword args, defaults preserve existing call sites);
      `timeout` is passed to every `requests.request` call
  - Acceptance: `grep -n "timeout" light_s3_client/__init__.py` — shows both the parameter
    and the `requests.request(..., timeout=timeout)` pass-through; paste
- [ ] Retry loop: on `ConnectionError`/`Timeout` exceptions **or** HTTP status
      500/502/503/504, retry up to `max_retries` times sleeping
      `backoff_factor * (2 ** attempt)` seconds between attempts (`time.sleep` — tests mock
      it). 4xx statuses and other `RequestException`s are NEVER retried. After the last
      attempt, behavior is exactly today's (synthetic 500 `Response` for transport errors,
      exception mapping for HTTP errors).
  - Acceptance: `grep -n "backoff_factor\|2 \*\* " light_s3_client/__init__.py`; paste
- [ ] The synthetic-500 error paths collapse into one helper (`_error_response(msg_dict)`)
      instead of today's four copy-pasted blocks — behavior identical (same JSON body shape,
      same `log.error` calls)
  - Acceptance: `grep -c "response._content = bytes" light_s3_client/__init__.py` → 1; paste
- [ ] `TYPE_CHECKING` stub for `do_request` updated to the new signature
  - Acceptance: `grep -n "max_retries" light_s3_client/__init__.py` → ≥2 hits (impl + stub); paste
- [ ] Named tests in `tests/test_unit.py` (offline; mock `requests.request` and `time.sleep`):
  - [ ] `test_do_request_passes_timeout`: default call → `requests.request` received
        `timeout=60` (assert on the mock's call kwargs, exact)
  - [ ] `test_do_request_retries_on_connection_error`: side_effect
        `[ConnectionError, ConnectionError, ok_response]` → returns the 200 response and
        `requests.request` was called exactly 3 times
  - [ ] `test_do_request_retries_on_503_then_succeeds`: side_effect `[503, 200]` → returns
        the 200 response; `time.sleep` called once with `0.5` (exact)
  - [ ] `test_do_request_no_retry_on_404`: single 404 → `BucketNotFound` raised and
        `requests.request` called exactly once
  - [ ] `test_do_request_gives_up_after_max_retries`: `max_retries=2`, all attempts
        `ConnectionError` → synthetic response with `status_code == 500` and
        `requests.request` called exactly 3 times (initial + 2 retries)

## Files

`light_s3_client/__init__.py`, `tests/test_unit.py` (2 code files) + docs ride-along:
`README.md`, `ai-instructions.md` (document the new transport defaults).

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_do_request_passes_timeout|test_do_request_retries_on_connection_error|test_do_request_retries_on_503_then_succeeds|test_do_request_no_retry_on_404|test_do_request_gives_up_after_max_retries"` → 5; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "max_retries" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-10: transport hardening"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 5 named tests collected and green; NO retry on 4xx
(attack this: a retried 403 would double-bill mutating requests); exactly one synthetic-error
helper remains; existing feature-module call sites unchanged and green;
`git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
