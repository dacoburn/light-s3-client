# Phase dacoburn-9: Multipart management — list uploads, list parts, public abort

> **Status:** planned — ready to implement
> **Depends on:** —
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Orphaned multipart uploads cost money and are invisible today (`_abort_multipart_upload`
is private and there is no way to find stale uploads). Expose the management surface:
enumerate in-progress uploads, inspect their parts, and abort them.

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-9: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

All in `light_s3_client/multipart/__init__.py`:

- [ ] `def list_multipart_uploads(self, Bucket: str) -> list` — `GET {server}/{Bucket}/?uploads`;
      parse `ListMultipartUploadsResult/Upload` into a list of
      `{"Key": ..., "UploadId": ..., "Initiated": ...}` (single entry normalized to a
      one-element list; no uploads → `[]`)
  - Acceptance: `grep -n "def list_multipart_uploads" light_s3_client/multipart/__init__.py`
- [ ] `def list_parts(self, Bucket: str, Key: str, UploadId: str) -> list` —
      `GET {url}?uploadId=<UploadId>`; parse `ListPartsResult/Part` into
      `{"PartNumber": int, "ETag": ..., "Size": int}` dicts (ints, not strings; `[]` when empty)
  - Acceptance: `grep -n "def list_parts" light_s3_client/multipart/__init__.py`
- [ ] `def abort_multipart_upload(self, Bucket: str, Key: str, UploadId: str) -> bool` —
      public wrapper: delegates to the existing `_abort_multipart_upload` logic, returns
      `True` on success / `False` on `BucketNotFound` (no duplicated DELETE code — refactor
      the private helper if needed so there is exactly one abort implementation)
  - Acceptance: `grep -n "def abort_multipart_upload" light_s3_client/multipart/__init__.py`
- [ ] Binding pattern in `light_s3_client/__init__.py` for all three (`setattr` +
      `TYPE_CHECKING` stubs)
  - Acceptance: `grep -c "list_multipart_uploads\|list_parts\|abort_multipart_upload" light_s3_client/__init__.py` → ≥6; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_list_multipart_uploads_parses_entries`: mocked XML with two uploads →
        exact-equality assert on the returned list
  - [ ] `test_list_multipart_uploads_empty`: mocked result with no `Upload` → `assert result == []`
  - [ ] `test_list_parts_types`: mocked two-part XML → `assert result[0]["PartNumber"] == 1`
        and `assert isinstance(result[0]["Size"], int)`
  - [ ] `test_abort_multipart_upload_true_on_204`: mocked 204 → `is True`; requested URL
        contains exact substring `uploadId=`

## Files

`light_s3_client/multipart/__init__.py`, `light_s3_client/__init__.py`, `tests/test_unit.py`
(3 code files) + docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_list_multipart_uploads_parses_entries|test_list_multipart_uploads_empty|test_list_parts_types|test_abort_multipart_upload_true_on_204"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "abort_multipart_upload" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-9: multipart management"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; exactly ONE
abort implementation exists (grep for duplicated DELETE-with-uploadId code); numeric fields
come back as ints; `git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
