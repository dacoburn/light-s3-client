# Phase dacoburn-2: list_buckets + list_objects pagination

> **Status:** planned — ready to implement
> **Depends on:** —
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** The client can enumerate all buckets, and `list_objects` returns ALL keys instead of
silently truncating at S3's 1000-key page limit (today it reads only the first page of
`list-type=2`).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-2: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] `def list_buckets(self) -> list` in `light_s3_client/buckets/__init__.py` —
      `GET {server}/`; parse `ListAllMyBucketsResult` with `xmltodict` and return the list of
      bucket **names** (`[]` when the account has none; a single bucket, which xmltodict
      returns as a dict, must still yield a one-element list)
  - Acceptance: `grep -n "def list_buckets" light_s3_client/buckets/__init__.py`
- [ ] `list_objects` pagination: keep the existing signature's behavior but extend it to
      `def list_objects(self, Bucket: str, Prefix: str, MaxKeys: Optional[int] = None) -> list`.
      Loop while the parsed `ListBucketResult` has `IsTruncated == "true"`, passing
      `continuation-token=<NextContinuationToken>` (URL-encoded with
      `urllib.parse.quote(token, safe="")`) on the next request; stop early once `MaxKeys`
      keys are collected (when given). Existing callers (`list_objects(bucket, prefix)`) must
      work unchanged.
  - Acceptance: `grep -n "continuation-token" light_s3_client/buckets/__init__.py` and
    `grep -n "IsTruncated" light_s3_client/buckets/__init__.py`; paste both
- [ ] Binding pattern for `list_buckets` + updated `list_objects` stub in
      `light_s3_client/__init__.py` (`setattr` + `TYPE_CHECKING` signatures)
  - Acceptance: `grep -n "list_buckets\|def list_objects" light_s3_client/__init__.py`; paste
- [ ] Named tests in `tests/test_unit.py` (offline, mock `requests.request`):
  - [ ] `test_list_buckets_returns_names`: mocked two-bucket XML →
        `assert result == ["bucket-a", "bucket-b"]` (exact)
  - [ ] `test_list_buckets_single_bucket_is_list`: mocked one-bucket XML →
        `assert result == ["only-bucket"]`
  - [ ] `test_list_objects_paginates`: two mocked pages (page 1: `IsTruncated=true` +
        `NextContinuationToken=tok1`, 2 keys; page 2: `IsTruncated=false`, 1 key) →
        `assert result == ["k1", "k2", "k3"]` AND the second request's URL contains the
        encoded token (assert with exact substring `continuation-token=tok1`)
  - [ ] `test_list_objects_respects_max_keys`: same two pages, `MaxKeys=2` →
        `assert result == ["k1", "k2"]` and only ONE HTTP call was made

## Files

`light_s3_client/buckets/__init__.py`, `light_s3_client/__init__.py`, `tests/test_unit.py`
(3 code files) + docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_list_buckets_returns_names|test_list_buckets_single_bucket_is_list|test_list_objects_paginates|test_list_objects_respects_max_keys"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "list_buckets" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-2: list_buckets + pagination"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; the pagination
loop keys off `IsTruncated`/`NextContinuationToken`; a two-arg `list_objects` call still works
(backward compatible); `git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
