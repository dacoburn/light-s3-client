# Architecture Reference — light-s3-client

> Read this before implementing any phase. Phase files live in [`phases/`](phases/); session
> rules in [`working-agreement.md`](working-agreement.md); found defects in
> [`defects.md`](defects.md); the phase index at the repo root in
> [`../light-s3-client.md`](../light-s3-client.md).

## Project overview

**Purpose:** A lightweight, boto3-free Python client for Amazon S3 and S3-compatible services
(MinIO, etc.). It speaks the S3 REST API directly over `requests`, signs requests itself
(AWS Signature V4 by default, V2 legacy), and mirrors boto3's method/parameter naming so it can
be a drop-in for the subset it implements.

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python ≥ 3.8 (classifiers through 3.13) |
| HTTP | `requests>=2.31,<3` — the ONLY transport |
| XML | `xmltodict~=0.13.0` — the ONLY XML parser/builder |
| Tests | pytest; unit tests mock `requests` (offline), integration tests target MinIO via `docker-compose.yml` |
| Build/release | Hatch + hatchling; trusted publishing via GitHub Actions (see `README-dev.md`) |
| Versioning | `light_s3_client/version.py` `__version__`; pre-commit hook + CI enforce a bump per PR |

No new runtime dependencies may be added by a phase unless the phase file says so explicitly.

## Module layout & the method-binding pattern

```
light_s3_client/
├── __init__.py        # do_request() + Client class + setattr bindings + TYPE_CHECKING stubs
├── exceptions.py      # S3Error base; BucketNotFound, AccessDeniedToBucket, UnknownBucketError
├── version.py         # __version__
├── auth/__init__.py       # create_aws_signature (V2/V4), _get_server_url, build_vars
├── buckets/__init__.py    # bucket-level ops: list_objects, get_object, head_object, get_bucket_keys
├── files/__init__.py      # file ops: download_file, upload_fileobj, delete_file
├── multipart/__init__.py  # upload_file_multipart, _abort_multipart_upload
└── objects/__init__.py    # put_object_tagging, get_object_tagging
```

`Client` methods are **not** defined on the class. Each is a plain function in a submodule
taking `self` first, then bound in `__init__.py`:

```python
setattr(Client, 'list_objects', buckets_module.list_objects)
```

and mirrored as a stub in the `if TYPE_CHECKING:` block inside `Client` so Pylance resolves it.
**Every new public method needs all four pieces in the same phase:**

1. the function in the correct submodule (with docstring),
2. the `setattr` binding in `light_s3_client/__init__.py`,
3. the `TYPE_CHECKING` stub with the exact signature,
4. documentation in `README.md` + `ai-instructions.md`.

## Request flow

Every operation builds a URL from `self._get_server_url()` (`https://s3-{region}.s3.amazonaws.com`
or the `server` override), gets auth headers from `self.create_aws_signature(method, url,
headers, payload)`, and performs the HTTP call through the module-level `do_request()`
(bound as a `staticmethod`). `do_request` converts transport failures into a synthetic 500
`Response`, passes 200/204 through, and maps error statuses to exceptions:

| Status | Result |
|--------|--------|
| 200, 204 | returns the `Response` |
| 403 | raises `AccessDeniedToBucket` |
| 404 | raises `BucketNotFound` |
| other | raises `UnknownBucketError` (with parsed S3 `<Error><Code>/<Message>` when possible) |

Boolean-returning convenience methods (e.g. `get_object`, `delete_file`) catch the expected
not-found exception and return `False` rather than letting it propagate — follow that pattern.

## Signing (auth module)

- **V4 (default):** canonical request over `host`, `x-amz-content-sha256`, `x-amz-date`;
  bytes/str payloads are hashed, file-like payloads use `UNSIGNED-PAYLOAD`; query strings are
  canonicalized via `_build_canonical_querystring` (handles valueless params like `?uploads`).
  Any new header that must be signed has to be added to the `signing_headers` dict — headers
  merged after signing are NOT covered by the signature.
- **V2 (legacy):** kept for old S3-compatible services; selected via
  `Client(signature_version="v2")`. New features are NOT required to support V2 unless the
  phase says so, but must not break it.

## Testing conventions

- `tests/test_unit.py` — offline, mocks `requests` (`unittest.mock`). **This is the acceptance
  suite**; every phase adds named tests here (or in a new `tests/test_<area>.py`, offline).
- `tests/test_integration.py` — ordered end-to-end run against MinIO
  (`docker-compose up -d`, credentials `minioadmin`/`minioadmin`). Never a phase gate.
- Run: `python -m pytest tests/test_unit.py -q`.

## Invariants (what the verifier attacks every phase)

- **Single transport / single signer.** No `requests.get/post/...` calls and no hand-built
  `Authorization` headers anywhere outside `do_request` / the auth module. Check:
  `grep -rn "requests\." light_s3_client/ --include=__init__.py | grep -v "light_s3_client\\\\__init__\|requests.request\|requests.exceptions\|import"` → no feature-module hits.
- **The four-piece binding pattern** (submodule function, `setattr`, `TYPE_CHECKING` stub,
  docs) is complete for every public method added — a missing stub or missing `setattr` is a
  defect even if a direct call happens to work.
- **boto3-compatible surface.** Public method names and parameter names match boto3's S3
  client (`Bucket`, `Key`, `Prefix`, `VersionId`, PascalCase kwargs). No invented spellings.
- **Error mapping is stable.** 403→`AccessDeniedToBucket`, 404→`BucketNotFound`,
  other→`UnknownBucketError`; all custom exceptions inherit `S3Error`. Existing return types
  of shipped methods never change silently (breaking changes need an explicit phase decision
  recorded under Deviations below).
- **No secrets in the repo.** Credentials only from env / test mocks / documented MinIO
  defaults. Check the diff for anything that looks like a real key.
- **Offline acceptance.** Every acceptance test runs with no network. A unit test that only
  passes because its mock deviates from real S3 XML/headers is a wrong test.
- **No new runtime dependencies** unless the phase file explicitly allows it
  (`pyproject.toml` `dependencies` unchanged otherwise).
- **XML in/out goes through `xmltodict`** (`parse`/`unparse`) — no string-templated XML bodies.

## Deviations / open questions

- **`get_object` returns `bool` today** (existence check), which diverges from boto3 (returns
  the object). Phase dacoburn-3 resolves this: existence moves to `object_exists`, and
  `get_object` becomes content retrieval. Recorded here so no other phase "fixes" it ad hoc.

When implementation reveals this file is wrong or ambiguous, the **planner** records the dated
resolution here; the **verifier** files defects in [`defects.md`](defects.md). Implementers
never edit this file.
