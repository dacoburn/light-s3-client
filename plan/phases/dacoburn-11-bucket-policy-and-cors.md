# Phase dacoburn-11: Bucket policy + CORS configuration

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-1 (bucket lifecycle), dacoburn-4 (content_md5)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Manage bucket access policy (JSON) and CORS rules (XML) — get/put/delete for both.

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-11: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

All in `light_s3_client/buckets/__init__.py`. Policy is JSON (string in/out, boto3-style);
CORS is XML via `xmltodict` (boto3 dict shape `{"CORSRules": [...]}`):

- [ ] `def put_bucket_policy(self, Bucket: str, Policy: str) -> bool` —
      `PUT {server}/{Bucket}/?policy`, body = `Policy` (validated with `json.loads` first —
      `ValueError` on invalid JSON, no HTTP call), body as signing payload; `True` on 200/204
  - Acceptance: `grep -n "def put_bucket_policy" light_s3_client/buckets/__init__.py` and
    `grep -n "json.loads" light_s3_client/buckets/__init__.py`; paste both
- [ ] `def get_bucket_policy(self, Bucket: str) -> str` — `GET ?policy`; returns the policy
      JSON string; `""` when no policy exists (404 `NoSuchBucketPolicy` → catch `BucketNotFound`)
  - Acceptance: `grep -n "def get_bucket_policy" light_s3_client/buckets/__init__.py`
- [ ] `def delete_bucket_policy(self, Bucket: str) -> bool` — `DELETE ?policy`; `True` on 204
  - Acceptance: `grep -n "def delete_bucket_policy" light_s3_client/buckets/__init__.py`
- [ ] `def put_bucket_cors(self, Bucket: str, CORSConfiguration: dict) -> bool` —
      `PUT ?cors`; accepts boto3 shape `{"CORSRules": [{"AllowedMethods": [...],
      "AllowedOrigins": [...], ...}]}`, converts to `CORSConfiguration/CORSRule` XML via
      `xmltodict.unparse`, adds `Content-MD5` from `content_md5(body)`, body as signing payload
  - Acceptance: `grep -n "def put_bucket_cors" light_s3_client/buckets/__init__.py` and
    `grep -n "CORSRule" light_s3_client/buckets/__init__.py`; paste both
- [ ] `def get_bucket_cors(self, Bucket: str) -> dict` — returns the boto3 shape
      (`{"CORSRules": [...]}`, single rule normalized to a one-element list); `{}` when no
      CORS config (404 `NoSuchCORSConfiguration`)
  - Acceptance: `grep -n "def get_bucket_cors" light_s3_client/buckets/__init__.py`
- [ ] `def delete_bucket_cors(self, Bucket: str) -> bool` — `DELETE ?cors`; `True` on 204
  - Acceptance: `grep -n "def delete_bucket_cors" light_s3_client/buckets/__init__.py`
- [ ] Binding pattern in `light_s3_client/__init__.py` for all six (`setattr` +
      `TYPE_CHECKING` stubs)
  - Acceptance: `grep -c "bucket_policy\|bucket_cors" light_s3_client/__init__.py` → ≥12; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_put_bucket_policy_rejects_invalid_json`: `Policy="{not json"` →
        `pytest.raises(ValueError)`, zero HTTP calls
  - [ ] `test_get_bucket_policy_returns_string`: mocked policy JSON →
        `assert result == '{"Version": "2012-10-17", "Statement": []}'` (exact) and
        `assert result == ""` for mocked 404
  - [ ] `test_put_bucket_cors_xml_shape`: one rule with two methods; parse sent body →
        `assert parsed["CORSConfiguration"]["CORSRule"]["AllowedMethod"] == ["GET", "PUT"]`;
        headers include `Content-MD5`
  - [ ] `test_get_bucket_cors_normalizes_single_rule`: mocked single-rule XML →
        `assert isinstance(result["CORSRules"], list) and len(result["CORSRules"]) == 1`

## Files

`light_s3_client/buckets/__init__.py`, `light_s3_client/__init__.py`, `tests/test_unit.py`
(3 code files) + docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_put_bucket_policy_rejects_invalid_json|test_get_bucket_policy_returns_string|test_put_bucket_cors_xml_shape|test_get_bucket_cors_normalizes_single_rule"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "put_bucket_policy" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-11: bucket policy + CORS"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; the policy body
is signed (payload passed to `create_aws_signature`); CORS XML round-trips through `xmltodict`
(no string templates); `git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
