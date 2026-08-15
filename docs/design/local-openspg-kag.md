# Local OpenSPG + KAG deployment

## Outcome

Run the official OpenSPG/KAG Server locally in the shared Docker Compose project `tidewise-app`,
consume the independently operated `tidewise-infra` middleware, and install the KAG 0.8.0
developer toolkit in an isolated Python 3.10 environment.

## Scope and ownership

- OpenSPG Server owns the Web UI, API, schema, builder, graph and reasoning services.
- MySQL owns OpenSPG product metadata.
- Neo4j owns graph, search and vector indexes used by OpenSPG.
- MinIO owns uploaded source files.
- The KAG Python toolkit is an optional local developer client of OpenSPG Server.

This first installation does not integrate Tidewise services, migrate previous Semantica data,
configure an LLM/embedding provider, or claim production readiness.

## Deployment decisions

- Base the stack on the official OpenSPG 0.8 Compose topology.
- Use Compose project name `tidewise-app`, service name `server`, and fixed local container name
  `reason-server`.
- Keep MySQL, Neo4j and MinIO plus their existing persistent volumes in `tidewise-infra`.
- Mount `overrides/kag/kag_thinker.yaml` read-only because the pinned Server image requires the
  `KAGModelPlanner.rewrite_prompt` constructor setting but omits it from its bundled thinker
  pipeline. Verify this compatibility seam with `scripts/check-kag-thinker-pipeline.sh`.
- Preserve the official `release-openspg-neo4j` network alias because OpenSPG seeds that hostname
  into the `KAG_ENV` project defaults.
- Bind all published ports to `127.0.0.1`.
- Add named volumes so container recreation does not discard local data.
- Keep the official local demo credentials; never reuse them outside this workstation.
- Pin the KAG source checkout to tag `v0.8.0`.
- Keep downloaded source, Python environment and runtime data outside Git.

## Acceptance seam

The installation is accepted when:

1. Docker reports `reason-server` healthy while MySQL, Neo4j and MinIO remain healthy in
   `tidewise-infra`.
2. `http://127.0.0.1:8887` returns the OpenSPG/KAG product page.
3. The local Python environment can execute `kag --help` and `knext --help`.

Model-backed extraction and question answering require a separate generation-model and embedding-
model configuration after the base stack is healthy.

## Rollback and recovery

- Stop and remove only Reason Server with `./scripts/stop.sh`.
- Shared middleware data is never removed from this repository.
- The previous repository worktree is recoverable from the Git stash named
  `pre-openspg-kag-rebuild-2026-08-09`.
