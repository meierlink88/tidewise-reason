# Pipeline Standard

This repository uses **Pipeline** as the only name for a complete business process. Do not introduce
`Workflow` classes, files or parallel orchestration interfaces.

## Model

- A Pipeline owns ordering, durable run state, idempotency, retries, terminal outcomes and external
  side effects for one business process.
- A Stage is an internal step owned by one Pipeline. A Stage is not a business entry and must not be
  exported from the capability package.
- API and CLI are entry adapters. They validate their transport, then call the same Pipeline
  interface. They contain no business decisions.
- A Worker only drives pending Pipeline runs. A Store only persists Pipeline run state. Runtime code
  only composes dependencies.

## Required source layout

```text
<area>/<capability>/
  pipeline.py
  contracts.py
  api.py                 # when HTTP is supported
  cli.py                 # when CLI is supported
  worker.py              # when asynchronous execution is supported
  store.py               # when durable state is required
  stages/                # internal only
  adapters.py            # provider seams, not business entries
```

Only the Pipeline class is exported from the capability package. Callers, evaluations and tests at
the business seam must not invoke a Stage or provider write directly.

## Interface

A durable asynchronous Pipeline normally exposes only:

```python
submit(request) -> Acceptance
get_status(run_id) -> Status | None
process_pending(limit=...) -> int
```

The exact transport may differ, but API and CLI must reuse these methods and the same contracts.

## Side-effect rule

Irreversible side effects must be checkpointed before the call and resumed from the stored stage.
Retries must not repeat completed upstream side effects. A downstream provider adapter cannot be
used as an alternate publication path.

## Verification

Every Pipeline must prove:

1. API and CLI submit through the same Pipeline interface.
2. request replay is idempotent;
3. a semantic duplicate produces no downstream write;
4. a downstream retry resumes without repeating completed upstream writes;
5. no evaluation or production caller imports an internal Stage as a business entry.
