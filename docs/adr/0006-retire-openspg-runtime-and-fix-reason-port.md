# ADR 0006: Retire OpenSPG runtime and fix the Reasoning Server port

- Status: Accepted
- Date: 2026-08-25

## Context

OpenSPG and KAG are no longer deployed as part of Tidewise Reason. Keeping local and dormant UAT
Compose definitions, compatibility overrides and lifecycle scripts would preserve an executable
path that the product no longer supports. The active Reasoning Server also needs a stable endpoint
for Agent OS, Swagger and operational checks.

## Decision

- Remove the local OpenSPG Compose project, its KAG compatibility override and its lifecycle and
  verification scripts.
- Remove the dormant OpenSPG UAT deployment bundle. This repository has no UAT deployment workflow.
- Do not delete Docker images, database state or named volumes as part of this source change.
- Retain historical OpenSPG design and Schema material only as non-executable research records.
- Keep the active runtime in the `tidewise-reasoning` Compose project with the `api` and `neo4j`
  services.
- Fix the Reasoning Server binding in `infra/graphiti/compose.yaml` to
  `127.0.0.1:8890:8890`. `REASON_API_PORT` is not part of the runtime configuration contract.
- Publish the FastAPI OpenAPI document at `/openapi.json` and Swagger UI at `/docs` on that fixed
  endpoint.

## Consequences

- Agent OS and local operators use `http://127.0.0.1:8890` without per-environment port discovery.
- Port conflicts fail explicitly instead of silently moving the Reasoning Server to another port.
- OpenSPG cannot be restarted from this repository without reverting this decision or introducing a
  separately reviewed runtime.
- Historical OpenSPG documents do not authorize or configure a live OpenSPG deployment.

## Supersedes

This ADR supersedes ADR 0001's decision to retain a reversibly startable OpenSPG runtime and ADR
0002's reference to the legacy `reason-server`. Their Graphiti and controlled-ingestion decisions
remain in force.
