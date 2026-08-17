# Local OpenSPG + KAG deployment

## Outcome

Run the official OpenSPG/KAG Server `latest` image locally in the shared Docker Compose project
`tidewise-app` and consume the independently operated `tidewise-infra` middleware. The official
image, including its bundled KAG toolkit, is the sole runtime release.

## Scope and ownership

- OpenSPG Server owns the Web UI, API, schema, builder, graph and reasoning services.
- MySQL owns OpenSPG product metadata.
- Neo4j owns graph, search and vector indexes used by OpenSPG.
- MinIO owns uploaded source files.
- The KAG Python toolkit bundled in the official Server image is the default developer client.

This first installation does not integrate Tidewise services, migrate previous Semantica data,
configure an LLM/embedding provider, or claim production readiness.

## Deployment decisions

- Use `spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest` exactly as published by
  OpenSPG and pull it before every service start.
- Do not build OpenSPG or KAG from source, maintain an alternate runtime image, or inject a
  replacement JAR/wheel into the official image.
- Use Compose project name `tidewise-app`, service name `server`, and fixed local container name
  `reason-server`.
- Keep MySQL, Neo4j and MinIO plus their existing persistent volumes in `tidewise-infra`.
- Preserve the official `release-openspg-neo4j` network alias because OpenSPG seeds that hostname
  into the `KAG_ENV` project defaults.
- Bind all published ports to `127.0.0.1`.
- Keep the official local demo credentials; never reuse them outside this workstation.
- Keep extension source, runtime configuration, data and credentials outside the official image;
  do not patch its installed Python packages in place.

## Acceptance seam

The installation is accepted when:

1. Docker reports `reason-server` healthy while MySQL, Neo4j and MinIO remain healthy in
   `tidewise-infra`.
2. `http://127.0.0.1:8887` returns the OpenSPG/KAG product page.
3. The official Server container can execute `kag --help` and `knext --help`.

Model-backed extraction and question answering require a separate generation-model and embedding-
model configuration after the base stack is healthy.

## Rollback and recovery

- Stop and remove only Reason Server with `./scripts/stop.sh`.
- Shared middleware data is never removed from this repository.
- Restarting pulls the current official `latest` image; the image digest printed by
  `scripts/verify-runtime.sh` identifies the exact artifact used for a run.
