# Phase dacoburn-5: Key URL-encoding correctness + user metadata on uploads

> **Status:** planned — ready to implement
> **Depends on:** dacoburn-4 (extra_signed_headers)
> **Read first:** [architecture.md](../architecture.md), [working-agreement.md](../working-agreement.md)
> Work ONLY on this phase. Touch ONLY the files in its **Files** list.

**Goal:** Keys containing spaces, `+`, `#`, `?`, or non-ASCII characters currently produce
broken or mis-signed URLs because keys are interpolated raw into the URL. Fix encoding at the
single URL-construction point, and let uploads carry user metadata (`x-amz-meta-*`) — signed,
as SigV4 requires (the existing unsigned `x-amz-server-side-encryption` header is folded into
the signed set at the same time).

## Step 0 — lifecycle (before any code)

- [ ] `git add -A && git commit -m "pre dacoburn-5: baseline"`; paste `git log --oneline -1`
- [ ] `python -m pytest tests/test_unit.py -q` — record the baseline test count in `ai-updates.md`

## Implementation

- [ ] `def encode_key(key: str) -> str` module function in `light_s3_client/auth/__init__.py`
      — `urllib.parse.quote(key, safe="/")`; `build_vars` uses it for the URL (the returned
      `s3_key` stays unencoded)
  - Acceptance: `grep -n "def encode_key" light_s3_client/auth/__init__.py`
- [ ] Every URL built from a Key in `light_s3_client/files/__init__.py` goes through
      `build_vars`/`encode_key` — no raw `f"...{Key}"` URL interpolation remains in the module
  - Acceptance: `grep -n "encode_key\|build_vars" light_s3_client/files/__init__.py`; paste
    (and `grep -n 'f"{self._get_server_url()}' light_s3_client/files/__init__.py` → no hits
    that embed a raw Key)
- [ ] `upload_fileobj` extended to
      `def upload_fileobj(self, Fileobj, Bucket: str, Key: str, Metadata: Optional[dict] = None)`
      — each entry becomes a signed `x-amz-meta-<lowercased-name>` header via
      `extra_signed_headers`; the existing `x-amz-server-side-encryption` header moves into
      `extra_signed_headers` too. Two-/three-arg calls keep working unchanged.
  - Acceptance: `grep -n "x-amz-meta" light_s3_client/files/__init__.py` and
    `grep -n "extra_signed_headers" light_s3_client/files/__init__.py`; paste both
- [ ] `head_object` surfaces returned user metadata: any `x-amz-meta-*` response header lands
      in the returned dict under a `"Metadata"` key (`{name-without-prefix: value}`)
  - Acceptance: `grep -n '"Metadata"' light_s3_client/buckets/__init__.py`
- [ ] Stubs updated in `light_s3_client/__init__.py` (`upload_fileobj` new signature)
  - Acceptance: `grep -n "Metadata" light_s3_client/__init__.py`; paste
- [ ] Named tests in `tests/test_unit.py` (offline):
  - [ ] `test_encode_key_special_chars`: `assert encode_key("dir/my file+v2#1.txt") == "dir/my%20file%2Bv2%231.txt"` (exact)
  - [ ] `test_download_url_is_encoded`: `download_file` for key `"a b.txt"` → the requested
        URL ends with `"/a%20b.txt"` (exact substring)
  - [ ] `test_upload_metadata_headers_signed`: upload with `Metadata={"Owner": "team-a"}` →
        request headers include `x-amz-meta-owner: team-a` AND `SignedHeaders=` contains
        `x-amz-meta-owner` (exact substring asserts)
  - [ ] `test_head_object_returns_metadata`: mocked 200 with `x-amz-meta-owner: team-a` →
        `assert result["Metadata"] == {"owner": "team-a"}` (exact)

## Files

`light_s3_client/auth/__init__.py`, `light_s3_client/files/__init__.py`,
`light_s3_client/buckets/__init__.py`, `light_s3_client/__init__.py`, `tests/test_unit.py`
*(5 files — OVER the normal limit; approved as a unit because the encoding fix is one change
with call sites in three modules. If it grows further, split metadata support out.)* + docs
ride-along: `README.md`, `ai-instructions.md`.

## Step Z — lifecycle (after all code)

- [ ] `python -m pytest tests/test_unit.py --collect-only -q | grep -cE "test_encode_key_special_chars|test_download_url_is_encoded|test_upload_metadata_headers_signed|test_head_object_returns_metadata"` → 4; paste
- [ ] Full `python -m pytest tests/test_unit.py -q` — count EXCEEDS baseline; paste FULL output
- [ ] Docs updated: `grep -c "Metadata" README.md ai-instructions.md` → ≥1 in each; paste
- [ ] `git add -A && git commit -m "dacoburn-5: key encoding + upload metadata"`; paste `git log --oneline -1`
- [ ] Set this file's Status + the index row in `light-s3-client.md` to `awaiting verification`

**Acceptance (verification session):** the 4 named tests collected and green; a key with a
space produces an encoded URL whose signature verifies against the encoded canonical URI
(attack: sign-then-encode mismatches); metadata headers appear in `SignedHeaders`;
`git diff -- plan/ light-s3-client.md` shows only checkbox flips + Status.
