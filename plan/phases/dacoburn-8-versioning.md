# Phase dacoburn-8: Versioning — bucket versioning, list_object_versions, VersionId support

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-2 (pagination pattern), dacoburn-3 (get_object dict contract)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Version-aware S3 management: turn versioning on/off per bucket, enumerate versions,
and address a specific version on get/head/delete.

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-8: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] `def put_bucket_versioning(self, Bucket: str, Status: str) -> bool` in
      `light_s3_client/buckets/__init__.py` — `Status in ("Enabled", "Suspended")` else
      `ValueError`; `PUT {server}/{Bucket}/?versioning` with a `VersioningConfiguration` XML
      body via `xmltodict.unparse`, body as signing payload; `True` on 200
  - Acceptance: `grep -n "def put_bucket_versioning" light_s3_client/buckets/__init__.py`
- [ ] `def get_bucket_versioning(self, Bucket: str) -> dict` — `GET ?versioning`; returns
      `{"Status": "Enabled"}` / `{"Status": "Suspended"}` / `{}` (never-configured buckets
      return an empty `VersioningConfiguration`)
  - Acceptance: `grep -n "def get_bucket_versioning" light_s3_client/buckets/__init__.py`
- [ ] `def list_object_versions(self, Bucket: str, Prefix: str = "") -> list` — `GET
      ?versions&prefix=...`; returns a list of
      `{"Key": ..., "VersionId": ..., "IsLatest": ..., "DeleteMarker": bool}` covering both
      `Version` and `DeleteMarker` entries (single entries normalized to lists); paginates on
      `IsTruncated` via `key-marker`/`version-id-marker`
  - Acceptance: `grep -n "def list_object_versions" light_s3_client/buckets/__init__.py` and
    `grep -n "version-id-marker" light_s3_client/buckets/__init__.py`; paste both
- [ ] `VersionId: Optional[str] = None` parameter added to `get_object` and `head_object`
      (buckets module) and `delete_file` (files module) — when given, append
      `?versionId=<VersionId>` to the request URL (before signing). Existing positional calls
      keep working.
  - Acceptance: `grep -n "versionId" light_s3_client/buckets/__init__.py light_s3_client/files/__init__.py`; paste
- [ ] Binding pattern in `light_s3_client/__init__.py`: `setattr` for the three new methods +
      stubs updated for all five signatures
  - Acceptance: `grep -n "put_bucket_versioning\|get_bucket_versioning\|list_object_versions" light_s3_client/__init__.py` → 6 hits; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_put_bucket_versioning_body`: parse sent body →
        `assert parsed["VersioningConfiguration"]["Status"] == "Enabled"`; invalid status →
        `pytest.raises(ValueError)` with zero HTTP calls
  - [ ] `test_get_bucket_versioning_unconfigured`: mocked empty config XML → `assert result == {}`
  - [ ] `test_list_object_versions_mixed_entries`: mocked XML with one `Version` + one
        `DeleteMarker` → exact-equality assert on the two returned dicts (incl.
        `DeleteMarker: True/False`)
  - [ ] `test_delete_file_with_version_id`: `delete_file(b, k, VersionId="v1")` → requested
        URL contains exact substring `?versionId=v1`

## Files

`light_s3_client/buckets/__init__.py`, `light_s3_client/files/__init__.py`,
`light_s3_client/__init__.py`, `tests/test_unit.py` *(4 files — at the phase-size limit)* +
docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_put_bucket_versioning_body|test_get_bucket_versioning_unconfigured|test_list_object_versions_mixed_entries|test_delete_file_with_version_id"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "list_object_versions" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-8: versioning support"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; `?versionId=` is
part of the URL **before** signing (attack: append-after-sign breaks the signature);
back-compat positional calls to `get_object`/`head_object`/`delete_file` still pass existing
tests; `git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
