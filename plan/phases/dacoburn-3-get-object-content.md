# Phase dacoburn-3: get_object content retrieval + download_fileobj

> **Status:** planned — ready to implement
> **Depends on:** —
> **Read first:** [architecture.md](../architecture.md) (see Deviations — this phase resolves the recorded `get_object` deviation), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** `get_object` actually returns object content (boto3-style), the old boolean
existence check survives as `object_exists`, and `download_fileobj` writes an object into any
file-like target. This is a **deliberate breaking change** already recorded in
`architecture.md` → Deviations.

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-3: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] `def object_exists(self, Bucket: str, Key: str) -> bool` in
      `light_s3_client/buckets/__init__.py` — the current `get_object` body moves here
      verbatim (True on 200, False on `BucketNotFound`)
  - Acceptance: `grep -n "def object_exists" light_s3_client/buckets/__init__.py`
- [ ] `def get_object(self, Bucket: str, Key: str) -> dict` in
      `light_s3_client/buckets/__init__.py` — `GET {server}/{Bucket}/{Key}`; on 200 return
      `{"Body": <bytes>, "ContentType": ..., "ContentLength": ..., "ETag": ...,
      "LastModified": ...}` with `None`-valued header keys removed (same filtering pattern as
      `head_object`); on `BucketNotFound` return `{}`
  - Acceptance: `grep -n '"Body"' light_s3_client/buckets/__init__.py`
- [ ] `def download_fileobj(self, Bucket: str, Key: str, Fileobj) -> bool` in
      `light_s3_client/files/__init__.py` — streams the GET response into `Fileobj.write()`
      in chunks (use `response.iter_content(chunk_size=8192)`); `True` on success, `False` on
      `BucketNotFound`
  - Acceptance: `grep -n "def download_fileobj" light_s3_client/files/__init__.py` and
    `grep -n "iter_content" light_s3_client/files/__init__.py`; paste both
- [ ] Binding pattern in `light_s3_client/__init__.py`: `setattr` + `TYPE_CHECKING` stubs for
      `object_exists` and `download_fileobj`; the `get_object` stub's return type updated to
      `dict`
  - Acceptance: `grep -n "object_exists\|download_fileobj\|def get_object" light_s3_client/__init__.py`; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_get_object_returns_body_bytes`: mocked 200 with content `b"hello"` →
        `assert result["Body"] == b"hello"` (exact)
  - [ ] `test_get_object_missing_returns_empty_dict`: mocked 404 → `assert result == {}`
  - [ ] `test_object_exists_true_and_false`: mocked 200 → `is True`; mocked 404 → `is False`
  - [ ] `test_download_fileobj_writes_content`: mocked streaming 200 with `b"chunk1chunk2"`
        into an `io.BytesIO` → `assert buf.getvalue() == b"chunk1chunk2"` (exact)
- [ ] Existing unit tests that relied on `get_object` returning `bool` updated to call
      `object_exists` (behavior-preserving rename at the call sites — no test deleted)
  - Acceptance: `grep -rn "get_object(" tests/test_unit.py`; paste — no remaining assertion
    treats the return value as a bool

## Files

`light_s3_client/buckets/__init__.py`, `light_s3_client/files/__init__.py`,
`light_s3_client/__init__.py`, `tests/test_unit.py` *(4 files — at the phase-size limit)* +
docs ride-along: `README.md`, `ai-instructions.md` (both must re-document `get_object`'s new
return value and add `object_exists`/`download_fileobj`).

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_get_object_returns_body_bytes|test_get_object_missing_returns_empty_dict|test_object_exists_true_and_false|test_download_fileobj_writes_content"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "object_exists" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-3: get_object content + download_fileobj"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; `object_exists`
preserves the old boolean semantics; `get_object` returns `{}`/dict-with-`Body`; README and
ai-instructions describe the NEW `get_object` contract (grep for the old "Returns True" wording
— it must be gone); `git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
