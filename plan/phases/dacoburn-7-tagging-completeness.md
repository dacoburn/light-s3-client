# Phase dacoburn-7: Tagging completeness — delete_object_tagging + bucket tagging

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-1 (buckets exist), dacoburn-4 (content_md5)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Round out tagging: objects can be untagged, and buckets get the full
get/put/delete tagging trio (object get/put tagging already exist).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-7: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

All in `light_s3_client/objects/__init__.py` (object-level) and
`light_s3_client/buckets/__init__.py` (bucket-level); XML via `xmltodict.unparse` following
the existing `put_object_tagging` body shape (`Tagging → TagSet → Tag` list):

- [ ] `def delete_object_tagging(self, Bucket: str, Key: str) -> bool` —
      `DELETE {url}?tagging`; `True` on 204, `False` on `BucketNotFound`
  - Acceptance: `grep -n "def delete_object_tagging" light_s3_client/objects/__init__.py`
- [ ] `def put_bucket_tagging(self, Bucket: str, Tags: dict) -> bool` —
      `PUT {server}/{Bucket}/?tagging`, XML body + `Content-MD5` header from
      `content_md5(body)` (required by S3), body passed as signing payload; `True` on 200/204
  - Acceptance: `grep -n "def put_bucket_tagging" light_s3_client/buckets/__init__.py` and
    `grep -n "content_md5" light_s3_client/buckets/__init__.py`; paste both
- [ ] `def get_bucket_tagging(self, Bucket: str) -> dict` — parse `Tagging/TagSet/Tag` into a
      plain `{key: value}` dict (single tag normalized from dict to list); `{}` when the
      bucket has no tag set (S3 answers 404 `NoSuchTagSet` → catch `BucketNotFound`)
  - Acceptance: `grep -n "def get_bucket_tagging" light_s3_client/buckets/__init__.py`
- [ ] `def delete_bucket_tagging(self, Bucket: str) -> bool` — `DELETE ?tagging`; `True` on 204
  - Acceptance: `grep -n "def delete_bucket_tagging" light_s3_client/buckets/__init__.py`
- [ ] Binding pattern in `light_s3_client/__init__.py` for all four (`setattr` +
      `TYPE_CHECKING` stubs)
  - Acceptance: `grep -c "delete_object_tagging\|put_bucket_tagging\|get_bucket_tagging\|delete_bucket_tagging" light_s3_client/__init__.py` → 8; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_delete_object_tagging_true_on_204`: mocked 204 → `is True`; URL ends with `?tagging`
  - [ ] `test_put_bucket_tagging_sends_md5_and_xml`: parse sent body →
        `assert parsed["Tagging"]["TagSet"]["Tag"] == [{"Key": "env", "Value": "prod"}, {"Key": "team", "Value": "core"}]`;
        headers include `Content-MD5`
  - [ ] `test_get_bucket_tagging_roundtrip`: mocked TagSet XML →
        `assert result == {"env": "prod"}` (exact; single-tag normalization covered)
  - [ ] `test_get_bucket_tagging_empty_when_no_tagset`: mocked 404 → `assert result == {}`

## Files

`light_s3_client/objects/__init__.py`, `light_s3_client/buckets/__init__.py`,
`light_s3_client/__init__.py`, `tests/test_unit.py` *(4 files — at the phase-size limit)* +
docs ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_delete_object_tagging_true_on_204|test_put_bucket_tagging_sends_md5_and_xml|test_get_bucket_tagging_roundtrip|test_get_bucket_tagging_empty_when_no_tagset"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "put_bucket_tagging" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-7: tagging completeness"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; bucket tagging
PUT carries a correct `Content-MD5` (recompute it from the sent body and compare); XML bodies
go through `xmltodict.unparse`; `git diff -- plan/ light-s3-client.md` shows only checkbox
flips + Status.
