# Phase dacoburn-12: ACLs — canned ACLs for objects and buckets

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-1 (buckets), dacoburn-4 (extra_signed_headers)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Read and set access control via **canned ACLs** (`private`, `public-read`, etc.) on
objects and buckets. Full grant-level ACL editing is out of scope (cut a later phase if ever
needed — AWS itself steers toward policies).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-12: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

Canned ACL allow-list (module constant `CANNED_ACLS` in `light_s3_client/objects/__init__.py`):
`private`, `public-read`, `public-read-write`, `authenticated-read`, `aws-exec-read`,
`bucket-owner-read`, `bucket-owner-full-control`. Invalid values → `ValueError`, no HTTP call.

- [ ] `def put_object_acl(self, Bucket: str, Key: str, ACL: str) -> bool` in
      `light_s3_client/objects/__init__.py` — `PUT {url}?acl` with **signed** header
      `x-amz-acl: <ACL>` (via `extra_signed_headers`); `True` on 200
  - Acceptance: `grep -n "def put_object_acl" light_s3_client/objects/__init__.py` and
    `grep -n "x-amz-acl" light_s3_client/objects/__init__.py`; paste both
- [ ] `def get_object_acl(self, Bucket: str, Key: str) -> dict` — `GET {url}?acl`; parse
      `AccessControlPolicy` into `{"Owner": {...}, "Grants": [...]}` (boto3 shape; single
      grant normalized to a list); `{}` on `BucketNotFound`
  - Acceptance: `grep -n "def get_object_acl" light_s3_client/objects/__init__.py`
- [ ] `def put_bucket_acl(self, Bucket: str, ACL: str) -> bool` and
      `def get_bucket_acl(self, Bucket: str) -> dict` in
      `light_s3_client/buckets/__init__.py` — same contracts against `{server}/{Bucket}/?acl`
      (import `CANNED_ACLS` from the objects module — one allow-list, not two)
  - Acceptance: `grep -n "def put_bucket_acl\|def get_bucket_acl" light_s3_client/buckets/__init__.py`
    and `grep -rn "CANNED_ACLS" light_s3_client/` → exactly one definition; paste both
- [ ] Binding pattern in `light_s3_client/__init__.py` for all four (`setattr` +
      `TYPE_CHECKING` stubs)
  - Acceptance: `grep -c "object_acl\|bucket_acl" light_s3_client/__init__.py` → ≥8; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_put_object_acl_signed_header`: `ACL="public-read"` → request headers include
        `x-amz-acl: public-read` AND `SignedHeaders=` contains `x-amz-acl` (exact substrings)
  - [ ] `test_put_object_acl_rejects_invalid`: `ACL="everyone"` →
        `pytest.raises(ValueError)`, zero HTTP calls
  - [ ] `test_get_object_acl_parses_grants`: mocked `AccessControlPolicy` XML with one grant →
        `assert isinstance(result["Grants"], list)` and exact-equality on the grantee dict
  - [ ] `test_bucket_acl_roundtrip_shapes`: `put_bucket_acl` hits `?acl` on the bucket URL
        (exact substring `f"/{bucket}/?acl"`); `get_bucket_acl` mocked → returns
        `Owner` + `Grants` keys

## Files

`light_s3_client/objects/__init__.py`, `light_s3_client/buckets/__init__.py`,
`light_s3_client/__init__.py`, `tests/test_unit.py` *(4 files — at the phase-size limit)* +
docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_put_object_acl_signed_header|test_put_object_acl_rejects_invalid|test_get_object_acl_parses_grants|test_bucket_acl_roundtrip_shapes"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "put_object_acl" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-12: canned ACLs"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; `x-amz-acl` is
in `SignedHeaders` (not just present); exactly one `CANNED_ACLS` definition repo-wide;
`git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
