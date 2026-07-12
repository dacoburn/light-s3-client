# Phase dacoburn-4: copy_object + delete_objects (batch) + signer support for extra headers

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-3
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Server-side copy and batch delete (up to 1000 keys per call). Both need two signer
capabilities the auth module lacks today, which this phase adds: signing extra `x-amz-*`
headers (SigV4 requires every `x-amz-*` header to be signed) and a `Content-MD5` helper
(required by the DeleteObjects API).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-4: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] Auth: extend the signature entry point to
      `def create_aws_signature(self, method, url, headers, payload=None, extra_signed_headers: Optional[dict] = None) -> dict`
      in `light_s3_client/auth/__init__.py`. V4 merges `extra_signed_headers` (lower-cased
      keys) into `signing_headers` so they are covered by the signature, and returns them in
      the result dict so callers can merge them into the request. V2 ignores them. Existing
      call sites keep working (parameter is optional).
  - Acceptance: `grep -n "extra_signed_headers" light_s3_client/auth/__init__.py`; paste
- [ ] Auth: `def content_md5(body: bytes) -> str` module function in
      `light_s3_client/auth/__init__.py` — base64-encoded MD5 digest (`hashlib.md5`), exactly
      what the `Content-MD5` header expects
  - Acceptance: `grep -n "def content_md5" light_s3_client/auth/__init__.py`
- [ ] `def copy_object(self, Bucket: str, Key: str, CopySource: str) -> bool` in
      `light_s3_client/objects/__init__.py` — `PUT {server}/{Bucket}/{Key}` with signed header
      `x-amz-copy-source: /<CopySource>` (accept both `"srcbucket/srckey"` and
      `{"Bucket": ..., "Key": ...}` boto3 forms); `True` on 200, `False` on `BucketNotFound`
  - Acceptance: `grep -n "x-amz-copy-source" light_s3_client/objects/__init__.py`
- [ ] `def delete_objects(self, Bucket: str, Delete: dict) -> dict` in
      `light_s3_client/objects/__init__.py` — boto3 shape
      `Delete={"Objects": [{"Key": "..."}, ...]}`; `POST {server}/{Bucket}/?delete` with an
      XML `<Delete>` body built via `xmltodict.unparse` (invariant), `Content-MD5` from
      `content_md5(body)`, body passed as the signing payload. Returns
      `{"Deleted": [...], "Errors": [...]}` parsed from the `DeleteResult` (missing sections →
      empty lists; single entries normalized to one-element lists). Reject >1000 keys with
      `ValueError` before any HTTP call.
  - Acceptance: `grep -n "def delete_objects" light_s3_client/objects/__init__.py` and
    `grep -n "1000" light_s3_client/objects/__init__.py`; paste both
- [ ] Binding pattern in `light_s3_client/__init__.py` for `copy_object` + `delete_objects`
      (`setattr` + `TYPE_CHECKING` stubs); `create_aws_signature` stub updated
  - Acceptance: `grep -n "copy_object\|delete_objects" light_s3_client/__init__.py` → 4 hits; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_copy_object_sends_signed_copy_source`: mocked 200 → `is True`; the request
        headers include `x-amz-copy-source` AND the `Authorization` header's
        `SignedHeaders=` list contains `x-amz-copy-source` (exact substring assert)
  - [ ] `test_delete_objects_builds_delete_xml`: two keys; parse the sent body with
        `xmltodict.parse` → `assert [o["Key"] for o in parsed["Delete"]["Object"]] == ["k1", "k2"]`;
        request headers include `Content-MD5`
  - [ ] `test_delete_objects_returns_deleted_and_errors`: mocked `DeleteResult` with one
        Deleted + one Error → exact-equality assert on the returned dict
  - [ ] `test_delete_objects_rejects_over_1000`: 1001 keys → `pytest.raises(ValueError)` and
        zero HTTP calls
  - [ ] `test_content_md5_known_vector`: `assert content_md5(b"hello") == "XUFAKrxLKna5cZ2REBfFkg=="` (exact)

## Files

`light_s3_client/auth/__init__.py`, `light_s3_client/objects/__init__.py`,
`light_s3_client/__init__.py`, `tests/test_unit.py` *(4 files — at the phase-size limit)* +
docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_copy_object_sends_signed_copy_source|test_delete_objects_builds_delete_xml|test_delete_objects_returns_deleted_and_errors|test_delete_objects_rejects_over_1000|test_content_md5_known_vector"` → 5; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "copy_object" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-4: copy_object + delete_objects + signer extras"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 5 named tests collected and green; `x-amz-copy-source`
appears in `SignedHeaders` (not merely in the request headers — attack this one specifically);
the Delete XML goes through `xmltodict.unparse`; the >1000 guard fires before any HTTP;
`git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
