# Phase dacoburn-6: generate_presigned_url (SigV4 query-string signing)

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-5 (encode_key)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Time-limited shareable URLs for download and upload without exposing credentials —
SigV4 query-string presigning (`X-Amz-Algorithm=AWS4-HMAC-SHA256&...&X-Amz-Signature=...`).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-6: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] `def generate_presigned_url(self, ClientMethod: str, Params: dict, ExpiresIn: int = 3600) -> str`
      in `light_s3_client/auth/__init__.py` (boto3 signature). Supports
      `ClientMethod in ("get_object", "put_object")` mapping to GET/PUT; anything else raises
      `ValueError`. `Params = {"Bucket": ..., "Key": ...}`; key encoded via `encode_key`.
      Query params (canonically sorted, per `_build_canonical_querystring`):
      `X-Amz-Algorithm=AWS4-HMAC-SHA256`, `X-Amz-Credential=<access_key>/<scope>` (URL-encoded),
      `X-Amz-Date=<amzdate>`, `X-Amz-Expires=<ExpiresIn>`, `X-Amz-SignedHeaders=host`;
      canonical request uses payload hash literal `UNSIGNED-PAYLOAD`; signature appended as
      `X-Amz-Signature`. Reuses `_get_v4_signing_key` and `_build_canonical_querystring` —
      no duplicated signing code.
  - Acceptance: `grep -n "def generate_presigned_url" light_s3_client/auth/__init__.py` and
    `grep -n "UNSIGNED-PAYLOAD" light_s3_client/auth/__init__.py`; paste both
- [ ] `ExpiresIn` validated: `1 <= ExpiresIn <= 604800` (7 days, the SigV4 maximum), else
      `ValueError`
  - Acceptance: `grep -n "604800" light_s3_client/auth/__init__.py`
- [ ] Binding pattern in `light_s3_client/__init__.py` (`setattr` + `TYPE_CHECKING` stub)
  - Acceptance: `grep -n "generate_presigned_url" light_s3_client/__init__.py` → 2 hits; paste
- [ ] Named tests in `tests/test_unit.py` (offline — presigning needs no HTTP; freeze time by
      monkeypatching the datetime source so the whole URL is deterministic):
  - [ ] `test_presigned_url_deterministic`: fixed credentials/region/time → assert the FULL
        generated URL equals a precomputed constant (exact-equality; compute the constant once
        while implementing, then it pins the algorithm against regressions)
  - [ ] `test_presigned_url_contains_required_params`: parsed query of the result contains all
        five `X-Amz-*` params + `X-Amz-Signature` (exact key set assert)
  - [ ] `test_presigned_url_put_method`: `ClientMethod="put_object"` → canonical method PUT →
        signature differs from the get_object URL for identical inputs (`assert url_get != url_put`)
  - [ ] `test_presigned_url_rejects_bad_inputs`: `ClientMethod="delete_object"` →
        `pytest.raises(ValueError)`; `ExpiresIn=604801` → `pytest.raises(ValueError)`

## Files

`light_s3_client/auth/__init__.py`, `light_s3_client/__init__.py`, `tests/test_unit.py`
(3 code files) + docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_presigned_url_deterministic|test_presigned_url_contains_required_params|test_presigned_url_put_method|test_presigned_url_rejects_bad_inputs"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "generate_presigned_url" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-6: presigned URLs"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; the deterministic
URL test's constant reproduces byte-for-byte; signing helpers are reused, not copy-pasted
(diff the auth module for duplicated key-derivation code); `git diff -- plan/ light-s3-client.md`
shows only checkbox flips + Status.
