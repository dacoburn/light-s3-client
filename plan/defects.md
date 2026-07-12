# Defect Register — light-s3-client

> **Owned by the VERIFIER role exclusively.** Planners and implementers never edit this file —
> not even to mark a defect fixed (a completion claim is not the implementer's to certify). When
> a remediation phase closes a defect, the verifier that certifies that phase marks it
> `FIXED (<phase>)` here.

Statuses: **OPEN** / **FIXED (<phase>)** / **REGRESSED** (fixed, then partially undone).

## Verified implementation state

| Phase | Claimed | Verifier verdict |
|-------|---------|------------------|
| _(none yet)_ | — | No phase has reached verification. |

## Defect register

_(empty — no defects filed yet)_

| ID | Severity | Status | Defect | Where |
|----|----------|--------|--------|-------|
| — | — | — | — | — |

## Invariant watch-list (what the verifier attacks every phase)

Mirror of the invariants in [`architecture.md`](architecture.md), run against every phase's
diff; file a D-number on any violation:

- A `requests.*` call or hand-built `Authorization` header in a feature module (bypassing
  `do_request` / `create_aws_signature`).
- A new public method missing any of the four binding pieces: submodule function, `setattr`
  in `light_s3_client/__init__.py`, `TYPE_CHECKING` stub, docs in `README.md` +
  `ai-instructions.md`.
- A public method or parameter name that diverges from boto3's S3 client naming.
- A changed return type or error mapping on an already-shipped method without a recorded
  deviation in `architecture.md`.
- Anything resembling a real credential in the diff (only env vars, mocks, or the documented
  MinIO defaults are allowed).
- An acceptance test that needs the network, or a mock whose XML/headers deviate from real S3
  responses just enough to make the test pass.
- A new entry in `pyproject.toml` `dependencies` that the phase file did not authorize.
- String-concatenated/templated XML instead of `xmltodict.unparse`.
- A signed-header addition merged into request headers *after* `create_aws_signature` was
  called (the signature won't cover it).
